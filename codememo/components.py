import imgui
from imgui import Vec2 as _Vec2

from .objects import (
    Snippet,
    Node,
    NodeLink,
    NodeCollection,
)

CODE_CHAR_WIDTH = 8
CODE_CHAR_HEIGHT = 17


__all__ = [
    'ImguiComponent',
    'MenuBar',
    'CodeSnippetWindow',
    'CodeNode',
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

    def __repr__(self):
        return f'<Vec2 ({self.x}, {self.y})>'


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
    DEFAULT_SNIPPET_WINDOW_HEIGHT = -140
    DEFAULT_COMMENT_WINDOW_HEIGHT = 60
    DEFAULT_COMMENT_BUFFER_SIZE = 4096

    def __init__(self, snippet, comment=None, max_width=640, max_height=360):
        if not isinstance(snippet, Snippet):
            raise TypeError(f'should be an instance of {Snippet}')
        self.snippet = snippet
        self.window_name = f'snippet: {snippet.name}'
        self.rows = snippet.content.splitlines()
        self.comment = '' if comment is None else comment

        n_digit = len('%i' % (len(self.rows) + snippet.line_start - 1))
        snippet_height = (len(self.rows) + 2) * CODE_CHAR_HEIGHT
        self.width_lineno = CODE_CHAR_WIDTH * n_digit
        self.width_code = max([len(v) for v in self.rows]) * CODE_CHAR_WIDTH
        self.width = min(self.width_lineno + self.width_code + 30, max_width)
        self.height = min(snippet_height + self.DEFAULT_COMMENT_WINDOW_HEIGHT, max_height)

        self.selected = [False] * len(self.rows)
        self.window_opened = False

        self.collapsing_header_expanded = True
        self.snippet_window_height = self.DEFAULT_SNIPPET_WINDOW_HEIGHT
        self.prev_hsplitter_dragging_delta_y = 0.0

    def reset_selected(self):
        self.selected = [False] * len(self.rows)

    def reset_hsplitter_draggin_delta_y(self):
        self.prev_hsplitter_dragging_delta_y = 0.0

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

    def handle_hsplitter(self):
        imgui.invisible_button('hsplitter', *imgui.Vec2(-1, 8))
        if imgui.is_item_active():
            if imgui.is_mouse_dragging(0):
                curr_delta = imgui.get_mouse_drag_delta(0).y
                delta = curr_delta - self.prev_hsplitter_dragging_delta_y
                self.snippet_window_height += delta
                self.prev_hsplitter_dragging_delta_y = curr_delta
            else:
                self.reset_hsplitter_draggin_delta_y()
            if imgui.is_mouse_double_clicked():
                self.snippet_window_height = self.DEFAULT_SNIPPET_WINDOW_HEIGHT

    def create_context_menu(self):
        states = {'opened': False}

        def context_menu():
            if not states['opened']:
                states['opened'] = imgui.begin_popup_context_item('Context menu', mouse_button=2)
            else:
                return

            if states['opened']:
                # imgui.selectable('link to root')  # TODO: should be in the context menu for the whole snippet
                imgui.selectable('link to leaf')
                imgui.end_popup()
        return context_menu

    def display_table(self):
        imgui.columns(2)

        imgui.text('no.')
        imgui.set_column_width(0, self.width_lineno)
        imgui.next_column()
        imgui.text('code')
        imgui.next_column()
        imgui.separator()

        context_menu = self.create_context_menu()
        for i, row in enumerate(self.rows):
            imgui.text(str(i+1))
            imgui.next_column()

            self.handle_selectable_row(i, row)
            if self.selected[i]:
                context_menu()
            imgui.next_column()

    def display_comment_window(self):
        imgui.push_item_width(-1)
        changed, text = imgui.input_text_multiline('', self.comment, self.DEFAULT_COMMENT_BUFFER_SIZE, height=-5)
        if changed:
            self.comment = text
        imgui.pop_item_width()

    def render(self):
        if not self.window_opened:
            return
        _, self.window_opened = imgui.begin(self.window_name, closable=True, flags=imgui.WINDOW_NO_SCROLLBAR)
        if not self.window_opened:
            imgui.end()
            return
        imgui.set_window_size(self.width, self.height)

        # --- Make the height of the following windows adjustable
        # ref: https://github.com/ocornut/imgui/issues/125#issuecomment-135775009
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, imgui.Vec2(0, 0))

        # Table for code snippet
        current_window_size = imgui.get_window_content_region_max()
        if self.collapsing_header_expanded:
            h_snippet = self.snippet_window_height
        else:
            h_snippet = current_window_size.y - 60
        imgui.begin_child('code snippet', -5, h_snippet, border=True, flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR)
        self.display_table()
        imgui.end_child()

        # Horizontal splitter
        self.handle_hsplitter()

        # Comment window
        imgui.begin_child('comment', 0, 0, border=False, flags=imgui.WINDOW_NO_SCROLLBAR)
        self.collapsing_header_expanded, visible = imgui.collapsing_header('Comment')
        if self.collapsing_header_expanded:
            self.display_comment_window()
        imgui.end_child()

        imgui.pop_style_var()
        # ---

        imgui.end()


NODE_SLOT_RADIUS = 4.0
NODE_WINDOW_PADDING = Vec2(8.0, 8.0)

class CodeNodeComponent(ImguiComponent):
    def __init__(self, _id, pos, node):
        """
        Parameters
        ----------
        _id : int
        name : str
        pos : Vec2
        node : codememo.objects.Node
        """
        self.id = _id
        self.pos = pos
        self.size = Vec2(320, 180)
        self.node = node
        self.root = node.root
        self.leaves = node.leaves
        self.name = node.snippet.name
        self.snippet_window = CodeSnippetWindow(node.snippet, node.comment)
        self.container = None

    def get_leaf_slot_pos(self, slot_no):
        y = self.pos.y + self.size.y * (slot_no + 1) / (len(self.leaves) + 1)
        return Vec2(self.pos.x + self.size.x, y)

    def get_root_slot_pos(self):
        return Vec2(self.pos.x, self.pos.y + self.size.y / 2.)

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
        imgui.text(f'{self.node.snippet.name}')
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
                self.snippet_window.window_opened = True
                imgui.set_next_window_focus()
        self.snippet_window.render()

        # TODO: for context menu
        self.container.handle_active_node(self, old_any_active)

        # NOTE: we cannot predefined colors since renderer should be assigned first.
        node_bg_color = imgui.get_color_u32_rgba(0.7, 0.3, 0.3, 1) if (
            self.container.check_node_activated(self)
        ) else imgui.get_color_u32_rgba(0.25, 0.25, 0.25, 1)
        node_fg_color = imgui.get_color_u32_rgba(0.5, 0.5, 0.5, 1)

        draw_list.add_rect_filled(*node_rect_min, *node_rect_max, node_bg_color, 4.0)
        draw_list.add_rect(*node_rect_min, *node_rect_max, node_fg_color, 4.0)


LAYOUT_NODE_OFFSET_X = 80
LAYOUT_NODE_OFFSET_Y = 80

class CodeNodeViewer(ImguiComponent):
    """ A viewer for CodeNodeComponent.
    reference: https://gist.github.com/ocornut/7e9b3ec566a333d725d4
    """
    def __init__(self, app, node_collection):
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
        self.opened = False

        self.init_nodes_and_links(node_collection)

    def init_nodes_and_links(self, node_collection):
        trees, orphans = node_collection.resolve_tree()
        self.links = node_collection.resolve_index_links_from_trees(trees)

        # Calculate node positions for layout, note that orphan nodes are prepended
        # at the first column.
        positions = []
        ux, uy = LAYOUT_NODE_OFFSET_X, LAYOUT_NODE_OFFSET_Y
        x_offset = ux if len(orphans) != 0 else 0
        y_offset = 0
        tree_widths = [max([len(layer) for layer in tree]) for tree in trees]
        for n, tree in enumerate(trees):
            for i, layer in enumerate(tree):
                for j, node in enumerate(layer):
                    positions.append(Vec2(i*ux + x_offset, j*uy + y_offset))
            # update `y_offset` for next tree
            y_offset += tree_widths[n] * uy
        for i, v in enumerate(orphans):
            positions.append(Vec2(0, i*uy))

        # Instantiate `CodeNodeComponent`s with calculated positions
        nodes = []
        for tree in trees:
            nodes.extend([v for layer in tree for v in layer])
        nodes.extend(orphans)
        self.nodes = [CodeNodeComponent(i, positions[i], v) for i, v in enumerate(nodes)]

        # Set container (viewer) for nodes
        for node in self.nodes:
            node.set_container(self)

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
            p2 = offset + node_root.get_leaf_slot_pos(link.leaf_slot)
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

    def display_menu_bar(self):
        imgui.begin_menu_bar()
        if imgui.begin_menu('File'):
            imgui.menu_item('Save', 'Ctrl+S')
            clicked, selected = imgui.menu_item('Quit')
            if clicked:
                self.close()
            imgui.end_menu()
        imgui.end_menu_bar()

    def close(self):
        """Let host application know that this component is going to be closed,
        and clear references to this object in order to release memory."""
        self.app.remove_component(self)
        self.nodes = []
        self.links = []
        self.app = None

    def render(self):
        _, self.opened = imgui.begin('CodeNodeViewer', closable=True, flags=imgui.WINDOW_MENU_BAR)
        if not self.opened:
            imgui.end()
            self.close()
            return

        imgui.set_window_size(600, 400)
        self.display_menu_bar()
        self.draw_node_list()
        imgui.same_line()
        self.draw_node_canvas()
        imgui.separator()
        imgui.end()
