"""Regression tests for ebi.core.setup_session (used by main()).

These pin the fix from PR #27: when no profile is configured anywhere,
ebi must NOT call ebcli.lib.aws.set_profile, because ebcli would then
pin botocore to the 'default' profile and credentials coming only from
environment variables (e.g. CI with OIDC-issued credentials) would fail
with ProfileNotFound.
"""

import boto3

from ebcli.lib import aws as ebaws

from ebi import core


class TestEnvOnlyCredentials:
    """Credentials only via env vars, no ~/.aws files, no profile."""

    def _setup_env(self, monkeypatch):
        monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'AKIATESTEXAMPLE')
        monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test-secret')
        monkeypatch.setenv('AWS_DEFAULT_REGION', 'ap-northeast-1')

    def test_no_profile_is_propagated_to_ebcli(self, monkeypatch):
        self._setup_env(monkeypatch)

        core.setup_session()

        # The regression: main() used to call set_profile('default')
        # unconditionally via session.profile_name.
        assert ebaws._profile is None

    def test_credentials_resolve_through_ebcli_session(self, monkeypatch):
        """ebcli's botocore session must resolve env credentials.

        This is the same in-process path used by
        appversion.make_application_version via ebcli.lib.s3 /
        elasticbeanstalk. Before the fix this raised ProfileNotFound.
        No network access happens during credential resolution.
        """
        self._setup_env(monkeypatch)

        core.setup_session()

        creds = ebaws._get_botocore_session().get_credentials()
        assert creds is not None
        assert creds.access_key == 'AKIATESTEXAMPLE'
        assert creds.secret_key == 'test-secret'

    def test_region_is_propagated_to_ebcli(self, monkeypatch):
        self._setup_env(monkeypatch)

        core.setup_session()

        assert ebaws.get_region_name() == 'ap-northeast-1'


class TestProfileFromEnvVar:
    """AWS_PROFILE must still be honored and propagated to ebcli."""

    def test_aws_profile_env_var_propagates(
            self, monkeypatch, write_credentials_file):
        write_credentials_file('envprofile', 'AKIAENVPROFILE', 'env-secret')
        monkeypatch.setenv('AWS_PROFILE', 'envprofile')

        core.setup_session()

        assert ebaws._profile == 'envprofile'

    def test_aws_profile_credentials_resolve_through_ebcli_session(
            self, monkeypatch, write_credentials_file):
        write_credentials_file('envprofile', 'AKIAENVPROFILE', 'env-secret')
        monkeypatch.setenv('AWS_PROFILE', 'envprofile')

        core.setup_session()

        creds = ebaws._get_botocore_session().get_credentials()
        assert creds is not None
        assert creds.access_key == 'AKIAENVPROFILE'


class TestExplicitProfileOption:
    """--profile on the command line (passed as setup_session(profile=...))."""

    def test_explicit_profile_propagates(self, write_credentials_file):
        write_credentials_file('cliprofile', 'AKIACLIPROFILE', 'cli-secret')

        core.setup_session(profile='cliprofile')

        assert ebaws._profile == 'cliprofile'
        assert boto3._get_default_session().profile_name == 'cliprofile'

    def test_explicit_profile_credentials_resolve_through_ebcli_session(
            self, write_credentials_file):
        write_credentials_file('cliprofile', 'AKIACLIPROFILE', 'cli-secret')

        core.setup_session(profile='cliprofile')

        creds = ebaws._get_botocore_session().get_credentials()
        assert creds is not None
        assert creds.access_key == 'AKIACLIPROFILE'

    def test_explicit_region_propagates(self, monkeypatch):
        monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'AKIATESTEXAMPLE')
        monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test-secret')

        core.setup_session(region='eu-west-1')

        assert ebaws.get_region_name() == 'eu-west-1'
