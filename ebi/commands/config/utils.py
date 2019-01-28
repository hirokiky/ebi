import os
from functools import reduce

import yaml

from .ebcli import (
    beanstalk_directory,
    ProjectRoot,
    resolve_config_location,
)


class TemporaryMergedYaml:
    def __init__(self, yaml_paths, cfg_name):
        cfgs = [
            self.__read_yaml_file(resolve_config_location(path))
            for path in yaml_paths
        ]
        self.cfg = self.__merge(cfgs)
        self.cfg_path = f'{beanstalk_directory}{cfg_name}.cfg.yml'
        self.tempfile, self.delete = self.__init_tempfile(
            self.cfg, self.cfg_path
        )

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def close(self):
        cwd = os.getcwd()
        try:
            ProjectRoot.traverse()
            self.tempfile.close()
            if self.delete:
                os.remove(self.cfg_path)
        finally:
            os.chdir(cwd)

    @staticmethod
    def __init_tempfile(cfg, cfg_path):
        cwd = os.getcwd()
        try:
            ProjectRoot.traverse()
            delete = not os.path.exists(cfg_path)
            tempfile = open(cfg_path, 'w')
            tempfile.write(yaml.safe_dump(cfg))
            tempfile.flush()
        finally:
            os.chdir(cwd)

            return tempfile, delete

    @staticmethod
    def __merge(dicts):
        return reduce(lambda a, b: a.update(b) or a, dicts, {})

    @staticmethod
    def __read_yaml_file(path):
        with open(path) as yaml_file:
            return yaml.safe_load(yaml_file.read())
