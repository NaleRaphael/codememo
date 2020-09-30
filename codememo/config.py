import os
import os.path as osp
import json

__all__ = ['AppConfig']


def check_all_keys_exist(template, target):
    if not isinstance(template, dict):
        raise TypeError('`template` should be a dict, got %s' % type(template))
    if not isinstance(target, dict):
        raise TypeError('`target` should be a dict, got %s' % type(target))

    for k, v in template.items():
        if k not in target:
            return False
        if isinstance(v, dict):
            if not check_all_keys_exist(v, target[k]):
                return False
    return True


class Defaults(object):
    pass


class ConfigBase(object):
    """
    name : str
        Name of config class.
    keys : list
        Keys to control customizable attributes. If an attribute name is
        not listed in this list, it would not be writen into the config
        file. So that user cannot modify it.
    """
    name = ''
    keys = []

    def to_dict(self):
        return {k: getattr(self, k) for  k in self.keys}

    def _check_remaining_kwargs(self, **kwargs):
        # Check whether there are remaining values for configuration
        if len(kwargs) != 0:
            import warnings
            msg = (
                f'{self.name}: There are unknown configuration values, '
                f'did you added them by accident? {kwargs}'
            )
            warnings.warn(msg, RuntimeWarning)


class AppDefaults(Defaults):
    dir_home = os.getenv('HOME', osp.expanduser('~'))
    dir_config = osp.join(dir_home, '.codememo')
    fn_config = osp.join(dir_config, 'config.json')


class AppConfig(ConfigBase):
    name = 'app'

    def __init__(self, **kwargs):
        super(AppConfig, self).__init__()
        kwargs = {} if kwargs is None else kwargs
        self.dir_config = AppDefaults.dir_config
        self.fn_config = AppDefaults.fn_config
        self.display = DisplayConfig(
            **kwargs.pop(DisplayConfig.name, {})
        )
        self.text_input = TextInputConfig(
            **kwargs.pop(TextInputConfig.name, {})
        )
        self._check_remaining_kwargs(**kwargs)

    @classmethod
    def load(cls):
        if not osp.exists(AppDefaults.fn_config):
            # Config file does not exist, so we create it with default values
            config = cls()
            config.write()
            return config
        else:
            with open(AppDefaults.fn_config, 'r') as f:
                content = json.load(f)

            # Update config file if there are missing keys
            config = cls(**content)
            if not check_all_keys_exist(config.to_dict(), content):
                config.write()
            return config

    def write(self):
        os.makedirs(AppDefaults.dir_config, exist_ok=True)
        with open(AppDefaults.fn_config, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_dict(self):
        return {
            self.text_input.name: self.text_input.to_dict(),
        }


class DisplayDefaults(Defaults):
    # NOTE: Settings related to display, but since we are using event-based
    # rendering, these settings are not actually used. But we might make user
    # able to switch the rendering mode in the future.
    fps = 30.0
    frame_update_interval = 1/fps


class DisplayConfig(ConfigBase):
    name = 'display'

    def __init__(self, **kwargs):
        super(DisplayConfig, self).__init__()
        self.fps = DisplayDefaults.fps
        self.frame_update_interval = DisplayDefaults.frame_update_interval


class TextInputDefaults(Defaults):
    """
    convert_tab_to_spaces : bool
        If this is enabled, tab key will be converted to spaces in those
        imgui widgets for text input.
    tab_to_spaces_number : int
        Number of spaces would be converted from a single tab key.
    """
    convert_tab_to_spaces = True
    tab_to_spaces_number = 4   # 1 tab for 4 spaces


class TextInputConfig(ConfigBase):
    name = 'text_input'
    keys = ['convert_tab_to_spaces', 'tab_to_spaces_number']

    def __init__(self, **kwargs):
        super(TextInputConfig, self).__init__()
        for k in self.keys:
            setattr(self, k, kwargs.pop(k, getattr(TextInputDefaults, k)))
        self._check_remaining_kwargs(**kwargs)
