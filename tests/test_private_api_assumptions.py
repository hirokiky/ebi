"""Pin the private boto3/botocore APIs that ebi.core depends on.

ebi.core.setup_session relies on:

* boto3._get_default_session()                       (private function)
* boto3.Session._session                             (private attribute,
  the underlying botocore session)
* botocore_session.get_config_variable('profile')    (returns None when
  no profile is configured, the env var value when AWS_PROFILE is set)

If a boto3/botocore upgrade ever breaks these assumptions, these tests
fail and point straight at the contract instead of producing an obscure
runtime error in ebi.
"""

import boto3
import botocore.session


class TestGetDefaultSession:
    def test_boto3_exposes_get_default_session(self):
        assert hasattr(boto3, '_get_default_session')
        assert callable(boto3._get_default_session)

    def test_returns_the_session_created_by_setup_default_session(self):
        boto3.setup_default_session()
        session = boto3._get_default_session()
        assert isinstance(session, boto3.Session)
        assert session is boto3.DEFAULT_SESSION

    def test_session_wraps_a_botocore_session(self):
        boto3.setup_default_session()
        session = boto3._get_default_session()
        assert isinstance(session._session, botocore.session.Session)


class TestProfileConfigVariable:
    def test_profile_is_none_when_not_configured(self):
        """The very assumption behind the PR #27 fix.

        With no --profile, no AWS_PROFILE and no config files, the
        botocore config variable 'profile' must be None so that ebi
        skips ebaws.set_profile entirely.
        """
        boto3.setup_default_session()
        session = boto3._get_default_session()
        assert session._session.get_config_variable('profile') is None

    def test_profile_name_falls_back_to_default(self):
        """Documents why Session.profile_name cannot be used instead.

        profile_name is 'default' even when nothing is configured;
        propagating it to ebcli is exactly the regression fixed by
        PR #27 (ProfileNotFound for env-only credentials).
        """
        boto3.setup_default_session()
        session = boto3._get_default_session()
        assert session.profile_name == 'default'

    def test_profile_reflects_aws_profile_env_var(
            self, monkeypatch, write_credentials_file):
        # The profile must exist: boto3.Session.__init__ resolves scoped
        # config during _setup_loader and raises ProfileNotFound otherwise.
        write_credentials_file('envprofile', 'AKIAENVPROFILE', 'env-secret')
        monkeypatch.setenv('AWS_PROFILE', 'envprofile')
        boto3.setup_default_session()
        session = boto3._get_default_session()
        assert session._session.get_config_variable('profile') == 'envprofile'

    def test_profile_reflects_explicit_profile_name(
            self, write_credentials_file):
        write_credentials_file('cliprofile', 'AKIACLIPROFILE', 'cli-secret')
        boto3.setup_default_session(profile_name='cliprofile')
        session = boto3._get_default_session()
        assert session._session.get_config_variable('profile') == 'cliprofile'
