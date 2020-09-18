from pathlib import Path

from .vendor import imgui
from .vendor.imgui import Vec2 as _Vec2

from .objects import (
    Snippet,
    Node,
    NodeLink,
    NodeCollection,
)
from .events import NodeEvent, NodeEventPublisher
from .interanl import GlobalState

CODE_CHAR_WIDTH = 8
CODE_CHAR_HEIGHT = 14


__all__ = [
    'ImguiComponent',
    'MenuBar',
    'CodeSnippetWindow',
    'CodeNode',
    'CodeNodeCreatorWindow',
    'CodeNodeViewer',
    'ErrorMessageModal',
    'ConfirmationModal',
    'OpenFileDialog',
    'SaveFileDialog',
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
        self.file_dialog = None

    def render(self):
        if imgui.begin_main_menu_bar():
            self.render_menu_file()
            imgui.end_main_menu_bar()

    def render_menu_file(self):
        if imgui.begin_menu('File', True):
            self._menu_file__new_project()
            self._menu_file__open_project()
            imgui.separator()
            self._menu_file__quit()
            imgui.end_menu()

    def _menu_file__quit(self):
        clicked, selected = imgui.menu_item('Quit')
        if clicked:
            exit(1)

    def _menu_file__new_project(self):
        clicked, selected = imgui.menu_item('New Project', 'Ctrl+N')
        if clicked:
            self.app.add_component(CodeNodeViewer(self.app, NodeCollection([])))

    def _menu_file__open_project(self):
        clicked, selected = imgui.menu_item('Open Project', 'Ctrl+O')

        if clicked:
            def open_project(fn):
                try:
                    node_collection = NodeCollection.load(fn)
                except Exception as ex:
                    GlobalState().push_error(ex)
                else:
                    viewer = CodeNodeViewer(self.app, node_collection, fn_src=fn)
                    self.app.add_component(viewer)

            self.file_dialog = OpenFileDialog(self.app, open_project)


class CodeSnippetWindow(ImguiComponent):
    """A window to show code snippet."""
    DEFAULT_SNIPPET_WINDOW_HEIGHT = -140
    DEFAULT_SNIPPET_BUFFER_SIZE = 65536
    DEFAULT_COMMENT_WINDOW_HEIGHT = 60
    DEFAULT_COMMENT_BUFFER_SIZE = 4096

    def __init__(self, node, max_width=640, max_height=360, **kwargs):
        self.node = node
        snippet = node.snippet
        self.snippet = snippet
        self.window_name = f'snippet: {snippet.name}'
        rows = snippet.content.splitlines()
        self.rows = [''] if len(rows) == 0 else rows
        self.comment = '' if node.comment is None else node.comment

        self.event_publisher = NodeEventPublisher()

        n_digit = len('%i' % (len(self.rows) + snippet.line_start - 1))
        snippet_height = (len(self.rows) + 2) * CODE_CHAR_HEIGHT
        self._snippet_height = snippet_height
        self.width_lineno = CODE_CHAR_WIDTH * n_digit
        self.width_code = max([len(v) for v in self.rows]) * CODE_CHAR_WIDTH
        self.width = min(self.width_lineno + self.width_code + 30, max_width)
        self.height = min(snippet_height + self.DEFAULT_COMMENT_WINDOW_HEIGHT + 20, max_height)

        self.selected = [False] * len(self.rows)
        self.reference_info = None
        self.window_opened = False

        self.collapsing_header_expanded = True
        self.snippet_window_height = self.DEFAULT_SNIPPET_WINDOW_HEIGHT
        self.prev_hsplitter_dragging_delta_y = 0.0

        self.is_edit_mode = False
        self.edited_content = ''    # used for caching snippet content for editing

        # Additional settings for text input
        self.convert_tab_to_spaces = kwargs.get('convert_tab_to_spaces', True)
        self.tab_to_spaces_number = kwargs.get('tab_to_spaces_number', 4)

        self.input_text_callback_flags = (
            imgui.INPUT_TEXT_ALLOW_TAB_INPUT |
            imgui.INPUT_TEXT_CALLBACK_ALWAYS |
            imgui.INPUT_TEXT_CALLBACK_CHAR_FILTER |
            imgui.INPUT_TEXT_CALLBACK_RESIZE
        )
        self.input_text_callback_config = imgui.core.InputTextCallbackConfig(
            convert_tab_to_spaces=self.convert_tab_to_spaces,
            tab_to_spaces_number=self.tab_to_spaces_number,
        )

    def reset_selected(self):
        self.selected = [False] * len(self.rows)

    def reset_hsplitter_draggin_delta_y(self):
        self.prev_hsplitter_dragging_delta_y = 0.0

    def get_selected_lines(self):
        start = self.selected.index(True) + 1
        stop = len(self.selected) - self.selected[::-1].index(True)
        stop = stop if start != stop else None
        if stop and not all(self.selected[start:stop]):
            raise RuntimeError('Seleted rows are not contiguous')
        return start, stop

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
        highlighted = (self.reference_info is not None) and self.reference_info.line_info.in_range(i+1)
        if highlighted:
            imgui.push_style_color(imgui.COLOR_HEADER, 0.5, 0.8, 0.5, 0.4)
            clicked, selected = imgui.selectable(row, selected=True)
            imgui.pop_style_color()
        else:
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
        if self.collapsing_header_expanded:
            imgui.push_style_color(imgui.COLOR_BUTTON, 1, 1, 1, 0.1)
            imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 1, 1, 1, 0.1)
            imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 1, 1, 1, 0.1)
            imgui.begin_group()
            imgui.invisible_button('##spacing', *imgui.Vec2(-1, 3))
            imgui.set_cursor_pos_x(10)
            imgui.button('##hsplitter', *imgui.Vec2(-5, 2))
            imgui.invisible_button('##spacing', *imgui.Vec2(-1, 3))
            imgui.end_group()
            imgui.pop_style_color()
            imgui.pop_style_color()
            imgui.pop_style_color()

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
        else:
            imgui.invisible_button('##hsplitter', *imgui.Vec2(-1, 8))

    def create_context_menu(self):
        states = {'opened': False}

        def context_menu(is_any_row_selected):
            if not states['opened']:
                states['opened'] = imgui.begin_popup_context_item('Context menu', mouse_button=2)
            else:
                return

            if states['opened']:
                # Prepare to enter edit mode
                if imgui.selectable('Edit')[0]:
                    self.is_edit_mode = True
                    self.edited_content = self.node.snippet.content

                # Clear highlighted lines
                if imgui.selectable('Clear highlight')[0] and self.reference_info:
                    self.reference_info = None

                # Add the following menu items only when lines are selected
                if is_any_row_selected:
                    if imgui.selectable('Add leaf reference')[0]:
                        ref_start, ref_stop = self.get_selected_lines()
                        event_args = dict(
                            root_node=self.node,
                            ref_start=ref_start,
                            ref_stop=ref_stop,
                        )
                        event = NodeEvent('add_reference', **event_args)
                        self.event_publisher.dispatch(event)
                    if imgui.selectable('Cancel selection')[0]:
                        self.reset_selected()
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

        for i, row in enumerate(self.rows):
            imgui.text(str(i+1))
            imgui.next_column()
            self.handle_selectable_row(i, row)
            imgui.next_column()

    def display_comment_window(self):
        imgui.push_item_width(-1)
        changed, text = imgui.input_text_multiline(
            '##comment', self.comment, self.DEFAULT_COMMENT_BUFFER_SIZE, height=-5,
            flags=self.input_text_callback_flags, callback_config=self.input_text_callback_config
        )
        if changed:
            self.comment = text
        imgui.pop_item_width()

    def _render_view_mode(self):
        # Make the height of the following windows adjustable
        # ref: https://github.com/ocornut/imgui/issues/125#issuecomment-135775009
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, imgui.Vec2(0, 0))

        # Table for code snippet
        current_window_size = imgui.get_window_content_region_max()
        if self.collapsing_header_expanded:
            h_snippet = self.snippet_window_height
        else:
            h_snippet = current_window_size.y - 60
        imgui.set_next_window_content_size(self.width_code, self._snippet_height)
        imgui.begin_child(
            'code snippet', -5, h_snippet, border=True,
            flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR
        )
        self.display_table()
        imgui.end_child()

        # Context menu
        # NOTE: This should be invoked right after the end of displaying table.
        context_menu = self.create_context_menu()
        is_any_row_selected = any(self.selected)
        context_menu(is_any_row_selected)

        # Horizontal splitter
        self.handle_hsplitter()

        # Comment window
        imgui.begin_child('comment', 0, 0, border=False, flags=imgui.WINDOW_NO_SCROLLBAR)
        self.collapsing_header_expanded, visible = imgui.collapsing_header('Comment')
        if self.collapsing_header_expanded:
            self.display_comment_window()
        imgui.end_child()

        imgui.pop_style_var()

    def _render_edit_mode(self):
        imgui.begin_child('code snippet', 0, -25, border=False)
        imgui.push_item_width(-1)
        changed, text = imgui.input_text_multiline(
            '##code-snippet-content', self.edited_content,
            self.DEFAULT_SNIPPET_BUFFER_SIZE, height=-5,
            flags=self.input_text_callback_flags,
            callback_config=self.input_text_callback_config,
        )
        if changed:
            self.edited_content = text
        imgui.pop_item_width()
        imgui.end_child()

        # Buttons
        imgui.begin_group()
        pos = Vec2(*imgui.get_cursor_position())
        width = imgui.get_window_content_region_width()
        imgui.set_cursor_pos(Vec2(pos.x + width - 92, pos.y))
        is_btn_save_clicked = imgui.button('Save')
        imgui.same_line()
        is_btn_cancel_clicked = imgui.button('Cancel')
        imgui.end_group()

        if is_btn_save_clicked:
            self.is_edit_mode = False
            self.node.snippet.content = self.edited_content
            self.rows = self.node.snippet.content.splitlines()
            self.selected = [False] * len(self.rows)
            self.edited_content = ''
        elif is_btn_cancel_clicked:
            self.is_edit_mode = False
            self.edited_content = ''

    def render(self):
        if not self.window_opened:
            return
        _, self.window_opened = imgui.begin(self.window_name, closable=True, flags=imgui.WINDOW_NO_SCROLLBAR)
        if not self.window_opened:
            imgui.end()
            return
        imgui.set_window_size(self.width, self.height)

        if self.is_edit_mode:
            self._render_edit_mode()
        else:
            self._render_view_mode()

        imgui.end()


NODE_SLOT_RADIUS = 4.0
NODE_WINDOW_PADDING = Vec2(8.0, 8.0)
NODE_MAX_NAME_LEGNTH = 8    # number of characters

class CodeNodeComponent(ImguiComponent):
    def __init__(self, _id, pos, node, **kwargs):
        """
        Parameters
        ----------
        _id : int
            ID of this node.
        pos : Vec2
            Initial position of this node on canvas.
        node : codememo.objects.Node
            A `codememo.objects.Node` instance including necessary information
            for this node.
        """
        self.id = _id
        self.pos = pos
        self.size = Vec2(60, 13)    # just an initial value, should be set after rendered
        self.node = node
        self.root = node.root
        self.leaves = node.leaves
        self.name = node.snippet.name
        self.snippet_window = CodeSnippetWindow(node, **kwargs)
        self.container = None
        self.is_showing_context_menu = False
        self.confirmation_modal = False

    @property
    def display_name(self):
        """Name of node to display on canvas."""
        if len(self.name) > NODE_MAX_NAME_LEGNTH:
            return f'{self.name[:NODE_MAX_NAME_LEGNTH - 3]}...'
        else:
            return self.name

    def get_leaf_slot_pos(self, slot_no):
        y = self.pos.y + self.size.y * (slot_no + 1) / (len(self.leaves) + 1)
        return Vec2(self.pos.x + self.size.x, y)

    def get_root_slot_pos(self):
        return Vec2(self.pos.x, self.pos.y + self.size.y / 2.)

    def set_container(self, container):
        if not isinstance(container, CodeNodeViewer):
            raise TypeError(f'require a container {CodeNodeViewer} to render')
        self.container = container
        self.snippet_window.event_publisher.register(self.container)

    def handle_event__add_reference(self, event):
        root = event.get('root_node')
        kwargs = {k: event.get(k) for k in ['ref_start', 'ref_stop']}
        self.container.add_leaf_reference(root, self.node, **kwargs)

    def render(self, draw_list, offset):
        assert isinstance(self.container, CodeNodeViewer), (
            f'require a container {CodeNodeViewer} to render, got {self.container}'
        )

        # TODO: rewrite this with a better approach
        is_selecting_root_node = 'event__add_reference' in self.container.state_cache
        can_be_added_as_reference = self.node.root is None and is_selecting_root_node

        node_rect_min = Vec2(*(offset + self.pos))

        # Display node contents first
        draw_list.channels_set_current(1)   # foreground
        old_any_active = imgui.is_any_item_active()
        imgui.set_cursor_screen_pos(node_rect_min + NODE_WINDOW_PADDING)
        imgui.begin_group()
        imgui.text(f'{self.display_name}')
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
            # Show full name in tooltip if length of name is too long
            if len(self.name) > NODE_MAX_NAME_LEGNTH:
                imgui.set_tooltip(self.name)

            # Open CodeSnippetWindow when double-clicked or ALT + click
            if imgui.is_mouse_double_clicked() or (
                imgui.get_io().key_alt and imgui.is_mouse_clicked()
            ):
                self.snippet_window.window_opened = True
                imgui.set_next_window_focus()
        self.snippet_window.render()

        # Handle event of adding reference node
        if self.container.state_cache and can_be_added_as_reference:
            if imgui.is_item_clicked():
                event = self.container.state_cache['event__add_reference']
                self.handle_event__add_reference(event)

        # TODO: for context menu
        self.container.handle_active_node(self, old_any_active)

        # NOTE: we cannot predefined colors since renderer should be assigned first.
        node_bg_color = imgui.get_color_u32_rgba(0.7, 0.3, 0.3, 1) if (
            self.container.check_node_activated(self)
        ) else imgui.get_color_u32_rgba(0.25, 0.25, 0.25, 1)
        node_fg_color = imgui.get_color_u32_rgba(0.2, 0.8, 0.4, 1) if (
            can_be_added_as_reference
        ) else imgui.get_color_u32_rgba(0.5, 0.5, 0.5, 1)

        draw_list.add_rect_filled(*node_rect_min, *node_rect_max, node_bg_color, 4.0)
        draw_list.add_rect(*node_rect_min, *node_rect_max, node_fg_color, 4.0)

        self.is_showing_context_menu = imgui.begin_popup_context_item('node-context-menu', 2)
        if self.is_showing_context_menu:
            if self.node.root is not None and imgui.selectable('Remove root reference')[0]:
                # Can be used to reset reference_info when snippet are modified
                self.confirmation_modal = ConfirmationModal(
                    'Confirm',
                    'Are you sure you want to remove root reference of this node?',
                    lambda: self.container.remove_root_reference(self.node),
                )
            if imgui.selectable('Remove node')[0]:
                self.confirmation_modal = ConfirmationModal(
                    'Confirm',
                    f'Are you sure you want to remove this node \n"{self.name}"?',
                    lambda: self.container.remove_node_component(self),
                )
            imgui.end_popup()

        if self.confirmation_modal:
            self.confirmation_modal.render()
            if self.confirmation_modal.terminated:
                self.confirmation_modal = None


class CodeNodeCreatorWindow(ImguiComponent):
    """A window for creating node."""
    INPUT_SNIPPET_NAME_MAX_LENGTH = 128
    INPUT_SNIPPET_PATH_MAX_LENGTH = 256     # should depend on OS
    INPUT_SNIPPET_URL_MAX_LENGTH = 2048
    INPUT_SNIPPET_CONTENT_MAX_LENGTH = 65536
    INPUT_START_LINE_MAX_LENGTH = 16
    SUPPORTED_LANGUAGES = {
        '': 'raw',
        '.c': 'c', '.h': 'c',
        '.cpp': 'cpp', '.hpp': 'cpp',
        '.py': 'python', '.pyx': 'python',
    }

    def __init__(self, app, creation_pos=None, **kwargs):
        self.app = app
        self.creation_pos = creation_pos
        self.container = None
        self.event_publisher = NodeEventPublisher()
        self.valid_languages = list(set(self.SUPPORTED_LANGUAGES.values()))

        self.input_snippet_name = ''
        self.input_snippet_path = ''
        self.input_snippet_url = ''
        self.input_language_index = self.valid_languages.index('raw')
        self.input_snippet = ''
        self.input_start_line = '1'

        self.modal_opened = False

        # Additional settings for text input
        self.convert_tab_to_spaces = kwargs.get('convert_tab_to_spaces', True)
        self.tab_to_spaces_number = kwargs.get('tab_to_spaces_number', 4)

        self.input_text_callback_flags = (
            imgui.INPUT_TEXT_ALLOW_TAB_INPUT |
            imgui.INPUT_TEXT_CALLBACK_ALWAYS |
            imgui.INPUT_TEXT_CALLBACK_CHAR_FILTER |
            imgui.INPUT_TEXT_CALLBACK_RESIZE
        )
        self.input_text_callback_config = imgui.core.InputTextCallbackConfig(
            convert_tab_to_spaces=self.convert_tab_to_spaces,
            tab_to_spaces_number=self.tab_to_spaces_number,
        )

    def set_container(self, container):
        if not isinstance(container, CodeNodeViewer):
            raise TypeError(f'require a container {CodeNodeViewer} to render')
        self.container = container
        self.event_publisher.register(container)

    def close(self):
        self.app.remove_component(self)
        self.app = None

    def create(self):
        if self.input_snippet_name == '':
            error_msg = f'"Snippet name" cannot be empty'
            GlobalState().push_error(ValueError(error_msg))
            return

        lang = self.valid_languages[self.input_language_index]
        snippet = Snippet(
            self.input_snippet_name, self.input_snippet,
            line_start=None, lang=lang,
            path=self.input_snippet_path,
            url=self.input_snippet_url,
        )
        node = Node(snippet)
        event_args = dict(node=node, node_pos=self.creation_pos)
        event = NodeEvent('create_node', **event_args)
        self.event_publisher.dispatch(event)
        self.close()

    def display_error_modal(self, error_msg):
        imgui.open_popup('Error')
        self.modal_opened, _ = imgui.begin_popup_modal(
            'Error', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE
        )
        if self.modal_opened:
            imgui.text(f'Error: {error_msg}')
            if imgui.button('Close'):
                self.close()
            imgui.end_popup()

    def _check_input_number(self, value):
        try:
            int(value)
        except ValueError:
            return False
        if len(value) > self.INPUT_START_LINE_MAX_LENGTH:
            return False
        return True

    def render(self):
        imgui.begin('code-node-creater-window')
        imgui.set_window_size(300, 200)

        # Inputs
        imgui.begin_child('inputs', 0, -25)
        imgui.text('Snippet name:')
        imgui.same_line()
        imgui.push_item_width(-1)
        changed, text = imgui.input_text(
            '##snippet-name', self.input_snippet_name, self.INPUT_SNIPPET_NAME_MAX_LENGTH,
            flags=imgui.INPUT_TEXT_CHARS_NO_BLANK
        )
        imgui.pop_item_width()
        if changed:
            self.input_snippet_name = text

        # TODO: Detect language automatically

        imgui.text('Language:')
        imgui.same_line()
        imgui.push_item_width(-1)
        clicked, current = imgui.combo(
            '##language', self.input_language_index, self.valid_languages
        )
        imgui.pop_item_width()
        if clicked:
            self.input_language_index = current

        imgui.text('Path:')
        imgui.same_line()
        imgui.push_item_width(-1)
        changed, text = imgui.input_text(
            '##path', self.input_snippet_path, self.INPUT_SNIPPET_PATH_MAX_LENGTH
        )
        imgui.pop_item_width()
        if changed:
            self.input_snippet_path = text

        imgui.text('URL:')
        imgui.same_line()
        imgui.push_item_width(-1)
        changed, text = imgui.input_text(
            '##url', self.input_snippet_url, self.INPUT_SNIPPET_URL_MAX_LENGTH
        )
        imgui.pop_item_width()
        if changed:
            self.input_snippet_url = text

        imgui.text('Start line:')
        imgui.same_line()
        imgui.push_item_width(-1)
        changed, text = imgui.input_text(
            '##start-line', self.input_start_line, self.INPUT_START_LINE_MAX_LENGTH,
            flags=imgui.INPUT_TEXT_CHARS_NO_BLANK
        )
        imgui.pop_item_width()
        if changed:
            if self._check_input_number(text):
                self.input_start_line = text
            else:
                error_msg = (
                    f'Value of "Start line" should be an integer and not exceed '
                    f'{self.INPUT_START_LINE_MAX_LENGTH} digits.'
                )
                GlobalState().push_error(ValueError(error_msg))
                return

        imgui.text('Snippet:')
        imgui.push_item_width(-1)
        changed, text = imgui.input_text_multiline(
            '##snippet', self.input_snippet, self.INPUT_SNIPPET_CONTENT_MAX_LENGTH, height=-5,
            flags=self.input_text_callback_flags, callback_config=self.input_text_callback_config
        )
        imgui.pop_item_width()
        if changed:
            self.input_snippet = text
        imgui.end_child()

        # Buttons
        imgui.begin_group()
        pos = Vec2(*imgui.get_cursor_position())
        width = imgui.get_window_content_region_width()
        imgui.set_cursor_pos(Vec2(pos.x + width - 107, pos.y))
        is_btn_create_clicked = imgui.button('Create')
        imgui.same_line()
        is_btn_cancel_clicked = imgui.button('Cancel')
        imgui.end_group()

        if is_btn_create_clicked:
            self.create()
        if is_btn_cancel_clicked:
            self.close()

        imgui.end()


LAYOUT_NODE_OFFSET_X = 80
LAYOUT_NODE_OFFSET_Y = 80

class CodeNodeViewer(ImguiComponent):
    """ A viewer for CodeNodeComponent.
    reference: https://gist.github.com/ocornut/7e9b3ec566a333d725d4
    """
    def __init__(self, app, node_collection, fn_src=None):
        """
        Parameters
        ----------
        app : codememo.Application
            Reference of running application.
        node_collection : codememo.objects.NodeCollection
            Collection of nodes.
        fn_src : str, optional
            Filename of the source which `node_collection` is loaded from.
        """
        self.app = app
        self.fn_src = fn_src

        # NOTE: We should avoid duplicate of window name (identifier) because
        # it relates to the focus mechanism. See also the implementation of
        # `CodeNodeViewer.handle_event__add_reference()`
        fn = 'untitled' if fn_src is None else Path(fn_src).with_suffix('').name
        self.window_name = f'CodeNode Viewer: {fn}'

        self.node_collection = node_collection
        self.node_components = []
        self.links = []
        self.id_selected = -1
        self.id_hovered_in_list = -1
        self.id_hovered_in_scene = -1
        self.panning = Vec2(0.0, 0.0)

        # Screen position of node canvas, it can be use as a reference to
        # calculate mousce position on canvas when we are going to create
        # a node. And here it's just an initail value, it should be updated
        # by `self.draw_node_canvas()`.
        self._canvas_screen_pos = Vec2(0.0, 0.0)

        # --- Flags for view control
        # Show grid
        self.show_grid = False
        # Highlight lines in CodeSnippetWindow when leaf node is clicked
        self.enable_reference_highlight = True

        self.file_dialog = None

        self.prev_dragging_delta = Vec2(0.0, 0.0)
        self.prev_panning_delta = Vec2(0.0, 0.0)
        self.opened = False
        self.state_cache = {}

        self.init_nodes_and_links()

    @classmethod
    def load(self, app, fn):
        node_collection = NodeCollection.load(fn)
        return cls(app, node_collection, fn_src=fn)

    def save_data(self, fn):
        self.node_collection.save(fn)

        # Update window name
        self.fn_src = fn
        self.window_name = f"CodeNode Viewer: {Path(fn).with_suffix('').name}"

    def add_leaf_reference(self, root, target, **kwargs):
        try:
            self.node_collection.add_leaf_reference(root, target, **kwargs)
            self.links = self.node_collection.resolve_links()
        except Exception as ex:
            GlobalState().push_error(ex)

    def remove_root_reference(self, node):
        try:
            self.node_collection.remove_root_reference(node)
            self.links = self.node_collection.resolve_links()
        except Exception as ex:
            GlobalState().push_error(ex)

    def init_nodes_and_links(self):
        trees, orphans = self.node_collection.resolve_tree()
        self.links = self.node_collection.resolve_links_from_trees(trees)

        # TODO: add a flag to control whether we should re-calculate the layout
        # (would be useful when we are going to add a new node or link)
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
        init_kwargs = {
            'convert_tab_to_spaces': self.app.config.text_input.convert_tab_to_spaces,
            'tab_to_spaces_number': self.app.config.text_input.tab_to_spaces_number,
        }
        self.node_components = [
            CodeNodeComponent(i, positions[i], v, **init_kwargs)
            for i, v in enumerate(nodes)
        ]

        # Set container (viewer) for nodes
        for node in self.node_components:
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

    def create_node_component(self, node, node_pos=None):
        self.node_collection.nodes.append(node)

        init_kwargs = {
            'convert_tab_to_spaces': self.app.config.text_input.convert_tab_to_spaces,
            'tab_to_spaces_number': self.app.config.text_input.tab_to_spaces_number,
        }

        index = len(self.node_components)
        component = CodeNodeComponent(index, node_pos, node, **init_kwargs)
        component.set_container(self)
        self.node_components.append(component)

    def remove_node_component(self, node_component):
        try:
            self.node_collection.remove_node(node_component.node)
            idx = self.node_components.index(node_component)
            self.node_components.pop(idx)
            self.links = self.node_collection.resolve_links()
            if self.id_selected == idx:
                self.id_selected = -1   # reset index of selected node
        except Exception as ex:
            GlobalState().push_error(ex)

    def init_canvas(self):
        imgui.text(f'Hold middle mouse button to pan ({self.panning.x}, {self.panning.y})')
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, Vec2(1, 1))
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, Vec2(0, 0))
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, *(0.05, 0.1, 0.15))
        imgui.begin_child('panning_region', 0, 0, flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_MOVE)
        imgui.pop_style_var()
        imgui.pop_style_var()
        imgui.pop_style_color()
        imgui.push_item_width(120.0)

    def finalize_canvas(self):
        imgui.pop_item_width()
        imgui.end_child()

    def handle_menu_item_save(self):
        clicked, selected = imgui.menu_item('Save', 'Ctrl+S')

        if clicked:
            if self.fn_src is not None:
                self.save_data(self.fn_src)
            else:
                # This viewer is opened from scratch, so that it's `fn_src` is None
                self.file_dialog = SaveFileDialog(self.app, self.save_data)

    def handle_menu_item_save_as(self):
        clicked, selected = imgui.menu_item('Save as')
        if clicked:
            self.file_dialog = SaveFileDialog(self.app, self.save_data)

    def handle_menu_item_close(self):
        clicked, selected = imgui.menu_item('Close')
        if clicked:
            self.close()

    def handle_menu_item_rearrange_nodes(self):
        clicked, selected = imgui.menu_item('Rearrange nodes')
        if clicked:
            self.init_nodes_and_links()

    def handle_menu_item_show_grid(self):
        _, self.show_grid = imgui.checkbox('Show grid', self.show_grid)

    def handle_menu_item_enable_reference_highlight(self):
        clicked, self.enable_reference_highlight = imgui.checkbox(
            'Reference highlight', self.enable_reference_highlight
        )
        if clicked:
            if not self.enable_reference_highlight:
                self.reset_highlighted_lines_in_snippet()

    def handle_state(self):
        if self.state_cache:
            # Remove event and arguments of "add_reference" if this window is
            # not focused anymore. And that means user can cancel the action
            # by clicking elsewhere.
            if not imgui.is_window_focused():
                del self.state_cache['event__add_reference']

    def handle_file_dialog(self):
        if self.file_dialog and self.file_dialog.terminated:
            self.file_dialog = None

    def handle_active_node(self, node_component, old_any_active):
        node_widgets_active = (not old_any_active) and imgui.is_any_item_active()

        if imgui.is_item_hovered():
            self.id_hovered_in_scene = node_component.id

        node_moving_active = imgui.is_item_active()
        if node_widgets_active or node_moving_active:
            self.handle_selected_node(node_component)
        if node_moving_active:
            if imgui.is_mouse_dragging(0):
                curr_delta = Vec2(*imgui.get_mouse_drag_delta(0))
                delta = curr_delta - self.prev_dragging_delta
                node_component.pos = node_component.pos + delta
                self.prev_dragging_delta = curr_delta
            else:
                # NOTE: Reset it only when mouse is not dragging to avoid redundant
                # calls even when a node is not clicked.
                self.reset_dragging_delta()

    def handle_selected_node(self, node_component):
        if self.enable_reference_highlight:
            self.reset_highlighted_lines_in_snippet()
            self.id_selected = node_component.id
            self.highlight_referenced_lines_in_snippet(node_component)
        else:
            self.id_selected = node_component.id

    def handle_context_menu_canvas(self):
        states = [node.is_showing_context_menu for node in self.node_components]
        is_any_context_menu_showing = any(states)

        # NOTE: To prevent confict, show this context menu only when no context menu
        # of node is showing.
        if not is_any_context_menu_showing:
            if imgui.begin_popup_context_item('context-menu', 2):
                if imgui.selectable('Create node')[0]:
                    init_kwargs = {
                        'convert_tab_to_spaces': self.app.config.text_input.convert_tab_to_spaces,
                        'tab_to_spaces_number': self.app.config.text_input.tab_to_spaces_number,
                    }
                    mouse_pos = Vec2(*imgui.get_mouse_position())
                    node_pos_on_canvas = mouse_pos - self._canvas_screen_pos
                    node_creater = CodeNodeCreatorWindow(
                        self.app, creation_pos=node_pos_on_canvas, **init_kwargs
                    )
                    node_creater.set_container(self)
                    self.app.add_component(node_creater)
                imgui.end_popup()

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

    # TODO: Replace name-based handler resolution with a decorator to mark
    # this method as a valid event handler.
    # event handler for "add_reference"
    def handle_event__add_reference(self, event):
        self.state_cache['event__add_reference'] = event
        imgui.set_window_focus_labeled(self.window_name)

    def handle_event__create_node(self, event):
        node = event.get('node')
        node_pos = event.get('node_pos')
        self.create_node_component(node, node_pos=node_pos)

    def reset_highlighted_lines_in_snippet(self):
        if self.id_selected == -1:
            return
        ids = [v.id for v in self.node_components]
        selected = self.node_components[ids.index(self.id_selected)]
        root_node = selected.node.root
        if root_node is None:
            return
        nodes = [v.node for v in self.node_components]
        idx = nodes.index(root_node)
        self.node_components[idx].snippet_window.reference_info = None

    def highlight_referenced_lines_in_snippet(self, node_component):
        root_node = node_component.node.root
        if root_node is None:
            return
        nodes = [v.node for v in self.node_components]
        idx = nodes.index(root_node)
        self.node_components[idx].snippet_window.reference_info = node_component.node.ref_info

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

        nodes = [v.node for v in self.node_components]

        for link in self.links:
            node_leaf = self.node_components[nodes.index(link.leaf)]
            node_root = self.node_components[nodes.index(link.root)]
            p1 = offset + node_leaf.get_root_slot_pos()
            p2 = offset + node_root.get_leaf_slot_pos(link.leaf_slot)
            draw_list.add_line(*p1, *p2, imgui.get_color_u32_rgba(1, 1, 0, 1))
            slot_color = imgui.get_color_u32_rgba(0.75, 0.75, 0.75, 1)
            draw_list.add_circle_filled(*p1, 4.0, slot_color)
            draw_list.add_circle_filled(*p2, 4.0, slot_color)

    def display_nodes(self, draw_list, offset):
        for node in self.node_components:
            imgui.push_id(str(node.id))
            node.render(draw_list, offset)
            imgui.pop_id()

    def draw_node_list(self):
        imgui.begin_child('node_list', 100, 0, flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR)
        imgui.text('nodes')
        imgui.separator()

        for node_component in self.node_components:
            imgui.push_id(str(node_component.id))
            clicked, selected = imgui.selectable(
                node_component.name, node_component.id == self.id_selected
            )
            if clicked:
                # TODO: If selected node is not in the visible range, pan the canvas
                # until it shows up.

                # Highlight those referenced lines in root node
                self.handle_selected_node(node_component)
            if imgui.is_item_hovered():
                self.id_hovered_in_list = node_component.id
            imgui.pop_id()

        imgui.end_child()

    def draw_node_canvas(self):
        self.reset_hovered_id_cache()

        imgui.begin_group()
        self.init_canvas()

        self._canvas_screen_pos = Vec2(*imgui.get_cursor_screen_pos())
        offset = self._canvas_screen_pos + self.panning
        draw_list = imgui.get_window_draw_list()

        if self.show_grid:
            self.display_grid(draw_list)
        self.display_links(draw_list, offset)
        self.display_nodes(draw_list, offset)

        draw_list.channels_merge()

        self.handle_panning()
        self.finalize_canvas()

        # Display message to notify user of reference selection
        if self.state_cache.get('event__add_reference', False):
            msg = '(Please select a node to link)'
            cur_pos = Vec2(*imgui.get_cursor_screen_pos())
            win_width = imgui.get_window_width()
            pos = cur_pos + Vec2(win_width - 340, -20)
            draw_list.add_text(*pos, imgui.get_color_u32_rgba(1,1,0,1), msg)

        imgui.end_group()

    def display_menu_bar(self):
        imgui.begin_menu_bar()
        if imgui.begin_menu('File'):
            self.handle_menu_item_save()    # overwrite the original file
            self.handle_menu_item_save_as()
            imgui.separator()
            self.handle_menu_item_close()
            imgui.end_menu()
        if imgui.begin_menu('View'):
            self.handle_menu_item_rearrange_nodes()
            self.handle_menu_item_show_grid()
            self.handle_menu_item_enable_reference_highlight()
            imgui.end_menu()
        imgui.end_menu_bar()

    def close(self):
        """Let host application know that this component is going to be closed,
        and clear references to this object in order to release memory."""
        self.app.remove_component(self)
        self.node_components = []
        self.links = []
        self.app = None

    def render(self):
        _, self.opened = imgui.begin(
            self.window_name, closable=True, flags=imgui.WINDOW_MENU_BAR
        )
        if not self.opened:
            imgui.end()
            self.close()
            return

        imgui.set_window_size(600, 400)
        self.handle_state()
        self.handle_file_dialog()
        self.display_menu_bar()
        self.draw_node_list()
        imgui.same_line()
        imgui.begin_group()
        self.draw_node_canvas()
        imgui.end_group()
        self.handle_context_menu_canvas()
        imgui.end()


class ErrorMessageModal(ImguiComponent):
    """A modal for showing error message."""

    def __init__(self, app, error_msg):
        """
        Parameters
        ----------
        app : codememo.Application
            Reference of running application.
        error_msg : str
            Error message.
        """
        from textwrap import wrap as wrap_text

        self.app = app
        self.error_msg = '\n'.join(wrap_text(error_msg, width=40))
        self.opened = False
        self.modal_opened = False
        self.close_button_clicked = False

    def close(self):
        self.app.remove_component(self)
        self.app = None

    def render(self):
        _, self.opened = imgui.begin('error-modal-window', flags=imgui.WINDOW_NO_TITLE_BAR)
        imgui.set_window_size(0, 0)

        # NOTE: Show this window at left-top corner since it just a container
        # for showing modal.
        imgui.set_window_position_labeled('error-modal-window', -10, -10)
        if not self.opened:
            imgui.end()
            return
        imgui.open_popup('Error')
        imgui.same_line()
        self.modal_opened, _ = imgui.begin_popup_modal(
            'Error', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE
        )
        if self.modal_opened:
            imgui.text(f'{self.error_msg}')

            # HACK: Use an empty label as the anchor to set cursor to center
            # of current line.
            imgui.text('')
            imgui.same_line(imgui.get_window_width()/2 - 21)
            if imgui.button('Close'):
                self.close()
            imgui.end_popup()
        else:
            self.close()
        imgui.end()


class ConfirmationModal(ImguiComponent):
    def __init__(self, title, message, callback):
        self.title = title
        self.message = message
        self.callback = callback
        self.modal_opened = False
        self.terminated = False

    def render(self):
        imgui.open_popup(self.title)
        self.modal_opened, _ = imgui.begin_popup_modal(
            self.title, flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE
        )
        if self.modal_opened:
            imgui.text(self.message)

            # HACK: Use an empty label as the anchor to set cursor to center
            # of current line.
            imgui.text('')
            imgui.same_line(imgui.get_window_width()/2 - 30)
            if imgui.button('Yes'):
                self.callback()
                self.terminated = True
            imgui.same_line()
            if imgui.button('No'):
                self.terminated = True
            imgui.end_popup()


class OpenFileDialog(ImguiComponent):
    INPUT_FILENAME_MAX_LENGTH = 256

    def __init__(self, app, callback):
        """
        app : codememo.Application
            Reference of running application.
        callback : function
            A callback function which will be invoked after a file is selected.
            Note that this dialog will be closed then.
            Passed arguments: [filename: str]
        """
        self.app = app
        self.filename = str(Path('').absolute())
        self.callback = callback
        self.error_msg = ''
        self.window_opened = False
        self.terminated = False
        self.app.add_component(self)

    def close(self):
        self.terminated = True
        self.app.remove_component(self)

    def render(self):
        _, self.window_opened = imgui.begin(
            'Open file', closable=True,
            flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_SAVED_SETTINGS
        )
        if not self.window_opened:
            self.close()
            imgui.end()
            return

        imgui.set_window_size(320, 95)

        imgui.text('Filename')
        imgui.push_item_width(-1)
        changed, text = imgui.input_text(
            '##filename', self.filename, self.INPUT_FILENAME_MAX_LENGTH
        )
        imgui.pop_item_width()
        if changed:
            self.filename = text

        imgui.text(self.error_msg)
        win_width = imgui.get_window_content_region_width()
        imgui.same_line(win_width - 28)

        if imgui.button('Open'):
            fn = Path(self.filename)
            try:
                # Use this to check whehter there are illegal characters in name
                is_valid = not fn.is_dir()
            except OSError:
                is_valid = False

            if not is_valid:
                self.error_msg = 'Invalid filename.'
            elif fn.exists():
                self.callback(self.filename)
                self.close()
            elif not fn.exists():
                self.error_msg = 'File does not exist.'
            else:
                # Should not be here...
                GlobalState().push_error(ValueError('Cannot resolve filename.'))
                imgui.end()
                return

        imgui.end()


class SaveFileDialog(ImguiComponent):
    INPUT_FILENAME_MAX_LENGTH = 256

    def __init__(self, app, callback):
        """
        app : codememo.Application
            Reference of running application.
        callback : function
            A callback function which will be invoked after filename is sucessfully
            validated. Note that this dialog will be closed then.
            Passed arguments: [filename: str]
        """
        self.app = app
        self.filename = str(Path('').absolute())
        self.callback = callback
        self.error_msg = ''
        self.confirmation_modal = None
        self.window_opened = False
        self.modal_opened = False
        self.terminated = False
        self.app.add_component(self)

    def close(self):
        self.terminated = True
        self.app.remove_component(self)

    def render(self):
        _, self.window_opened = imgui.begin(
            'Save file', closable=True,
            flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_SAVED_SETTINGS
        )
        if not self.window_opened:
            self.close()
            imgui.end()
            return

        imgui.set_window_size(320, 95)

        imgui.text('Filename')
        imgui.push_item_width(-1)
        changed, text = imgui.input_text(
            '##filename', self.filename, self.INPUT_FILENAME_MAX_LENGTH
        )
        imgui.pop_item_width()
        if changed:
            self.filename = text

        imgui.text(self.error_msg)
        win_width = imgui.get_window_content_region_width()
        imgui.same_line(win_width - 28)

        if imgui.button('Save'):
            fn = Path(self.filename)
            try:
                # Use this to check whehter there are illegal characters in name
                is_valid = not fn.is_dir()
            except OSError:
                is_valid = False

            if not is_valid:
                self.error_msg = 'Invalid filename.'
            elif not fn.exists():
                self.callback(self.filename)
                self.close()
            elif fn.exists():
                from textwrap import wrap as wrap_text

                self.error_msg = ''
                msg = (
                    f'File already exists, are you sure you want to overwrite it?'
                    f'\n{self.filename}'
                )
                self.confirmation_modal = ConfirmationModal(
                    'Error', msg, lambda: self.callback() or self.close(),
                )
            else:
                # Should not be here...
                GlobalState().push_error(ValueError('Cannot resolve filename.'))
                imgui.end()
                return

        if self.confirmation_modal:
            self.confirmation_modal.render()
            if self.confirmation_modal.terminated:
                self.confirmation_modal = None

        imgui.end()
