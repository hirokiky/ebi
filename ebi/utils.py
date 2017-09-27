import yaml
import os
from functools import reduce

CONFIG_DIR = '.elasticbeanstalk'
CONFIG_EXT = '.cfg.yml'
FILENAME_DELIMITER =  '__'

def merge_configs(config_names):
    composed = _compose(
        yaml.load,
        _read_file,
        _make_fullpath,
    )

    configs = [composed(config_name) for config_name in config_names]
    merged = reduce(lambda a, b: _merge_dict(b, a), configs)

    temp_filename = FILENAME_DELIMITER.join(config_names) + CONFIG_EXT
    temp_filepath = os.path.join(os.getcwd(), CONFIG_DIR, temp_filename)
    _make_temp_ymlfile(merged, temp_filepath)
    return temp_filepath

def _make_temp_ymlfile(data, filepath):
    dirname = os.path.dirname(filepath)
    os.makedirs(dirname, exist_ok=True)
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

def _read_file(path):
    with open(path, 'r') as f:
        return f.read()

def _compose(*functions):
    initiator = lambda x: x
    compose2 = lambda f, g: (lambda x: f(g(x)))
    return reduce(compose2 , functions, initiator)

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
