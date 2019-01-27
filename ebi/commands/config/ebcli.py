"""These functions originated from `ebcli`.

They are dupulicated here beacse it is not open-source fully.
"""

import os

beanstalk_directory = '.elasticbeanstalk' + os.path.sep


class NotFoundError(Exception):
    pass


class NotInitializedError(Exception):
    pass


def resolve_config_location(cfg_name):
    """
    Need to check if config name is a file path, a file reference,
       or a configuration name.
    Acceptable formats are:
    /full/path/to/file.cfg.yml
    ./relative/path/to/file.cfg.yml
    ~/user/path/to/file.cfg.yml
    relativefile.cfg.yml
    relative/path/to/filename.whatever
    filename.cfg.yml
    filename
    filename.yml

    If cfg_name is not a path, we will resolve it in this order:
     1. Private config files: .elasticbeanstalk/saved_configs/cfg_name.cfg.yml
     2. Public config files: .elasticbeanstalk/cfg_name.cfg.yml
    """
    slash = os.path.sep
    filename = os.path.expanduser(cfg_name)
    full_path = os.path.abspath(filename)
    if os.path.isfile(full_path):
        return full_path

    if slash not in cfg_name:
        for folder in ('saved_configs' + os.path.sep, ''):
            folder = folder + cfg_name
            for extension in ('.cfg.yml', '', '.yml'):
                file_location = folder + extension
                if _eb_file_exists(file_location):
                    return _get_project_file_full_location(
                        beanstalk_directory + file_location
                    )

    else:
        raise NotFoundError('File ' + cfg_name + ' not found.')

    return None


def _eb_file_exists(location):
    cwd = os.getcwd()
    try:
        ProjectRoot.traverse()
        path = beanstalk_directory + location
        return os.path.isfile(path)
    finally:
        os.chdir(cwd)


class ProjectRoot(object):
    __root = None

    @classmethod
    def traverse(cls):
        if cls.__root:
            return cls.__root

        cwd = os.getcwd()
        if not os.path.isdir(beanstalk_directory):
            os.chdir(os.path.pardir)

            if cwd == os.getcwd():
                raise NotInitializedError('EB is not yet initialized')

            ProjectRoot.traverse()
        else:
            cls.__root = cwd

    @classmethod
    def _reset_root(cls):
        cls.__root = None


def _get_project_file_full_location(location):
    cwd = os.getcwd()
    try:
        ProjectRoot.traverse()
        full_path = os.path.abspath(location)
        return full_path
    finally:
        os.chdir(cwd)


def get_filename_without_extension(file_location):
    filename = os.path.basename(file_location)
    extension = 'fake'
    while extension != '':
        filename, extension = os.path.splitext(filename)
    return filename
