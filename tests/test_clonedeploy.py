from ebi.commands import clonedeploy


def test_base36encode_zero_is_empty():
    assert clonedeploy.base36encode(0) == ''


def test_base36encode_known_values():
    assert clonedeploy.base36encode(1) == '1'
    assert clonedeploy.base36encode(35) == 'z'
    assert clonedeploy.base36encode(36) == '10'
    assert clonedeploy.base36encode(1295) == 'zz'


def test_make_next_env_names(monkeypatch):
    monkeypatch.setattr(clonedeploy.time, 'time', lambda: 36)
    env_name, cname = clonedeploy.make_next_env_names('myenv', 'mycname')
    assert env_name == 'myenv-10'
    assert cname == 'mycname-10'
