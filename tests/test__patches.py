import pytest
import imgui
import pyglet
from pyglet import gl
from pyglet.window import key as gk
from pynput.keyboard import Key, Controller, Listener

from codememo._patches import create_renderer


VALID_EVENTS = ['press', 'release']
VALID_KEYNAMES = ['ctrl', 'alt', 'cmd', 'shift']
KEY_STATE_MAP = {'press': True, 'release': False}


class KeyEventTestCase(object):
    """A test case for key event test.

    Note that keys like a-z, 0-9 ... are not supported. because they don't exist
    in `imgui.KeyMap` and `PygletMixin.REVERSE_KEY_MAP`.
    """
    def __init__(self, event_type, key, expected_pressing_keys):
        """
        Parameters
        ----------
        event_type : str
            Type of key event, should be either 'press' or 'release'.
        key : pynput.keyboard.key
            Key to press/release.
        expected_pressing_keys : list
            List of pressing keys. Can be used to detect key combination.
        """
        if event_type not in VALID_EVENTS:
            raise ValueError(f'`event_type` should be one of {VALID_EVENTS}')
        if not all([v in VALID_KEYNAMES for v in expected_pressing_keys]):
            raise ValueError(f'not all keys are listed in {VALID_KEYNAMES}')
        self.event_type = event_type
        self.key = key
        self.expected_pressing_keys = expected_pressing_keys
        self.failure_reason = None

    def __repr__(self):
        return (f'<KeyEventTestCase ({self.event_type}, input: {self.key}, '
            f'expected: {self.expected_pressing_keys}), failure_reason: {self.failure_reason}>')

    def dispatch(self, keyboard):
        if not isinstance(keyboard, Controller):
            raise TypeError(f'`keyboard` should be an instance of {Controller}')
        action = getattr(keyboard, self.event_type)
        action(self.key)

    def _get_key_state_in_io(self, key_name):
        return getattr(imgui.get_io(), f'key_{key_name}')

    def validate(self, key_state_cache):
        passed = True
        if key_state_cache.has_pressing_keys:
            passed &= key_state_cache.pressed_keys == set(self.expected_pressing_keys)
            if not passed:
                self.failure_reason = 'expected key mismatched'
        for k in self.expected_pressing_keys:
            passed &= self._get_key_state_in_io(k) == KEY_STATE_MAP['press']
            if not passed:
                self.failure_reason = 'pressed key not detected'
        return passed


class KeyTestApplication(object):
    def __init__(self):
        # NOTE: `on_key_press` and `on_key_release` events cannot be detected
        # by `pyglet` when `window.visible` is False.
        self.window = pyglet.window.Window(
            width=320, height=320, resizable=True, visible=True
        )
        gl.glClearColor(0, 0, 0, 1)

        imgui.create_context()
        self.imgui_impl = create_renderer(self.window)
        self.frame_update_interval = 1./30
        self.init_draw_process()

        # Test related variables
        self.test_cases = []
        self.current_case = None
        self.idx_test_case = 0
        self.failed_cases = []
        self.ready_to_exit = False
        self.wait_for_check = False

        self.key_state_cache = KeyStateCache()
        self.keyboard = Controller()
        self.key_listener = Listener(
            on_press=self.key_state_cache.on_press,
            on_release=self.key_state_cache.on_release,
        )

    def add_test_case(self, case):
        self.test_cases.append(case)

    def clear_test_cases(self):
        self.test_cases = []

    def init_draw_process(self):
        def update(dt):
            imgui.new_frame()

            # Since we cannot put this callback to the event handler stack after
            # `on_key_press()` and `on_key_release()` defined in `PygletMixin`,
            #  we put it here to check the keyboard state of previous frame.
            check_keyboard_state()

            if self.idx_test_case >= len(self.test_cases):
                pyglet.app.exit()
            else:
                if not self.wait_for_check and self.current_case is None:
                    self.current_case = self.test_cases[self.idx_test_case]
                    self.current_case.dispatch(self.keyboard)
                    self.idx_test_case += 1
                    self.wait_for_check = True

        def on_draw(dt):
            update(self.frame_update_interval)
            self.window.clear()
            imgui.render()
            self.imgui_impl.render(imgui.get_draw_data())

        # Use `pyglet.clock` rather than event-based method to trigger next
        # rendering. Otherwise, program will be suspended if window is in headless mode.
        pyglet.clock.schedule_interval(on_draw, self.frame_update_interval)

        def on_key_press(symbol, modifiers):
            if symbol == pyglet.window.key.ESCAPE:
                return pyglet.event.EVENT_HANDLED

        self.window.push_handlers(on_key_press)

        # callback for validating dispatched key event
        def check_keyboard_state():
            if self.wait_for_check and self.current_case is not None:
                # clear cached key state if a key is released
                if self.current_case.event_type == 'release':
                    self.key_state_cache.reset_state(self.current_case.key)

                passed = self.current_case.validate(self.key_state_cache)
                if not passed:
                    self.failed_cases.append(self.current_case)

                self.current_case = None        # reset
                self.wait_for_check = False     # reset

    def _reset_all_key_state(self):
        import string

        keys = [v for v in (string.ascii_lowercase + string.digits)]
        mods = ['alt', 'ctrl', 'cmd', 'shift']

        for k in keys:
            self.keyboard.release(k)

        for k in mods:
            self.keyboard.release(getattr(Key, k))

    def run(self):
        self.key_listener.start()

        pyglet.app.run()
        self.imgui_impl.shutdown()

        self.key_listener.stop()
        self._reset_all_key_state()

        return self.failed_cases

    def __del__(self):
        self.keyboard._display.close()
        del self.keyboard


@pytest.fixture
def key_event_test_cases():
    return [
        KeyEventTestCase('press', Key.alt, ['alt']),
        KeyEventTestCase('release', Key.alt, []),
        KeyEventTestCase('press', Key.ctrl, ['ctrl']),
        KeyEventTestCase('release', Key.ctrl, []),
        KeyEventTestCase('press', Key.shift, ['shift']),
        KeyEventTestCase('release', Key.shift, []),

        # Key combination: alt + ctrl
        KeyEventTestCase('press', Key.alt, ['alt']),
        KeyEventTestCase('press', Key.ctrl, ['alt', 'ctrl']),
        KeyEventTestCase('release', Key.alt, ['ctrl']),
        KeyEventTestCase('release', Key.ctrl, []),

        # Key combination: shift + ctrl
        KeyEventTestCase('press', Key.shift, ['shift']),
        KeyEventTestCase('press', Key.ctrl, ['shift', 'ctrl']),
        KeyEventTestCase('release', Key.ctrl, ['shift']),
        KeyEventTestCase('release', Key.shift, []),
    ]


class KeyStateCache(object):
    def __init__(self):
        self.pressed_keys = set()
        self.released_keys = set()

    @property
    def has_pressing_keys(self):
        return len(self.pressed_keys) != 0

    def clear_state(self):
        self.pressed_keys.clear()
        self.released_keys.clear()

    def reset_state(self, key):
        self.pressed_keys.remove(key.name)
        self.released_keys.remove(key.name)

    def on_press(self, key):
        self.pressed_keys.add(key.name)

    def on_release(self, key):
        self.released_keys.add(key.name)

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()


@pytest.mark.run_with_display
class TestPatches:
    def test_run(self, key_event_test_cases):
        test_app = KeyTestApplication()
        for case in key_event_test_cases:
            test_app.add_test_case(case)
        failed_cases = test_app.run()

        assert failed_cases == []
