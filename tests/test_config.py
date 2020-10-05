from pathlib import Path
import sys, json
import string, random

import pytest

import codememo.config as mod_config
from codememo.config import (
    AppConfig, AppDefaults,
    AppHistory, RecentlyOpenedFilesHistory,
)


@pytest.fixture
def setup_app_defaults(mocker, tmpdir):
    dir_home = tmpdir.mkdir('home')
    dir_config = Path(dir_home).joinpath('.codememo')
    fn_config = dir_config.joinpath('config.json')
    fn_history = dir_config.joinpath('history.json')

    frame = sys._getframe()
    mocked_attrs = {k: frame.f_locals.get(k) for k in [
        'dir_config', 'fn_config', 'fn_history'
    ]}

    for k, v in mocked_attrs.items():
        mocker.patch.object(AppDefaults, k, str(v))

    return mocked_attrs


def generate_random_file_name(name_length):
    return ''.join([random.choice(string.ascii_letters) for i in range(name_length)])


class TestAppConfig:
    def test__load(self, setup_app_defaults):
        mocked_attrs = setup_app_defaults
        fn_config = mocked_attrs['fn_config']

        # config file should not exist currently
        assert not Path(fn_config).exists()

        config = AppConfig.load()
        for k, v in mocked_attrs.items():
            assert getattr(config, k) == str(v)

        # config file should be created after the first call of `load()`
        assert Path(fn_config).exists()

    def test__load_with_missing_keys(self, setup_app_defaults, mocker):
        mocked_attrs = setup_app_defaults
        fn_config = mocked_attrs['fn_config']
        spy_func = mocker.spy(mod_config, 'check_all_keys_exist')

        # preload once to create file
        ori_config = AppConfig.load()

        # modify config file for next loading
        with open(fn_config, 'r') as f:
            content = json.load(f)
        content.pop(list(content.keys())[0])    # remove an arbitrary key
        with open(fn_config, 'w') as f:
            json.dump(content, f, indent=2)

        # load modified config file
        config = AppConfig.load()

        # because there are missing keys in config file, so the check
        # processed by `check_all_keys_exist()` should failed
        assert spy_func.called
        assert spy_func.spy_return == False

        # missing keys will be recovered automatically
        assert ori_config.to_dict() == config.to_dict()

    def test__load_with_redundant_keys(self, setup_app_defaults):
        mocked_attrs = setup_app_defaults
        fn_config = mocked_attrs['fn_config']

        # preload once to create file
        ori_config = AppConfig.load()

        # modify config file for next loading
        with open(fn_config, 'r') as f:
            content = json.load(f)
        content.update({'test_key': 'foo'})     # add an arbitrary key
        with open(fn_config, 'w') as f:
            json.dump(content, f, indent=2)

        # load modified config file
        with pytest.warns(RuntimeWarning, match='unknown configuration values'):
            config = AppConfig.load()

        # missing keys will be recovered automatically
        assert ori_config.to_dict() == config.to_dict()


class TestAppHistory:
    def test__load_with_missing_keys(self, setup_app_defaults, mocker):
        mocked_attrs = setup_app_defaults
        fn_history = mocked_attrs['fn_history']
        spy_func = mocker.spy(mod_config, 'check_all_keys_exist')

        # preload config once to create the config directory
        AppConfig.load()

        # preload once to create file
        ori_history = AppHistory.load(fn_history)

        # modify history file for next loading
        with open(fn_history, 'r') as f:
            content = json.load(f)
        content.pop(list(content.keys())[0])    # remove an arbitrary key
        with open(fn_history, 'w') as f:
            json.dump(content, f, indent=2)

        # load modified history file
        history = AppHistory.load(fn_history)

        # because there are missing keys in history file, so the check
        # processed by `check_all_keys_exist()` should failed
        assert spy_func.called
        assert spy_func.spy_return == False

        # missing keys will be recovered automatically
        assert ori_history.to_dict() == history.to_dict()


class TestRecentlyOpenedFilesHistory:
    def test__add(self):
        history_limit = RecentlyOpenedFilesHistory.limit

        name_length = 16
        dummy_files = []

        # prevent duplicate names
        while len(dummy_files) < history_limit:
            fn = generate_random_file_name(name_length)
            if fn in dummy_files:
                continue
            dummy_files.append(fn)

        recent_files = RecentlyOpenedFilesHistory()

        for fn in dummy_files:
            recent_files.add(fn)

        # recently opened files are stored in a stack-like structure
        assert recent_files.files == dummy_files[::-1]

        # newly opened file will be pushed to the top
        recent_files.add(dummy_files[0])
        assert recent_files.files[0] == dummy_files[0]

        recent_files.clear()
        assert len(recent_files) == 0
