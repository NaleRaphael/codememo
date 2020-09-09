import imgui
from imgui.integrations.pyglet import create_renderer
import pyglet
from pyglet import gl

from .components import (
    ImguiComponent,
    MenuBar,
    CodeSnippetWindow,
    CodeNodeViewer,
    ErrorMessageModal,
)
from .config import AppConfig
from .interanl import GlobalState

__all__ = ['Application']


class Application(object):
    def __init__(self):
        self.config = AppConfig.load()
        self.frame_update_interval = self.config.display.frame_update_interval
        self.window = pyglet.window.Window(width=960, height=540, resizable=True)
        gl.glClearColor(0, 0, 0, 1)

        imgui.create_context()
        self.imgui_impl = create_renderer(self.window)

        self.imgui_components = []
        self.init_components()
        self.init_draw_process()

        self._removed_components = []
        self._internal_state = GlobalState()

    def init_components(self):
        self.imgui_components = [
            MenuBar(self),
        ]

    def init_draw_process(self):
        def update(dt):
            imgui.new_frame()
            try:
                for component in self.imgui_components:
                    while self._internal_state.error_occured:
                        error = self._internal_state.pop_error()
                        self.add_component(ErrorMessageModal(self, str(error)))
                    component.render()
            except Exception as ex:
                self.dump_data(ex)

        @self.window.event
        def on_draw():
            # TODO: limit fps? Currently, passed `dt` does not affect fps
            # since draw event is triggered by `pyglet.window.event`.
            # However, using `pyglet.clock.schedule_interval(update, 1/fps)`
            # is less efficiently.
            update(self.frame_update_interval)

            self.window.clear()
            imgui.render()
            self.imgui_impl.render(imgui.get_draw_data())
            self.finalize()

        # NOTE: Avoid closing application when ESCAPE is pressed
        # ref: https://stackoverflow.com/a/3205391
        def on_key_press(symbol, modifiers):
            if symbol == pyglet.window.key.ESCAPE:
                return pyglet.event.EVENT_HANDLED

        self.window.push_handlers(on_key_press)

    def add_component(self, component):
        if not isinstance(component, ImguiComponent):
            raise TypeError(f'should be an instance of {ImguiComponent}')
        self.imgui_components.append(component)

    def remove_component(self, component):
        idx = self.imgui_components.index(component)
        self._removed_components.append(self.imgui_components.pop(idx))

    def dump_data(self, error):
        """Dump data if unexpected error occured."""
        from pathlib import Path
        from datetime import datetime
        import traceback

        crash_time = datetime.now().strftime('%Y%m%d-%H%M%S')
        dir_dump = Path(self.config.dir_config, f'dump_{crash_time}')
        dir_dump.mkdir(parents=True, exist_ok=True)

        serial_num = 0
        for component in self.imgui_components:
            if isinstance(component, CodeNodeViewer):
                if component.fn_src is None:
                    fn = f'untitled_{serial_num}.json'
                    serial_num += 1
                else:
                    fn = Path(component.fn_src).with_suffix('.json').name
                component.save_data(str(Path(dir_dump, fn)))

        fn_log = str(Path(dir_dump, 'traceback.txt'))
        with open(fn_log, 'w') as f:
            traceback.print_tb(error.__traceback__, limit=None, file=f)
            f.write(str(error))

    def finalize(self):
        while self._removed_components:
            comp = self._removed_components.pop()
            del comp

    def run(self):
        pyglet.app.run()
        self.imgui_impl.shutdown()
