import sys

import pygame
import OpenGL.GL as gl
from imgui.integrations.pygame import PygameRenderer
import imgui

from codememo.components import (
    ImguiComponent,
    MenuBar,
    CodeSnippetWindow,
    CodeNodeViewer,
    ErrorMessageModal,
)
from codememo.config import AppConfig, AppHistory
from codememo.interanl import GlobalState
from codememo.shortcuts import ShortcutRegistry, IOWrapper


class PygameIOWrapper(IOWrapper):
    def __init__(self, io):
        super(PygameIOWrapper, self).__init__(io)

    def is_key_pressed(self, key):
        pass


class PygameApplication(object):
    def __init__(self):
        self.config = AppConfig.load()
        self.history = AppHistory.load(self.config.fn_history)

        self.frame_update_interval = self.config.display.frame_update_interval

        size = (960, 540)
        self.init_pygame_window(size)

        imgui.create_context()
        self.imgui_impl = PygameRenderer()

        io = imgui.get_io()
        io.display_size = size

        self.shortcuts_registry = ShortcutRegistry(PygameIOWrapper(self.imgui_impl.io))

        self.imgui_components = []
        self.init_components()

        self._removed_components = []
        self._internal_state = GlobalState()

    def init_pygame_window(self, size):
        pygame.init()
        pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)

    def init_components(self):
        self.imgui_components = [
            MenuBar(self),
        ]

    def main_loop(self):
        def update_frame():
            imgui.new_frame()
            try:
                for component in self.imgui_components:
                    while self._internal_state.error_occured:
                        error = self._internal_state.pop_error()
                        self.add_component(ErrorMessageModal(self, str(error)))
                    component.render()
            except Exception as ex:
                self.dump_data(ex)

        def draw_frame():
            update_frame()

            gl.glClearColor(0, 0, 0, 1)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            imgui.render()
            self.imgui_impl.render(imgui.get_draw_data())
            pygame.display.flip()
            self.finalize()

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            self.imgui_impl.process_event(event)
            draw_frame()

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
            import sys
            traceback.print_exception(*sys.exc_info())
            traceback.print_tb(error.__traceback__, limit=None, file=f)
            f.write(str(error))

    def finalize(self):
        while self._removed_components:
            comp = self._removed_components.pop()
            del comp

    def run(self):
        self.main_loop()


if __name__ == '__main__':
    app = PygameApplication()
    app.run()
