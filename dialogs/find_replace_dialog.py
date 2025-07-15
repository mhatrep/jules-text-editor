import tkinter as tk
from tkinter import ttk, messagebox

class FindReplaceDialog(tk.Toplevel):
    def __init__(self, editor_instance):
        super().__init__(editor_instance.root)
        self.editor = editor_instance # Reference to the main TextEditor app instance
        self.active_tab = None

        self.title("Find/Replace")
        self.transient(editor_instance.root)
        # self.grab_set() # Making it non-modal initially, can be changed
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Variables
        self.find_what_var = tk.StringVar()
        self.replace_with_var = tk.StringVar()
        self.match_case_var = tk.BooleanVar()
        self.whole_word_var = tk.BooleanVar()
        self.regex_var = tk.BooleanVar()
        self.search_backwards_var = tk.BooleanVar() # For future "Find Previous"

        self.current_matches = [] # Stores (start_index, end_index) of current matches in the editor's text_area
        self.current_match_index = -1 # Index of the currently highlighted match in self.current_matches

        # Store last search parameters to detect changes
        self.last_find_what = ""
        self.last_case_sensitive = False
        self.last_whole_word = False
        self.last_regex = False
        self.last_known_mod_seq = -1
        # self.last_search_backwards = False # If find previous is implemented

        self._setup_ui()
        self._load_initial_state()

        # Bind text changes in find_what_var to clear previous search results
        self.find_what_var.trace_add("write", self._on_find_text_or_option_changed)

        # Position the dialog
        self._center_dialog()

        # Initial focus
        self.find_entry.focus_set()
        self.find_entry.select_range(0, tk.END)


    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Find What
        find_frame = ttk.Frame(main_frame)
        find_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(find_frame, text="Find what:").pack(side=tk.LEFT, padx=(0,5))
        self.find_entry = ttk.Entry(find_frame, textvariable=self.find_what_var, width=40)
        self.find_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.find_entry.bind("<Return>", self._find_next_action)
        self.find_entry.bind("<KP_Enter>", self._find_next_action)


        # Replace With
        replace_frame = ttk.Frame(main_frame)
        replace_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(replace_frame, text="Replace with:").pack(side=tk.LEFT, padx=(0,5))
        self.replace_entry = ttk.Entry(replace_frame, textvariable=self.replace_with_var, width=40)
        self.replace_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.replace_entry.bind("<Return>", self._replace_action)
        self.replace_entry.bind("<KP_Enter>", self._replace_action)

        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=(0,10))

        left_options_frame = ttk.Frame(options_frame)
        left_options_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.match_case_check = ttk.Checkbutton(left_options_frame, text="Match Case", variable=self.match_case_var, command=self._on_find_text_or_option_changed)
        self.match_case_check.pack(anchor=tk.W)
        self.whole_word_check = ttk.Checkbutton(left_options_frame, text="Whole Word", variable=self.whole_word_var, command=self._on_find_text_or_option_changed)
        self.whole_word_check.pack(anchor=tk.W)

        right_options_frame = ttk.Frame(options_frame) # Placeholder if more options needed on right
        right_options_frame.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        self.regex_check = ttk.Checkbutton(right_options_frame, text="Regular Expression", variable=self.regex_var, command=self._on_find_text_or_option_changed)
        self.regex_check.pack(anchor=tk.W)
        # self.search_backwards_check = ttk.Checkbutton(right_options_frame, text="Search Backwards", variable=self.search_backwards_var, command=self._on_find_text_or_option_changed)
        # self.search_backwards_check.pack(anchor=tk.W)


        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5,0))

        self.status_label = ttk.Label(button_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=(0,10), expand=True, fill=tk.X)

        self.find_next_btn = ttk.Button(button_frame, text="Find Next", command=self._find_next_action, state=tk.DISABLED)
        self.find_next_btn.pack(side=tk.LEFT, padx=2)

        self.find_prev_btn = ttk.Button(button_frame, text="Find Previous", command=self._find_prev_action, state=tk.DISABLED)
        self.find_prev_btn.pack(side=tk.LEFT, padx=2)

        self.replace_btn = ttk.Button(button_frame, text="Replace", command=self._replace_action, state=tk.DISABLED)
        self.replace_btn.pack(side=tk.LEFT, padx=2)

        self.replace_all_btn = ttk.Button(button_frame, text="Replace All", command=self._replace_all_action, state=tk.DISABLED)
        self.replace_all_btn.pack(side=tk.LEFT, padx=2)

        self.close_btn = ttk.Button(button_frame, text="Close", command=self._on_close)
        self.close_btn.pack(side=tk.RIGHT, padx=2) # Keep close on the right

    def _load_initial_state(self):
        """Load settings from editor or previous session if implemented"""
        # For now, set defaults or get from editor config if available
        # Example: self.match_case_var.set(self.editor.config.getboolean("FindReplace", "MatchCase", fallback=False))
        self.active_tab = self.editor.get_current_tab()
        self._update_button_states()

    def _on_find_text_or_option_changed(self, *args):
        # This method is called when find text changes or any option (case, whole word, regex) changes.
        # It should clear the previous search results and highlights.
        if self.editor and self.active_tab:
            self.editor.clear_all_search_highlights_active_tab()
            self.editor.clear_current_search_highlight_active_tab()

        self.current_matches = []
        self.current_match_index = -1
        self.status_label.config(text="") # Clear status message

        # Update last known search parameters for the editor to decide if it's a "new" search
        self.last_find_what = self.find_what_var.get()
        self.last_case_sensitive = self.match_case_var.get()
        self.last_whole_word = self.whole_word_var.get()
        self.last_regex = self.regex_var.get()
        # self.last_search_backwards = self.search_backwards_var.get()

        self._update_button_states()

    # def _on_option_changed(self, *args): # Combined into _on_find_text_or_option_changed
    #     self._clear_previous_search()
    #     self._update_button_states()

    def _clear_current_search_state(self): # Renamed from _clear_previous_search for clarity
        """Clears current matches and index, and tells editor to clear highlights."""
        if self.editor and self.active_tab:
            self.editor.clear_all_search_highlights_active_tab()
            self.editor.clear_current_search_highlight_active_tab()
        self.current_matches = []
        self.current_match_index = -1
        self.status_label.config(text="")
        # Do not reset last_find_what here, as it's needed to compare for "new search" logic

    def _update_button_states(self):
        find_text_present = bool(self.find_what_var.get())
        self.active_tab = self.editor.get_current_tab() # Ensure active_tab is fresh
        active_tab_exists = self.active_tab and hasattr(self.active_tab, 'text_area') and self.active_tab.text_area

        if find_text_present and active_tab_exists:
            self.find_next_btn.config(state=tk.NORMAL)
            self.find_prev_btn.config(state=tk.NORMAL) # If find previous is added
            self.replace_all_btn.config(state=tk.NORMAL)
        else:
            self.find_next_btn.config(state=tk.DISABLED)
            self.find_prev_btn.config(state=tk.DISABLED)
            self.replace_all_btn.config(state=tk.DISABLED)

        # Replace button enabled if a match is currently selected/highlighted AND find text is present
        if self.current_match_index != -1 and find_text_present and active_tab_exists:
            self.replace_btn.config(state=tk.NORMAL)
        else:
            self.replace_btn.config(state=tk.DISABLED)

    def _find_next_action(self, event=None, search_backwards=False):
        self.active_tab = self.editor.get_current_tab() # Ensure active_tab is fresh
        if not self.find_what_var.get() or not self.active_tab:
            self.status_label.config(text="No search term or no active tab.")
            self._update_button_states()
            return

        if self.last_known_mod_seq != -1 and self.last_known_mod_seq != self.active_tab.find_replace_mod_seq:
            messagebox.showinfo("Text Changed", "The document has been modified. Please start a new search.", parent=self)
            self._clear_current_search_state()
            return

        self.last_known_mod_seq = self.active_tab.find_replace_mod_seq
        self.editor.find_next_action_from_dialog(
            find_what=self.find_what_var.get(),
            case_sensitive=self.match_case_var.get(),
            whole_word=self.whole_word_var.get(),
            regex=self.regex_var.get(),
            search_backwards=search_backwards # Pass this along
        )
        # The editor's find_next_action_from_dialog will call self.update_search_results
        # which in turn calls self._update_button_states()

    def _find_prev_action(self, event=None):
        self._find_next_action(event, search_backwards=True)

    def _replace_action(self, event=None):
        self.active_tab = self.editor.get_current_tab()
        if self.current_match_index == -1 or not self.active_tab or not self.find_what_var.get():
            self.status_label.config(text="No match selected or no search term.")
            self._update_button_states()
            return

        if self.last_known_mod_seq != self.active_tab.find_replace_mod_seq:
            messagebox.showinfo("Text Changed", "The document has been modified. Please start a new search.", parent=self)
            self._clear_current_search_state()
            return

        self.editor.replace_action_from_dialog(
            find_what=self.find_what_var.get(),
            replace_with=self.replace_with_var.get(),
            case_sensitive=self.match_case_var.get(),
            whole_word=self.whole_word_var.get(),
            regex=self.regex_var.get()
        )
        # Editor's method will update results or call find_next, which updates dialog

    def _replace_all_action(self, event=None):
        self.active_tab = self.editor.get_current_tab()
        if not self.find_what_var.get() or not self.active_tab:
            self.status_label.config(text="No search term or no active tab.")
            self._update_button_states()
            return

        count = self.editor.replace_all_action_from_dialog(
            find_what=self.find_what_var.get(),
            replace_with=self.replace_with_var.get(),
            case_sensitive=self.match_case_var.get(),
            whole_word=self.whole_word_var.get(),
            regex=self.regex_var.get()
        )
        # Editor's method updates the dialog status via update_search_results
        # and clears internal match list.
        self._update_button_states() # Ensure buttons are updated after replace all

    def show(self):
        """Shows the dialog and brings it to front."""
        self.active_tab = self.editor.get_current_tab() # Ensure it's current
        if self.active_tab and hasattr(self.active_tab, 'text_area') and self.active_tab.text_area.tag_ranges(tk.SEL):
            try:
                selected_text = self.active_tab.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected_text and "\n" not in selected_text: # Don't auto-fill for multi-line selections
                    self.find_what_var.set(selected_text)
                    # self.find_entry.select_range(0, tk.END) # Already handled by focus_set + select_range below
            except tk.TclError:
                pass # No selection or error getting it

        self.deiconify()
        self.lift()
        self.find_entry.focus_set()
        self.find_entry.select_range(0, tk.END) # Select existing text in find entry
        self.find_entry.icursor(tk.END)       # Move cursor to end of find entry

        self._on_find_text_or_option_changed() # This will clear highlights and reset states
        self._update_button_states()


    def _on_close(self):
        if self.editor: # Check if editor instance exists
            if self.active_tab: # Check if active_tab was set
                 self.editor.clear_all_search_highlights_active_tab()
                 self.editor.clear_current_search_highlight_active_tab()
            self.editor.find_replace_dialog_instance = None # Let editor know dialog is closed
        self.destroy()

    def _center_dialog(self):
        self.update_idletasks()
        parent = self.editor.root
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        # parent_height = parent.winfo_height() # Not always needed for top-right placement

        dialog_width = self.winfo_width()
        # dialog_height = self.winfo_height()

        # Position near top-right of the parent window, with some offset
        offset_x = 20
        offset_y = 20
        x = parent_x + parent_width - dialog_width - offset_x
        y = parent_y + offset_y

        # Ensure it's not off-screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        if x + dialog_width > screen_width: x = screen_width - dialog_width
        if y < 0 : y = 0 # Ensure not above screen top
        if x < 0 : x = 0

        self.geometry(f'+{x}+{y}')

    # Public method for editor to call when find results are updated
    def update_search_results(self, matches, current_match_idx, status_message=""):
        self.current_matches = matches
        self.current_match_index = current_match_idx
        if status_message:
            self.status_label.config(text=status_message)
        elif matches:
            self.status_label.config(text=f"Match {current_match_idx + 1} of {len(matches)}")
        else:
            self.status_label.config(text="Not found")
        self._update_button_states()


if __name__ == '__main__':
    # This is a mock TextEditor class for testing the dialog independently
    class MockEditor:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Mock Editor")
            self.root.geometry("800x600")
            self.find_replace_dialog_instance = None

            # Mock current tab and text area
            self.mock_tab = ttk.Frame(self.root)
            self.mock_tab.pack(expand=True, fill=tk.BOTH)
            self.mock_text_area = tk.Text(self.mock_tab)
            self.mock_text_area.pack(expand=True, fill=tk.BOTH)
            self.mock_text_area.insert(tk.END, "Hello world, this is a test.\nAnother line for testing world.")
            self.mock_text_area.tag_configure("search_highlight", background="yellow")
            self.mock_text_area.tag_configure("current_search_highlight", background="orange")


            ttk.Button(self.root, text="Open Find/Replace", command=self.open_find_replace_dialog_instance).pack()

        def get_current_tab(self):
            # Mock implementation
            class MockEditorTab:
                def __init__(self, text_area):
                    self.text_area = text_area
                    # Add other attributes if FindReplaceDialog expects them
            return MockEditorTab(self.mock_text_area)

        def clear_all_search_highlights_active_tab(self):
            print("Editor: Clearing all search highlights")
            self.mock_text_area.tag_remove("search_highlight", "1.0", tk.END)

        def clear_current_search_highlight_active_tab(self):
            print("Editor: Clearing current search highlight")
            self.mock_text_area.tag_remove("current_search_highlight", "1.0", tk.END)

        def open_find_replace_dialog_instance(self):
            if self.find_replace_dialog_instance and self.find_replace_dialog_instance.winfo_exists():
                self.find_replace_dialog_instance.lift()
                self.find_replace_dialog_instance.focus_set()
            else:
                self.find_replace_dialog_instance = FindReplaceDialog(self)
                self.find_replace_dialog_instance.show()


    editor_app = MockEditor()
    editor_app.root.mainloop()
