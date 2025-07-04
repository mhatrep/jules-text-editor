import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont # Corrected import
import os

class EditorTab:
    def __init__(self, notebook_widget, app_instance, file_path=None):
        self.app = app_instance
        self.notebook = notebook_widget
        self.frame = ttk.Frame(self.notebook)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.line_numbers_font = tkfont.Font(family=app_instance.editor_font.cget("family"), size=app_instance.editor_font.cget("size"))
        self.line_numbers = tk.Canvas(self.frame, width=40, bg='lightgrey', highlightthickness=0)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.text_area = tk.Text(self.frame, wrap=tk.WORD, undo=True, yscrollcommand=self.sync_scroll_text, font=app_instance.editor_font)
        self.text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.current_file = file_path
        self.text_changed = False

        self.text_area.bind("<<Modified>>", self.on_text_changed_tab_and_update_lines)
        self.text_area.bind("<Configure>", self.on_text_changed_tab_and_update_lines) # Update on resize
        self.text_area.bind("<MouseWheel>", self.on_scroll_wheel) # For Windows/
        self.text_area.bind("<Button-4>", self.on_scroll_wheel) # For Linux scroll up
        self.text_area.bind("<Button-5>", self.on_scroll_wheel) # For Linux scroll down

        # Bindings for status bar updates
        self.text_area.bind("<KeyRelease>", self.on_key_or_mouse_release)
        self.text_area.bind("<ButtonRelease-1>", self.on_key_or_mouse_release) # Left mouse button

        # Custom scrollbar that calls our sync method
        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.text_area.yview)
        # self.text_area.config(yscrollcommand=self.scrollbar.set) # This will be set via sync_scroll_text
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=self.sync_scroll_text)


        self.redraw_line_numbers() # Initial draw

        if file_path:
            self.load_file_content(file_path)
        else:
            self.update_tab_title()

    def load_file_content(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
            self.current_file = filepath
            self.text_changed = False
            self.text_area.edit_modified(False)
            self.update_tab_title()
        except Exception as e:
            messagebox.showerror("Error Opening File", str(e))
            self.close_tab(check_save=False) # Close tab if file cannot be loaded

    def update_tab_title(self):
        tab_text = os.path.basename(self.current_file) if self.current_file else "Untitled"
        if self.text_changed:
            tab_text = "*" + tab_text

        # Check if the tab still exists in the notebook
        try:
            current_tabs = self.notebook.tabs()
            if self.frame_id() in current_tabs:
                 self.notebook.tab(self.frame_id(), text=tab_text)
            # else: tab might have been closed, do nothing
        except tk.TclError:
            # This can happen if the tab is already destroyed
            pass


    def on_text_changed_tab_and_update_lines(self, event=None):
        # Handle text modification
        if event and str(event.type) == "Modified":
            if self.text_area.edit_modified():
                if not self.text_changed: # Mark changed only once until saved
                    self.text_changed = True
                    self.update_tab_title()
            self.text_area.edit_modified(False) # Reset Tkinter's internal modified flag

        # Always redraw line numbers on any relevant event (Modified, Configure)
        # Using after(1) to ensure text_area layout is updated before redrawing
        self.text_area.after(1, self.redraw_line_numbers)
        if event and (str(event.type) == "Modified" or str(event.type) == "Configure"):
            self.app.update_status_bar()


    def on_key_or_mouse_release(self, event=None):
        # This is primarily for updating line/col in status bar
        self.app.update_status_bar()

    def on_scroll_wheel(self, event):
        # This ensures that when the text_area is scrolled by mouse wheel,
        # our sync_scroll_text (which calls redraw_line_numbers) is triggered.
        # For Windows, event.delta is usually +/-120. For Linux, event.num is 4 or 5.
        if event.num == 4: # Scroll up on Linux
            self.text_area.yview_scroll(-1, "units")
        elif event.num == 5: # Scroll down on Linux
            self.text_area.yview_scroll(1, "units")
        elif event.delta: # For Windows and other systems
            self.text_area.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # The yscrollcommand will call sync_scroll_text, which calls redraw_line_numbers
        return "break" # Prevent default scroll behavior if we handled it.

    def sync_scroll_text(self, *args):
        # This method is called by the text_area's yscrollcommand
        self.scrollbar.set(*args) # Update the actual scrollbar
        self.redraw_line_numbers() # Redraw line numbers based on new scroll position

    def redraw_line_numbers(self):
        self.line_numbers.delete("all")

        # Get the first and last visible line index in the text_area
        first_visible_char_index = self.text_area.index("@0,0")
        last_visible_char_index = self.text_area.index(f"@0,{self.text_area.winfo_height()}")

        # Convert char indices to line numbers (1-based)
        first_line_num = int(first_visible_char_index.split('.')[0])
        # For last_line_num, be careful if the last visible part is less than a full line.
        # index(f"end-1c linend").split('.')[0] gives the total number of lines with content.
        # We need to iterate based on what's visible.

        # Alternative: Iterate through dlines (displayed lines)
        # This is more robust for wrapped lines if we wanted to number logical lines.
        # For physical lines as they appear, this is fine.

        i = first_line_num
        # Iterate while the top of the line is visible within the text area's height
        while True:
            # Get the bounding box of the current line's start
            # The format is line.char, e.g., "1.0", "2.0"
            dline_info = self.text_area.dlineinfo(f"{i}.0")
            if dline_info is None: # No such line (e.g., past the end of the document)
                break

            # dline_info: (x, y, width, height, baseline) of the displayed line
            # y is the y-offset of the top of the line from the top of the text_area's content area
            # (not the widget itself, but where line 1.0 would be if fully scrolled up)

            # We need the y relative to the visible part of the text_area
            # The y from dlineinfo is already relative to the text content's top.
            # We need to find where this y appears in the visible canvas.

            # Get the fraction of the text_area that is currently scrolled
            # yview_fraction_top, yview_fraction_bottom = self.text_area.yview()
            # content_height = int(self.text_area.index('end-1c').split('.')[0]) * dline_info[3] if dline_info else 0 # Approx

            # Simpler: y_pos for drawing on canvas is y_of_line_in_text_content - y_offset_of_visible_area
            # y_offset_of_visible_area can be obtained from where first_visible_char_index starts.
            # y_offset_of_visible_area = self.text_area.dlineinfo(first_visible_char_index)[1] if self.text_area.dlineinfo(first_visible_char_index) else 0

            line_y_in_text_content = dline_info[1]
            first_visible_line_bbox = self.text_area.dlineinfo(first_visible_char_index)
            if not first_visible_line_bbox: break # Should not happen if first_line_num is valid

            # y-coordinate on the canvas for this line number
            # This is the y of the line (from dlineinfo) minus the y of the first visible line's start.
            # Plus half the line height to center the text.
            canvas_y = (line_y_in_text_content - first_visible_line_bbox[1]) + (dline_info[3] / 2)

            # Check if this line is actually visible within the canvas height
            if canvas_y > self.line_numbers.winfo_height():
                break # Line is below the visible area of the line number canvas

            # Draw the line number
            # Adjust x to right-align numbers, or fixed position. width-2 for padding from right.
            self.line_numbers.create_text(38, canvas_y, anchor=tk.NE, text=str(i), font=self.line_numbers_font)

            i += 1
            if i > int(self.text_area.index(f"{tk.END}-1c").split('.')[0]): # Don't go beyond total lines
                 break

        # Dynamic width for line numbers canvas (optional, can be complex)
        # last_line_str_len = len(str(i-1))
        # new_width = max(40, last_line_str_len * 8 + 10) # Adjust 8 and 10 based on font
        # if self.line_numbers.winfo_width() != new_width:
        #     self.line_numbers.config(width=new_width)
        #     # May need to repack or update layout


    def get_content(self):
        return self.text_area.get("1.0", tk.END + "-1c") # -1c to avoid extra newline

    def frame_id(self):
        return self.frame # The frame itself is its ID in the notebook

    def close_tab(self, check_save=True):
        if check_save and not self.check_unsaved_changes_tab():
            return False # Don't close

        current_tabs = list(self.notebook.tabs())
        try:
            tab_index = current_tabs.index(self.frame_id())
            self.notebook.forget(tab_index)
            self.app.tabs.pop(tab_index) # Remove from app's list of tabs
            if not self.app.tabs: # If no tabs left, create a new untitled one or exit
                if self.app.quitting_app: # if app is quitting, don't create new tab
                    if len(self.notebook.tabs()) == 0: # if it was the last tab during quit
                        self.app.root.destroy()
                else:
                    self.app.new_file_action()
            self.app.update_app_title()
            return True
        except (ValueError, tk.TclError): # Tab not found or error during forget
            # This might happen if tab was already closed or during shutdown
            if not self.app.tabs and not self.app.quitting_app:
                 self.app.new_file_action()
            elif not self.app.tabs and self.app.quitting_app and len(self.notebook.tabs()) == 0:
                 self.app.root.destroy()
            return False


    def check_unsaved_changes_tab(self):
        if self.text_changed:
            self.notebook.select(self.frame_id()) # Bring tab to front
            file_display_name = os.path.basename(self.current_file) if self.current_file else "Untitled"
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Do you want to save the changes to {file_display_name}?"
            )
            if response is True:  # Yes
                return self.app.save_file_action(save_as_if_needed=False) # Try to save current tab
            elif response is False:  # No
                return True  # Proceed without saving
            else:  # Cancel
                return False  # Do nothing
        return True # No changes


class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        self.quitting_app = False
        self.tabs = []

        # Default font configuration
        self.current_font_family = "TkFixedFont" # Default fixed-width font
        self.current_font_size = 10
        self.current_font_weight = "normal"
        self.current_font_slant = "roman"
        self.editor_font = tkfont.Font(
            family=self.current_font_family,
            size=self.current_font_size,
            weight=self.current_font_weight,
            slant=self.current_font_slant
        )

        # Create main menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.new_file_action_handler, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open...", command=self.open_file_action_handler, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save", command=lambda: self.save_action_handler(save_as_if_needed=False), accelerator="Ctrl+S")
        self.file_menu.add_command(label="Save As...", command=self.save_as_action_handler, accelerator="Ctrl+Shift+S")
        self.file_menu.add_command(label="Close Tab", command=self.close_current_tab_action_handler, accelerator="Ctrl+W")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_editor_action)

        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Undo", command=self.undo_action, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Redo", command=self.redo_action, accelerator="Ctrl+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut_action, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Copy", command=self.copy_action, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Paste", command=self.paste_action, accelerator="Ctrl+V")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", command=self.select_all_action, accelerator="Ctrl+A")

        # Format menu
        self.format_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Format", menu=self.format_menu)

        self.trim_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Trim", menu=self.trim_menu)
        self.trim_menu.add_command(label="Trim Leading Whitespace", command=lambda: self.trim_whitespace("leading"))
        self.trim_menu.add_command(label="Trim Trailing Whitespace", command=lambda: self.trim_whitespace("trailing"))
        self.trim_menu.add_command(label="Trim Both Ends Whitespace", command=lambda: self.trim_whitespace("both"))

        self.case_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Change Case", menu=self.case_menu)
        self.case_menu.add_command(label="To Uppercase", command=lambda: self.change_case("upper"))
        self.case_menu.add_command(label="To Lowercase", command=lambda: self.change_case("lower"))
        self.case_menu.add_command(label="To Title Case", command=lambda: self.change_case("title"))

        self.format_menu.add_separator()
        self.format_menu.add_command(label="Sort Lines...", command=self.sort_lines_dialog)

        # Search Menu (for Find/Replace)
        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Search", menu=self.search_menu)
        self.search_menu.add_command(label="Find/Replace...", command=self.open_find_replace_dialog, accelerator="Ctrl+F")

        # View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Change Font...", command=self.open_font_dialog)


        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Status Bar
        self.status_bar_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=2)
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label_line_col = ttk.Label(self.status_bar_frame, text="Ln 1, Col 1", width=20)
        self.status_label_line_col.pack(side=tk.LEFT, padx=5)

        self.status_label_total_lines = ttk.Label(self.status_bar_frame, text="Lines: 1", width=15)
        self.status_label_total_lines.pack(side=tk.LEFT, padx=5)

        self.status_label_file_path = ttk.Label(self.status_bar_frame, text="File: Untitled", anchor=tk.W) # Anchor W to keep it left aligned if it expands
        self.status_label_file_path.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # TODO: Add more labels for file size, encoding if desired later


        # Create initial tab
        self.new_file_action() # This will also trigger initial status update via on_tab_changed and update_status_bar
        self.update_app_title()


        # Bind keyboard shortcuts
        self.root.bind_all("<Control-n>", self.new_file_action_handler)
        self.root.bind_all("<Control-o>", self.open_file_action_handler)
        self.root.bind_all("<Control-s>", lambda event: self.save_action_handler(save_as_if_needed=False))
        self.root.bind_all("<Control-S>", self.save_as_action_handler) # Ctrl+Shift+S
        self.root.bind_all("<Control-w>", self.close_current_tab_action_handler)
        self.root.bind_all("<Control-f>", self.open_find_replace_dialog) # This one already returns "break"


        # Edit shortcuts (need to be routed to active tab's text_area)
        self.root.bind_all("<Control-z>", lambda event: self.undo_action())
        self.root.bind_all("<Control-y>", lambda event: self.redo_action())
        self.root.bind_all("<Control-x>", lambda event: self.cut_action())
        self.root.bind_all("<Control-c>", lambda event: self.copy_action())
        self.root.bind_all("<Control-v>", lambda event: self.paste_action())
        self.root.bind_all("<Control-a>", lambda event: self.select_all_action())

        self.root.protocol("WM_DELETE_WINDOW", self.exit_editor_action)

    def get_current_tab(self):
        try:
            selected_tab_frame_id = self.notebook.select()
            if not selected_tab_frame_id: # No tab selected (e.g. all closed programmatically)
                 if self.tabs: return self.tabs[0] # fallback, though ideally should not happen
                 return None

            for tab_obj in self.tabs:
                if str(tab_obj.frame_id()) == str(selected_tab_frame_id):
                    return tab_obj
            return None # Should not happen if tabs list is consistent with notebook
        except tk.TclError: # Notebook might be empty or widget destroyed
            return None


    def on_tab_changed(self, event=None):
        self.update_app_title()
        self.update_status_bar() # Update status bar when tab changes

    def update_status_bar(self):
        current_tab = self.get_current_tab()
        if current_tab and current_tab.text_area:
            # Line and Column
            cursor_pos = current_tab.text_area.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            self.status_label_line_col.config(text=f"Ln {line}, Col {col + 1}") # Col is 0-indexed

            # Total Lines
            total_lines = int(current_tab.text_area.index(f"{tk.END}-1c").split('.')[0])
            self.status_label_total_lines.config(text=f"Lines: {total_lines}")

            # File Path
            file_path_display = "Untitled"
            if current_tab.current_file:
                file_path_display = os.path.basename(current_tab.current_file)
            self.status_label_file_path.config(text=f"File: {file_path_display}")

            # TODO: Add file size, encoding later
        else:
            self.status_label_line_col.config(text="Ln --, Col --")
            self.status_label_total_lines.config(text="Lines: --")
            self.status_label_file_path.config(text="File: --")


    def update_app_title(self):
        current_tab = self.get_current_tab()
        if current_tab:
            base_name = os.path.basename(current_tab.current_file) if current_tab.current_file else "Untitled"
            title = f"Jules Text Editor - {base_name}"
            if current_tab.text_changed:
                title = "*" + title
            self.root.title(title)
        else:
            self.root.title("Jules Text Editor")


    def new_file_action(self, event=None):
        new_tab = EditorTab(self.notebook, self)
        self.tabs.append(new_tab)
        self.notebook.add(new_tab.frame, text="Untitled")
        self.notebook.select(new_tab.frame_id()) # Make the new tab active
        new_tab.text_area.focus_set()
        self.update_app_title()
        self.update_status_bar() # Update for new tab

    def new_file_action_handler(self, event=None):
        self.new_file_action()
        return "break"

    # Actual logic methods (return True/False or data, no "break")
    def new_file_action(self):
        new_tab = EditorTab(self.notebook, self)
        self.tabs.append(new_tab)
        self.notebook.add(new_tab.frame, text="Untitled")
        self.notebook.select(new_tab.frame_id())
        new_tab.text_area.focus_set()
        self.update_app_title()
        self.update_status_bar()

    def open_file_action_handler(self, event=None):
        self.open_file_action()
        return "break"

    def open_file_action(self):
        filepath = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if filepath:
            for tab in self.tabs:
                if tab.current_file == filepath:
                    self.notebook.select(tab.frame_id())
                    self.update_status_bar()
                    return

            new_tab = EditorTab(self.notebook, self, file_path=filepath)
            if new_tab.current_file:
                self.tabs.append(new_tab)
                self.notebook.add(new_tab.frame)
                new_tab.update_tab_title()
                self.notebook.select(new_tab.frame_id())
                new_tab.text_area.focus_set()
            else:
                new_tab.frame.destroy()
        self.update_app_title()
        self.update_status_bar()

    def save_action_handler(self, event=None, save_as_if_needed=True):
        self.save_file(save_as_if_needed=save_as_if_needed)
        return "break"

    def save_as_action_handler(self, event=None):
        self.save_as_file()
        return "break"

    def save_file(self, save_as_if_needed=True): # Renamed from save_file_action
        current_tab = self.get_current_tab()
        if not current_tab:
            return False

        if not current_tab.current_file or save_as_if_needed:
            return self.save_as_file()

        try:
            content = current_tab.get_content()
            with open(current_tab.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            current_tab.text_changed = False
            current_tab.text_area.edit_modified(False)
            current_tab.update_tab_title()
            self.update_app_title()
            self.update_status_bar()
            return True
        except Exception as e:
            messagebox.showerror("Error Saving File", str(e))
            return False

    def save_as_file(self): # Renamed from save_as_file_action
        current_tab = self.get_current_tab()
        if not current_tab:
            return False

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=os.path.basename(current_tab.current_file) if current_tab.current_file else "Untitled.txt",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if filepath:
            current_tab.current_file = filepath
            if self.save_file(save_as_if_needed=False): # Call the core save logic
                # Status bar updated by save_file on success
                return True
            else:
                # current_tab.current_file = None # Optionally revert if save failed. Or keep new path.
                self.update_status_bar() # Reflect potential path change even if save failed
                return False
        self.update_status_bar() # Reflect that dialog was cancelled or path not chosen
        return False

    def close_current_tab_action_handler(self, event=None):
        self.close_current_tab_action()
        return "break"

    def close_current_tab_action(self):
        current_tab = self.get_current_tab()
        closed_successfully = False
        if current_tab:
            if current_tab.close_tab():
                closed_successfully = True

        # update_status_bar is called by on_tab_changed if a new tab is selected,
        # or if a new "Untitled" tab is created by close_tab.
        # If the last tab was closed and app is exiting, it doesn't matter.
        # If last tab closed & new one created, on_tab_changed handles it.
        # Explicit call here if no tab change occurred but state might need refresh (e.g. last tab closed, app not exiting yet)
        if not self.tabs and not self.quitting_app: # Edge case: last tab closed, new one should have been made by close_tab
             pass # Handled by new_file_action called within close_tab
        self.update_status_bar() # General update after close operation.

    def exit_editor_action(self):
        self.quitting_app = True
        # Iterate over a copy of tabs list because it might be modified during iteration by close_tab
        for tab in list(self.tabs): # list(self.tabs) creates a copy
            if not tab.close_tab(): # If any tab cancel closing, abort exit
                self.quitting_app = False
                return

        # If all tabs were closed successfully (or there were no tabs)
        if not self.tabs: # Ensure all tabs are indeed gone
             self.root.destroy()
        # else: something went wrong, or a tab refused to close and logic error.
        # For robustness, if tabs somehow still exist, don't destroy root. This shouldn't be reached if close_tab is correct.



    # Edit actions now need to target the current tab's text_area
    def get_active_text_area(self):
        current_tab = self.get_current_tab()
        if current_tab:
            return current_tab.text_area
        return None

    def undo_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            try:
                text_area.edit_undo()
            except tk.TclError: pass # No more undos
        return "break"

    def redo_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            try:
                text_area.edit_redo()
            except tk.TclError: pass # No more redos
        return "break"

    def cut_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area and text_area.tag_ranges(tk.SEL):
            text_area.event_generate("<<Cut>>")
        return "break"

    def copy_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area and text_area.tag_ranges(tk.SEL):
            text_area.event_generate("<<Copy>>")
        return "break"

    def paste_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            text_area.event_generate("<<Paste>>")
        return "break"

    def select_all_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            text_area.tag_add(tk.SEL, "1.0", tk.END)
            text_area.mark_set(tk.INSERT, "1.0")
            text_area.see(tk.INSERT)
        return "break"

    # --- Text Processing Methods ---
    def _process_text(self, operation_func):
        text_area = self.get_active_text_area()
        if not text_area:
            return

        try:
            sel_start = text_area.index(tk.SEL_FIRST)
            sel_end = text_area.index(tk.SEL_LAST)
            selected_text = text_area.get(sel_start, sel_end)
            processed_text = operation_func(selected_text)
            if selected_text != processed_text:
                text_area.delete(sel_start, sel_end)
                text_area.insert(sel_start, processed_text)
                text_area.event_generate("<<Modified>>") # Manually trigger modified event
        except tk.TclError: # No selection
            full_text = text_area.get("1.0", tk.END + "-1c")
            processed_text = operation_func(full_text)
            if full_text != processed_text:
                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", processed_text)
                text_area.event_generate("<<Modified>>") # Manually trigger modified event

    def trim_whitespace(self, mode="both"):
        """Trims whitespace from selected text or whole content."""
        def do_trim(text):
            lines = text.splitlines(keepends=True)
            processed_lines = []
            if mode == "leading":
                for line in lines:
                    # Handle lines with only whitespace correctly by not adding keepends char if line becomes empty
                    stripped_line = line.lstrip()
                    if not stripped_line.strip() and line.endswith('\n') and stripped_line == '': # if line was all whitespace + newline
                        processed_lines.append('\n')
                    elif not stripped_line and line.endswith('\n'): # if line was just newline
                         processed_lines.append(line)
                    else:
                        processed_lines.append(line.lstrip())
            elif mode == "trailing":
                for line in lines:
                     processed_lines.append(line.rstrip() + ('\n' if line.endswith('\n') and line.rstrip() else ''))
                # Join and then split to correctly handle multiple newlines at the end
                temp_text = "".join(processed_lines)
                return temp_text.rstrip() + ('\n' if temp_text.endswith('\n') else '')

            elif mode == "both":
                 for line in lines:
                    stripped_line = line.strip()
                    if not stripped_line and line.endswith('\n'): # if line was all whitespace + newline
                        processed_lines.append('\n')
                    elif line.strip(): # only add stripped line if it's not empty
                        processed_lines.append(line.strip() + ('\n' if line.endswith('\n') else ''))
                    # else: if line was all whitespace and no newline, it becomes empty and is omitted

            # Reconstruct text, trying to preserve original line ending structure for "both" and "leading"
            if mode == "leading" or mode == "both":
                return "".join(processed_lines)
            else: # Trailing needs careful reconstruction to avoid adding too many newlines
                 # For trailing, it might be better to operate on the whole block if no selection
                text_area = self.get_active_text_area()
                if not text_area: return text # Should not happen here
                try:
                    text_area.index(tk.SEL_FIRST) # check if selection exists
                except tk.TclError: # No selection, operate on full text and preserve final newline
                    processed_text = "\n".join([line.rstrip() for line in text.splitlines()])
                    if text.endswith('\n'):
                       processed_text += '\n'
                    return processed_text

                # If selection, process line by line
                return "\n".join([line.rstrip() for line in text.splitlines()])


        self._process_text(do_trim)

    def change_case(self, case_type):
        """Changes case of selected text or whole content."""
        def do_change_case(text):
            if case_type == "upper":
                return text.upper()
            elif case_type == "lower":
                return text.lower()
            elif case_type == "title":
                return text.title()
            return text
        self._process_text(do_change_case)

    def sort_lines_dialog(self):
        text_area = self.get_active_text_area()
        if not text_area:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Sort Lines")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("300x200")

        # Variables
        sort_order_var = tk.StringVar(value="asc") # asc, desc
        case_sensitive_var = tk.BooleanVar(value=True)
        remove_duplicates_var = tk.BooleanVar(value=False)

        # UI Elements
        tk.Label(dialog, text="Sort Order:").pack(pady=5)
        ttk.Radiobutton(dialog, text="Ascending", variable=sort_order_var, value="asc").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(dialog, text="Descending", variable=sort_order_var, value="desc").pack(anchor=tk.W, padx=20)

        ttk.Checkbutton(dialog, text="Case Sensitive", variable=case_sensitive_var).pack(anchor=tk.W, padx=20, pady=5)
        ttk.Checkbutton(dialog, text="Remove Duplicate Lines", variable=remove_duplicates_var).pack(anchor=tk.W, padx=20, pady=5)

        def on_apply():
            self.apply_sort_lines(
                sort_order_var.get(),
                case_sensitive_var.get(),
                remove_duplicates_var.get()
            )
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10, fill=tk.X, side=tk.BOTTOM)
        ttk.Button(button_frame, text="Apply", command=on_apply).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')


    def apply_sort_lines(self, order, case_sensitive, remove_duplicates):
        text_area = self.get_active_text_area()
        if not text_area:
            return

        try:
            sel_start_line = text_area.index(tk.SEL_FIRST + " linestart")
            sel_end_line = text_area.index(tk.SEL_LAST + " lineend") # include the full last selected line
            if text_area.get(sel_end_line + "-1c", sel_end_line) == '\n': # If last char of selection is newline
                 sel_end_actual = sel_end_line
            else: # Selection does not end with a newline, so lineend might be start of next line if not careful
                 sel_end_actual = text_area.index(tk.SEL_LAST + " lineend")
                 # if the selection does not end with a newline, lineend will point to the start of the next line.
                 # we want to ensure we get the content up to the end of the selected line.
                 # however, if the selection is "abc" in "abc\ndef", SEL_LAST is 1.3, lineend is 1.end (or 2.0)
                 # if SEL_LAST is already at end of line (e.g. selected full line), lineend is correct.
                 # A simpler way: get text, then split.

            text_to_sort = text_area.get(sel_start_line, sel_end_actual)
            is_selection = True
        except tk.TclError: # No selection, sort all lines
            sel_start_line = "1.0"
            sel_end_actual = tk.END + "-1c" # Exclude the text widget's default trailing newline
            text_to_sort = text_area.get(sel_start_line, sel_end_actual)
            is_selection = False

        lines = text_to_sort.splitlines()

        # Store trailing newline status for the whole block if it's not a selection
        # and for the last line of selection if it is a selection
        original_had_trailing_newline = text_to_sort.endswith('\n')


        if not lines: # No lines to sort (empty selection or empty document)
            return

        if remove_duplicates:
            if case_sensitive:
                seen = set()
                unique_lines = [line for line in lines if not (line in seen or seen.add(line))]
            else:
                seen_lower = set()
                unique_lines = []
                for line in lines:
                    lower_line = line.lower()
                    if lower_line not in seen_lower:
                        unique_lines.append(line)
                        seen_lower.add(lower_line)
            lines = unique_lines


        sort_key = str if case_sensitive else lambda s: s.lower()
        lines.sort(key=sort_key, reverse=(order == "desc"))

        sorted_text = "\n".join(lines)

        # Add back the trailing newline if the original block had one.
        # This is important because splitlines() removes it.
        if original_had_trailing_newline and sorted_text: # and sorted_text to avoid adding \n to empty result
            sorted_text += "\n"
        elif not original_had_trailing_newline and sorted_text.endswith('\n') and len(lines) == 1 and not lines[0]:
            # Special case: if original was " " (no newline) and sorted is "\n" (e.g. from [""])
            # make it "" to match original no-newline. This happens if "Remove Duplicates" results in one empty line.
             pass # Let it be, or strip? If original was " ", sort makes it "", then \n is added.
                  # If original was " \n", sort makes it "", then \n is added.
                  # Better to be consistent: if original had newline, result has newline.
                  # If original did not, result does not (unless it's an empty string becoming one line).

        # If the result is empty and the original selection was not empty but just whitespace
        # that got removed (e.g. sorting " \n " with remove duplicates),
        # ensure we don't add a newline if original didn't end with one.
        if not sorted_text and not original_had_trailing_newline and text_to_sort.strip() == "":
             pass # sorted_text is already "", no \n needed
        elif not sorted_text and original_had_trailing_newline and text_to_sort.strip() == "":
             sorted_text = "\n" # original was like " \n \n", result is single \n


        if text_to_sort != sorted_text:
            text_area.delete(sel_start_line, sel_end_actual if is_selection else tk.END)
            # For full text replacement, ensure we don't add an extra newline if sorted_text already ends with one
            # and tk.END is used.
            if not is_selection and sorted_text.endswith("\n"):
                 text_area.insert(sel_start_line, sorted_text[:-1]) # Insert without its own \n, text widget adds one
            elif not is_selection: # Full text, not ending with \n
                 text_area.insert(sel_start_line, sorted_text)
            else: # Selection
                 text_area.insert(sel_start_line, sorted_text)

            text_area.event_generate("<<Modified>>")

    # --- Find/Replace Methods ---
    def open_find_replace_dialog(self, event=None):
        if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists():
            self.find_replace_dialog.lift()
            self.find_replace_dialog.focus_set()
            # Populate find_entry from selection if any
            text_area = self.get_active_text_area()
            if text_area:
                try:
                    selected_text = text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                    if selected_text and "\n" not in selected_text: # Only use single-line selections
                        self.find_entry.delete(0, tk.END)
                        self.find_entry.insert(0, selected_text)
                except tk.TclError:
                    pass # No selection or multi-line selection
            return "break"

        dialog = tk.Toplevel(self.root)
        dialog.title("Find/Replace")
        dialog.transient(self.root)
        # dialog.grab_set() # Non-modal for now, so user can interact with text
        dialog.resizable(False, False)
        self.find_replace_dialog = dialog # Store reference to check if exists

        # Variables
        self.find_what_var = tk.StringVar()
        self.replace_with_var = tk.StringVar()
        self.case_sensitive_find_var = tk.BooleanVar(value=False)
        self.whole_word_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        self.wrap_around_var = tk.BooleanVar(value=True) # Search from start if end reached
        self.search_backwards_var = tk.BooleanVar(value=False)


        # UI Elements
        input_frame = ttk.Frame(dialog)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(input_frame, text="Find what:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.find_entry = ttk.Entry(input_frame, textvariable=self.find_what_var, width=40)
        self.find_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(input_frame, text="Replace with:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.replace_entry = ttk.Entry(input_frame, textvariable=self.replace_with_var, width=40)
        self.replace_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)

        input_frame.columnconfigure(1, weight=1) # Make entry fields expandable

        options_frame = ttk.LabelFrame(dialog, text="Options")
        options_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive_find_var).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Whole word", variable=self.whole_word_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Regular expression", variable=self.regex_var).grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Wrap around", variable=self.wrap_around_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Search backwards", variable=self.search_backwards_var).grid(row=2, column=0, sticky=tk.W, padx=5)


        button_frame = ttk.Frame(dialog)
        button_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Button(button_frame, text="Find Next", command=self.find_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Replace", command=self.replace_once).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Replace All", command=self.replace_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # Populate find_entry from selection if any
        text_area = self.get_active_text_area()
        if text_area:
            try:
                selected_text = text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected_text and "\n" not in selected_text: # Only use single-line selections
                    self.find_entry.insert(0, selected_text)
            except tk.TclError:
                pass # No selection

        self.find_entry.focus_set()
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')
        return "break"

    def _search_in_text(self, text_widget, pattern, start_index, end_index, case_sensitive, whole_word, regex, backwards):
        nocase = not case_sensitive

        if regex:
            # For regex, whole_word needs to be part of the pattern if desired
            # Tk's text.search does not directly support whole word for regex.
            # We might need to use Python's re module and then map positions.
            # For now, basic regex support without explicit whole word from checkbox.
            # User can include \b in regex for whole word.
            import re
            flags = 0 if case_sensitive else re.IGNORECASE

            content = text_widget.get(start_index, end_index)

            if backwards:
                # Search backwards: find all matches and take the last one before start_index
                # This is complex with Python's re. finditer and then filter
                matches = []
                # Adjust start_index for content slicing if it's from text_widget.index
                # The content is from start_index to end_index.
                # We need to map re match positions back to text_widget indices.

                # This simplified version for regex backwards is not implemented here.
                # Tk's -backwards is better for non-regex.
                # For regex backwards, one would typically search forward in reversed text or iterate.
                # Let's rely on tk's search for non-regex backwards and python's re for forward.
                # For now, regex backwards is not fully supported with python re here.
                # Tk's own regex might be better if it supports backwards.
                # Let's assume forward search for regex for now.
                if backwards:
                     # messagebox.showinfo("Info", "Regex backward search not fully implemented with Python re yet. Using Tk's search if possible.")
                     # Fallback to Tk's search if it supports regex and backwards.
                     # count_var = tk.IntVar()
                     # pos = text_widget.search(pattern, start_index, backwards=True, regexp=True, nocase=nocase, exact=whole_word, stopindex=end_index, count=count_var)
                     # if pos: return pos, count_var.get() else: return None, 0
                     # For now, let's just say it's not supported with python re
                     pass


            match_iter = re.finditer(pattern, content, flags)

            if backwards: # Iterate all and find the last one whose start is before current cursor
                last_match = None
                current_offset = text_widget.count("1.0", start_index)[0] # Number of chars from 1.0 to start_index

                # Iterate through all matches in the relevant portion of the text
                # The content is sliced from search_start to search_end.
                # We need to search within this slice and map indices.

                # Let's simplify: for regex, backwards is hard.
                # We'll search from 1.0 up to the start_index and take the last match.
                if start_index != "1.0": # only if not at the beginning
                    content_before_start = text_widget.get("1.0", start_index)
                    for m in re.finditer(pattern, content_before_start, flags):
                        last_match = m
                if last_match:
                    # Map match object start/end in content_before_start back to main text_widget indices
                    match_start_offset = last_match.start()
                    match_end_offset = last_match.end()
                    # This needs careful index calculation using text_widget.index(f"1.0 + {offset} chars")
                    # For simplicity, this part is not fully robust for regex backwards.
                    # Using tk's search is preferred if its regex is sufficient.
                    # For now, this path will likely not be hit or be perfect.
                    # Let's focus on forward search for regex.
                    # A truly robust regex backward would search forward in segments.
                    pass # Placeholder for complex regex backward logic


            # Forward regex search:
            for m in match_iter:
                # Map m.start() and m.end() from `content` string to text_widget indices
                # `content` was obtained from `start_index` to `end_index`
                # A match at m.start() in `content` is at `start_index + m.start() characters`
                # This needs `text_widget.index(f"{start_index} + {m.start()} chars")`
                # and `text_widget.index(f"{start_index} + {m.end()} chars")`

                # Simplified approach: search entire document and find first match after start_index
                # This is inefficient for large docs if start_index is far.
                # A better way is to get content from start_index to end and search in that.

                # Let's use the content sliced from start_index:
                match_pos_in_slice = m.start()
                # Convert this to an absolute position in the text widget
                # pos = text_widget.index(f"{start_index} + {match_pos_in_slice} chars")
                # length = m.end() - m.start()
                # return pos, length

                # More direct: search from start_index in the whole document, take first match
                # Python's re.search finds the *first* occurrence.
                # If start_index is 'insert', we search from there.
                doc_content = text_widget.get("1.0", tk.END)
                offset_at_start_index = 0
                if start_index != "1.0":
                    offset_at_start_index = len(text_widget.get("1.0", start_index))

                m_full = re.search(pattern, doc_content[offset_at_start_index:], flags)
                if m_full:
                    abs_match_start = offset_at_start_index + m_full.start()
                    pos = text_widget.index(f"1.0 + {abs_match_start} chars")
                    length = len(m_full.group(0))
                    return pos, length
                return None, 0 # No match found after start_index
            return None, 0 # No matches from iterator

        else: # Not regex - use Tk's text.search
            count_var = tk.IntVar()
            # Adjust start_index for backwards search if it's at the beginning of a selection
            # to ensure the selection itself can be found again if "Find Next" is pressed repeatedly.
            current_sel = text_widget.tag_ranges(tk.SEL)
            if backwards and current_sel and start_index == current_sel[0]:
                 effective_start = start_index # Search from beginning of current selection
            elif backwards:
                 effective_start = start_index
            else: # Forward
                 effective_start = start_index

            pos = text_widget.search(pattern, effective_start,
                                     stopindex=end_index,
                                     backwards=backwards,
                                     regexp=regex, # Should be False here
                                     nocase=nocase,
                                     exact=whole_word,
                                     count=count_var)
            if pos:
                return pos, count_var.get()
            return None, 0

    def find_next(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area: return "break"

        find_what = self.find_what_var.get()
        if not find_what:
            messagebox.showinfo("Find Next", "Find string is empty.", parent=self.find_replace_dialog)
            return "break"

        case_sensitive = self.case_sensitive_find_var.get()
        whole_word = self.whole_word_var.get()
        use_regex = self.regex_var.get()
        wrap_around = self.wrap_around_var.get()
        search_backwards = self.search_backwards_var.get()

        text_area.tag_remove(tk.SEL, "1.0", tk.END) # Clear previous selection

        if search_backwards:
            start_index = text_area.index(tk.INSERT + "-1c") if text_area.index(tk.INSERT) != "1.0" else "1.0"
            stop_index = "1.0"
        else: # Forward
            start_index = text_area.index(tk.INSERT)
            stop_index = tk.END

        # If there's a selection, and we are searching forward, start after the selection
        # If searching backward, start before the selection.
        # This is implicitly handled by tk.INSERT if selection is made by this find tool.
        # If user made a selection, tk.INSERT is usually at the end of it.

        found_pos, length = self._search_in_text(text_area, find_what, start_index, stop_index,
                                                 case_sensitive, whole_word, use_regex, search_backwards)

        if found_pos:
            end_sel_pos = f"{found_pos} + {length} chars"
            text_area.tag_add(tk.SEL, found_pos, end_sel_pos)
            text_area.mark_set(tk.INSERT, end_sel_pos if not search_backwards else found_pos)
            text_area.see(found_pos)
            self.find_replace_dialog.lift()
        else: # Not found in the primary search direction
            if wrap_around:
                if search_backwards: # Wrapped from top, now search from end to current tk.INSERT
                    start_index = tk.END + "-1c" # Start from the very end
                    # stop_index remains tk.INSERT (original start) or where search began
                else: # Wrapped from end, now search from beginning to current tk.INSERT
                    start_index = "1.0"
                    # stop_index remains tk.INSERT

                wrapped_pos, wrapped_length = self._search_in_text(text_area, find_what, start_index, text_area.index(tk.INSERT),
                                                                  case_sensitive, whole_word, use_regex, search_backwards)
                if wrapped_pos:
                    end_sel_pos = f"{wrapped_pos} + {wrapped_length} chars"
                    text_area.tag_add(tk.SEL, wrapped_pos, end_sel_pos)
                    text_area.mark_set(tk.INSERT, end_sel_pos if not search_backwards else wrapped_pos)
                    text_area.see(wrapped_pos)
                    self.find_replace_dialog.lift()
                else:
                    messagebox.showinfo("Find Next", f"Cannot find '{find_what}'", parent=self.find_replace_dialog)
            else: # No wrap around
                messagebox.showinfo("Find Next", f"Cannot find '{find_what}'", parent=self.find_replace_dialog)

        if self.find_replace_dialog and self.find_replace_dialog.winfo_exists():
             self.find_replace_dialog.lift()
        return "break"


    def replace_once(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area: return "break"

        find_what = self.find_what_var.get()
        replace_with = self.replace_with_var.get()

        if not find_what:
            messagebox.showinfo("Replace", "Find string is empty.", parent=self.find_replace_dialog)
            return "break"

        # Check if current selection matches find_what criteria
        # This is important because "Replace" should only act on a found and selected item
        try:
            selected_text = text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            # We need to verify if this selected_text actually matches find_what with current options
            # This is a bit complex. A simpler way: if there's a selection, replace it, then find next.
            # If no selection, find next, then if found, replace it.

            sel_first = text_area.index(tk.SEL_FIRST)
            sel_last = text_area.index(tk.SEL_LAST)

            # Verify if the selected text matches 'find_what' according to current settings.
            # This is tricky. For now, assume if there's a selection, it's the one to replace.
            # A more robust way would be to re-search from sel_first for length of sel_last-sel_first
            # to confirm it's a valid match.

            if sel_first and sel_last: # If there is a selection
                 # Check if the selected text actually matches 'find_what' with current options.
                 # This is a simplification. A proper check would involve re-evaluating the match.
                 # For instance, if user changes "Case Sensitive" *after* a find, current selection might no longer be valid.
                 # For now, we assume the selection is valid if it exists.
                text_area.delete(sel_first, sel_last)
                text_area.insert(sel_first, replace_with)
                text_area.mark_set(tk.INSERT, f"{sel_first} + {len(replace_with)} chars")
                text_area.tag_remove(tk.SEL, "1.0", tk.END) # Clear selection after replace
                text_area.event_generate("<<Modified>>")
                self.find_next() # Automatically find the next occurrence
            else: # No selection, just do a "Find Next"
                self.find_next()
                # If find_next successfully selected something, now we can replace it.
                # This requires find_next to signal success or for us to check selection.
                # This makes replace_once coupled with find_next's state.
                # Alternative: find_next, then if found, replace.
                # Let's try: if find_next() results in a selection, then replace.
                # The current find_next already selects. So if after find_next() there's a selection, replace it.
                # This means "Replace" button effectively means "Replace current selection if valid, then Find Next"
                # OR "Find Next, then if found, replace *that*".
                # The common UX is: "Replace" acts on current selection if it's a find match, then finds next.
                # If no selection, or selection is not a find match, it does "Find Next". If that finds something,
                # the item is selected, and a *second* click on "Replace" would replace it.
                # Let's stick to: if selection exists and is a "valid" find, replace it and find next.
                # For now, if selection exists, it's replaced.
                pass


        except tk.TclError: # No selection
            self.find_next() # Find the first instance, it will be selected. User can then click Replace again.

        if self.find_replace_dialog and self.find_replace_dialog.winfo_exists():
             self.find_replace_dialog.lift()
        return "break"

    def replace_all(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area: return "break"

        find_what = self.find_what_var.get()
        replace_with = self.replace_with_var.get()

        if not find_what:
            messagebox.showinfo("Replace All", "Find string is empty.", parent=self.find_replace_dialog)
            return "break"

        case_sensitive = self.case_sensitive_find_var.get()
        whole_word = self.whole_word_var.get()
        use_regex = self.regex_var.get()
        # wrap_around and search_backwards are not typically used for "Replace All" in its basic sense.
        # Replace All usually goes from start to end.

        count = 0
        start_index = "1.0"
        while True:
            found_pos, length = self._search_in_text(text_area, find_what, start_index, tk.END,
                                                     case_sensitive, whole_word, use_regex, False) # Always forward for replace all
            if found_pos:
                end_replace_pos = f"{found_pos} + {length} chars"
                text_area.delete(found_pos, end_replace_pos)
                text_area.insert(found_pos, replace_with)
                count += 1
                start_index = f"{found_pos} + {len(replace_with)} chars" # Continue search after the replaced text
                if start_index == text_area.index(tk.END): # Reached end
                    break
            else: # No more occurrences
                break

        if count > 0:
            text_area.event_generate("<<Modified>>")
            messagebox.showinfo("Replace All", f"Replaced {count} occurrence(s).", parent=self.find_replace_dialog)
        else:
            messagebox.showinfo("Replace All", f"Cannot find '{find_what}'.", parent=self.find_replace_dialog)

        if self.find_replace_dialog and self.find_replace_dialog.winfo_exists():
             self.find_replace_dialog.lift()
        return "break"

    # --- Font Dialog Methods ---
    def open_font_dialog(self):
        if hasattr(self, "font_dialog") and self.font_dialog.winfo_exists():
            self.font_dialog.lift()
            self.font_dialog.focus_set()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Font")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        self.font_dialog = dialog

        # Variables
        font_family_var = tk.StringVar(value=self.current_font_family)
        font_size_var = tk.IntVar(value=self.current_font_size)
        font_bold_var = tk.BooleanVar(value=(self.current_font_weight == "bold"))
        font_italic_var = tk.BooleanVar(value=(self.current_font_slant == "italic"))

        available_families = sorted(list(set(tkfont.families())))

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Font Family:").grid(row=0, column=0, sticky=tk.W, pady=2)
        family_combobox = ttk.Combobox(main_frame, textvariable=font_family_var, values=available_families, state="readonly", width=30)
        family_combobox.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        try:
            family_combobox.set(self.current_font_family)
        except tk.TclError:
            if available_families:
                font_family_var.set(available_families[0])

        ttk.Label(main_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, pady=2)
        size_spinbox = ttk.Spinbox(main_frame, from_=8, to=72, textvariable=font_size_var, width=5)
        size_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        bold_cb = ttk.Checkbutton(main_frame, text="Bold", variable=font_bold_var)
        bold_cb.grid(row=2, column=0, sticky=tk.W, pady=2)
        italic_cb = ttk.Checkbutton(main_frame, text="Italic", variable=font_italic_var)
        italic_cb.grid(row=2, column=1, sticky=tk.W, pady=2)

        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        preview_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        preview_label = ttk.Label(preview_frame, text="AaBbCcDdEe 123 !@#", font=self.editor_font)
        preview_label.pack(padx=5, pady=5)

        def update_preview_binding(event=None): # Renamed to avoid conflict
            self.update_font_preview(preview_label, font_family_var, font_size_var, font_bold_var, font_italic_var)

        family_combobox.bind("<<ComboboxSelected>>", update_preview_binding)
        size_spinbox.config(command=update_preview_binding)
        bold_cb.config(command=update_preview_binding)
        italic_cb.config(command=update_preview_binding)

        self.update_font_preview(preview_label, font_family_var, font_size_var, font_bold_var, font_italic_var)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.E, pady=10)

        def on_apply():
            new_family = font_family_var.get()
            new_size = font_size_var.get()
            new_weight = "bold" if font_bold_var.get() else "normal"
            new_slant = "italic" if font_italic_var.get() else "roman"

            self.apply_new_font(new_family, new_size, new_weight, new_slant)
            dialog.destroy()

        ttk.Button(button_frame, text="Apply", command=on_apply).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)

        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

    def update_font_preview(self, preview_label, family_var, size_var, bold_var, italic_var):
        family = family_var.get()
        try:
            size = size_var.get()
            if size < 1: size = 1 # Ensure size is positive
        except tk.TclError:
            size = self.current_font_size

        weight = "bold" if bold_var.get() else "normal"
        slant = "italic" if italic_var.get() else "roman"

        try:
            preview_font = tkfont.Font(family=family, size=size, weight=weight, slant=slant)
            preview_label.config(font=preview_font)
        except tk.TclError as e:
            # print(f"Error updating font preview: {e}") # For debugging
            preview_label.config(font=tkfont.Font(family=self.current_font_family, size=self.current_font_size)) # Fallback to current editor font

    def apply_new_font(self, family, size, weight, slant):
        self.current_font_family = family
        self.current_font_size = size
        self.current_font_weight = weight
        self.current_font_slant = slant

        self.editor_font.config(family=family, size=size, weight=weight, slant=slant)

        new_line_number_font_config = {"family": family, "size": size}
        # Potentially adjust line number canvas width if font size changes significantly
        # For now, keep it fixed but update its font.

        for tab in self.tabs:
            tab.text_area.config(font=self.editor_font)
            tab.line_numbers_font.config(**new_line_number_font_config)
            tab.redraw_line_numbers()


if __name__ == "__main__":
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()
