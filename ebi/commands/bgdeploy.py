import logging
import sys
import time

import boto3

from .. import appversion
from . import utils

logger = logging.getLogger(__name__)


def get_instance_health(group_name, number):
    autoscale = boto3.client('autoscaling')
    as_json = autoscale.describe_auto_scaling_groups(
        AutoScalingGroupNames=[group_name])
    instances = as_json['AutoScalingGroups'][0]['Instances']
    instance_number = len(instances)
    if instance_number != number:
        return False

    if not instances:
        return True

    # Wait for the all of instance status to be healthy.
    ec2 = boto3.client('ec2')
    res = ec2.describe_instance_status(
        InstanceIds=[instance['InstanceId'] for instance in instances])
    statuses = res['InstanceStatuses']
    # describe_instance_status returns only running instances by default,
    # so fewer statuses than instances means some are not running yet.
    if len(statuses) != instance_number:
        return False
    for status in statuses:
        if status['InstanceStatus']['Status'] != 'ok':
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
    master_env_name = utils.get_environ_name_for_cname(parsed.app_name, parsed.cname)
    if parsed.blue_env == master_env_name:
        primary_env_name = parsed.blue_env
        secondary_env_name = parsed.green_env
    elif parsed.green_env == master_env_name:
        primary_env_name = parsed.green_env
        secondary_env_name = parsed.blue_env
    else:
        logger.error('master env for cname %s was not in %s', parsed.cname, parsed.app_name)
        sys.exit(1)

    ###
    # Deploying
    ###
    version, description = utils.get_version_and_description(parsed)

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.docker_compose, parsed.ebext, description)
    logger.info('Ok, now deploying the version %s for %s', version, secondary_env_name)
    utils.deploy_version(secondary_env_name, version, parsed)

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
    utils.add_common_args(parser)
    parser.add_argument('--capacity', help='Set the number of instances.',
                        action='store_true', default=False)
    parser.set_defaults(func=main)
