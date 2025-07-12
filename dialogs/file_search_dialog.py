import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import fnmatch
import re
import collections

class FileSearchDialog:
    def __init__(self, parent_editor, title="Advanced File Search"):
        self.parent_editor = parent_editor
        self.top = tk.Toplevel(parent_editor.root)
        self.top.title(title)
        self.top.transient(parent_editor.root)

        self.base_dir_var = tk.StringVar()
        current_tab = self.parent_editor.get_current_tab()
        if current_tab and current_tab.current_file:
            self.base_dir_var.set(os.path.dirname(current_tab.current_file))
        else:
            self.base_dir_var.set(os.path.expanduser("~"))

        self.file_types = ["*.* (All Files)", "*.txt", "*.py", "*.csv", "*.log", "*.json", "*.yaml", "*.xml", "*.ini"]
        self.file_type_var = tk.StringVar(value=self.file_types[0])

        self.search_phrase_var = tk.StringVar()
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        self.lines_before_var = tk.IntVar(value=10)
        self.lines_after_var = tk.IntVar(value=10)

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Base Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        dir_entry = ttk.Entry(main_frame, textvariable=self.base_dir_var, width=50)
        dir_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        dir_button = ttk.Button(main_frame, text="Browse...", command=self._browse_directory)
        dir_button.grid(row=0, column=2, sticky=tk.W, padx=(5,0), pady=2)

        ttk.Label(main_frame, text="File Types:").grid(row=1, column=0, sticky=tk.W, pady=2)
        file_type_combo = ttk.Combobox(main_frame, textvariable=self.file_type_var, values=self.file_types, width=47)
        file_type_combo.grid(row=1, column=1, sticky=tk.EW, pady=2)

        ttk.Label(main_frame, text="Search Phrase:").grid(row=2, column=0, sticky=tk.W, pady=2)
        phrase_entry = ttk.Entry(main_frame, textvariable=self.search_phrase_var, width=50)
        phrase_entry.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=2)

        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5,10))

        ttk.Checkbutton(options_frame, text="Case Sensitive", variable=self.case_sensitive_var).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(options_frame, text="Use Regular Expression", variable=self.regex_var).pack(side=tk.LEFT, padx=(0,10))

        ttk.Label(options_frame, text="Lines Before:").pack(side=tk.LEFT, padx=(5,0))
        ttk.Spinbox(options_frame, from_=0, to=100, textvariable=self.lines_before_var, width=5).pack(side=tk.LEFT, padx=(0,10))

        ttk.Label(options_frame, text="Lines After:").pack(side=tk.LEFT, padx=(5,0))
        ttk.Spinbox(options_frame, from_=0, to=100, textvariable=self.lines_after_var, width=5).pack(side=tk.LEFT)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.E, pady=(10,0))

        search_btn = ttk.Button(button_frame, text="Search", command=self._start_search)
        search_btn.pack(side=tk.LEFT, padx=(0,5))

        close_btn = ttk.Button(button_frame, text="Close", command=self.top.destroy)
        close_btn.pack(side=tk.LEFT)

        phrase_entry.focus_set()
        self.top.bind("<Return>", self._start_search)
        self.top.bind("<Escape>", lambda e: self.top.destroy())

        self.top.update_idletasks()
        x = parent_editor.root.winfo_x() + (parent_editor.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = parent_editor.root.winfo_y() + (parent_editor.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')

    def _browse_directory(self):
        dir_path = filedialog.askdirectory(parent=self.top, initialdir=self.base_dir_var.get())
        if dir_path:
            self.base_dir_var.set(dir_path)

    def _start_search(self, event=None):
        base_dir = self.base_dir_var.get()
        file_pattern = self.file_type_var.get()
        if " (" in file_pattern: # Remove the descriptive part like " (*.*)"
            file_pattern = file_pattern.split(" (", 1)[0] # Keep only the pattern part
        search_phrase = self.search_phrase_var.get()

        if not base_dir or not os.path.isdir(base_dir):
            messagebox.showerror("Error", "Base directory is invalid or not specified.", parent=self.top)
            return
        if not search_phrase: # Search phrase is mandatory for this dialog
            messagebox.showerror("Error", "Search phrase cannot be empty.", parent=self.top)
            return

        results = self._execute_search_logic(base_dir, file_pattern, search_phrase)
        if results:
            self.parent_editor._display_search_results( # Call method on parent TextEditor instance
                results, search_phrase, self.regex_var.get(), self.case_sensitive_var.get()
            )
            self.top.destroy()
        else:
            messagebox.showinfo("Search Complete", "No matches found.", parent=self.top)

    def _execute_search_logic(self, base_dir, file_pattern, search_phrase):
        results = []
        lines_before_count = self.lines_before_var.get()
        lines_after_count = self.lines_after_var.get()
        use_regex = self.regex_var.get()
        case_sensitive = self.case_sensitive_var.get()
        search_flags = 0 if case_sensitive else re.IGNORECASE

        if not use_regex:
            # For simple search, escape the search phrase to treat special characters literally
            search_phrase_compiled = re.escape(search_phrase)
        else:
            # For regex search, compile the user's pattern
            try:
                search_phrase_compiled = re.compile(search_phrase, search_flags)
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regular expression: {e}", parent=self.top)
                return [] # Return empty list on regex compilation error

        for root, _, files in os.walk(base_dir):
            for filename in files:
                if fnmatch.fnmatch(filename, file_pattern):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            all_file_lines = list(f) # Read all lines at once

                        lines_buffer = collections.deque(maxlen=lines_before_count)
                        for line_num_zero_based, line_content in enumerate(all_file_lines):
                            line_content_stripped = line_content.rstrip('\r\n') # Strip EOL for matching and display

                            match_iter = None
                            if use_regex:
                                match_iter = search_phrase_compiled.finditer(line_content_stripped)
                            else: # Simple search (already escaped)
                                match_iter = re.finditer(search_phrase_compiled, line_content_stripped, search_flags)

                            for match in match_iter:
                                start_char, end_char = match.span()
                                context_before = list(lines_buffer)
                                context_after = []
                                for i in range(1, lines_after_count + 1):
                                    if line_num_zero_based + i < len(all_file_lines):
                                        context_after.append(all_file_lines[line_num_zero_based + i].rstrip('\r\n'))
                                    else:
                                        break
                                results.append({
                                    "filepath": filepath,
                                    "line_number": line_num_zero_based + 1, # 1-based for display
                                    "matched_line": line_content_stripped,
                                    "context_before": list(context_before), # Convert deque to list
                                    "context_after": context_after,
                                    "match_start": start_char,
                                    "match_end": end_char
                                })

                            # Add current line to buffer for 'before' context of next lines
                            if lines_before_count > 0:
                                lines_buffer.append(line_content_stripped)
                    except Exception as e:
                        # Log or print error, but continue searching other files
                        print(f"Error reading or processing file {filepath}: {e}")
        return results
