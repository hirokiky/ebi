import argparse
import logging

import boto3
import botocore.session
from ebcli.lib import aws as ebaws

from .commands.bgdeploy import apply_args as apply_args_bgdeploy
from .commands.clonedeploy import apply_args as apply_args_clonedeploy
from .commands.create import apply_args as apply_args_create
from .commands.deploy import apply_args as apply_args_deploy


def main():
    """ Main function called from console_scripts
    """
    logger = logging.getLogger('ebi')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parser_bgdeploy = subparsers.add_parser('bgdeploy')
    parser_clonedeploy = subparsers.add_parser('clonedeploy')
    parser_create = subparsers.add_parser('create')
    parser_deploy = subparsers.add_parser('deploy')

    apply_args_bgdeploy(parser_bgdeploy)
    apply_args_clonedeploy(parser_clonedeploy)
    apply_args_create(parser_create)
    apply_args_deploy(parser_deploy)

    parsed = parser.parse_args()

    if not hasattr(parsed, 'func'):
        parser.print_help()
        return

    conf = {}
    if parsed.profile:
        conf['profile_name'] = parsed.profile
    if parsed.region:
        conf['region_name'] = parsed.region
    boto3.setup_default_session(**conf)

    # Resolve the effective region/profile through botocore's public API
    # (instead of reaching into boto3's private _get_default_session()._session)
    # and mirror them onto ebcli's AWS layer so `eb` subprocesses use the same.
    botocore_session = botocore.session.Session()
    if parsed.profile:
        botocore_session.set_config_variable('profile', parsed.profile)
    if parsed.region:
        botocore_session.set_config_variable('region', parsed.region)
    ebaws.set_region(botocore_session.get_config_variable('region'))
    # botocore resolves 'profile' from the explicit value or the
    # AWS_PROFILE/AWS_DEFAULT_PROFILE env vars and does not fall back to
    # 'default' (unlike boto3.Session.profile_name), so credentials provided
    # only via environment variables keep working.
    profile = botocore_session.get_config_variable('profile')
    if profile:
        ebaws.set_profile(profile)
    parsed.func(parsed)
