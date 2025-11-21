import os
from typing import Callable, Optional
from nicegui import ui

class LocalFilePicker(ui.dialog):
    def __init__(self, directory: str, on_select: Callable[[str], None], show_hidden_files: bool = False, mode: str = 'file'):
        """
        :param directory: Starting directory.
        :param on_select: Callback function when a file/folder is selected.
        :param show_hidden_files: Whether to show hidden files.
        :param mode: 'file' to select a file, 'dir' to select a directory.
        """
        super().__init__()
        if os.path.exists(directory):
            self.path = os.path.abspath(directory)
        else:
            self.path = os.getcwd()
        self.on_select = on_select
        self.show_hidden_files = show_hidden_files
        self.mode = mode
        self.file_ext = None  # Optional filter, e.g., '.epub'

        with self, ui.card().classes('w-[600px] h-[600px] flex flex-col bg-slate-900 border border-slate-700 text-slate-200'):
            # Header
            with ui.row().classes('w-full items-center gap-2 p-2 border-b border-slate-700 bg-slate-950'):
                ui.icon('folder_open', color='secondary')
                self.path_label = ui.label(self.path).classes('font-mono text-xs text-slate-400 flex-grow break-all')

                # Up Button
                ui.button(icon='arrow_upward', on_click=self.go_up).props('flat dense round color="secondary"')

                # Close Button
                ui.button(icon='close', on_click=self.close).props('flat dense round color="negative"')

            # File List
            self.scroll_area = ui.scroll_area().classes('flex-grow w-full p-2')

            # Footer (for Directory Mode)
            if self.mode == 'dir':
                with ui.row().classes('w-full p-2 border-t border-slate-700 bg-slate-950 justify-end'):
                    ui.button('Select This Folder', on_click=self.select_current_dir) \
                        .props('unelevated no-caps color="secondary" text-color="white"')

        self.update_list()

    def set_extension_filter(self, ext: str):
        self.file_ext = ext
        self.update_list()

    def go_up(self):
        self.path = os.path.dirname(self.path)
        self.update_list()

    def update_list(self):
        self.path_label.set_text(self.path)
        self.scroll_area.clear()

        try:
            items = sorted(os.listdir(self.path), key=lambda x: x.lower())
        except PermissionError:
            ui.notify("Permission denied", type="negative")
            return
        except FileNotFoundError:
            # Fallback to current working directory if path is lost
            ui.notify(f"Directory not found: {self.path}", type="negative")
            self.path = os.getcwd()
            # Avoid infinite recursion if cwd is also bad (unlikely but possible)
            if os.path.exists(self.path):
                self.update_list()
            return

        with self.scroll_area:
            # List Directories first
            for item in items:
                full_path = os.path.join(self.path, item)
                if not self.show_hidden_files and item.startswith('.'):
                    continue

                if os.path.isdir(full_path):
                    self._create_item_row(item, full_path, is_dir=True)

            # List Files
            if self.mode == 'file':
                for item in items:
                    full_path = os.path.join(self.path, item)
                    if not self.show_hidden_files and item.startswith('.'):
                        continue

                    if os.path.isfile(full_path):
                        if self.file_ext and not item.endswith(self.file_ext):
                            continue
                        self._create_item_row(item, full_path, is_dir=False)

    def _create_item_row(self, name, full_path, is_dir):
        color = 'text-yellow-500' if is_dir else 'text-slate-300'
        icon = 'folder' if is_dir else 'description'

        row = ui.row().classes(f'w-full cursor-pointer hover:bg-slate-800 p-1 rounded items-center gap-2 transition-colors')
        with row:
            ui.icon(icon).classes(color)
            ui.label(name).classes('text-sm font-mono text-slate-300 truncate flex-grow')

        # Bind click directly to the row
        row.on('click', lambda: self.handle_click(full_path, is_dir))

    def handle_click(self, full_path, is_dir):
        if is_dir:
            self.path = full_path
            self.update_list()
        else:
            if self.mode == 'file':
                self.on_select(full_path)
                self.close()

    def select_current_dir(self):
        self.on_select(self.path)
        self.close()
