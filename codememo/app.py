import imgui
from imgui.integrations.pyglet import create_renderer
import pyglet
from pyglet import gl

from .components import (
    ImguiComponent,
    MenuBar,
    CodeSnippetWindow,
    CodeNodeViewer,
)
from .config import FPS, FRAME_UPDATE_INTERVAL

__all__ = ['Application']


class Application(object):
    def __init__(self):
        self.window = pyglet.window.Window(width=960, height=540, resizable=True)
        gl.glClearColor(0, 0, 0, 1)

        imgui.create_context()
        self.imgui_impl = create_renderer(self.window)

        self.imgui_components = []
        self.init_components()
        self.init_draw_process()

        self._removed_components = []

    def init_components(self):
        self.imgui_components = [
            MenuBar(self),
        ]

    def init_draw_process(self):
        def update(dt):
            imgui.new_frame()
            for component in self.imgui_components:
                component.render()

        @self.window.event
        def on_draw():
            # TODO: limit fps? Currently, passed `dt` does not affect fps
            # since draw event is triggered by `pyglet.window.event`.
            # However, using `pyglet.clock.schedule_interval(update, 1/fps)`
            # is less efficiently.
            update(FRAME_UPDATE_INTERVAL)

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

    def finalize(self):
        while self._removed_components:
            comp = self._removed_components.pop()
            del comp

    def run(self):
        pyglet.app.run()
        self.imgui_impl.shutdown()
