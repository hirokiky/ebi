import logging
import os
import shutil
import tempfile
import zipfile

import boto3
from ebcli.core import fileoperations
from ebcli.lib import s3 as ebs3
from ebcli.lib import elasticbeanstalk
from ebcli.objects.exceptions import NotFoundError

logger = logging.getLogger('ebi')


DOCKERRUN_NAME = 'Dockerrun.aws.json'
DOCKER_COMPOSE_NAME = 'docker-compose.yml'
DOCKEREXT_NAME = '.ebextensions/'


def make_version_file_with_ebignore(version_label, dockerrun=None, docker_compose=None, ebext=None):
    """ Making zip file to upload for ElasticBeanstalk based on ebigore

    :param version_label: will be name of the created zip file

    * Including :param dockerrun: file as Dockerrun.aws.json
    * Including :param docker-compose: file as docker-compose.yml (for Amazon linux2)
    * Including :param exext: directory as .ebextensions/

    :return: File path to created zip file (current directory).
    """
    ebext = ebext or DOCKEREXT_NAME

    tempd = tempfile.mkdtemp()
    try:
        ignore_files = fileoperations.get_ebignore_list()

        # Dockerrun, docker-compose and ebextentions files are added to zip file later.
        ignore_files |= {DOCKERRUN_NAME, DOCKER_COMPOSE_NAME}
        ignore_ebext_files = set()
        for file in os.listdir(DOCKEREXT_NAME):
            ebext_file_path = os.path.join(DOCKEREXT_NAME, file)
            if os.path.isfile(ebext_file_path):
                ignore_ebext_files.add(ebext_file_path)
        ignore_files |= ignore_ebext_files

        zip_filename = version_label + ".zip"
        temp_zip_path = os.path.join(tempd, zip_filename)
        fileoperations.zip_up_project(temp_zip_path, ignore_list=ignore_files)
        shutil.copyfile(temp_zip_path, zip_filename)

        logger.info(f'Adding {DOCKERRUN_NAME}, {DOCKER_COMPOSE_NAME}, {DOCKEREXT_NAME} to archive.')
        with zipfile.ZipFile(zip_filename, 'a', allowZip64=True) as f:
            for file in os.listdir(ebext):
                source_ebext_file_path = os.path.join(ebext, file)
                target_ebext_file_path = os.path.join(DOCKEREXT_NAME, file)
                if os.path.isfile(source_ebext_file_path):
                    f.write(source_ebext_file_path, arcname=target_ebext_file_path)

            if docker_compose:
                f.write(docker_compose, arcname=DOCKER_COMPOSE_NAME)
                if dockerrun:
                    f.write(dockerrun, arcname=DOCKERRUN_NAME)
            else:
                dockerrun = dockerrun or DOCKERRUN_NAME
                f.write(dockerrun, arcname=DOCKERRUN_NAME)

        return zip_filename

    finally:
        shutil.rmtree(tempd)


def make_version_file(version_label, dockerrun=None, docker_compose=None, ebext=None):
    """ Making zip file to upload for ElasticBeanstalk

    :param version_label: will be name of the created zip file

    * Including :param dockerrun: file as Dockerrun.aws.json
    * Including :param docker-compose: file as docker-compose.yml (for Amazon linux2)
    * Including :param ebext: directory as .ebextensions/

    :return: File path to created zip file (current directory).
    """
    dockerrun = dockerrun or DOCKERRUN_NAME

    ebext = ebext or DOCKEREXT_NAME

    tempd = tempfile.mkdtemp()
    try:
        deploy_ebext = os.path.join(tempd, DOCKEREXT_NAME)
        shutil.copytree(ebext, deploy_ebext)

        # docker-compose takes precedence over dockerrun
        if docker_compose:
            deploy_docker_compose = os.path.join(tempd, DOCKER_COMPOSE_NAME)
            shutil.copyfile(docker_compose, deploy_docker_compose)
        else:
            deploy_dockerrun = os.path.join(tempd, DOCKERRUN_NAME)
            shutil.copyfile(dockerrun, deploy_dockerrun)

        return shutil.make_archive(version_label, 'zip', root_dir=tempd)
    finally:
        shutil.rmtree(tempd)


def upload_app_version(app_name, bundled_zip):
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


def make_application_version(app_name, version, dockerrun, docker_compose, ebext, use_ebignore, description):
    if use_ebignore:
        if os.path.isfile(".ebignore"):
            bundled_zip = make_version_file_with_ebignore(version, dockerrun=dockerrun, docker_compose=docker_compose, ebext=ebext)
        else:
            logger.info('.ebignore does not exist. Make a version file not using ebignore')
            bundled_zip = make_version_file(version, dockerrun=dockerrun, docker_compose=docker_compose, ebext=ebext)
    else:
        bundled_zip = make_version_file(version, dockerrun=dockerrun, docker_compose=docker_compose, ebext=ebext)
    try:
        bucket, key = upload_app_version(app_name, bundled_zip)

        logger.info('Creating application version')
        eb = boto3.client('elasticbeanstalk')
        eb.create_application_version(
            ApplicationName=app_name,
            VersionLabel=version,
            Description=description,
            SourceBundle={
                'S3Bucket': bucket,
                'S3Key': key,
            }
        )
    finally:
        os.remove(bundled_zip)
