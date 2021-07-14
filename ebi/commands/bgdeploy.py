import logging
import subprocess
import sys
import time

import boto3

from .. import appversion

logger = logging.getLogger(__name__)


def get_environ_name_for_cname(app_name, cname):
    """ Determine environment name having :param cname: on :param app_name:.

    If cname duplicated, longer one will be returned.
    For example, there are myenv.ap-northeast-1.elasticbeanstalk.com and myenv.elasticbeanstal.com,
    myenv.ap-northeast-1.elasticbeanstal.com will be returned.
    """
    eb = boto3.client('elasticbeanstalk')
    res = eb.describe_environments(ApplicationName=app_name)
    if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise ValueError('ElasticBeanstalk client did not return 200 for describing environments')

    for e in reversed(sorted(res['Environments'], key=lambda x: len(x['CNAME']))):
        if e['CNAME'].startswith(cname + '.'):
            return e['EnvironmentName']
    raise ValueError('Could not find environment for applied app_name and cname')


def get_instance_health(group_name, number):
    autoscale = boto3.client('autoscaling')
    as_json = autoscale.describe_auto_scaling_groups(
        AutoScalingGroupNames=[group_name])
    instances = as_json['AutoScalingGroups'][0]['Instances']
    instance_number = len(instances)
    if instance_number != number:
        return False

    for instance in instances:
        # Wait for the all of instance status to be healthy.
        ec2 = boto3.client('ec2')
        instance = ec2.describe_instance_status(InstanceIds=[instance['InstanceId']])
        if not instance['InstanceStatuses']:
            return False
        elif instance['InstanceStatuses'][0]['InstanceStatus']['Status'] != 'ok':
            return False
    return True


def update_secondary_group_capacity(primary_group_name, secondary_group_name, secondary_env_name, app_name):
    autoscale = boto3.client('autoscaling')
    as_json = autoscale.describe_auto_scaling_groups(
        AutoScalingGroupNames=[primary_group_name])
    number = as_json['AutoScalingGroups'][0]['DesiredCapacity']
    min_size = as_json['AutoScalingGroups'][0]['MinSize']
    max_size = as_json['AutoScalingGroups'][0]['MaxSize']

    autoscale.update_auto_scaling_group(
        AutoScalingGroupName=secondary_group_name,
        MaxSize=max_size,
        MinSize=min_size,
        DesiredCapacity=number
    )
    logger.info(
        'The number of instances to run was set to %d, the minimum size to %d, the maximum size to %d',
        number,
        min_size,
        max_size
    )

    # Wait for the instance to come up.
    logger.info('Wait for the instance to come up')
    start = time.time()
    while not get_instance_health(secondary_group_name, number):
        passed_time = time.time() - start
        # Make timeout 20 minutes
        if passed_time >= 20 * 60:
            logger.warning("The capacity set operation timed out.")
            sys.exit(1)
        time.sleep(30)

    logger.info("The all of instances are healthy.")

    # update EB environment description
    eb = boto3.client('elasticbeanstalk')
    eb.update_environment(
        ApplicationName=app_name,
        EnvironmentName=secondary_env_name,
        OptionSettings=[
            {'Namespace': 'aws:autoscaling:asg', 'OptionName': 'MinSize', 'Value': str(min_size)},
            {'Namespace': 'aws:autoscaling:asg', 'OptionName': 'MaxSize', 'Value': str(max_size)}
        ]
    )


def main(parsed):
    master_env_name = get_environ_name_for_cname(parsed.app_name, parsed.cname)
    if parsed.blue_env == master_env_name:
        primary_env_name = parsed.blue_env
        secondary_env_name = parsed.green_env
    elif parsed.green_env == master_env_name:
        primary_env_name = parsed.green_env
        secondary_env_name = parsed.blue_env
    else:
        raise ValueError('master env for cname {p.cname} was not in {p.app_name}'.format(p=parsed))

    ###
    # Deploying
    ###
    if parsed.version:
        version = parsed.version
    elif parsed.prefix:
        version = "{}_{}".format(parsed.prefix, int(time.time()))
    else:
        version = str(int(time.time()))

    if parsed.description:
        description = parsed.description
    else:
        description = ''

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.docker_compose, parsed.ebext, parsed.use_ebignore, description)
    logger.info('Ok, now deploying the version %s for %s', version, secondary_env_name)
    payload = ['eb', 'deploy', secondary_env_name,
               '--version=' + version]
    if parsed.profile:
        payload.append('--profile=' + parsed.profile)
    if parsed.region:
        payload.append('--region=' + parsed.region)
    if parsed.timeout:
        payload.append('--timeout=' + parsed.timeout)
    r = subprocess.call(payload)
    if r != 0:
        logger.error("Failed to deploy version %s to environment %s",
                     version, secondary_env_name)
        sys.exit(r)

    ###
    # Set desired capacity
    ###
    if parsed.capacity:
        autoscale = boto3.client('autoscaling')
        as_json = autoscale.describe_tags(
            Filters=[
                {
                    'Name': 'Value',
                    'Values': [secondary_env_name, primary_env_name]
                },
            ]
        )
        for x in as_json['Tags']:
            if x['Key'] == 'Name' and x['Value'] == secondary_env_name:
                secondary_group_name = x['ResourceId']
            elif x['Key'] == 'Name' and x['Value'] == primary_env_name:
                primary_group_name = x['ResourceId']
        update_secondary_group_capacity(
            primary_group_name,
            secondary_group_name,
            secondary_env_name,
            parsed.app_name
        )

    ###
    # Swapping
    ###
    if parsed.noswap:
        logger.info('DONE successfully without Swapping. just deployed secondary environment %s',
                    secondary_env_name)
        return

    eb = boto3.client('elasticbeanstalk')
    logger.info('Swapping primary %s => new primary %s',
                primary_env_name, secondary_env_name)
    eb.swap_environment_cnames(SourceEnvironmentName=primary_env_name,
                               DestinationEnvironmentName=secondary_env_name)
    logger.info('DONE successfully. Primary %s => new primary %s.'
                'If problem, re-swap new primary to primary',
                primary_env_name, secondary_env_name)


def apply_args(parser):
    parser.add_argument('app_name', help='Application name to deploy')
    parser.add_argument('green_env', help='green env name')
    parser.add_argument('blue_env', help='blue env name')
    parser.add_argument('cname', help='cname prefix for primary environment')
    parser.add_argument('--noswap', help='Without swapping, it will just deploy for secondary'
                                         'environment',
                        action='store_true', default=False)
    parser.add_argument('--version', help='Version label you want to specify')
    parser.add_argument('--prefix', help='Version label prefix you want to specify')
    parser.add_argument('--description', help='Description for this version')
    parser.add_argument('--profile', help='AWS account')
    parser.add_argument('--region', help='AWS region')
    parser.add_argument('--timeout', help='The number of minutes before the deploy timeout')
    parser.add_argument('--dockerrun', help='Path to file used as Dockerrun.aws.json')
    parser.add_argument('--docker-compose', help='Path to file used as docker-compose.yml')
    parser.add_argument('--ebext', help='Path to directory used as .ebextensions/')
    parser.add_argument('--use-ebignore', help='Zip project based on .ebignore',
                        action='store_true', default=True)
    parser.add_argument('--capacity', help='Set the number of instances.',
                        action='store_true', default=False)
    parser.set_defaults(func=main)
