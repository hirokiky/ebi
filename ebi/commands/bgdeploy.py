import logging
import subprocess
import sys
import time

import boto3

from .. import appversion

logger = logging.getLogger(__name__)


def get_environ_name_for_cname(app_name, cname):
    """ Determine environment name having :param cname: on :param app_name:.
    """
    return ''


def generate_green_environment_names(base_env_name, base_cname):
    """ Generate environment name and cname for applied env.
    'uploader-api', 'myservice-uploader'
        =>  'uploader-api-1446805048', 'myservice-uploader-1446805048'

    :return: tuple of environment name and cname
    """
    t = str(int(time.time()))
    return base_env_name + t, base_cname + t


def main(parsed):
    ###
    # Cloning
    ###
    blue_environment_name = get_environ_name_for_cname(parsed.app_name, parsed.cname)

    green_environment_name, green_cname = generate_green_environment_names(parsed.env_name,
                                                                           parsed.cname)

    payload = ['eb', 'clone', blue_environment_name,
               '--exact',
               '--clone_name=' + green_environment_name,
               '--cname=' + green_cname]
    if parsed.profile:
        payload.append('--profile=' + parsed.profile)
    if parsed.region:
        payload.append('--region=' + parsed.region)

    r = subprocess.call(payload)
    if r != 0:
        logger.error("Failed to clone environment %s", blue_environment_name)
        sys.exit(r)
    logger.info('Cloned environment %s => %s', blue_environment_name, green_environment_name)

    ###
    # Deploying
    ###
    if parsed.version:
        version = parsed.version
    else:
        version = str(int(time.time()))

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.ebext)
    logger.info('Ok, now deploying the version %s for %s', version, green_environment_name)
    payload = ['eb', 'deploy', green_environment_name,
               '--version=' + version]
    if parsed.profile:
        payload.append('--profile=' + parsed.profile)
    if parsed.region:
        payload.append('--region=' + parsed.region)
    r = subprocess.call(payload)
    if r != 0:
        logger.error("Failed to deploy version %s to environment %s",
                     version, green_environment_name)
        sys.exit(r)

    ###
    # Swapping
    ###

    eb = boto3.client('elasticbeanstalk')
    logger.info('Swapping blue %s => green %s',
                blue_environment_name, green_environment_name)
    eb.swap_environment_cnames(SourceEnvironmentName=green_environment_name,
                               DestinationEnvironmentName=blue_environment_name)
    logger.info('DONE successfully. Blue %s => Green %s.'
                'If no problem, terminate Blue. If problem, re-swap Green to Blue',
                blue_environment_name, green_environment_name)


def apply_args(parser):
    parser.add_argument('app_name', help='Application name to deploy')
    parser.add_argument('env_name', help='Environ name to deploy')
    parser.add_argument('cname', help='cname of Blue environment')
    parser.add_argument('--version', help='Version label you want to specify')
    parser.add_argument('--profile', help='AWS account')
    parser.add_argument('--region', help='AWS region')
    parser.add_argument('--dockerrun', help='Path to file used as Dockerrun.aws.json')
    parser.add_argument('--ebext', help='Path to directory used as .ebextensions/')
    parser.set_defaults(func=main)
