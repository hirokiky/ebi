import logging
import sys
import time

import boto3

logger = logging.getLogger(__name__)


def get_version_and_description(parsed):
    """ Determine version label and description from parsed arguments.
    """
    if parsed.version:
        version = parsed.version
    elif parsed.prefix:
        version = f"{parsed.prefix}_{int(time.time())}"
    else:
        version = str(int(time.time()))

    if parsed.description:
        description = parsed.description
    else:
        description = ''
    return version, description


def append_common_options(payload, parsed):
    """ Append common eb command options to :param payload: from parsed arguments.
    """
    if parsed.profile:
        payload.append(f'--profile={parsed.profile}')
    if parsed.region:
        payload.append(f'--region={parsed.region}')
    if parsed.timeout:
        payload.append(f'--timeout={parsed.timeout}')


def get_environ_name_for_cname(app_name, cname):
    """ Determine environment name having :param cname: on :param app_name:.

    If cname duplicated, longer one will be returned.
    For example, there are myenv.ap-northeast-1.elasticbeanstalk.com and myenv.elasticbeanstalk.com,
    myenv.ap-northeast-1.elasticbeanstalk.com will be returned.
    """
    eb = boto3.client('elasticbeanstalk')
    environments = []
    for page in eb.get_paginator('describe_environments').paginate(ApplicationName=app_name):
        environments.extend(page['Environments'])

    # Terminated environments may still be returned and can carry a stale or
    # reused CNAME, so they must not be matched.
    environments = [e for e in environments if e.get('Status') != 'Terminated']

    for e in sorted(environments, key=lambda x: len(x['CNAME']), reverse=True):
        if e['CNAME'].startswith(f'{cname}.'):
            return e['EnvironmentName']
    logger.error('Could not find environment for applied app_name and cname')
    sys.exit(1)


def add_common_args(parser):
    """ Add arguments common to all subcommands to :param parser:.
    """
    parser.add_argument('--version', help='Version label you want to specify')
    parser.add_argument('--prefix', help='Version label prefix you want to specify')
    parser.add_argument('--description', help='Description for this version')
    parser.add_argument('--profile', help='AWS account')
    parser.add_argument('--region', help='AWS region')
    parser.add_argument('--timeout', help='The number of minutes before the deploy timeout')
    parser.add_argument('--dockerrun', help='Path to file used as Dockerrun.aws.json')
    parser.add_argument('--docker-compose', help='Path to file used as docker-compose.yml')
    parser.add_argument('--ebext', help='Path to directory used as .ebextensions/')
