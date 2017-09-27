import os

from functools import reduce

from ebcli.operations import saved_configs

import yaml


CONFIG_DIR = '.elasticbeanstalk'
SAVED_CONFIG_DIR = 'saved_configs'
CONFIG_EXT = '.cfg.yml'
CONFIG_NAME_DELIMITER = '__'


def merge_configs(cfg_names):
    """Merge config files and save as a single ymlfile.

    :param cfg_names: List of config_name string, without dir or extension
    :return: Tuple of (String of merged file location with dir and extenstion,
                       String of merged file name without dir or extenstion)
    ['ourproj', 'myenv'] -> ('/home/user/..../ourproj__myenv.cfg.yml', 'ourproj__myenv')
    """
    process_cfg = _compose(
        yaml.load,
        _read_file,
        saved_configs.resolve_config_location
    )

    configs = [process_cfg(cfg_name) for cfg_name in cfg_names]
    merged = reduce(lambda a, b: _merge_dict(b, a), configs)

    temp_cfg_name = CONFIG_NAME_DELIMITER.join(cfg_names)
    temp_filename =  temp_cfg_name + CONFIG_EXT
    temp_cfg_location = os.path.join(os.getcwd(),
                                 CONFIG_DIR, SAVED_CONFIG_DIR, temp_filename)
    _make_temp_ymlfile(merged, temp_filepath)
    return temp_cfg_location, temp_cfg_name


def _make_temp_ymlfile(data, filepath):
    dirname = os.path.dirname(filepath)
    os.makedirs(dirname, exist_ok=True)
    with open(filepath, 'w') as wf:
        yaml.dump(data, wf, default_flow_style=False)


def _read_file(path):
    with open(path, 'r') as rf:
        return rf.read()


def _compose(*functions):
    initiator = lambda x: x
    compose2 = lambda f, g: (lambda x: f(g(x)))
    return reduce(compose2, functions, initiator)


def _merge_dict(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            _merge_dict(value, node)
        else:
            destination[key] = value
    return destination
