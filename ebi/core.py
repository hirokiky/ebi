from __future__ import absolute_import
from __future__ import print_function

import argparse
import logging

import boto3
from ebcli.lib import aws as ebaws

from .commands.bgdeploy import apply_args as apply_args_bgdeploy
from .commands.clonedeploy import apply_args as apply_args_clonedeploy
from .commands.create import apply_args as apply_args_create
from .commands.deploy import apply_args as apply_args_deploy


def main():
    """ Main function called from console_scripts
    """
    logger = logging.getLogger('ebi')
    logger.propagate = True
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
    session = boto3._get_default_session()
    ebaws.set_region(session._session.get_config_variable('region'))
    ebaws.set_profile(session.profile_name)
    parsed.func(parsed)
