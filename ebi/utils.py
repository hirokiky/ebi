import os

from functools import reduce

import yaml


CONFIG_DIR = '.elasticbeanstalk'
SAVED_CONFIG_DIR = 'saved_configs'
CONFIG_EXT = '.cfg.yml'
CONFIG_NAME_DELIMITER = '__'


def merge_configs(cfg_names):
    """Merge config files and save as a single ymlfile.

    :param cfg_names: List of config_name string, following ebcli's naming rule
    :return: String of merged file path, with dir and extenstion
    """
    process_cfg = _compose(
        yaml.load,
        _read_file,
        _make_fullpath,
    )

    configs = [process_cfg(cfg_name) for cfg_name in cfg_names]
    merged = reduce(lambda a, b: _merge_dict(b, a), configs)

    temp_filename = CONFIG_NAME_DELIMITER.join(cfg_names) + CONFIG_EXT
    temp_filepath = os.path.join(os.getcwd(),
                                 CONFIG_DIR, SAVED_CONFIG_DIR, temp_filename)
    _make_temp_ymlfile(merged, temp_filepath)
    return temp_filepath


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

def _make_fullpath(cfg):
    return os.path.join(CONFIG_DIR, cfg + CONFIG_EXT)

def _merge_dict(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            _merge_dict(value, node)
        else:
            destination[key] = value
    return destination
