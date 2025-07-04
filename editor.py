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
        self.frame = ttk.Frame(self.notebook, padding=2) # Added padding=2
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

        # Search highlight tag
        self.text_area.tag_configure("search_highlight", background="yellow", foreground="black")
        self.text_area.tag_configure("current_search_highlight", background="orange", foreground="black")

        # For managing debounced keyword highlighting
        self._keyword_highlight_after_id = None

        # For managing debounced syntax highlighting
        self._syntax_highlight_after_id = None
        self.current_language_name = None

        # Filter state for this tab
        self.original_text_for_filter = None
        self.is_filtered_view = False
        self.current_filter_str = ""
        self.current_filter_case_sensitive = False
        self.current_filter_invert = False # Added for invert state

        # Syntax highlighting tags
        self.text_area.tag_configure("hl_keyword", foreground="#0000FF")  # Blue
        self.text_area.tag_configure("hl_comment", foreground="#008000")  # Green
        self.text_area.tag_configure("hl_string", foreground="#A52A2A")   # Brown/SaddleBrown
        self.text_area.tag_configure("hl_number", foreground="#FF00FF")  # Magenta
        self.text_area.tag_configure("hl_operator", foreground="#FF8C00") # DarkOrange
        self.text_area.tag_configure("hl_builtin", foreground="#20B2AA")  # LightSeaGreen
        # Add more tags as needed for other token types


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

        # Apply initial keyword highlighting if any are set globally
        self.apply_keyword_highlights(self.app.keyword_highlight_settings)
        # Detect and apply syntax highlighting based on initial file_path
        self._detect_and_set_language(self.current_file)


    def load_file_content(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
            self.current_file = filepath # Set current_file before detecting language
            self.text_changed = False
            self.text_area.edit_modified(False)
            self.update_tab_title()
            self._detect_and_set_language(self.current_file) # Detect language for newly loaded file
            self.apply_keyword_highlights(self.app.keyword_highlight_settings) # Apply after loading
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
            # Only process if text area is not disabled (i.e., not in read-only filtered view)
            if self.text_area.cget("state") == tk.NORMAL:
                if self.text_area.edit_modified():
                    if not self.text_changed: # Mark changed only once until saved
                        self.text_changed = True
                        self.update_tab_title() # This will add '*'
                self.text_area.edit_modified(False) # Reset Tkinter's internal modified flag
            else: # Text area is disabled, likely due to filtering. Programmatic changes don't set 'text_changed'.
                 self.text_area.edit_modified(False) # Still reset this internal Tk flag

        # Always redraw line numbers on any relevant event (Modified, Configure)
        # Using after(1) to ensure text_area layout is updated before redrawing
        self.text_area.after(1, self.redraw_line_numbers)
        if event and (str(event.type) == "Modified" or str(event.type) == "Configure"):
            self.app.update_status_bar()
            if str(event.type) == "Modified":
                self.clear_search_highlight_tags() # Clear find/replace highlights

                # Schedule keyword highlighting update (debounced)
                if self.app.keyword_highlight_settings.get("active", False):
                    if self._keyword_highlight_after_id:
                        self.text_area.after_cancel(self._keyword_highlight_after_id)
                    self._keyword_highlight_after_id = self.text_area.after(500,
                        lambda: self.apply_keyword_highlights(self.app.keyword_highlight_settings))

                # Schedule syntax highlighting update (debounced)
                if self.current_language_name:
                    if self._syntax_highlight_after_id:
                        self.text_area.after_cancel(self._syntax_highlight_after_id)
                    self._syntax_highlight_after_id = self.text_area.after(500, self.apply_syntax_highlighting)


    def clear_search_highlight_tags(self):
        self.text_area.tag_remove("search_highlight", "1.0", tk.END)
        self.text_area.tag_remove("current_search_highlight", "1.0", tk.END)

    def apply_text_filter(self, filter_str, case_sensitive, invert_filter):
        # print(f"DEBUG: Tab '{self.current_file}' apply_text_filter: '{filter_str}', CS: {case_sensitive}, Invert: {invert_filter}")

        # Update current filter state for this tab
        self.current_filter_str = filter_str
        self.current_filter_case_sensitive = case_sensitive
        self.current_filter_invert = invert_filter

        # Make text area temporarily writable for modifications
        # original_state = self.text_area.cget("state") # Not needed if we set explicitly
        self.text_area.config(state=tk.NORMAL) # Always make normal before changing content

        if not filter_str:  # Filter is empty, restore original text if needed
            if self.is_filtered_view and self.original_text_for_filter is not None:
                current_insert = self.text_area.index(tk.INSERT)
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", self.original_text_for_filter)
                self.original_text_for_filter = None
                self.is_filtered_view = False
                try:
                    self.text_area.mark_set(tk.INSERT, current_insert)
                    self.text_area.see(current_insert)
                except tk.TclError:
                    self.text_area.mark_set(tk.INSERT, "1.0")
            # Text area remains NORMAL if filter is cleared
        else:  # Filter is active
            if not self.is_filtered_view:
                self.original_text_for_filter = self.text_area.get("1.0", tk.END + "-1c")
                self.is_filtered_view = True

            source_text_for_filtering = self.original_text_for_filter
            lines = source_text_for_filtering.splitlines(keepends=True) # Keep endings for rejoining
            matching_lines = []

            str_to_find = filter_str if case_sensitive else filter_str.lower()

            for line_content_with_ending in lines:
                line_to_check_in = line_content_with_ending if case_sensitive else line_content_with_ending.lower()

                match_found = (str_to_find in line_to_check_in)

                if invert_filter:
                    if not match_found:
                        matching_lines.append(line_content_with_ending)
                else: # Normal filter
                    if match_found:
                        matching_lines.append(line_content_with_ending)

            self.text_area.delete("1.0", tk.END)
            if matching_lines:
                self.text_area.insert("1.0", "".join(matching_lines))

            self.text_area.config(state=tk.DISABLED) # Make filtered view read-only
            # print(f"DEBUG: Filtered. Displaying {len(matching_lines)} lines. State: DISABLED")

        # Refresh UI elements that depend on text content
        self.redraw_line_numbers()
        if self.current_language_name:
            self.apply_syntax_highlighting() # This will use current text_area content
        if self.app.keyword_highlight_settings.get("active", False):
            self.apply_keyword_highlights(self.app.keyword_highlight_settings)

        self.app.update_status_bar()


    def _detect_and_set_language(self, filepath):
        self.current_language_name = None # Reset before detection
        # print(f"DEBUG: Tab {self.current_file if self.current_file else 'Untitled'} detecting lang for path: {filepath}")

        if not filepath:
            self.apply_syntax_highlighting() # Will clear if no lang
            return

        _, extension = os.path.splitext(filepath)
        extension = extension.lower()

        if self.app and hasattr(self.app, 'language_definitions'): # Ensure app and definitions exist
            for lang_name, lang_def in self.app.language_definitions.items():
                if extension in lang_def.get("extensions", []):
                    self.current_language_name = lang_name
                    # print(f"DEBUG: Detected language: {lang_name} for {filepath}")
                    break

        self.apply_syntax_highlighting()


    def _clear_syntax_highlight_tags(self):
        # Helper to clear all defined syntax highlighting tags
        # Assumes hl_tags are defined in self.app (TextEditor instance) or passed
        # For now, let's list them explicitly based on what's configured
        syntax_tags_to_clear = ["hl_keyword", "hl_comment", "hl_string",
                                "hl_number", "hl_operator", "hl_builtin"]
        for tag in syntax_tags_to_clear:
            try:
                self.text_area.tag_remove(tag, "1.0", tk.END)
            except tk.TclError:
                pass # Tag might not exist or have instances

    def apply_syntax_highlighting(self):
        if not self.current_language_name or not self.app.language_definitions:
            return

        lang_def = self.app.language_definitions.get(self.current_language_name)
        if not lang_def or not lang_def.get("rules"):
            return

        self._clear_syntax_highlight_tags()

        # Optimization: Disable text widget updates during highlighting for performance
        # This is not directly possible in Tkinter without complex hacks.
        # Instead, we rely on debouncing and careful regex.

        all_text = self.text_area.get("1.0", tk.END)
        if not all_text.strip(): # No content to highlight
            return

        import re

        for rule in lang_def["rules"]:
            token_type = rule["token_type"]
            pattern_str = rule["pattern"]

            try:
                # Pre-compile regex for slight efficiency if called many times, though finditer does this.
                # compiled_pattern = re.compile(pattern_str) # Not strictly needed for finditer
                for match in re.finditer(pattern_str, all_text):
                    start_offset, end_offset = match.span()

                    # Convert character offsets to Tkinter Text widget indices
                    # This needs to be robust for multiline text.
                    # "1.0 + N chars" works across lines.
                    start_idx = self.text_area.index(f"1.0 + {start_offset} chars")
                    end_idx = self.text_area.index(f"1.0 + {end_offset} chars")

                    self.text_area.tag_add(token_type, start_idx, end_idx)
            except re.error as e:
                print(f"Regex error for language {self.current_language_name}, pattern {pattern_str}: {e}")
            except tk.TclError as e:
                # This can happen if indices are invalid, e.g. during rapid text changes
                # before debouncing kicks in fully or if text length changed mid-iteration.
                print(f"TclError during syntax highlighting: {e}. Text might have changed.")
                # It might be safer to break or return if text changes during highlighting.
                # For now, just print and continue. This should be rare with debouncing.
                return # Stop highlighting if text area state is unstable

    def apply_keyword_highlights(self, highlight_settings):
        # Clear previous user keyword highlights
        for i in range(len(self.app.pastel_colors) + 5): # Clear a few more tags than colors, just in case
            try:
                self.text_area.tag_remove(f"user_keyword_{i}", "1.0", tk.END)
            except tk.TclError: # Tag might not exist yet
                pass

        if not highlight_settings or not highlight_settings.get("active", False) or not highlight_settings.get("parsed_keywords"):
            return

        keywords = highlight_settings["parsed_keywords"]
        case_sensitive = highlight_settings["case_sensitive"]
        whole_word = highlight_settings["whole_word"]
        kw_to_color = highlight_settings["keyword_to_color_map"]
        kw_to_tag = highlight_settings["keyword_to_tag_name_map"]

        for keyword_text in keywords:
            tag_name = kw_to_tag.get(keyword_text)
            color = kw_to_color.get(keyword_text)
            if not tag_name or not color:
                continue

            self.text_area.tag_configure(tag_name, background=color, foreground="black") # Ensure foreground for readability

            start_index = "1.0"
            while True:
                # Simplified search logic adapted from TextEditor._search_in_text
                nocase_local = not case_sensitive

                # For whole word with keyword highlighting, we construct a regex if needed
                # or use 'exact' for non-regex simple whole word.
                # Since keyword highlighting is not using TextEditor's main regex engine flag,
                # we decide here how to handle whole_word.
                # Let's use a simple string search with 'exact' if whole_word is true.

                search_pattern = keyword_text
                use_regexp_for_this_keyword = False # Default to string search

                if whole_word:
                    # A common way to do whole word for string search is to wrap with word boundaries
                    # if the underlying search method doesn't support 'exact' well or for more control.
                    # However, tk.Text.search 'exact' option should work for basic whole word.
                    # If we wanted regex-style whole word, we'd build \bkeyword\b pattern.
                    # For keyword highlighting, let's assume 'exact' is sufficient for non-regex "whole word"
                    pass


                # We need a count variable for text_widget.search
                length_var = tk.IntVar()
                pos = self.text_area.search(search_pattern, start_index, tk.END,
                                            nocase=nocase_local,
                                            regexp=use_regexp_for_this_keyword, # False for now
                                            exact=whole_word, # Use exact for whole word if not doing custom regex
                                            count=length_var)

                if pos:
                    match_len = length_var.get()
                    if match_len == 0 and len(search_pattern) > 0 : # Sometimes count is not set for exact matches if pattern is literal
                        match_len = len(search_pattern)

                    if match_len > 0:
                        end_pos = self.text_area.index(f"{pos} + {match_len} chars")
                        self.text_area.tag_add(tag_name, pos, end_pos)
                        start_index = end_pos
                    else: # No length, cannot proceed with this match
                        break
                else: # No more matches for this keyword
                    break

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

        # Ensure text area is updated for dlineinfo to be accurate
        self.text_area.update_idletasks()

        first_visible_char_index = self.text_area.index("@0,0")

        # Handle case where text_area might be empty or not yet fully initialized
        if not first_visible_char_index:
            return

        try:
            first_line_num_str = first_visible_char_index.split('.')[0]
            if not first_line_num_str: # Should not happen with valid index like "1.0"
                return
            first_line_num = int(first_line_num_str)
        except ValueError:
            return # Invalid index format

        current_displayed_line_idx = first_line_num

        first_visible_line_bbox = self.text_area.dlineinfo(f"{first_line_num}.0")
        if not first_visible_line_bbox: # No info for the first supposed visible line (e.g., empty text area)
            return

        y_offset_of_visible_area_top = first_visible_line_bbox[1]

        while True:
            dline_info = self.text_area.dlineinfo(f"{current_displayed_line_idx}.0")

            if dline_info is None: # No more displayed lines
                break

            line_y_in_text_content = dline_info[1]
            line_height = dline_info[3]

            canvas_y = (line_y_in_text_content - y_offset_of_visible_area_top) + (line_height / 2)

            if canvas_y < 0 and current_displayed_line_idx > first_line_num :
                 # This can happen if first_line_num was > 1 due to scrolling, then content changed
                 # such that total lines are less than first_line_num.
                 pass # The dlineinfo check for None should handle termination.


            if canvas_y > self.line_numbers.winfo_height() + line_height: # line_height added for buffer
                # Stop if the line would be drawn completely below the visible canvas area
                break

            # Only draw if line is somewhat visible
            if (line_y_in_text_content + line_height) >= y_offset_of_visible_area_top and \
               line_y_in_text_content <= y_offset_of_visible_area_top + self.line_numbers.winfo_height():
                self.line_numbers.create_text(38, canvas_y, anchor=tk.NE, text=str(current_displayed_line_idx), font=self.line_numbers_font)

            current_displayed_line_idx += 1

        # Dynamic width for line numbers canvas (optional, can be complex)
        # last_line_str_len = len(str(i-1))

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

        # current_tabs = list(self.notebook.tabs()) # Not needed if removing by self
        try:
            # self.notebook.forget(self.frame_id()) # This is correct
            # Find self in the app's list of EditorTab objects to remove it.
            # The visual tab needs to be removed from the notebook first.

            original_tab_count = len(self.app.tabs)
            selected_tab_before_close = self.app.notebook.index(tk.CURRENT) # Get index of currently selected tab in notebook

            self.notebook.forget(self.frame_id()) # Remove from GUI

            if self in self.app.tabs:
                self.app.tabs.remove(self)
            else:
                # This state indicates a mismatch between notebook tabs and self.app.tabs tracking
                # This ideally shouldn't happen. For robustness, we proceed.
                print(f"Warning: EditorTab instance {self} was not found in self.app.tabs during close_tab.")

            if not self.app.tabs: # If this was the last tab object in our list
                if self.app.quitting_app:
                    # If quitting and no actual tabs left in notebook, destroy root
                    if len(self.app.notebook.tabs()) == 0:
                        self.app.root.destroy()
                    # else, other tabs might exist if self.app.tabs was out of sync, let exit_editor_action handle
                else:
                    self.app.new_file_action() # Create a new untitled tab
            else:
                # If other tabs remain, try to select a sensible one.
                # If the closed tab was selected, select the previous one or first one.
                # Notebook's own selection behavior after forget might handle this,
                # but an explicit select can ensure on_tab_changed fires.
                if len(self.app.notebook.tabs()) > 0:
                    if selected_tab_before_close >= len(self.app.notebook.tabs()): # if last tab was closed
                        self.app.notebook.select(len(self.app.notebook.tabs()) - 1)
                    # else: notebook might auto-select, or current selection is still valid.
                    # on_tab_changed will be triggered if selection changes.
                else: # Should be covered by "if not self.app.tabs" creating new one
                    pass

            # update_app_title and update_status_bar are called by on_tab_changed
            # if a new tab is selected or created.
            # If no tab change event (e.g. closing an unfocused tab), we might need an explicit update.
            # However, TextEditor.close_current_tab_action calls update_status_bar explicitly.
            # And update_app_title is also typically called via on_tab_changed.
            # Let's ensure on_tab_changed is robustly called if selection actually changes.
            # The notebook <<NotebookTabChanged>> event should handle this.
            self.app.update_app_title() # Explicitly update title
            self.app.update_status_bar() # Explicitly update status bar

            return True
        except tk.TclError as e: # Catch specific Tcl errors from notebook operations
            print(f"Error closing tab (TclError): {e}")
            # Fallback or recovery might be needed if notebook is in a bad state
            return False
        except Exception as e: # Catch any other unexpected errors
            print(f"Unexpected error closing tab: {e}")
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
        self.known_fixed_fonts = sorted([
            "TkFixedFont", "Courier New", "Courier", "Consolas", "DejaVu Sans Mono",
            "Liberation Mono", "Menlo", "Monaco", "Source Code Pro", "Fira Code",
            "Inconsolata", "Fixedsys", "Terminal", "Monospace"
        ]) # Sorted for consistent fallback behavior if needed

        system_fonts = set(tkfont.families()) # Use a set for efficient lookup

        # Determine a suitable default fixed-width font, prioritizing Courier New
        preferred_defaults = ["Courier New", "Consolas", "TkFixedFont"]

        default_family_to_set = None
        for preferred_font in preferred_defaults:
            if preferred_font in system_fonts:
                default_family_to_set = preferred_font
                break

        if not default_family_to_set: # If none of the top preferences are found
            # Try any other known fixed-width font
            for ff in self.known_fixed_fonts:
                if ff in system_fonts:
                    default_family_to_set = ff
                    break

        if not default_family_to_set: # Absolute fallback if still nothing from known_fixed_fonts
            default_family_to_set = "TkFixedFont" # Rely on Tk to provide something

        self.current_font_family = default_family_to_set
        self.current_font_size = 14 # Changed default size
        self.current_font_weight = "normal"
        self.current_font_slant = "roman"

        self.editor_font = tkfont.Font(
            family=self.current_font_family,
            size=self.current_font_size,
            weight=self.current_font_weight,
            slant=self.current_font_slant
        )

        # Keyword Highlighting Settings
        self.keyword_highlight_settings = {
            "keywords_input_string": "",
            "parsed_keywords": [], # List of unique keyword strings
            "keyword_to_color_map": {}, # Maps keyword string to a color
            "keyword_to_tag_name_map": {}, # Maps keyword string to a tag name like "user_keyword_0"
            "case_sensitive": False,
            "whole_word": True,
            "active": False # Is highlighting currently active?
        }
        self.pastel_colors = [ # Background colors
            "#FFDFD3", "#FFFACD", "#D7E9F7", "#E0FFFF", "#F0FFF0",
            "#FFE4E1", "#FAFAD2", "#ADD8E6", "#E6E6FA", "#FFF0F5"
        ] # Light Salmon, LemonChiffon, LightBlue (custom), PaleTurquoise, Honeydew,
          # MistyRose, LightGoldenrodYellow, LightSkyBlue (alternative), Lavender, LavenderBlush

        # Syntax Highlighting Language Definitions
        self.language_definitions = {
            "python": {
                "extensions": [".py", ".pyw"],
                # Order matters: Comments and strings usually first
                "rules": [
                    {"token_type": "hl_comment", "pattern": r"#.*"},
                    # More robust string regex: handles escapes, and doesn't break on internal quotes if not matching type
                    {"token_type": "hl_string", "pattern": r"(\"\"\"(?:[^\"]|\\\"|\n)*?\"\"\"|\'\'\'(?:[^\']|\\\'|\n)*?\'\'\'|\"[^\"\\\n]*(?:\\.[^\"\\\n]*)*\"|\'[^\'\\\n]*(?:\\.[^\'\\\n]*)*\')"},
                    {"token_type": "hl_keyword", "pattern": r'\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b'},
                    {"token_type": "hl_builtin", "pattern": r'\b(abs|all|any|ascii|bin|bool|bytearray|bytes|callable|chr|classmethod|compile|complex|delattr|dict|dir|divmod|enumerate|eval|exec|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|print|property|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|vars|zip|__import__)\b'},
                    # Numbers: hex, octal, binary, float, int
                    {"token_type": "hl_number", "pattern": r'\b(?:0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+|[0-9]+\.?[0-9]*(?:[eE][+-]?[0-9]+)?|[0-9]+)\b'},
                    {"token_type": "hl_operator", "pattern": r"(\+|\-|\*|/|%|=|==|!=|>|<|>=|<=|&|\||\^|~|<<|>>|\*\*|//|@)"} # Added @ for decorators
                ]
            }
            # Other language definitions will be added here later
        }


        # Create main menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Toolbar
        self.toolbar_frame = ttk.Frame(self.root, relief=tk.FLAT, padding=2)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        # Filter Bar (initially hidden)
        self.filter_bar_frame = ttk.Frame(self.root, padding=(5,2)) # Padding: (left/right, top/bottom)
        # Packed by toggle_filter_bar method

        self.filter_text_var = tk.StringVar()
        ttk.Label(self.filter_bar_frame, text="Filter:").pack(side=tk.LEFT, padx=(0,5))
        self.filter_entry = ttk.Entry(self.filter_bar_frame, textvariable=self.filter_text_var, width=40)
        self.filter_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.filter_case_var = tk.BooleanVar(value=False)
        self.filter_case_checkbox = ttk.Checkbutton(self.filter_bar_frame, text="Case Sensitive", variable=self.filter_case_var)
        self.filter_case_checkbox.pack(side=tk.LEFT, padx=5)

        self.filter_invert_var = tk.BooleanVar(value=False)
        self.filter_invert_checkbox = ttk.Checkbutton(self.filter_bar_frame, text="Invert", variable=self.filter_invert_var)
        self.filter_invert_checkbox.pack(side=tk.LEFT, padx=5)

        # Using a simple text 'x' for close button for now
        self.filter_close_btn = ttk.Button(self.filter_bar_frame, text="✕", command=self.toggle_filter_bar, width=3)
        self.filter_close_btn.pack(side=tk.LEFT, padx=5)

        # Traces for filter changes
        self.filter_text_var.trace_add("write", self.on_filter_settings_changed)
        self.filter_case_var.trace_add("write", self.on_filter_settings_changed)
        self.filter_invert_var.trace_add("write", self.on_filter_settings_changed)

        # Example Toolbar Buttons (add more as needed)
        btn_padx = 3 # Increased padx for buttons
        btn_pady = 2

        self.new_btn = ttk.Button(self.toolbar_frame, text="New", command=self.new_file_action_handler)
        self.new_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)

        self.open_btn = ttk.Button(self.toolbar_frame, text="Open", command=self.open_file_action_handler)
        self.open_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)

        self.save_btn = ttk.Button(self.toolbar_frame, text="Save", command=lambda: self.save_action_handler(save_as_if_needed=False))
        self.save_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)

        # Separator could be a Frame with height or specific style
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=btn_pady) # Use btn_pady for consistency

        self.cut_btn = ttk.Button(self.toolbar_frame, text="Cut", command=self.cut_action)
        self.cut_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)

        self.copy_btn = ttk.Button(self.toolbar_frame, text="Copy", command=self.copy_action)
        self.copy_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)

        self.paste_btn = ttk.Button(self.toolbar_frame, text="Paste", command=self.paste_action)
        self.paste_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)

        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=btn_pady)

        self.undo_btn = ttk.Button(self.toolbar_frame, text="Undo", command=self.undo_action)
        self.undo_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)

        self.redo_btn = ttk.Button(self.toolbar_frame, text="Redo", command=self.redo_action)
        self.redo_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)


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

        self.format_menu.add_separator()

        # Line Spacing Sub-menu
        self.line_spacing_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Line Spacing", menu=self.line_spacing_menu)
        self.line_spacing_menu.add_command(label="Condense Internal Whitespace", command=self.condense_internal_whitespace)
        self.line_spacing_menu.add_command(label="Double Space Lines", command=self.double_space_lines)
        self.line_spacing_menu.add_command(label="Reduce Multiple Blank Lines to One", command=self.reduce_blank_lines)
        self.line_spacing_menu.add_command(label="Remove All Blank Lines", command=self.remove_all_blank_lines)
        # Future items:
        # self.line_spacing_menu.add_command(label="Triple Space Lines", command=self.triple_space_lines)


        # Line Alteration Sub-menu
        self.line_alteration_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Line Alteration", menu=self.line_alteration_menu)
        # Future items:
        self.line_alteration_menu.add_command(label="Delete Duplicate Consecutive Lines", command=self.delete_duplicate_consecutive_lines)
        self.line_alteration_menu.add_command(label="Reverse Lines", command=self.reverse_lines_action)

        # Join/Split Lines Sub-menu
        self.join_split_lines_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Join/Split Lines", menu=self.join_split_lines_menu)
        self.join_split_lines_menu.add_command(label="Join Lines (with space)", command=self.join_lines_with_space)
        self.join_split_lines_menu.add_command(label="Join Lines (with ', ')", command=self.join_lines_with_comma_space)
        # Future items will be added here


        # Search Menu (for Find/Replace)
        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Search", menu=self.search_menu)
        self.search_menu.add_command(label="Find/Replace...", command=self.open_find_replace_dialog, accelerator="Ctrl+F")

        # View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Change Font...", command=self.open_font_dialog)
        self.view_menu.add_command(label="Keyword Highlighting...", command=self.open_keyword_highlight_dialog)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Toggle Filter Bar", command=self.toggle_filter_bar, accelerator="Ctrl+Shift+F")


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
        self.root.bind_all("<Control-f>", self.open_find_replace_dialog)
        self.root.bind_all("<Control-F>", lambda event: self.toggle_filter_bar()) # Ctrl+Shift+F


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

        current_tab = self.get_current_tab()
        if current_tab:
            # Apply keyword highlighting to newly focused tab if active
            if self.keyword_highlight_settings.get("active", False):
                current_tab.apply_keyword_highlights(self.keyword_highlight_settings)

            # Apply syntax highlighting to newly focused tab if language is set
            if current_tab.current_language_name:
                current_tab.apply_syntax_highlighting()
            else: # If no language, ensure syntax highlights are cleared
                current_tab._clear_syntax_highlight_tags()

            # If filter bar is visible, apply its current settings to the new tab
            if self.filter_bar_frame.winfo_ismapped():
                self.on_filter_settings_changed()

            # Update Find/Replace button states if dialog is open
            if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists():
                self.update_find_replace_button_states()


    def on_filter_settings_changed(self, *args):
        # This method is called when filter text or case sensitivity changes
        if not self.filter_bar_frame.winfo_ismapped():
            # If filter bar is hidden, traces might still fire if vars are changed programmatically.
            # We only want to filter if the bar is visible and user is interacting, OR if toggle_filter_bar clears it.
            # toggle_filter_bar handles its case by setting filter_text_var to "" which then calls this.
            # So, if bar is not mapped, and filter_text_var is now empty, it means we need to clear filter.
            if not self.filter_text_var.get(): # If filter text is empty (e.g. cleared by hiding bar)
                current_tab = self.get_current_tab()
                if current_tab and current_tab.is_filtered_view: # If tab was filtered
                     current_tab.apply_text_filter("", self.filter_case_var.get(), self.filter_invert_var.get())
            return

        current_tab = self.get_current_tab()
        if current_tab:
            filter_str = self.filter_text_var.get()
            case_sens = self.filter_case_var.get()
            invert = self.filter_invert_var.get()
            current_tab.apply_text_filter(filter_str, case_sens, invert)

            # Update Find/Replace button states if dialog is open
            if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists():
                self.update_find_replace_button_states()


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
            if current_tab.is_filtered_view and current_tab.original_text_for_filter is not None:
                content_to_save = current_tab.original_text_for_filter
                # print(f"DEBUG: Saving original_text_for_filter for {current_tab.current_file}")
            else:
                content_to_save = current_tab.get_content() # Gets from text_area
                # print(f"DEBUG: Saving text_area content for {current_tab.current_file}")

            with open(current_tab.current_file, "w", encoding="utf-8") as f:
                f.write(content_to_save)

            # Regardless of what was saved (original or current view), if save is successful,
            # the document represented by current_tab.current_file is now considered saved.
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
                current_tab._detect_and_set_language(filepath) # Re-detect language and highlight
                # Status bar and app title are updated by save_file and its call to update_tab_title
                return True
            else:
                # current_tab.current_file = None # Optionally revert if save failed. Or keep new path.
                # If save failed, language might still be based on the new (failed) filepath.
                # This could be reset or left as is. For now, let _detect_and_set_language run.
                current_tab._detect_and_set_language(filepath)
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
        dialog.geometry("350x300") # Increased size for new options

        # Variables
        self.sort_type_var = tk.StringVar(value="alpha_asc") # New variable for sort type
        # Values: "alpha_asc", "alpha_desc", "len_asc", "len_desc", "reverse"

        self.case_sensitive_sort_var = tk.BooleanVar(value=True) # Renamed for clarity
        self.remove_duplicates_sort_var = tk.BooleanVar(value=False) # Renamed for clarity

        # --- UI Elements ---
        # Main content frame with padding
        main_dialog_frame = ttk.Frame(dialog, padding=10)
        main_dialog_frame.pack(expand=True, fill=tk.BOTH)

        type_frame = ttk.LabelFrame(main_dialog_frame, text="Sort Type", padding=5) # Pack into main_dialog_frame
        type_frame.pack(fill=tk.X) # Removed padx/pady from here

        ttk.Radiobutton(type_frame, text="Alphabetical (Ascending)", variable=self.sort_type_var, value="alpha_asc", command=self.update_sort_options_state).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Alphabetical (Descending)", variable=self.sort_type_var, value="alpha_desc", command=self.update_sort_options_state).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="By Length (Shortest First)", variable=self.sort_type_var, value="len_asc", command=self.update_sort_options_state).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="By Length (Longest First)", variable=self.sort_type_var, value="len_desc", command=self.update_sort_options_state).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Reverse Line Order", variable=self.sort_type_var, value="reverse", command=self.update_sort_options_state).pack(anchor=tk.W)

        options_frame = ttk.LabelFrame(main_dialog_frame, text="Options", padding=5) # Pack into main_dialog_frame
        options_frame.pack(pady=5, fill=tk.X) # Removed padx from here

        self.case_sensitive_checkbox = ttk.Checkbutton(options_frame, text="Case Sensitive", variable=self.case_sensitive_sort_var)
        self.case_sensitive_checkbox.pack(anchor=tk.W, padx=5)

        self.remove_duplicates_checkbox = ttk.Checkbutton(options_frame, text="Remove Duplicate Lines", variable=self.remove_duplicates_sort_var)
        self.remove_duplicates_checkbox.pack(anchor=tk.W, padx=5)

        self.update_sort_options_state() # Initial state update

        def on_apply():
            self.apply_sort_lines(
                self.sort_type_var.get(),
                self.case_sensitive_sort_var.get(),
                self.remove_duplicates_sort_var.get()
            )
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(main_dialog_frame) # Pack into main_dialog_frame
        button_frame.pack(pady=10, fill=tk.X, side=tk.BOTTOM)
        ttk.Button(button_frame, text="Apply", command=on_apply).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5) # padx=5 on Cancel too

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

    def update_sort_options_state(self):
        sort_type = self.sort_type_var.get()
        if sort_type == "alpha_asc" or sort_type == "alpha_desc":
            self.case_sensitive_checkbox.config(state=tk.NORMAL)
            self.remove_duplicates_checkbox.config(state=tk.NORMAL)
        elif sort_type == "len_asc" or sort_type == "len_desc":
            self.case_sensitive_checkbox.config(state=tk.DISABLED)
            self.remove_duplicates_checkbox.config(state=tk.NORMAL) # Duplicates can still be relevant
        elif sort_type == "reverse":
            self.case_sensitive_checkbox.config(state=tk.DISABLED)
            self.remove_duplicates_checkbox.config(state=tk.DISABLED)


    def apply_sort_lines(self, sort_type, case_sensitive, remove_duplicates):
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

        # Handle "Remove Duplicates" first if applicable and enabled for the sort type
        if remove_duplicates and sort_type not in ["reverse"]:
            # For alphabetical sort, case sensitivity for duplicates matters.
            # For length sort, duplicates are based on exact content.
            is_alpha_sort = sort_type.startswith("alpha")
            use_case_for_duplicates = case_sensitive if is_alpha_sort else True # Length sort duplicates are case sensitive

            if use_case_for_duplicates:
                seen = set()
                unique_lines = [line for line in lines if not (line in seen or seen.add(line))]
            else: # Case-insensitive duplicate removal (only for alphabetical)
                seen_lower = set()
                unique_lines = []
                for line in lines:
                    lower_line = line.lower()
                    if lower_line not in seen_lower:
                        unique_lines.append(line)
                        seen_lower.add(lower_line)
            lines = unique_lines

        # Apply sort based on type
        if sort_type == "alpha_asc":
            lines.sort(key=lambda s: s.lower() if not case_sensitive else s)
        elif sort_type == "alpha_desc":
            lines.sort(key=lambda s: s.lower() if not case_sensitive else s, reverse=True)
        elif sort_type == "len_asc":
            lines.sort(key=len)
        elif sort_type == "len_desc":
            lines.sort(key=len, reverse=True)
        elif sort_type == "reverse":
            lines.reverse()
        # Else: no change, or unknown sort_type

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
        # Main content frame with padding
        main_dialog_frame = ttk.Frame(dialog, padding=10)
        main_dialog_frame.pack(expand=True, fill=tk.BOTH)

        input_frame = ttk.Frame(main_dialog_frame) # Pack into main_dialog_frame
        input_frame.pack(fill=tk.X) # Removed padx/pady from here, main_dialog_frame has it

        ttk.Label(input_frame, text="Find what:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.find_entry = ttk.Entry(input_frame, textvariable=self.find_what_var, width=40)
        self.find_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(input_frame, text="Replace with:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.replace_entry = ttk.Entry(input_frame, textvariable=self.replace_with_var, width=40)
        self.replace_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)

        input_frame.columnconfigure(1, weight=1) # Make entry fields expandable

        options_frame = ttk.LabelFrame(main_dialog_frame, text="Options") # Pack into main_dialog_frame
        options_frame.pack(pady=5, fill=tk.X) # Removed padx from here

        ttk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive_find_var).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Whole word", variable=self.whole_word_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Regular expression", variable=self.regex_var).grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Wrap around", variable=self.wrap_around_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Search backwards", variable=self.search_backwards_var).grid(row=2, column=0, sticky=tk.W, padx=5)


        button_frame = ttk.Frame(main_dialog_frame) # Pack into main_dialog_frame
        button_frame.pack(pady=10, fill=tk.X) # Removed padx from here

        self.find_dialog_find_next_btn = ttk.Button(button_frame, text="Find Next", command=self.find_next)
        self.find_dialog_find_next_btn.pack(side=tk.LEFT, padx=5)

        self.find_dialog_replace_btn = ttk.Button(button_frame, text="Replace", command=self.replace_once)
        self.find_dialog_replace_btn.pack(side=tk.LEFT, padx=5)

        self.find_dialog_replace_all_btn = ttk.Button(button_frame, text="Replace All", command=self.replace_all)
        self.find_dialog_replace_all_btn.pack(side=tk.LEFT, padx=5)

        self.find_dialog_close_btn = ttk.Button(button_frame, text="Close", command=on_dialog_close) # Use on_dialog_close
        self.find_dialog_close_btn.pack(side=tk.RIGHT, padx=5)


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
        self.found_matches_for_nav = []
        self.current_match_index_for_nav = -1
        self.find_dialog_search_dirty_flag = True # Mark dirty on open

        def on_find_settings_changed(*args):
            self.find_dialog_search_dirty_flag = True
            # Auto-refresh and find first could be too aggressive on every key stroke in find_what
            # Let refresh happen on "Find Next" or explicit action for now if dirty.
            # OR: self.refresh_search_highlights_and_find_first()
            self.refresh_search_highlights() # Refresh highlights as options change
            # If there are matches, try to navigate to the first one visible or one near current cursor
            if self.found_matches_for_nav:
                # Try to find a match at or after current insert mark
                text_area = self.get_active_text_area()
                current_cursor_pos = text_area.index(tk.INSERT) if text_area else "1.0"
                new_idx = 0
                for i, (start, end) in enumerate(self.found_matches_for_nav):
                    if text_area.compare(start, ">=", current_cursor_pos):
                        new_idx = i
                        break
                self.current_match_index_for_nav = new_idx -1 # find_next will increment it
                # self.navigate_to_match(new_idx) # This would auto-jump
            else: # No matches found, clear current selection/highlight
                self.clear_current_search_highlight_active_tab()


        self.find_what_var.trace_add("write", on_find_settings_changed)
        self.case_sensitive_find_var.trace_add("write", on_find_settings_changed)
        self.whole_word_var.trace_add("write", on_find_settings_changed)
        self.regex_var.trace_add("write", on_find_settings_changed)
        # search_backwards_var and wrap_around_var don't change the set of matches, only navigation.

        def on_dialog_close(event=None):
            self.clear_all_search_highlights_active_tab()
            dialog.destroy()

        dialog.bind("<Escape>", on_dialog_close)
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close) # Handle window close button

        self.update_find_replace_button_states() # Initial state update

        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')
        return "break"

    def update_find_replace_button_states(self):
        if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists():
            current_tab = self.get_current_tab()
            if current_tab and current_tab.text_area.cget('state') == tk.DISABLED:
                self.find_dialog_replace_btn.config(state=tk.DISABLED)
                self.find_dialog_replace_all_btn.config(state=tk.DISABLED)
            else:
                self.find_dialog_replace_btn.config(state=tk.NORMAL)
                self.find_dialog_replace_all_btn.config(state=tk.NORMAL)
        # If dialog doesn't exist, or buttons not created yet, do nothing.

    def _search_in_text(self, text_widget, pattern, start_index, end_index, case_sensitive, whole_word, regex, backwards):
        nocase = not case_sensitive
        count_var = tk.IntVar() # Used by text_widget.search

        if regex:
            # When regex is True, 'whole_word' (exact) is typically handled by \b within the regex pattern itself.
            # Forcing 'exact=False' when regex=True to avoid conflicts or unexpected behavior.
            # The user should construct their regex to include whole word boundaries if needed.
            try:
                pos = text_widget.search(pattern, start_index,
                                         stopindex=end_index,
                                         backwards=backwards,
                                         regexp=True,
                                         nocase=nocase,
                                         exact=False, # Explicitly False when regex is True
                                         count=count_var)
                if pos:
                    return pos, count_var.get()
                return None, 0
            except tk.TclError as e:
                # Check if find_replace_dialog exists and is visible before using as parent
                parent_dialog = self.root
                if hasattr(self, "find_replace_dialog") and self.find_replace_dialog and self.find_replace_dialog.winfo_exists():
                    parent_dialog = self.find_replace_dialog
                messagebox.showerror("Regex Error", f"Invalid regular expression: {e}", parent=parent_dialog)
                self.clear_all_search_highlights_active_tab() # Clear highlights on regex error
                return None, 0
        else: # Not regex
            pos = text_widget.search(pattern, start_index,
                                     stopindex=end_index,
                                     backwards=backwards,
                                     regexp=False,
                                     nocase=nocase,
                                     exact=whole_word, # 'exact' is for non-regex search
                                     count=count_var)
            if pos:
                return pos, count_var.get()
            return None, 0

    def find_next(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area: return "break"

        find_what = self.find_what_var.get()
        if not find_what: # No search term, so ensure no highlights exist
            self.clear_all_search_highlights_active_tab()
            # messagebox.showinfo("Find Next", "Find string is empty.", parent=self.find_replace_dialog) # Can be noisy
            return "break"

        # If search settings changed or highlights are otherwise considered dirty, refresh them.
        # The trace on vars should call refresh_search_highlights already.
        # self.refresh_search_highlights() # This might be redundant if traces are working, but safe.

        if not self.found_matches_for_nav:
            messagebox.showinfo("Find Next", f"Cannot find '{find_what}'.", parent=self.find_replace_dialog)
            return "break"

        search_backwards = self.search_backwards_var.get()
        wrap_around = self.wrap_around_var.get()

        num_matches = len(self.found_matches_for_nav)
        nav_idx = self.current_match_index_for_nav # Preserve current before modification

        if search_backwards:
            nav_idx -= 1
            if nav_idx < 0:
                if wrap_around:
                    nav_idx = num_matches - 1
                else: # No wrap
                    nav_idx = 0
                    messagebox.showinfo("Find Next", "Beginning of document reached.", parent=self.find_replace_dialog)
                    # self.navigate_to_match(nav_idx) # Stay at the first match
                    # return "break" # Or let it navigate to nav_idx=0
        else: # Forward
            nav_idx += 1
            if nav_idx >= num_matches:
                if wrap_around:
                    nav_idx = 0
                else: # No wrap
                    nav_idx = num_matches - 1
                    messagebox.showinfo("Find Next", "End of document reached.", parent=self.find_replace_dialog)
                    # self.navigate_to_match(nav_idx) # Stay at the last match
                    # return "break"

        if 0 <= nav_idx < num_matches:
            self.navigate_to_match(nav_idx)
        elif num_matches > 0 : # e.g. wrap is off and went out of bounds, stay at first/last
             self.navigate_to_match(self.current_match_index_for_nav) # Re-select current if no move

        if self.find_replace_dialog and self.find_replace_dialog.winfo_exists():
             self.find_replace_dialog.lift()
        return "break"

    def replace_once(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area: return "break"

        replace_with = self.replace_with_var.get()

        # Check if there's a current valid highlighted match to replace
        # This means self.current_match_index_for_nav is valid and points to an item in self.found_matches_for_nav
        if self.found_matches_for_nav and 0 <= self.current_match_index_for_nav < len(self.found_matches_for_nav):
            start_pos, end_pos = self.found_matches_for_nav[self.current_match_index_for_nav]

            # Ensure the text at these positions still matches the find_what criteria
            # This is a safety check, as text could have been modified elsewhere.
            # For simplicity, we'll trust our stored match for now.
            # A more robust solution would re-verify.

            text_area.delete(start_pos, end_pos)
            text_area.insert(start_pos, replace_with)

            # After replacement, highlights are invalid. Refresh them.
            # The <<Modified>> event on text_area will trigger EditorTab's clear_search_highlight_tags.
            # We then need to re-scan and re-highlight.
            # The on_text_changed_tab_and_update_lines in EditorTab calls self.app.update_status_bar()
            # and self.clear_search_highlight_tags().
            # We need to ensure refresh_search_highlights() is called after modification.

            # Manually trigger a refresh of highlights and then find the next logical item.
            # The current_match_index_for_nav will be reset by refresh_search_highlights
            # if called via on_find_settings_changed.
            # Here, we need to carefully set it up for the next find.

            # Let's simplify: after replace, text is modified.
            # <<Modified>> -> EditorTab.on_text_changed_tab_and_update_lines -> EditorTab.clear_search_highlight_tags
            # This means all yellow/orange highlights are gone.
            # Now, call find_next. find_next should re-trigger refresh_search_highlights if needed.

            # To ensure find_next re-evaluates, we can mark highlights as dirty
            # self.find_dialog_search_dirty_flag = True
            # However, `on_find_settings_changed` already calls `refresh_search_highlights`.
            # The text modification itself will clear highlights in the tab.
            # The next call to find_next will then use the (now empty) self.found_matches_for_nav
            # or it will re-trigger refresh_search_highlights if find_what_var changes (it doesn't here).
            # This needs to be robust.

            # Simplest: after replace, explicitly refresh and then find next.
            cursor_after_replace = text_area.index(f"{start_pos} + {len(replace_with)} chars")
            text_area.mark_set(tk.INSERT, cursor_after_replace) # Move cursor after replaced text

            self.refresh_search_highlights() # Re-scan and highlight all based on current text

            # Now, find the next occurrence from the current cursor position.
            # We need to set current_match_index_for_nav appropriately so find_next picks the correct one.
            new_idx = 0
            found_after_replace = False
            for i, (start, end) in enumerate(self.found_matches_for_nav):
                if text_area.compare(start, ">=", cursor_after_replace):
                    new_idx = i
                    found_after_replace = True
                    break
            if not found_after_replace and self.found_matches_for_nav: # Wrapped or no more matches after this point
                new_idx = 0 # Go to first if wrap is on for find_next (or handle as find_next does)

            self.current_match_index_for_nav = new_idx -1 # So find_next (forward) will pick it up
            self.find_next()

        else: # No current selection to replace, just try to find the next one
            self.find_next()

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

    def clear_all_search_highlights_active_tab(self):
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.clear_search_highlight_tags() # This clears both general and current

    def clear_current_search_highlight_active_tab(self):
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.text_area.tag_remove("current_search_highlight", "1.0", tk.END)
            # Do not clear tk.SEL here as user might be selecting text for other purposes


    def refresh_search_highlights(self):
        active_tab = self.get_current_tab()
        if not active_tab:
            self.found_matches_for_nav = []
            return

        text_area = active_tab.text_area
        text_area.tag_remove("search_highlight", "1.0", tk.END)
        text_area.tag_remove("current_search_highlight", "1.0", tk.END)
        # Keep tk.SEL if user had something selected. Find will make its own selection.

        find_what = self.find_what_var.get()
        if not find_what:
            self.found_matches_for_nav = []
            return

        case_sensitive = self.case_sensitive_find_var.get()
        whole_word = self.whole_word_var.get()
        use_regex = self.regex_var.get()

        matches = []
        start_index = "1.0"
        while True:
            pos, length = self._search_in_text(text_area, find_what, start_index, tk.END,
                                               case_sensitive, whole_word, use_regex, False)
            if pos:
                end_pos = text_area.index(f"{pos} + {length} chars")
                text_area.tag_add("search_highlight", pos, end_pos)
                matches.append((pos, end_pos))
                start_index = end_pos
            else:
                break

        self.found_matches_for_nav = matches
        # self.current_match_index_for_nav = -1 # Reset by on_find_settings_changed or before find_next
        return # matches are stored in self.found_matches_for_nav

    def navigate_to_match(self, match_index, is_initial_find=False):
        text_area = self.get_active_text_area()
        if not text_area or not self.found_matches_for_nav or not (0 <= match_index < len(self.found_matches_for_nav)):
            if is_initial_find and self.found_matches_for_nav: # cycle if initial find lands out of bounds
                 pass # let find_next handle wrap around message
            else:
                return

        text_area.tag_remove("current_search_highlight", "1.0", tk.END)

        start_pos, end_pos = self.found_matches_for_nav[match_index]

        text_area.tag_add("current_search_highlight", start_pos, end_pos)
        text_area.tag_remove("search_highlight", start_pos, end_pos) # So current is distinct

        text_area.tag_remove(tk.SEL, "1.0", tk.END) # Clear old selection
        text_area.tag_add(tk.SEL, start_pos, end_pos)

        # For cursor position: if searching backwards, cursor at start of selection, else at end.
        # This is for subsequent typing or navigation.
        cursor_nav_pos = start_pos if self.search_backwards_var.get() and not is_initial_find else end_pos
        text_area.mark_set(tk.INSERT, cursor_nav_pos)
        text_area.see(start_pos) # Scroll to see the beginning of the match
        self.current_match_index_for_nav = match_index


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

        system_families = set(tkfont.families()) # Use a set for efficient lookup

        # Filter system fonts against our known fixed-width list
        # and ensure they are actually available on the system.
        available_fixed_fonts = [font for font in self.known_fixed_fonts if font in system_families]

        if not available_fixed_fonts:
            # Fallback strategy if no known fixed fonts are found
            # This is unlikely if TkFixedFont or Courier are standard Tk fallbacks
            if "TkFixedFont" in system_families:
                available_fixed_fonts = ["TkFixedFont"]
            elif "Courier" in system_families: # A very common fallback
                available_fixed_fonts = ["Courier"]
            else: # Last resort: show all system fonts, though not ideal for a code editor
                available_fixed_fonts = sorted(list(system_families))
                if not available_fixed_fonts: # Extremely unlikely (no fonts on system?)
                    available_fixed_fonts = ["TkFixedFont"] # Default to this, Tk might provide a very basic one

        # Ensure current font is in the list if possible, or select first available
        current_family_in_list = self.current_font_family
        if self.current_font_family not in available_fixed_fonts:
            if available_fixed_fonts:
                current_family_in_list = available_fixed_fonts[0]
            # If available_fixed_fonts is empty, it will use current_font_family which defaults to TkFixedFont
        font_family_var.set(current_family_in_list)


        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Font Family:").grid(row=0, column=0, sticky=tk.W, pady=2)
        # Use available_fixed_fonts for the combobox values
        family_combobox = ttk.Combobox(main_frame, textvariable=font_family_var, values=available_fixed_fonts, state="readonly", width=30)
        family_combobox.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        # font_family_var is already set to current_family_in_list, which is in available_fixed_fonts (or a fallback)
        # So, direct setting of combobox via .set() might be redundant if textvariable works as expected.
        # However, explicitly setting it ensures the displayed value matches the variable.
        if current_family_in_list in available_fixed_fonts:
             family_combobox.set(current_family_in_list)
        elif available_fixed_fonts: # Fallback if current somehow not in list but list has items
             family_combobox.set(available_fixed_fonts[0])
        # If available_fixed_fonts is empty, it implies a very basic system,
        # font_family_var would hold "TkFixedFont" or "Courier", and combobox would be empty or have that if it was added.
        # This state should be rare.

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
            tab.text_area.update_idletasks() # Ensure text area layout is updated
            tab.redraw_line_numbers()

    # --- Keyword Highlighting Methods ---
    def open_keyword_highlight_dialog(self):
        if hasattr(self, "keyword_dialog") and self.keyword_dialog.winfo_exists():
            self.keyword_dialog.lift()
            self.keyword_dialog.focus_set()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Keyword Highlighting")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        self.keyword_dialog = dialog

        # Variables from self.keyword_highlight_settings
        keywords_str_var = tk.StringVar(value=self.keyword_highlight_settings["keywords_input_string"])
        case_var = tk.BooleanVar(value=self.keyword_highlight_settings["case_sensitive"])
        whole_word_var = tk.BooleanVar(value=self.keyword_highlight_settings["whole_word"])

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Keywords (separated by '|'):").pack(anchor=tk.W, pady=(0,2))
        keywords_entry = ttk.Entry(main_frame, textvariable=keywords_str_var, width=50)
        keywords_entry.pack(fill=tk.X, pady=(0,10))
        keywords_entry.focus_set()

        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(options_frame, text="Case Sensitive", variable=case_var).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(options_frame, text="Whole Word Only", variable=whole_word_var).pack(side=tk.LEFT)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0), side=tk.BOTTOM) # Pack at bottom

        def on_apply():
            self.update_keyword_highlight_settings(
                keywords_str_var.get(),
                case_var.get(),
                whole_word_var.get()
            )
            # Dialog can remain open or be destroyed. Let's keep it open for now.
            # dialog.destroy()

        def on_clear_and_close(): # Renamed to be more descriptive
            self.clear_keyword_highlight_settings()
            keywords_str_var.set("") # Clear the entry in the dialog too
            # dialog.destroy() # Keep dialog open, user might want to enter new keywords or cancel

        def on_cancel():
            # Revert UI elements to match actual settings if dialog is cancelled without apply
            keywords_str_var.set(self.keyword_highlight_settings["keywords_input_string"])
            case_var.set(self.keyword_highlight_settings["case_sensitive"])
            whole_word_var.set(self.keyword_highlight_settings["whole_word"])
            dialog.destroy()


        ttk.Button(button_frame, text="Apply", command=on_apply).pack(side=tk.LEFT, padx=5) # Changed from RIGHT
        ttk.Button(button_frame, text="Clear All Highlights", command=on_clear_and_close).pack(side=tk.LEFT, padx=5) # Changed from RIGHT
        ttk.Button(button_frame, text="Close", command=on_cancel).pack(side=tk.RIGHT) # This one is fine on right

        dialog.bind("<Escape>", lambda e: on_cancel()) # Bind Esc to cancel
        dialog.protocol("WM_DELETE_WINDOW", on_cancel) # Handle window close button as cancel

        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

    def update_keyword_highlight_settings(self, input_str, case_sens, whole_word):
        self.keyword_highlight_settings["keywords_input_string"] = input_str
        self.keyword_highlight_settings["case_sensitive"] = case_sens
        self.keyword_highlight_settings["whole_word"] = whole_word

        raw_keywords = [kw.strip() for kw in input_str.split('|') if kw.strip()]

        # Determine unique keywords for color assignment based on original casing,
        # as multiple distinct original keywords might map to the same processed (e.g. lowercased) keyword.
        # However, for highlighting, we need a list of keywords that will actually be searched.
        # If not case sensitive for matching, "Word" and "word" are the same search.

        # Let's use a simpler approach: parsed_keywords are the unique strings to get colors.
        # The actual search will use these parsed_keywords but apply case_sensitive at search time.

        unique_keywords_for_coloring = sorted(list(set(raw_keywords))) # Processed for uniqueness for color mapping

        self.keyword_highlight_settings["parsed_keywords"] = raw_keywords # Store raw keywords for search

        self.keyword_highlight_settings["keyword_to_color_map"] = {}
        self.keyword_highlight_settings["keyword_to_tag_name_map"] = {}

        # Assign colors and tag names based on unique_keywords_for_coloring to ensure 'KEY' and 'key' get same color if overall matching is case-insensitive
        # but different colors if overall matching is case-sensitive AND they are treated as distinct keywords.
        # For simplicity now: each unique entry in raw_keywords (after strip) gets a color.
        # If "Hello" and "hello" are both in raw_keywords, they get different colors.
        # The "case_sensitive" checkbox will then control if "hello" matches "Hello" during search.

        temp_unique_raw_keywords = []
        seen_for_color_assignment = set()

        for kw in raw_keywords:
            # For color assignment, uniqueness can be based on the keyword itself or its lowercase form
            # depending on desired behavior. Let's use original form for distinct colors if user typed them differently.
            # Example: "KEY|key" -> KEY gets color1, key gets color2. Search for "KEY" might find "key" if case_sensitive is false.
            if kw not in seen_for_color_assignment:
                temp_unique_raw_keywords.append(kw)
                seen_for_color_assignment.add(kw)

        self.keyword_highlight_settings["parsed_keywords"] = temp_unique_raw_keywords # These are the unique keywords that will each get a color/tag

        for i, kw_original_case in enumerate(self.keyword_highlight_settings["parsed_keywords"]):
            color = self.pastel_colors[i % len(self.pastel_colors)]
            tag_name = f"user_keyword_{i}" # Tags are based on index in the unique list
            self.keyword_highlight_settings["keyword_to_color_map"][kw_original_case] = color
            self.keyword_highlight_settings["keyword_to_tag_name_map"][kw_original_case] = tag_name

        self.keyword_highlight_settings["active"] = bool(self.keyword_highlight_settings["parsed_keywords"])
        self.apply_all_tabs_keyword_highlights()

    def clear_keyword_highlight_settings(self):
        self.keyword_highlight_settings["keywords_input_string"] = ""
        self.keyword_highlight_settings["parsed_keywords"] = []
        self.keyword_highlight_settings["keyword_to_color_map"] = {}
        self.keyword_highlight_settings["keyword_to_tag_name_map"] = {}
        # Reset options to default when clearing all, or keep user's last choice?
        # Keeping user's last choice for case/whole_word seems reasonable.
        # self.keyword_highlight_settings["case_sensitive"] = False
        # self.keyword_highlight_settings["whole_word"] = True
        self.keyword_highlight_settings["active"] = False
        self.apply_all_tabs_keyword_highlights() # This will effectively clear highlights from tabs

    def apply_all_tabs_keyword_highlights(self):
        for tab in self.tabs:
            # Pass the entire settings dict to the tab method
            tab.apply_keyword_highlights(self.keyword_highlight_settings)

    # --- Sed-Inspired Text Operations ---

    def double_space_lines(self):
        """Inserts a blank line after each line in selection or full text."""
        def do_double_space(text):
            if not text: # Handle empty string case
                return ""
            lines = text.splitlines(keepends=False) # Don't keep ends, we'll add them
            # If the original text ended with a newline, the last line in lines will be empty if text was "a\n\b\n" -> ["a","b",""]
            # or the last line will be the content if text was "a\nb" -> ["a","b"]
            # We want to preserve whether the original block ended with a newline.
            original_ends_with_newline = text.endswith('\n')

            processed_lines = []
            for i, line_content in enumerate(lines):
                processed_lines.append(line_content)
                # Add a blank line after every line, except potentially after the very last line
                # if the original text didn't end with a newline AND it was the actual last line of content.
                if i < len(lines) - 1: # If not the last item from splitlines
                    processed_lines.append("") # Add the blank line
                elif original_ends_with_newline : # It is the last item, check if original ended with newline
                     processed_lines.append("")


            # Join with \n. This will add \n after every item.
            # If original_ends_with_newline is false, and last line had content, we don't want an extra \n at end of all.
            result = "\n".join(processed_lines)

            # If original did not end with newline, and result now does (because last processed_line was empty string from append)
            # and the original last line from splitlines was not empty.
            if not original_ends_with_newline and result.endswith('\n') and lines and lines[-1] != "":
                # This case is tricky. If original was "a\nb", lines=["a","b"]. processed_lines=["a","", "b"]. join-> "a\n\nb". Correct.
                # If original was "a", lines=["a"]. processed_lines=["a"]. join -> "a". Correct.
                # If original was "a\n", lines=["a",""]. processed_lines=["a","",""]. join -> "a\n\n". Correct.
                pass # Logic seems to handle this pass.

            # A simpler reconstruction:
            new_text = ""
            for i, line_content in enumerate(lines):
                new_text += line_content + "\n" # Add the line itself
                if i == len(lines) -1 and not original_ends_with_newline:
                    # This was the actual last line of content and original didn't have a newline after it
                    # So, we added one, but we shouldn't add another for double spacing.
                    pass
                else: # Add the blank line for double spacing
                    new_text += "\n"

            # The above simpler one adds an extra newline at the very end if original_ends_with_newline was true.
            # Let's use sed G logic: append \n then the new line.
            # sed G appends a newline, then the content of hold space (which is also a newline by default after G)
            # Effectively, it appends '\n\n' to each line if hold space is empty, or rather, it appends a newline.
            # No, sed G appends a newline character, then the contents of the hold space.
            # If hold space is empty, it effectively adds a newline.
            # A simple G on its own makes each line followed by one blank line.

            final_lines = []
            for line in text.splitlines(keepends=True): # Keep original line endings
                final_lines.append(line)
                if line.endswith('\n'):
                    final_lines.append('\n') # Add a blank line
                else: # Line didn't end with \n (it's the last line of file without trailing \n)
                    final_lines.append('\n\n') # Add \n then the blank line \n

            # Correction for last line if it didn't have newline initially
            if not text.endswith('\n') and final_lines:
                # The last element would be '\n\n' from the else block. We want it to be just '\n'
                # if the original last line was, say, "foo" (no newline) -> becomes "foo\n\n". Should be "foo\n".
                # This is tricky. Let's re-think.
                # Each line in the input should be followed by one additional newline.

                result_parts = []
                input_lines = text.splitlines(keepends=True)
                for i, line in enumerate(input_lines):
                    result_parts.append(line)
                    if line.endswith('\n'): # It's a normal line
                        result_parts.append('\n') # This is the double-spacing newline
                    elif i == len(input_lines) - 1: # Last line, and it doesn't end with \n
                        result_parts.append('\n') # Add a newline to it, then the double-space newline
                        result_parts.append('\n')

                # This logic might still add too many newlines at the end if the file already ends with multiple.
                # The simplest is: for each line, output it, then output a blank line.
                # Preserve original line endings.

                # Best approach:
                # 1. Split lines, keeping original endings.
                # 2. For each line, add it to output.
                # 3. Add an extra newline to output.
                # 4. Rejoin. This will naturally handle the end of file.

                split_lines = text.splitlines(keepends=True)
                if not split_lines: return "" # Empty input

                processed_text = []
                for line in split_lines:
                    processed_text.append(line)
                    processed_text.append("\n") # The double-spacing blank line

                # If the original text did NOT end with a newline, the last line added by us
                # (the double-spacing one) might be too much.
                # Example: "foo" -> splitlines(keepends=True) -> ["foo"]
                # processed_text -> ["foo", "\n"] -> join -> "foo\n" (This is single spaced)
                # It should be "foo\n\n" if we consider "foo" as a line.
                # No, sed G on "foo" (no newline) outputs "foo\n\n"
                # sed G on "foo\n" outputs "foo\n\n"
                # So, each logical line gets an extra \n.

                # Let's use the definition: after every original line, insert one blank line.
                # A blank line is effectively "\n".
                # So, if line is "content\n", it becomes "content\n\n".
                # If line is "content" (EOF), it becomes "content\n\n".

                output_lines = []
                for line in text.splitlines(keepends=False): # Process content only
                    output_lines.append(line)
                    output_lines.append("") # The blank line

                # If original text was empty or just newlines, handle that.
                if not text.strip(): # If text was all whitespace/empty
                    if text.count('\n') == 0 and len(text) > 0: # e.g. "   "
                        return text + "\n\n" # "   \n\n"
                    if text == "": return "\n" # Double spacing "" is one blank line? sed G on empty input is "\n"
                                            # No, sed G on empty input is one blank line.
                                            # If input is empty, result is empty. If input is "\n", result is "\n\n".

                    # For now, if input is all whitespace, let's just double space its newlines
                    # This general loop will handle it if we join by \n.
                    # If text = "\n", lines = ["", ""]. output_lines = ["", "", "", ""]. join -> "\n\n\n". Wrong. Should be "\n\n"
                    # If text = "a\n", lines = ["a", ""]. output_lines = ["a", "", "", ""]. join -> "a\n\n\n". Wrong. Should be "a\n\n".

                # Final attempt at simple logic for do_double_space
                if not text: return ""
                return '\n\n'.join(text.splitlines(keepends=False)) + ('\n\n' if text.endswith('\n') and text.strip() else ('\n' if text.endswith('\n') else '\n\n' if text else ''))
                # This is getting too complex.
                # The sed 'G' command is simple: it appends a newline then the content of hold space.
                # If hold space is empty (default after a line read unless 'h' was used), it just appends a newline.
                # So, every line gets an extra newline.

                result = []
                for line in text.splitlines(keepends=True):
                    result.append(line)
                    if not line.endswith('\n'): # If it's the last line without a newline
                        result.append('\n') # Add one for itself
                    result.append('\n') # Add the double-spacing newline

                # If original text was empty, result should be empty.
                if not text: return ""
                # If original text was just "foo" (no newline), result should be "foo\n\n"
                # Current logic: line="foo", result.append("foo"), result.append("\n"), result.append("\n") -> "foo\n\n" Correct.
                # If original text was "foo\n", result.append("foo\n"), result.append("\n") -> "foo\n\n" Correct.
                # If original was "\n" (one blank line), line="\n", result.append("\n"), result.append("\n") -> "\n\n". Correct.

                return "".join(result)

        self._process_text(do_double_space)

    def reduce_blank_lines(self):
        """Reduces multiple consecutive blank lines to a single blank line.
           Also removes leading/trailing blank lines from the processed block."""
        def do_reduce(text):
            if not text.strip(): # Empty or all whitespace
                return ""

            # Normalize line endings for processing
            text = text.replace('\r\n', '\n').replace('\r', '\n')

            # Strip leading and trailing whitespace from the entire block first.
            # This handles blank lines at the very start/end of the selection/document.
            stripped_text = text.strip()
            if not stripped_text: # If stripping made it empty
                return ""

            # Replace sequences of 2 or more newlines (potentially with whitespace lines between)
            # with just two newlines (which forms one blank line).
            # This regex finds a newline, followed by any number of whitespace-only lines also ending in newlines,
            # and replaces that whole sequence with a single blank line (\n\n).
            # To be more precise for "max one blank line":
            # A line with content, then \n, then \n (blank line), then line with content.
            # We want to turn \n\n\n (2 blank lines) into \n\n (1 blank line).
            # So, \n(\s*\n)+ should become \n\n

            import re
            # Replace 3 or more newlines with 2 newlines
            processed_text = re.sub(r'\n{3,}', '\n\n', stripped_text)

            # Ensure the result ends with a single newline if it has content.
            if processed_text:
                processed_text += '\n'
            return processed_text

        self._process_text(do_reduce)

    def remove_all_blank_lines(self):
        """Removes all lines that are blank or contain only whitespace."""
        def do_remove_all_blanks(text):
            lines = text.splitlines()
            non_blank_lines = [line for line in lines if line.strip()]
            if not non_blank_lines:
                return ""

            processed_text = "\n".join(non_blank_lines)
            # Ensure a single trailing newline if there's content
            if processed_text:
                processed_text += '\n'
            return processed_text

        self._process_text(do_remove_all_blanks)

    def delete_duplicate_consecutive_lines(self):
        """Deletes duplicate consecutive lines from selection or full text."""
        def do_uniq(text):
            if not text: return ""
            # Split lines, but handle if the text ends with a newline properly for restoration
            original_ends_with_newline = text.endswith('\n')
            lines = text.splitlines(keepends=False)

            if not lines: # Only newlines or empty
                return text # Return original (e.g. "\n\n" or "")

            output_lines = [lines[0]]
            for i in range(1, len(lines)):
                if lines[i] != lines[i-1]:
                    output_lines.append(lines[i])

            processed_text = "\n".join(output_lines)

            # Restore trailing newline if original had it and output is not empty
            if original_ends_with_newline and processed_text:
                processed_text += '\n'
            # If original did not have it, but .join added one (e.g. single line input)
            # and the single line was not empty.
            elif not original_ends_with_newline and processed_text.endswith('\n') and len(output_lines) == 1 and output_lines[0]:
                 processed_text = processed_text.rstrip('\n')

            return processed_text
        self._process_text(do_uniq)

    def reverse_lines_action(self):
        """Reverses the order of lines in selection or full text."""
        # This simply calls the existing sort logic with the "reverse" type.
        self.apply_sort_lines(sort_type="reverse", case_sensitive=False, remove_duplicates=False)

    def _process_selected_lines(self, line_operation_func, preserves_original_endings=True):
        """Helper to apply a function to each line in a selection or the whole document.

        Args:
            line_operation_func: A function that takes a single line string (without newline)
                                 and returns the processed line string (without newline).
            preserves_original_endings: If True, tries to keep original line endings (\n, \r\n, or none at EOF).
                                        If False, all processed lines will end with \n (except possibly the last one).
        """
        text_area = self.get_active_text_area()
        if not text_area:
            return

        try:
            sel_start_index = text_area.index(tk.SEL_FIRST)
            sel_end_index = text_area.index(tk.SEL_LAST)

            # If selection ends at the beginning of a line (e.g., user selected full lines),
            # we don't want to process that empty selection on the new line.
            if sel_end_index.endswith(".0") and sel_start_index != sel_end_index:
                sel_end_index = text_area.index(f"{sel_end_index} -1c") # Go to end of previous line

            original_selection_text = text_area.get(sel_start_index, sel_end_index)
            lines = original_selection_text.splitlines(keepends=True) # Keep endings to analyze them

            if not lines: # Empty selection or selection was just newlines that splitlines removed.
                 # If original_selection_text was just "\n", lines would be ['\n'].
                 # If it was "", lines is [].
                 if original_selection_text: # e.g. "\n"
                      processed_content = line_operation_func("") # Process an empty line content
                      if processed_content != "" or original_selection_text != processed_content + (original_selection_text[-1] if original_selection_text.endswith(('\n','\r')) else ''):
                           text_area.delete(sel_start_index, sel_end_index)
                           text_area.insert(sel_start_index, processed_content + (original_selection_text[-1] if original_selection_text.endswith(('\n','\r')) else ''))
                           text_area.event_generate("<<Modified>>")
                 return


            processed_lines = []
            modified = False

            for line_with_ending in lines:
                line_ending = ""
                if preserves_original_endings:
                    if line_with_ending.endswith("\r\n"):
                        line_ending = "\r\n"
                        line_content = line_with_ending[:-2]
                    elif line_with_ending.endswith("\n"):
                        line_ending = "\n"
                        line_content = line_with_ending[:-1]
                    else: # Last line, no newline
                        line_content = line_with_ending
                else: # Normalize all to \n
                    line_content = line_with_ending.rstrip("\r\n")
                    line_ending = "\n" # Will add this back unless it's last line and shouldn't have one

                processed_content = line_operation_func(line_content)
                if processed_content != line_content:
                    modified = True
                processed_lines.append(processed_content + line_ending)

            if not preserves_original_endings and processed_lines: # Adjust last line's newline if needed
                full_new_text_temp = "".join(processed_lines)
                if not original_selection_text.endswith(('\n', '\r')) and full_new_text_temp.endswith('\n'):
                    processed_lines[-1] = processed_lines[-1].rstrip('\n') # Remove the normalized \n

            if modified:
                text_area.delete(sel_start_index, sel_end_index)
                text_area.insert(sel_start_index, "".join(processed_lines))
                text_area.event_generate("<<Modified>>")

        except tk.TclError: # No selection, process whole document
            original_full_text = text_area.get("1.0", tk.END + "-1c") # Exclude Tk's auto-newline
            lines = original_full_text.splitlines(keepends=True)

            if not lines and original_full_text: # e.g. text is "  " but no newlines
                lines = [original_full_text]


            processed_lines = []
            modified = False
            for i, line_with_ending in enumerate(lines):
                line_ending = ""
                if preserves_original_endings:
                    if line_with_ending.endswith("\r\n"):
                        line_ending = "\r\n"
                        line_content = line_with_ending[:-2]
                    elif line_with_ending.endswith("\n"):
                        line_ending = "\n"
                        line_content = line_with_ending[:-1]
                    else: # Last line, no newline
                        line_content = line_with_ending
                else: # Normalize all to \n
                    line_content = line_with_ending.rstrip("\r\n")
                    line_ending = "\n"


                processed_content = line_operation_func(line_content)
                if processed_content != line_content:
                    modified = True

                # For full document, if it's the last line and original didn't end with newline,
                # and we are not preserving original endings (meaning we added one), remove it.
                if not preserves_original_endings and i == len(lines) -1 and not original_full_text.endswith(('\n','\r')):
                    processed_lines.append(processed_content) # No line_ending
                else:
                    processed_lines.append(processed_content + line_ending)

            if modified:
                final_text = "".join(processed_lines)
                # Ensure final text ends with a newline if it's not empty, common editor behavior
                # This might conflict with preserves_original_endings for the very last line of file.
                # The loop above tries to handle it.

                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", final_text)
                if not final_text.endswith('\n') and final_text: # Add final newline if missing (Tk behavior)
                    text_area.insert(tk.END, "\n")
                text_area.event_generate("<<Modified>>")


    def condense_internal_whitespace(self):
        """Replaces multiple internal spaces/tabs with a single space for each line."""
        import re
        def do_condense(line_content):
            # Does not trim leading/trailing whitespace from the line itself.
            return re.sub(r'[ \t]+', ' ', line_content)

        self._process_selected_lines(do_condense, preserves_original_endings=True)

    def join_lines_with_space(self):
        """Joins selected lines with a single space, after trimming each line."""
        def do_join(text):
            lines = text.splitlines()
            trimmed_lines = [line.strip() for line in lines]
            non_empty_lines = [line for line in trimmed_lines if line] # Filter out empty lines after strip

            if not non_empty_lines:
                return "" # If all lines were empty or became empty

            return " ".join(non_empty_lines)
            # _process_text will handle adding a final newline if it's replacing the whole document.
            # If it's replacing a selection, it typically preserves the selection's overall newline status
            # or lack thereof, which might mean the joined line doesn't get a newline if the selection didn't end with one.
            # This is usually fine.

        self._process_text(do_join)

    def join_lines_with_comma_space(self):
        """Joins selected lines with ', ', after trimming each line."""
        def do_join_comma(text):
            lines = text.splitlines()
            trimmed_lines = [line.strip() for line in lines]
            non_empty_lines = [line for line in trimmed_lines if line]

            if not non_empty_lines:
                return ""

            return ", ".join(non_empty_lines)

        self._process_text(do_join_comma)

    def toggle_filter_bar(self, event=None):
        if self.filter_bar_frame.winfo_ismapped():
            self.filter_bar_frame.pack_forget()
            # When hiding, clear the filter from the current tab
            current_tab = self.get_current_tab()
            if current_tab and current_tab.is_filtered_view:
                self.filter_text_var.set("") # This should trigger on_filter_settings_changed -> apply_text_filter
                # current_tab.apply_text_filter("", self.filter_case_var.get()) # Explicit call if trace doesn't fire fast enough or is disabled
        else:
            self.filter_bar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,2), before=self.notebook)
            self.filter_entry.focus_set()
        return "break" # For key binding


if __name__ == "__main__":
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()
