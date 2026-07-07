from types import SimpleNamespace

from ebi.commands import utils


def _parsed(**kwargs):
    defaults = dict(version=None, prefix=None, description=None,
                    profile=None, region=None, timeout=None)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_explicit_version_takes_precedence():
    version, description = utils.get_version_and_description(
        _parsed(version='v1', prefix='rel'))
    assert version == 'v1'
    assert description == ''


def test_prefix_appends_timestamp(monkeypatch):
    monkeypatch.setattr(utils.time, 'time', lambda: 1700000000)
    version, _ = utils.get_version_and_description(_parsed(prefix='rel'))
    assert version == 'rel_1700000000'


def test_default_version_is_timestamp(monkeypatch):
    monkeypatch.setattr(utils.time, 'time', lambda: 1700000000)
    version, _ = utils.get_version_and_description(_parsed())
    assert version == '1700000000'


def test_description_passthrough():
    _, description = utils.get_version_and_description(_parsed(description='hello'))
    assert description == 'hello'


def test_append_common_options_all_set():
    payload = []
    utils.append_common_options(
        payload, _parsed(profile='p', region='r', timeout='5'))
    assert payload == ['--profile=p', '--region=r', '--timeout=5']


def test_append_common_options_none_set():
    payload = ['eb', 'deploy']
    utils.append_common_options(payload, _parsed())
    assert payload == ['eb', 'deploy']
