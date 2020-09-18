"""In `pyimgui` v1.2.0, states of modifier keys won't be reset when keys are
released, and those states can only be reset when other non-modifier keys
are pressed. And this module is targeted at solving this issue.
"""
import pyglet
from pyglet.window import key, mouse

from .vendor.imgui.integrations.pyglet import PygletMixin as _PygletMixin
from .vendor.imgui.integrations.opengl import (
    FixedPipelineRenderer, ProgrammablePipelineRenderer
)


class PygletMixin(_PygletMixin):
    REVERSE_KEY_MAP = _PygletMixin.REVERSE_KEY_MAP
    REVERSE_KEY_MAP.update({
        98784247808: _PygletMixin.REVERSE_KEY_MAP[key.TAB]
    })

    def _on_mods_press(self, symbol, mods):
        """
        Variable:
        X: prev_state, Y: symbol, Z: mods, X': next_state

        Truth table:
        X Y Z | X'
        ----------
        0 0 0   0
        0 0 1   1
        0 1 0   1
        0 1 1   1
        1 0 0   0
        1 0 1   1
        1 1 0   1
        1 1 1   1

        Summary:
        X' = Y OR Z

        Explanation:
        **No matter what previous state is** (1), once **given key code (`symbol`)
        is a modifier key** (2) or **desired modifier key exists in given combination
        of modifier keys (`mods`)** (3), set state to True.

        (1): `X` won't affect the output `X'`
        (2): e.g. `symbol in (key.LCTRL, key.RCTRL)` -> Y = 1
        (3): e.g. `mods & key.MOD_CTRL` -> Z = 1
        """
        self.io.key_ctrl = (symbol in (key.LCTRL, key.RCTRL)) or (mods & key.MOD_CTRL)
        self.io.key_super = (symbol in (key.LCOMMAND, key.RCOMMAND)) or (mods & key.MOD_COMMAND)
        self.io.key_alt = (symbol in (key.LALT, key.RALT)) or (mods & key.MOD_ALT)
        self.io.key_shift = (symbol in (key.LSHIFT, key.RSHIFT)) or (mods & key.MOD_SHIFT)

    def _on_mods_release(self, symbol, mods):
        """
        Variable:
        X: prev_state, Y: symbol, Z: mods, X': next_state

        Boolean table:
        X Y Z | X'
        ----------
        0 0 0   0
        0 0 1   1
        0 1 0   0
        0 1 1   0
        1 0 0   1
        1 0 1   1
        1 1 0   0
        1 1 1   0

        Summary:
        X' = (NOT Y) AND (X OR Z)

        Explanation:
        **Once given key code (`symbol`) is a modifier key, reset state to False.** (1)
        Otherwise, **keep state in True when previous state (`X`) is True or desired
        modifier key exists in given combination of modifier keys (`mods`)** (2).

        (1): (NOT Y) AND ...
        (2): (X OR Z)
        """
        self.io.key_ctrl = (symbol not in (key.LCTRL, key.RCTRL)) and ((mods & key.MOD_CTRL) or self.io.key_ctrl)
        self.io.key_super = (symbol not in (key.LCOMMAND, key.RCOMMAND)) and ((mods & key.MOD_COMMAND) or self.io.key_super)
        self.io.key_alt = (symbol not in (key.LALT, key.RALT)) and ((mods & key.MOD_ALT) or self.io.key_alt)
        self.io.key_shift = (symbol not in (key.LSHIFT, key.RSHIFT)) and ((mods & key.MOD_SHIFT) or self.io.key_shift)

    def on_key_press(self, symbol, mods):
        if symbol in self.REVERSE_KEY_MAP:
            self.io.keys_down[self.REVERSE_KEY_MAP[symbol]] = True
        self._on_mods_press(symbol, mods)

    def on_key_release(self, symbol, mods):
        if symbol in self.REVERSE_KEY_MAP:
            self.io.keys_down[self.REVERSE_KEY_MAP[symbol]] = False
        self._on_mods_release(symbol, mods)


class PygletFixedPipelineRenderer(PygletMixin, FixedPipelineRenderer):
    def __init__(self, window, attach_callbacks=True):
        super(PygletFixedPipelineRenderer, self).__init__()
        self._set_pixel_ratio(window)
        self._map_keys()
        if attach_callbacks: self._attach_callbacks(window)


class PygletProgrammablePipelineRenderer(PygletMixin, ProgrammablePipelineRenderer):
    def __init__(self, window, attach_callbacks = True):
        super(PygletProgrammablePipelineRenderer, self).__init__()
        self._set_pixel_ratio(window)
        self._map_keys()
        if attach_callbacks: self._attach_callbacks(window)


class PygletRenderer(PygletFixedPipelineRenderer):
    def __init__(self, window, attach_callbacks=True):
        warnings.warn("PygletRenderer is deprecated; please use either "
                      "PygletFixedPipelineRenderer (for OpenGL 2.1, pyglet < 2.0) or "
                      "PygletProgrammablePipelineRenderer (for later versions) or "
                      "create_renderer(window) to auto-detect.",
                      DeprecationWarning)
        super(PygletRenderer, self).__init__(window, attach_callbacks)


def _convert_version_string_to_tuple(ver):
    return tuple([int(v) for v in ver.split('.')])


def create_renderer(window, attach_callbacks=True):
    """
    This is a helper function that wraps the appropriate version of the Pyglet
    renderer class, based on the version of pyglet being used.
    """
    # Determine the context version
    # Pyglet < 2.0 has issues with ProgrammablePipeline even when the context
    # is OpenGL 3, so we need to check the pyglet version rather than looking
    # at window.config.major_version to see if we want to use programmable.
    if _convert_version_string_to_tuple(pyglet.version) < (2, 0):
        return PygletFixedPipelineRenderer(window, attach_callbacks)
    else:
        return PygletProgrammablePipelineRenderer(window, attach_callbacks)
