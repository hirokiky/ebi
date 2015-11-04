import argparse
import logging
import os
import shutil
import subprocess
import tempfile
import time

import boto3
from ebcli.lib import aws as ebaws
from ebcli.lib import s3 as ebs3
from ebcli.lib import elasticbeanstalk
from ebcli.objects.exceptions import NotFoundError

DOCKERRUN_NAME = 'Dockerrun.aws.json'
DOCKEREXT_NAME = '.ebextensions/'


logger = logging.getLogger('ebi')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def make_version(version_label: str,
                 dockerrun:str=DOCKERRUN_NAME, ebext:str=DOCKEREXT_NAME) -> str:
    """ Making zip file to upload for ElasticBeanstalk

    :param version_label: will be name of the created zip file

    * Including :param dockerrun: file as Dockerrun.aws.json
    * Including :param exext: directory as .ebextensions/

    :return: File path to created zip file (current directory).
    """
    with tempfile.TemporaryDirectory() as tempd:
        deploy_dockerrun = os.path.join(tempd, DOCKERRUN_NAME)
        deploy_ebext = os.path.join(tempd, DOCKEREXT_NAME)
        shutil.copyfile(dockerrun, deploy_dockerrun)
        shutil.copytree(ebext, deploy_ebext)
        return shutil.make_archive(version_label, 'zip', root_dir=tempd)


def upload_app_version(app_name: str, bundled_zip: str) -> (str, str):
    """ Uploading zip file of app version to S3
    :param app_name: application name to deploy
    :param bundled_zip: String path to zip file
    :return: bucket name and key for file (as tuple).
    """
    bucket = elasticbeanstalk.get_storage_location()
    key = app_name + '/' + os.path.basename(bundled_zip)
    try:
        ebs3.get_object_info(bucket, key)
        logger.info('S3 Object already exists. Skipping upload.')
    except NotFoundError:
        logger.info('Uploading archive to s3 location: ' + key)
        ebs3.upload_application_version(bucket, key, bundled_zip)
    return bucket, key


def main():
    """ Main function called from console_scripts
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parser_create = subparsers.add_parser('create')
    parser_deploy = subparsers.add_parser('deploy')

    parser_create.add_argument('app_name', help='Application name to create')
    parser_create.add_argument('env_name', help='Environ name to deploy')
    parser_create.add_argument('cname', help='cname for created server')
    parser_create.add_argument('--version', help='Version label you want to specify')
    parser_create.add_argument('--profile', help='AWS account')
    parser_create.add_argument('--dockerrun', default=DOCKERRUN_NAME,
                               help='Path to file used as Dockerrun.aws.json')
    parser_create.add_argument('--ebext', default=DOCKEREXT_NAME,
                               help='Path to directory used as .ebextensions/')
    parser_create.add_argument('--cfg', help='Configuration template name to eb create')
    parser_create.set_defaults(sub='create')

    parser_deploy.add_argument('app_name', help='Application name to deploy')
    parser_deploy.add_argument('env_name', help='Environ name to deploy')
    parser_deploy.add_argument('--version', help='Version label you want to specify')
    parser_deploy.add_argument('--profile', help='AWS account')
    parser_deploy.add_argument('--dockerrun', default=DOCKERRUN_NAME,
                               help='Path to file used as Dockerrun.aws.json')
    parser_deploy.add_argument('--ebext', default=DOCKEREXT_NAME,
                               help='Path to directory used as .ebextensions/')
    parser_deploy.set_defaults(sub='deploy')
    parsed = parser.parse_args()

    if not hasattr(parsed, 'sub'):
        parser.print_help()
        return

    if parsed.version:
        version = parsed.version
    else:
        version = str(int(time.time()))

    if parsed.profile:
        session = boto3.session.Session(profile_name=parsed.profile)
    else:
        session = boto3.session.Session()
    eb = session.client('elasticbeanstalk')

    ebaws.set_region(session._session.get_config_variable('region'))
    ebaws.set_profile(session.profile_name)

    bundled_zip = make_version(version,
                               dockerrun=parsed.dockerrun,
                               ebext=parsed.ebext)
    bucket, key = upload_app_version(parsed.app_name, bundled_zip)

    logger.info('Creating application version')

    eb.create_application_version(
        ApplicationName=parsed.app_name,
        VersionLabel=version,
        SourceBundle={
            'S3Bucket': bucket,
            'S3Key': key,
        }
    )

    if parsed.sub == 'deploy':
        logger.info('Ok, now deploying the version %s for %s', version, parsed.env_name)
        subprocess.call(['eb', 'deploy', parsed.env_name, '--version=' + version,
                         '--profile=' + session.profile_name])
    elif parsed.sub == 'create':
        logger.info('Ok, now creating version %s or environment %s', version, parsed.env_name)
        payload = ['eb', 'create', parsed.env_name,
                   '--version=' + version,
                   '--cname=' + parsed.cname,
                   '--profile=' + session.profile_name]
        if parsed.cfg:
            payload.append('--cfg=' + parsed.cfg)
        subprocess.call(payload)
