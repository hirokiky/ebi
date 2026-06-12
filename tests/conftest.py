"""Shared fixtures isolating tests from real AWS config and global state.

ebi/core.py wires the default boto3 session into ebcli's module-level
state (ebcli.lib.aws), so every test must start from a clean slate:

* environment variables that influence credential/profile resolution,
* boto3.DEFAULT_SESSION (set by boto3.setup_default_session),
* ebcli.lib.aws module globals (_profile, _region_name, the cached
  botocore session, client cache, ...) -- reset via its own _flush()
  helper, plus _profile_env_var/_endpoint_url which _flush() skips.

No test here performs network access: resolving credentials from
environment variables or from a credentials file is purely local.
"""

import boto3
import pytest

from ebcli.lib import aws as ebaws

# Environment variables that affect profile/credential/region resolution.
AWS_ENV_VARS = (
    'AWS_PROFILE',
    'AWS_DEFAULT_PROFILE',
    'AWS_EB_PROFILE',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_SESSION_TOKEN',
    'AWS_SECURITY_TOKEN',
    'AWS_DEFAULT_REGION',
    'AWS_REGION',
    'AWS_CONFIG_FILE',
    'AWS_SHARED_CREDENTIALS_FILE',
)


def _reset_global_state():
    # boto3 caches the default session at module level.
    boto3.DEFAULT_SESSION = None
    # ebcli.lib.aws provides _flush() "for resetting tests only"; it
    # resets _api_clients, _profile, _id, _key, _region_name,
    # _verify_ssl and the cached botocore session.
    ebaws._flush()
    # Not covered by _flush(); restore the import-time defaults.
    ebaws._profile_env_var = 'AWS_EB_PROFILE'
    ebaws._endpoint_url = None


@pytest.fixture(autouse=True)
def isolated_aws_env(monkeypatch, tmp_path):
    """Isolate each test from real ~/.aws files, env vars and globals.

    HOME points at an empty temporary directory, so no real config or
    credentials files leak in; tests opt in to credentials via env vars
    or by writing files under this HOME.
    """
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setenv('HOME', str(home))
    for var in AWS_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    _reset_global_state()
    yield home
    _reset_global_state()


@pytest.fixture
def write_credentials_file(isolated_aws_env):
    """Return a helper writing a profile into ~/.aws/credentials."""

    def _write(profile, access_key, secret_key):
        aws_dir = isolated_aws_env / '.aws'
        aws_dir.mkdir(exist_ok=True)
        credentials = aws_dir / 'credentials'
        with credentials.open('a') as f:
            f.write(
                '[{0}]\n'
                'aws_access_key_id = {1}\n'
                'aws_secret_access_key = {2}\n'.format(
                    profile, access_key, secret_key)
            )

    return _write
