import imgui
from imgui import Vec2 as _Vec2

from .objects import Code as CodeSnippet

CODE_CHAR_WIDTH = 8
CODE_CHAR_HEIGHT = 17


__all__ = [
    'ImguiComponent',
    'MenuBar',
    'CodeSnippetWindow',
    'CodeNode',
    'CodeNodeLink',
    'CodeNodeViewer',
]


class Vec2(_Vec2):
    def __add__(self, *val):
        return Vec2(
            self.x + sum([v.x for v in val]),
            self.y + sum([v.y for v in val]),
        )

    def __sub__(self, val):
        return Vec2(
            self.x - val.x,
            self.y - val.y,
        )

    def __mul__(self, val):
        return Vec2(self.x * val, self.y * val)

    def __rmul__(self, val):
        return self.__mul__(val)


class ImguiComponent(object):
    def render(self):
        raise NotImplementedError


class MenuBar(ImguiComponent):
    def __init__(self, app):
        self.app = app

    def render(self):
        if imgui.begin_main_menu_bar():
            self.render_menu_file()
            imgui.end_main_menu_bar()

    def render_menu_file(self):
        if imgui.begin_menu('File', True):
            self._menu_file__import_snippet()
            self._menu_file__quit()
            imgui.end_menu()

    def _menu_file__quit(self):
        clicked, selected = imgui.menu_item('Quit')
        if clicked:
            exit(1)

    def _menu_file__import_snippet(self):
        clicked, selected = imgui.menu_item('Import Snippet', 'Ctrl+I')
        # TODO: implement this
        raise NotImplementedError


class CodeSnippetWindow(ImguiComponent):
    """A window to show code snippet."""

    def __init__(self, code_snippet, max_width=640, max_height=360):
        if not isinstance(code_snippet, CodeSnippet):
            raise TypeError(f'should be an instance of {CodeSnippet}')
        self.code_snippet = code_snippet
        self.window_name = f'snippet: {code_snippet.name}'
        self.rows = code_snippet.content.splitlines()

        n_digit = len('%i' % (len(self.rows) + code_snippet.line_start - 1))
        self.width_lineno = 15 * n_digit
        self.width_code = max([len(v) for v in self.rows]) * CODE_CHAR_WIDTH
        self.width = min(self.width_lineno + self.width_code, max_width)
        self.height = min((len(self.rows) + 1) * CODE_CHAR_HEIGHT + 45, max_height)

        self.selected = [False] * len(self.rows)
        self.expanded = True
        self.opened = False

    def reset_selected(self):
        self.selected = [False] * len(self.rows)

    def initialize_table(self):
        self.expanded, self.opened = imgui.begin(self.window_name, closable=True)
        imgui.set_window_size(self.width, self.height)
        imgui.columns(2)
        imgui.separator()
        imgui.set_column_width(0, self.width_lineno)

    def handle_selectable_row(self, i, row):
        """Deal with range selection by SHIFT key + click. Possible conditions:
        1. not clicked:
            do nothing.
        2. clicked, no selected item:
            set first selected item.
        3. clicked with SHIFT key, there is already a selected item:
            set True to all items in the range of previously and currently selected ones.
        4. clicked without SHIFT key, there is already a selected item:
            clear all selection and set current item to selected.
        """
        clicked, selected = imgui.selectable(row, selected=self.selected[i])

        if clicked:
            if not any(self.selected):
                self.selected[i] = True
            elif imgui.get_io().key_shift:
                idx_curr = i
                idx_prev = self.selected.index(True)
                self.reset_selected()
                if idx_prev > idx_curr:
                    idx_prev, idx_curr = idx_curr, idx_prev
                len_range = idx_curr - idx_prev + 1
                self.selected[idx_prev:idx_curr] = [True] * len_range
            else:
                self.reset_selected()
                self.selected[i] = True

    def create_context_menu(self):
        states = {'opened': False}

        def context_menu():
            if not states['opened']:
                states['opened'] = imgui.begin_popup_context_item('Context menu', mouse_button=2)
            else:
                return

            if states['opened']:
                imgui.selectable('link to root')
                imgui.selectable('link to leaf')
                imgui.end_popup()
        return context_menu

    def render(self):
        if not self.opened:
            return

        self.initialize_table()
        if not self.opened:
            imgui.end()
            return

        context_menu = self.create_context_menu()
        line_offset = self.code_snippet.line_start
        for i, row in enumerate(self.rows):
            imgui.text(str(i + line_offset))
            imgui.next_column()

            self.handle_selectable_row(i, row)
            if self.selected[i]:
                context_menu()
            imgui.next_column()
        imgui.separator()
        imgui.end()


class CodeNodeLink(ImguiComponent):
    def __init__(self, leaf_idx, leaf_slot, root_idx, root_slot):
        self.leaf_idx = leaf_idx
        self.leaf_slot = leaf_slot
        self.root_idx = root_idx
        self.root_slot = root_slot


NODE_SLOT_RADIUS = 4.0
NODE_WINDOW_PADDING = Vec2(8.0, 8.0)

class CodeNode(ImguiComponent):
    def __init__(self, _id, name, pos, code_snippet_window):
        """
        Parameters
        ----------
        _id : int
        name : str
        pos : Vec2
        code_snippet_window: CodeSnippetWindow
        """
        self.id = _id
        self.name = name
        self.pos = pos
        self.size = Vec2(320, 180)
        self.code_snippet_window = code_snippet_window
        self.root = None
        self.leaves = []
        self.container = None

    def set_root(self, root_node):
        self.root = root_node

    def add_leaf(self, leaf_node):
        self.leaves.append(leaf_node)

    def get_leaf_slot_pos(self, slot_no):
        y = self.pos.y + self.size.y * (slot_no + 1) / (len(self.leaves) + 1)
        return Vec2(self.pos.x, y)

    def get_root_slot_pos(self):
        return Vec2(self.pos.x + self.size.x, self.pos.y + self.size.y / 2.)

    def set_container(self, container):
        if not isinstance(container, CodeNodeViewer):
            raise TypeError(f'require a container {CodeNodeViewer} to render')
        self.container = container

    def render(self, draw_list, offset):
        assert isinstance(self.container, CodeNodeViewer), (
            f'require a container {CodeNodeViewer} to render, got {self.container}'
        )

        node_rect_min = Vec2(*(offset + self.pos))

        # Display node contents first
        draw_list.channels_set_current(1)   # foreground
        old_any_active = imgui.is_any_item_active()
        imgui.set_cursor_screen_pos(node_rect_min + NODE_WINDOW_PADDING)
        imgui.begin_group()
        imgui.text(f'{self.name}')
        imgui.end_group()

        # Save the size
        self.size = Vec2(*imgui.get_item_rect_size()) + 2 * NODE_WINDOW_PADDING
        node_rect_max = node_rect_min + self.size

        # Display node box
        draw_list.channels_set_current(0)
        imgui.set_cursor_screen_pos(node_rect_min)
        imgui.invisible_button('node', *self.size)

        # Display CodeSnippetWindow
        if imgui.is_item_hovered():
            # Open CodeSnippetWindow when double-clicked or CTRL + click
            if imgui.is_mouse_double_clicked() or (
                imgui.get_io().key_ctrl and imgui.is_mouse_clicked()
            ):
                self.code_snippet_window.opened = True
                imgui.set_next_window_focus()
        self.code_snippet_window.render()

        # TODO: for context menu
        self.container.handle_active_node(self, old_any_active)

        # NOTE: we cannot predefined colors since renderer should be assigned first.
        node_bg_color = imgui.get_color_u32_rgba(0.7, 0.3, 0.3, 1) if (
            self.container.check_node_activated(self)
        ) else imgui.get_color_u32_rgba(0.25, 0.25, 0.25, 1)
        node_fg_color = imgui.get_color_u32_rgba(0.5, 0.5, 0.5, 1)

        draw_list.add_rect_filled(*node_rect_min, *node_rect_max, node_bg_color, 4.0)
        draw_list.add_rect(*node_rect_min, *node_rect_max, node_fg_color, 4.0)


class CodeNodeViewer(ImguiComponent):
    """ A viewer for CodeNode.
    reference: https://gist.github.com/ocornut/7e9b3ec566a333d725d4
    """
    def __init__(self, app):
        self.app = app
        self.nodes = []
        self.links = []
        self.id_selected = -1
        self.id_hovered_in_list = -1
        self.id_hovered_in_scene = -1
        self.panning = Vec2(0.0, 0.0)
        self.show_grid = False
        self.open_context_menu = False
        self.temp_flag = True
        self.prev_dragging_delta = Vec2(0.0, 0.0)
        self.prev_panning_delta = Vec2(0.0, 0.0)

    def reset_hovered_id_cache(self):
        self.id_hovered_in_list = -1
        self.id_hovered_in_scene = -1

    def reset_dragging_delta(self):
        self.prev_dragging_delta = Vec2(0.0, 0.0)

    def reset_panning_delta(self):
        self.prev_panning_delta =  Vec2(0.0, 0.0)

    def check_node_activated(self, node):
        return (
            self.id_hovered_in_list == node.id or
            self.id_hovered_in_scene == node.id or
            (self.id_hovered_in_list == -1 and self.id_selected == node.id)
        )

    def init_canvas(self):
        imgui.text(f'Hold middle mouse button to pan ({self.panning.x}, {self.panning.y})')
        imgui.same_line(imgui.get_window_width() - 225)
        _, self.show_grid = imgui.checkbox('Show grid', self.show_grid)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, Vec2(1, 1))
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, Vec2(0, 0))
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, *(0.05, 0.1, 0.15))
        imgui.begin_child('panning_region', 0, 0, flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_MOVE)
        imgui.pop_style_var()
        imgui.pop_style_var()
        imgui.pop_style_color()
        imgui.push_item_width(120.0)

    def finalize_canvas(self):
        imgui.end_child()

    def handle_active_node(self, node, old_any_active):
        node_widgets_active = (not old_any_active) and imgui.is_any_item_active()

        if imgui.is_item_hovered():
            self.id_hovered_in_scene = node.id
            self.open_context_menu = imgui.is_mouse_clicked(1)

        node_moving_active = imgui.is_item_active()
        if node_widgets_active or node_moving_active:
            self.id_selected = node.id
        if node_moving_active:
            if imgui.is_mouse_dragging(0):
                curr_delta = Vec2(*imgui.get_mouse_drag_delta(0))
                delta = curr_delta - self.prev_dragging_delta
                node.pos = node.pos + delta
                self.prev_dragging_delta = curr_delta
            else:
                # NOTE: Reset it only when mouse is not dragging to avoid redundant
                # calls even when a node is not clicked.
                self.reset_dragging_delta()

    def handle_context_menu(self):
        pass

    def handle_panning(self):
        if not imgui.is_window_hovered():
            return
        if not imgui.is_any_item_active() and imgui.is_mouse_dragging(1):
            curr_delta = Vec2(*imgui.get_mouse_drag_delta(1))
            delta = curr_delta - self.prev_panning_delta
            self.panning = self.panning + delta
            self.prev_panning_delta = curr_delta
        else:
            self.reset_panning_delta()

    def display_grid(self, draw_list):
        grid_color = imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 0.15)
        grid_size = 64.0
        win_pos = Vec2(*imgui.get_cursor_screen_pos())
        canvas_size = Vec2(*imgui.get_window_size())

        x = self.panning.x % grid_size
        while x < canvas_size.x:
            draw_list.add_line(
                *(Vec2(x, 0.0) + win_pos),
                *(Vec2(x, canvas_size.y) + win_pos),
                grid_color
            )
            x += grid_size

        y = self.panning.y % grid_size
        while y < canvas_size.y:
            draw_list.add_line(
                *(Vec2(0.0, y) + win_pos),
                *(Vec2(canvas_size.x, y) + win_pos),
                grid_color
            )
            y += grid_size

    def display_links(self, draw_list, offset):
        draw_list.channels_split(2)
        draw_list.channels_set_current(0)   # background

        for link in self.links:
            node_leaf = self.nodes[link.leaf_idx]
            node_root = self.nodes[link.root_idx]
            p1 = offset + node_leaf.get_root_slot_pos()
            p2 = offset + node_root.get_leaf_slot_pos(link.root_slot)
            draw_list.add_line(*p1, *p2, imgui.get_color_u32_rgba(1, 1, 0, 1))
            slot_color = imgui.get_color_u32_rgba(0.75, 0.75, 0.75, 1)
            draw_list.add_circle_filled(*p1, 4.0, slot_color)
            draw_list.add_circle_filled(*p2, 4.0, slot_color)

    def display_nodes(self, draw_list, offset):
        for node in self.nodes:
            imgui.push_id(str(node.id))
            node.render(draw_list, offset)
            imgui.pop_id()

    def draw_node_list(self):
        imgui.begin_child('node_list', 100, 0)
        imgui.text('nodes')
        imgui.separator()

        for node in self.nodes:
            imgui.push_id(str(node.id))
            clicked, selected = imgui.selectable(node.name, node.id == self.id_selected)
            if clicked:
                self.id_selected = node.id
            if imgui.is_item_hovered():
                self.id_hovered_in_list = node.id
                self.open_context_menu = imgui.is_mouse_clicked(1)
            imgui.pop_id()

        imgui.end_child()

    def draw_node_canvas(self):
        self.reset_hovered_id_cache()

        imgui.begin_group()
        self.init_canvas()

        offset = Vec2(*imgui.get_cursor_screen_pos()) + self.panning
        draw_list = imgui.get_window_draw_list()

        if self.show_grid:
            self.display_grid(draw_list)
        self.display_links(draw_list, offset)
        self.display_nodes(draw_list, offset)

        draw_list.channels_merge()

        self.handle_context_menu()
        self.handle_panning()
        self.finalize_canvas()

        imgui.end_group()

    def render(self):
        imgui.begin('CodeNodeViewer')
        imgui.set_window_size(600, 400)
        self.draw_node_list()
        imgui.same_line()
        self.draw_node_canvas()
        imgui.separator()
        imgui.end()
