import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog # Added simpledialog
import tkinter.font as tkfont # Corrected import
from tkinterdnd2 import DND_FILES, TkinterDnD # For Drag & Drop - Corrected Case
import os
import string # Added for string.punctuation
import re # Added for regex operations
import collections # Added for Counter
import random # Added for shuffle
import quick_transformer # For QuickText feature
import subprocess
import csv # Added for Excel to CSVs & Stats tool
import configparser # Added for URL Manager
import webbrowser # Added for URL Manager
try:
    import graphviz # Changed from "from graphviz import Digraph"
except ImportError:
    graphviz = None # Placeholder if graphviz is not installed

# Attempt to import data_to_table_converter and its members
try:
    import data_to_table_converter
    from data_to_table_converter import DataParsingError
except ImportError:
    data_to_table_converter = None
    DataParsingError = Exception # Fallback to generic Exception if module not found

import fnmatch # For filename pattern matching


class FileSearchDialog:
    def __init__(self, parent_editor, title="Advanced File Search"):
        self.parent_editor = parent_editor
        self.top = tk.Toplevel(parent_editor.root)
        self.top.title(title)
        self.top.transient(parent_editor.root)
        # self.top.grab_set() # Non-modal for now, to allow interaction with main editor while search runs (future)

        # Sensible default directory
        self.base_dir_var = tk.StringVar()
        current_tab = self.parent_editor.get_current_tab()
        if current_tab and current_tab.current_file:
            self.base_dir_var.set(os.path.dirname(current_tab.current_file))
        else:
            self.base_dir_var.set(os.path.expanduser("~")) # Home directory as a fallback

        self.file_types = ["*.* (All Files)", "*.txt", "*.py", "*.csv", "*.log", "*.json", "*.yaml", "*.xml", "*.ini"]
        self.file_type_var = tk.StringVar(value=self.file_types[0])

        self.search_phrase_var = tk.StringVar()
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        self.lines_before_var = tk.IntVar(value=10)
        self.lines_after_var = tk.IntVar(value=10)

        # --- UI Layout ---
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1) # Make entry fields expand

        # Base Directory
        ttk.Label(main_frame, text="Base Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        dir_entry = ttk.Entry(main_frame, textvariable=self.base_dir_var, width=50)
        dir_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        dir_button = ttk.Button(main_frame, text="Browse...", command=self._browse_directory)
        dir_button.grid(row=0, column=2, sticky=tk.W, padx=(5,0), pady=2)

        # File Types
        ttk.Label(main_frame, text="File Types:").grid(row=1, column=0, sticky=tk.W, pady=2)
        file_type_combo = ttk.Combobox(main_frame, textvariable=self.file_type_var, values=self.file_types, width=47)
        file_type_combo.grid(row=1, column=1, sticky=tk.EW, pady=2)
        # Allow custom patterns by not setting state="readonly"

        # Search Phrase
        ttk.Label(main_frame, text="Search Phrase:").grid(row=2, column=0, sticky=tk.W, pady=2)
        phrase_entry = ttk.Entry(main_frame, textvariable=self.search_phrase_var, width=50)
        phrase_entry.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=2) # Span to align with dir_entry+button

        # Options Frame
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5,10))

        ttk.Checkbutton(options_frame, text="Case Sensitive", variable=self.case_sensitive_var).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(options_frame, text="Use Regular Expression", variable=self.regex_var).pack(side=tk.LEFT, padx=(0,10))

        ttk.Label(options_frame, text="Lines Before:").pack(side=tk.LEFT, padx=(5,0))
        ttk.Spinbox(options_frame, from_=0, to=100, textvariable=self.lines_before_var, width=5).pack(side=tk.LEFT, padx=(0,10))

        ttk.Label(options_frame, text="Lines After:").pack(side=tk.LEFT, padx=(5,0))
        ttk.Spinbox(options_frame, from_=0, to=100, textvariable=self.lines_after_var, width=5).pack(side=tk.LEFT)

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.E, pady=(10,0))

        search_btn = ttk.Button(button_frame, text="Search", command=self._start_search)
        search_btn.pack(side=tk.LEFT, padx=(0,5))

        close_btn = ttk.Button(button_frame, text="Close", command=self.top.destroy)
        close_btn.pack(side=tk.LEFT)

        phrase_entry.focus_set()
        self.top.bind("<Return>", self._start_search) # Allow Enter to start search
        self.top.bind("<Escape>", lambda e: self.top.destroy())

        # Center dialog
        self.top.update_idletasks()
        x = parent_editor.root.winfo_x() + (parent_editor.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = parent_editor.root.winfo_y() + (parent_editor.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')

    def _browse_directory(self):
        dir_path = filedialog.askdirectory(parent=self.top, initialdir=self.base_dir_var.get())
        if dir_path:
            self.base_dir_var.set(dir_path)

    def _start_search(self, event=None):
        # Placeholder for search logic to be implemented in next step
        base_dir = self.base_dir_var.get()
        file_pattern = self.file_type_var.get()
        if " (" in file_pattern: # Handle "desc (*.ext)" format
            file_pattern = file_pattern.split(" (", 1)[1][:-1]

        search_phrase = self.search_phrase_var.get()

        if not base_dir or not os.path.isdir(base_dir):
            messagebox.showerror("Error", "Base directory is invalid or not specified.", parent=self.top)
            return
        if not search_phrase:
            messagebox.showerror("Error", "Search phrase cannot be empty.", parent=self.top)
            return

        # For now, just print params. Search logic will be in another step.
        print(f"Search Params:\n  Dir: {base_dir}\n  Pattern: {file_pattern}\n  Phrase: {search_phrase}")
        print(f"  Case Sensitive: {self.case_sensitive_var.get()}")
        print(f"  Regex: {self.regex_var.get()}")
        print(f"  Lines Before: {self.lines_before_var.get()}")
        print(f"  Lines After: {self.lines_after_var.get()}")

        # In a real implementation, this would call the search worker
        # and then pass results to TextEditor._display_search_results
        # self.parent_editor._perform_file_search(self) # Example call
        # messagebox.showinfo("Search Started", "Search logic to be implemented.\nCheck console for parameters.", parent=self.top)
        results = self._execute_search_logic(base_dir, file_pattern, search_phrase)
        if results:
            self.parent_editor._display_search_results(
                results,
                search_phrase, # Pass search phrase for highlighting
                self.regex_var.get(),
                self.case_sensitive_var.get()
            )
            self.top.destroy() # Close dialog after displaying results
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
            search_phrase_compiled = re.escape(search_phrase) # Treat as literal
        else:
            try:
                search_phrase_compiled = re.compile(search_phrase, search_flags)
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regular expression: {e}", parent=self.top)
                return [] # Return empty results on regex error

        for root, _, files in os.walk(base_dir):
            for filename in files:
                if fnmatch.fnmatch(filename, file_pattern):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: # errors='ignore' for binary files
                            lines_buffer = collections.deque(maxlen=lines_before_count)

                            # Store all lines to allow lookahead for lines_after
                            all_file_lines = list(f) # Read all lines once
                            f.seek(0) # Reset pointer if we need to re-read (not needed with all_file_lines)

                        for line_num_zero_based, line_content in enumerate(all_file_lines):
                            line_content = line_content.rstrip('\r\n') # Remove newlines for matching & context

                            match_iter = None
                            if use_regex:
                                match_iter = search_phrase_compiled.finditer(line_content)
                            else: # Plain text search (already escaped and compiled)
                                match_iter = re.finditer(search_phrase_compiled, line_content, search_flags)

                            for match in match_iter:
                                start_char, end_char = match.span()

                                # Collect lines before
                                context_before = list(lines_buffer)

                                # Collect lines after
                                context_after = []
                                for i in range(1, lines_after_count + 1):
                                    if line_num_zero_based + i < len(all_file_lines):
                                        context_after.append(all_file_lines[line_num_zero_based + i].rstrip('\r\n'))
                                    else:
                                        break

                                results.append({
                                    "filepath": filepath,
                                    "line_number": line_num_zero_based + 1, # 1-based for display
                                    "matched_line": line_content,
                                    "context_before": list(context_before), # Make a copy
                                    "context_after": context_after,
                                    "match_start": start_char,
                                    "match_end": end_char
                                })

                            # Add current line to buffer for next iteration's "before" context
                            if lines_before_count > 0:
                                lines_buffer.append(line_content)

                    except Exception as e:
                        print(f"Error reading or processing file {filepath}: {e}")
                        # Optionally, add to a list of skipped/errored files to show the user
        return results


class FlowDiagramDialog:
    def __init__(self, parent_editor, title="Create Flow Diagram"):
        self.parent_editor = parent_editor # TextEditor instance
        self.top = tk.Toplevel(parent_editor.root)
        self.top.title(title)
        self.top.transient(parent_editor.root)
        self.top.grab_set() # Modal

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(0, weight=1) # Allow text area to expand

        # Diagram Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(title_frame, text="Diagram Title:").pack(side=tk.LEFT, padx=(0,5))
        self.title_var = tk.StringVar(value="[Flow Diagram]")
        title_entry = ttk.Entry(title_frame, textvariable=self.title_var, width=50)
        title_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Input Sequences
        input_frame = ttk.LabelFrame(main_frame, text="Flow Sequences (e.g., Step A->Step B->Step C, one per line)", padding=5)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        input_frame.rowconfigure(0, weight=1)
        input_frame.columnconfigure(0, weight=1)

        self.sequences_text = tk.Text(input_frame, height=15, width=70, wrap=tk.WORD, undo=True)
        sequences_scrollbar = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.sequences_text.yview)
        self.sequences_text.config(yscrollcommand=sequences_scrollbar.set)

        self.sequences_text.grid(row=0, column=0, sticky="nsew")
        sequences_scrollbar.grid(row=0, column=1, sticky="ns")

        self.sequences_text.insert("1.0", "Step A->Step B->Step C\nStep A->Step D\nStep D->Step B\nStep B->Step N->Step A") # Sample data

        # DOT Syntax Checkbox
        option_frame = ttk.Frame(main_frame)
        option_frame.pack(fill=tk.X, pady=(5,0))
        self.dot_syntax_var = tk.BooleanVar(value=False)
        dot_syntax_check = ttk.Checkbutton(option_frame, text="Use DOT Syntax Directly",
                                           variable=self.dot_syntax_var, command=self._on_dot_syntax_toggle)
        dot_syntax_check.pack(side=tk.LEFT)

        self.title_entry_widget = title_entry # Store for enable/disable
        self.input_frame_widget = input_frame # Store for label change

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0))

        generate_btn = ttk.Button(button_frame, text="Generate & Save Diagram", command=self._generate_and_save)
        generate_btn.pack(side=tk.LEFT, padx=(0,10))

        close_btn = ttk.Button(button_frame, text="Close", command=self.top.destroy)
        close_btn.pack(side=tk.RIGHT)

        self.sequences_text.focus_set()
        self._on_dot_syntax_toggle() # Set initial state of title entry and label

        # Center dialog
        self.top.update_idletasks()
        x = parent_editor.root.winfo_x() + (parent_editor.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = parent_editor.root.winfo_y() + (parent_editor.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')

    def _generate_and_save(self):
        if graphviz is None: # Check the module, not just Digraph
            messagebox.showerror("Dependency Missing",
                                 "The 'graphviz' Python library is not installed. Please install it to use this feature.",
                                 parent=self.top)
            return

        dot_script_mode = self.dot_syntax_var.get()
        input_content = self.sequences_text.get("1.0", tk.END + "-1c").strip()

        if not input_content:
            messagebox.showwarning("Input Missing", "Please enter flow sequences or DOT script.", parent=self.top)
            self.sequences_text.focus_set()
            return

        diagram_title_str = self.title_var.get().strip()
        if not dot_script_mode and not diagram_title_str:
            diagram_title_str = "[Flow Diagram]" # Default title for simplified mode if empty
        # In DOT script mode, title_var is mostly ignored unless DOT script is minimal

        filepath = filedialog.asksaveasfilename(
            parent=self.top,
            title="Save Flow Diagram As",
            defaultextension=".pdf",
            initialfile="flow_diagram.pdf",
            filetypes=[("PDF Files", "*.pdf"), ("PNG Files", "*.png"), ("SVG Files", "*.svg"), ("Graphviz DOT File", "*.gv"), ("All Files", "*.*")]
        )

        if not filepath:
            return # User cancelled save dialog

        # Determine format from extension, default to 'pdf' if not obvious
        # (though asksaveasfilename should handle extension based on selected filetype)
        # For dot.render, format is determined by the output filename's extension usually.
        # We can explicitly pass format if needed.

        # The filename from asksaveasfilename includes the full path and selected extension.
        # We need to pass the filename without extension to dot.render's `filename` param,
        # and it will append the format. Or, we can pass the full path and let it infer or specify format.

        base_filepath, file_extension = os.path.splitext(filepath)
        output_format = file_extension[1:] if file_extension else 'pdf' # remove dot, default to pdf

        try:
            if dot_script_mode:
                # Direct DOT syntax mode
                # The title from the UI is ignored here, assuming DOT script contains graph label if needed.
                dot_obj = graphviz.Source(input_content)
            else:
                # Simplified sequence input mode
                sequences_list = [s.strip() for s in input_content.splitlines() if s.strip()]
                if not sequences_list:
                    messagebox.showwarning("Input Missing", "No valid flow sequences provided for simplified input.", parent=self.top)
                    self.sequences_text.focus_set()
                    return
                dot_obj = self._create_graphviz_dot(sequences_list, diagram_title_str)

            # Render and save
            # dot_obj.render will append the format (e.g. .pdf) to base_filepath if format is specified
            # or infer from filename if full path is given.
            dot_obj.render(filename=base_filepath, format=output_format, cleanup=True, view=False)

            saved_file_actual_path = f"{base_filepath}.{output_format}"
            if output_format == 'gv' and not saved_file_actual_path.endswith('.gv'): # .gv is special, render might not add extension
                saved_file_actual_path = base_filepath # if saved as .gv, filename might be just base_filepath
            elif not os.path.exists(saved_file_actual_path):
                 # If dot.render saved it as base_filepath (e.g. for .gv format without explicit .gv in filename)
                 if os.path.exists(base_filepath) and output_format == 'gv':
                      saved_file_actual_path = base_filepath
                 else: # Fallback if actual path logic is tricky for some formats
                      # This branch might indicate an issue or an unexpected save name by graphviz
                      print(f"Warning: Expected file {saved_file_actual_path} not found, trying {base_filepath}")
                      if os.path.exists(base_filepath):
                          saved_file_actual_path = base_filepath
                      # else: still not found, proceed with original path for error message or opening attempt

            messagebox.showinfo("Success", f"Diagram saved successfully as {saved_file_actual_path}", parent=self.top)

            try: # Attempt to open the file
                if os.name == 'nt': # Windows
                    os.startfile(saved_file_actual_path)
                elif os.name == 'posix':
                    if 'darwin' in os.uname().sysname.lower(): # macOS
                         subprocess.call(['open', saved_file_actual_path])
                    else: # Linux and other POSIX
                         subprocess.call(['xdg-open', saved_file_actual_path])
            except Exception as e_open:
                messagebox.showwarning("Open File", f"Could not automatically open the diagram: {e_open}", parent=self.top)

        except Exception as e:
            messagebox.showerror("Diagram Generation Error", f"Could not generate or save diagram: {e}", parent=self.top)


    def _create_graphviz_dot(self, sequences, label):
        dot = graphviz.Digraph() # Use graphviz.Digraph
        dot.attr(splines='true', rankdir='TB') # TB for Top-to-Bottom, LR for Left-to-Right
        dot.attr('node', shape='plaintext', fontname='Helvetica', fontsize='11',
                 fontcolor='black', style='filled', fillcolor='#e9e9e9', width='1.5')
        dot.attr('edge', arrowhead='normal', arrowtail='dot', color='#20B2AA', style='solid')

        # Graph title
        dot.attr(labelloc='t', labeljust='c',
                 fontcolor='#20B2AA', fontname='Courier New Bold', fontsize='20')
        dot.attr(label=label)

        steps = set()
        edges_to_add = []

        for sequence in sequences:
            sequence_steps = [step.strip() for step in sequence.split('->') if step.strip()]
            if not sequence_steps:
                continue

            for step in sequence_steps:
                steps.add(step)

            for i in range(len(sequence_steps) - 1):
                edges_to_add.append((sequence_steps[i], sequence_steps[i+1]))

        for step in sorted(list(steps)): # Sort for consistent node ordering if desired
            dot.node(step, label=f'► {step}') # Using a different shape/prefix for steps

        for u, v in edges_to_add:
            dot.edge(u, v)

        return dot

    def _on_dot_syntax_toggle(self):
        if self.dot_syntax_var.get():
            self.title_entry_widget.config(state=tk.DISABLED)
            self.title_var.set("[Title defined in DOT script]")
            self.input_frame_widget.config(text="DOT Language Script")
            # Optionally, clear or change sample text in self.sequences_text
            # current_text = self.sequences_text.get("1.0", tk.END + "-1c")
            # if "->" in current_text: # Heuristic for simplified syntax
            #     self.sequences_text.delete("1.0", tk.END)
            #     self.sequences_text.insert("1.0", "digraph G {\n  rankdir=TB;\n  a -> b;\n  b -> c;\n}")
        else:
            self.title_entry_widget.config(state=tk.NORMAL)
            if self.title_var.get() == "[Title defined in DOT script]":
                 self.title_var.set("[Flow Diagram]") # Reset to default if it was the placeholder
            self.input_frame_widget.config(text="Flow Sequences (e.g., Step A->Step B->Step C, one per line)")
            # Optionally, restore sample simplified text if it was cleared
            # current_text = self.sequences_text.get("1.0", tk.END + "-1c")
            # if "digraph" in current_text.lower(): # Heuristic for DOT syntax
            #    self.sequences_text.delete("1.0", tk.END)
            #    self.sequences_text.insert("1.0", "Step A->Step B->Step C\nStep A->Step D\nStep D->Step B\nStep B->Step N->Step A")


class QuickTextDialog:
    """
    A dialog window for performing QuickText-style data transformations.
    Allows users to input data, define a pattern with placeholders, specify a delimiter,
    and transform the data, with live preview and pattern saving/loading capabilities.
    """
    def __init__(self, parent, title="QuickText Transformer"):
        self.parent = parent # The TextEditor instance (main application window)
        self.top = tk.Toplevel(parent.root)
        self.top.title(title)
        self.top.transient(parent.root) # Make it transient to the main window
        self.top.grab_set() # Make it modal initially

        # Store data passed if any (e.g., selected text from editor)
        self.initial_input_data = ""
        current_tab = parent.get_current_tab()
        if current_tab:
            try:
                selected_text = current_tab.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected_text:
                    self.initial_input_data = selected_text
            except tk.TclError: # No selection
                # Optionally, could use full tab content as default if no selection.
                # For now, only uses selection.
                pass


        # --- UI Elements ---
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Input Data Section
        input_frame = ttk.LabelFrame(main_frame, text="Input Data", padding=5)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.input_text = tk.Text(input_frame, height=10, width=80, wrap=tk.WORD, undo=True)
        self.input_text_scrollbar = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.input_text.yview)
        self.input_text.config(yscrollcommand=self.input_text_scrollbar.set)
        self.input_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if self.initial_input_data:
            self.input_text.insert("1.0", self.initial_input_data)


        # Controls Frame (Delimiter, Pattern)
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)

        # Delimiter
        ttk.Label(controls_frame, text="Delimiter:").pack(side=tk.LEFT, padx=(0,5))
        self.delimiter_var = tk.StringVar(value=",")
        self.delimiter_entry = ttk.Entry(controls_frame, textvariable=self.delimiter_var, width=5)
        self.delimiter_entry.pack(side=tk.LEFT, padx=(0,10))

        # Live Preview (Optional for now, just the checkbox)
        self.live_preview_var = tk.BooleanVar(value=False)
        self.live_preview_check = ttk.Checkbutton(controls_frame, text="Live Preview", variable=self.live_preview_var, command=self._on_live_preview_toggle)
        self.live_preview_check.pack(side=tk.LEFT, padx=(0,10))
        self._debounce_timer_id = None

        # Store patterns (session-specific)
        self.saved_patterns = {
            "SQL INSERT": "INSERT INTO table_name (column1, column2, column3) VALUES ('$1', '$2', '$3');",
            "HTML List": "<li>$1</li>",
            "CSV Output (reversed)": "$3,$2,$1",
        } # Name: Pattern string
        self.pattern_history_for_dialog = list(self.saved_patterns.keys()) # Just names for the dialog


        # Pattern Section
        pattern_frame = ttk.LabelFrame(main_frame, text="Pattern (e.g., Name: $1 $2. ID: $lineNumber. Use \\$ for literal $)", padding=5)
        pattern_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.pattern_text = tk.Text(pattern_frame, height=4, width=80, wrap=tk.WORD, undo=True)
        self.pattern_text_scrollbar = ttk.Scrollbar(pattern_frame, orient=tk.VERTICAL, command=self.pattern_text.yview)
        self.pattern_text.config(yscrollcommand=self.pattern_text_scrollbar.set)

        # Frame for pattern text and buttons next to it
        pattern_text_and_buttons_frame = ttk.Frame(pattern_frame)
        pattern_text_and_buttons_frame.pack(fill=tk.BOTH, expand=True)

        self.pattern_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, in_=pattern_text_and_buttons_frame) # Pack scrollbar first
        self.pattern_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, in_=pattern_text_and_buttons_frame)

        initial_pattern_name = self.pattern_history_for_dialog[0] if self.pattern_history_for_dialog else "Field1: $1, Field2: $2, Line: $lineNumber"
        initial_pattern_value = self.saved_patterns.get(initial_pattern_name, initial_pattern_name) # Fallback to name if not in map (e.g. default string)
        self.pattern_text.insert("1.0", initial_pattern_value)
        self.pattern_text.config(state=tk.NORMAL) # Explicitly ensure it's enabled


        # Buttons for pattern management (Save/Load)
        pattern_buttons_frame = ttk.Frame(pattern_frame) # New frame for buttons below pattern text area
        pattern_buttons_frame.pack(fill=tk.X, pady=(5,0))

        self.save_pattern_btn = ttk.Button(pattern_buttons_frame, text="Save Current Pattern", command=self._save_current_pattern)
        self.save_pattern_btn.pack(side=tk.LEFT, padx=(0,5))

        self.load_pattern_btn = ttk.Button(pattern_buttons_frame, text="Load Saved Pattern...", command=self._load_saved_pattern)
        self.load_pattern_btn.pack(side=tk.LEFT)


        # Output Section
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.output_text = tk.Text(output_frame, height=10, width=80, wrap=tk.WORD, undo=True)
        self.output_text_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.config(yscrollcommand=self.output_text_scrollbar.set)
        self.output_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED) # Output is read-only initially


        # Action Buttons Frame
        action_buttons_frame = ttk.Frame(main_frame)
        action_buttons_frame.pack(fill=tk.X, pady=(10,0))

        self.transform_btn = ttk.Button(action_buttons_frame, text="Transform", command=self._run_transform)
        self.transform_btn.pack(side=tk.LEFT, padx=5)

        self.copy_output_btn = ttk.Button(action_buttons_frame, text="Copy Output", command=self._copy_output)
        self.copy_output_btn.pack(side=tk.LEFT, padx=5)
        self.copy_output_btn.config(state=tk.DISABLED) # Enabled when output is generated

        self.close_btn = ttk.Button(action_buttons_frame, text="Close", command=self.top.destroy)
        self.close_btn.pack(side=tk.RIGHT, padx=5)

        # Bindings for live preview (if enabled)
        self.input_text.bind("<<Modified>>", self._debounced_maybe_live_transform)
        self.pattern_text.bind("<<Modified>>", self._debounced_maybe_live_transform)
        self.delimiter_var.trace_add("write", self._debounced_maybe_live_transform_trace) # Use different handler for trace

        # Set initial focus
        self.input_text.focus_set()

        # Center dialog
        self.top.update_idletasks()
        parent_root = self.parent.root
        x = parent_root.winfo_x() + (parent_root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = parent_root.winfo_y() + (parent_root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')


    def _run_transform(self, event=None):
        """
        Core transformation logic triggered by the 'Transform' button or live preview.
        Fetches input data, pattern, and delimiter from UI elements,
        calls the nimble_transformer.nimble_transform function,
        and displays the result or error in the output text area.
        """
        input_data = self.input_text.get("1.0", tk.END + "-1c")
        pattern = self.pattern_text.get("1.0", tk.END + "-1c").strip() # Strip pattern
        delimiter = self.delimiter_var.get()

        if not input_data.strip():
            messagebox.showwarning("Input Missing", "Input data is empty.", parent=self.top)
            self.input_text.focus_set()
            return

        if not pattern:
            messagebox.showwarning("Pattern Missing", "Pattern is empty.", parent=self.top)
            self.pattern_text.focus_set()
            return

        # Delimiter can be empty for line-by-line processing in nimble_transformer

        try:
            # Ensure quick_transformer is imported. This should be at the top of editor.py
            # import quick_transformer # Already imported at the top
            output = quick_transformer.quick_transform(input_data, pattern, delimiter)

            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, output)
            self.output_text.config(state=tk.DISABLED)
            self.copy_output_btn.config(state=tk.NORMAL if output else tk.DISABLED)

        except ValueError as e: # Catch errors from nimble_transform (e.g. CSV parsing)
            messagebox.showerror("Transformation Error", str(e), parent=self.top)
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, f"Error: {str(e)}")
            self.output_text.config(state=tk.DISABLED)
            self.copy_output_btn.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.top)
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, f"Unexpected Error: {e}")
            self.output_text.config(state=tk.DISABLED)
            self.copy_output_btn.config(state=tk.DISABLED)

    def _copy_output(self):
        """Copies the content of the output text area to the clipboard."""
        output_content = self.output_text.get("1.0", tk.END + "-1c")
        if output_content:
            self.top.clipboard_clear()
            self.top.clipboard_append(output_content)
            messagebox.showinfo("Copied", "Output copied to clipboard.", parent=self.top)
        else:
            messagebox.showwarning("Empty Output", "There is no output to copy.", parent=self.top)

    def _on_live_preview_toggle(self):
        if self.live_preview_var.get():
            # When enabling live preview, trigger an initial transformation.
            # We don't need to debounce this one as it's a single action.
            self._run_transform()
        # No specific action needed when disabling live preview; output just stops auto-updating.

    def _debounced_maybe_live_transform(self, event=None):
        """Handles text widget <<Modified>> events for live preview with debouncing."""
        # For Text widgets, the <<Modified>> event can fire multiple times for a single logical change.
        # We need to reset the internal modified flag of the text widget to correctly detect subsequent changes.
        # This should be done *after* we've scheduled the transform, or it might interfere with other bindings
        # or the ability to detect if a change actually occurred.
        # However, for live preview, we just care that *a* modification happened.

        widget = event.widget # Get the widget that triggered the event
        try:
            # Check and clear the internal modified flag. This is important because
            # programmatic changes (like our transform updating output, though not relevant here)
            # can also set this flag. For input/pattern text areas, we want to react to user edits.
            if widget.edit_modified():
                widget.edit_modified(False) # Reset the flag
            else:
                # If the flag wasn't set, it might be a Configure event or similar,
                # not a text content change we care about for debouncing this way.
                # Or, the flag was already cleared by a previous call in a rapid sequence.
                # We can still proceed to debounce, as some modification must have occurred
                # to trigger the binding.
                pass
        except AttributeError:
            # Not all event sources (like a trace on StringVar) will have 'edit_modified'.
            # This is fine; the primary purpose here is for Text widgets.
            pass

        if self.live_preview_var.get():
            if self._debounce_timer_id:
                self.top.after_cancel(self._debounce_timer_id)

            # Schedule _run_transform to be called after 500ms (adjust as needed)
            self._debounce_timer_id = self.top.after(500, self._run_transform)

    def _debounced_maybe_live_transform_trace(self, *args):
        """Handles StringVar trace events for live preview with debouncing."""
        if self.live_preview_var.get():
            if self._debounce_timer_id:
                self.top.after_cancel(self._debounce_timer_id)
            self._debounce_timer_id = self.top.after(500, self._run_transform)

    def _save_current_pattern(self):
        """
        Saves the current content of the pattern text area.
        Prompts the user for a name and stores the pattern for the current session.
        Handles empty patterns, empty names, and overwriting existing patterns.
        """
        current_pattern_text = self.pattern_text.get("1.0", tk.END + "-1c").strip()
        if not current_pattern_text:
            messagebox.showwarning("Empty Pattern", "Cannot save an empty pattern.", parent=self.top)
            return

        # Ask for a name for this pattern
        pattern_name = simpledialog.askstring("Save Pattern", "Enter a name for this pattern:", parent=self.top)

        if pattern_name: # User entered a name and didn't cancel
            pattern_name = pattern_name.strip()
            if not pattern_name:
                messagebox.showwarning("Invalid Name", "Pattern name cannot be empty.", parent=self.top)
                return

            if pattern_name in self.saved_patterns and \
               not messagebox.askyesno("Overwrite Pattern", f"A pattern named '{pattern_name}' already exists. Overwrite it?", parent=self.top):
                return # User chose not to overwrite

            self.saved_patterns[pattern_name] = current_pattern_text
            if pattern_name not in self.pattern_history_for_dialog: # Add to history if new
                self.pattern_history_for_dialog.append(pattern_name)

            messagebox.showinfo("Pattern Saved", f"Pattern '{pattern_name}' saved.", parent=self.top)
        # Else: user cancelled or entered empty name (handled by askstring returning None or subsequent check)

    def _load_saved_pattern(self):
        """
        Loads a previously saved pattern into the pattern text area.
        Displays a dialog with a list of saved pattern names for the user to choose from.
        If live preview is active, triggers a transformation after loading the pattern.
        """
        if not self.saved_patterns:
            messagebox.showinfo("No Saved Patterns", "There are no patterns saved in this session.", parent=self.top)
            return

        # Use a simple dialog with a listbox to choose a pattern
        # Could also use a Combobox directly on the main dialog if preferred for fewer popups.

        load_dialog = tk.Toplevel(self.top)
        load_dialog.title("Load Pattern")
        load_dialog.transient(self.top)
        load_dialog.grab_set()
        load_dialog.geometry("300x250") # Adjust size as needed

        ttk.Label(load_dialog, text="Select a pattern to load:").pack(pady=5)

        patterns_listbox = tk.Listbox(load_dialog, selectmode=tk.SINGLE, exportselection=False)
        for pattern_name_item in self.pattern_history_for_dialog: # Use history for order
            patterns_listbox.insert(tk.END, pattern_name_item)
        patterns_listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        if self.pattern_history_for_dialog: # Select first item if list is not empty
            patterns_listbox.select_set(0)
            patterns_listbox.activate(0)

        patterns_listbox.focus_set()

        result_pattern_value = None # To store selected pattern value

        def on_load_select():
            nonlocal result_pattern_value
            selected_indices = patterns_listbox.curselection()
            if selected_indices:
                selected_name = patterns_listbox.get(selected_indices[0])
                result_pattern_value = self.saved_patterns.get(selected_name)
                if result_pattern_value is not None:
                    self.pattern_text.delete("1.0", tk.END)
                    self.pattern_text.insert("1.0", result_pattern_value)
                    if self.live_preview_var.get(): # Trigger live preview if active
                        self._run_transform()
                load_dialog.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select a pattern from the list.", parent=load_dialog)


        def on_load_cancel():
            load_dialog.destroy()

        buttons_frame_load = ttk.Frame(load_dialog)
        buttons_frame_load.pack(pady=5, fill=tk.X)

        load_btn_inner = ttk.Button(buttons_frame_load, text="Load", command=on_load_select)
        load_btn_inner.pack(side=tk.LEFT, padx=10)

        cancel_btn_inner = ttk.Button(buttons_frame_load, text="Cancel", command=on_load_cancel)
        cancel_btn_inner.pack(side=tk.RIGHT, padx=10)

        patterns_listbox.bind("<Double-1>", lambda e: on_load_select()) # Double click to load
        load_dialog.bind("<Return>", lambda e: on_load_select()) # Enter to load
        load_dialog.bind("<Escape>", lambda e: on_load_cancel()) # Escape to cancel

        load_dialog.wait_window() # Wait for this dialog to close


class EditorTab:
    def __init__(self, notebook_widget, app_instance, file_path=None):
        self.app = app_instance
        self.notebook = notebook_widget
        self.frame = ttk.Frame(self.notebook, padding=2) # Added padding=2
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.line_numbers_font = tkfont.Font(family=app_instance.editor_font.cget("family"), size=app_instance.editor_font.cget("size"))
        self.line_numbers_canvas = tk.Canvas(self.frame, width=65, bg='lightgrey', highlightthickness=0) # Renamed for clarity

        # Visibility of line numbers for this tab, synced with app setting
        self.line_numbers_visible = self.app.show_line_numbers
        if self.line_numbers_visible:
            self.line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y)

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

        # Bindings for current line highlighting
        self.text_area.bind("<KeyRelease>", self.update_current_line_highlight, add="+") # Add to existing KeyRelease if any
        self.text_area.bind("<ButtonRelease-1>", self.update_current_line_highlight, add="+") # Add to existing ButtonRelease-1
        self.text_area.bind("<FocusIn>", self.update_current_line_highlight, add="+")

        # Search highlight tag
        self.text_area.tag_configure("search_highlight", background="yellow", foreground="black")
        self.text_area.tag_configure("current_search_highlight", background="orange", foreground="black")

        # For managing debounced keyword highlighting
        self._keyword_highlight_after_id = None

        # For managing debounced syntax highlighting
        self._syntax_highlight_after_id = None
        self.current_language_name = None

        # Filter state for this tab (now tab-specific)
        self.tab_original_text_for_filter: str | None = None
        self.is_tab_filtered_view: bool = False
        self.tab_filter_str: str = ""
        self.tab_filter_case_sensitive: bool = False
        self.tab_filter_invert: bool = False

        # Syntax highlighting tags
        self.text_area.tag_configure("hl_keyword", foreground="#0000FF")  # Blue
        self.text_area.tag_configure("hl_comment", foreground="#008000")  # Green
        self.text_area.tag_configure("hl_string", foreground="#A52A2A")   # Brown/SaddleBrown
        self.text_area.tag_configure("hl_number", foreground="#FF00FF")  # Magenta
        self.text_area.tag_configure("hl_operator", foreground="#FF8C00") # DarkOrange
        self.text_area.tag_configure("hl_builtin", foreground="#20B2AA")  # LightSeaGreen
        # Add more tags as needed for other token types

        # Tag for current line highlighting
        self.text_area.tag_configure("current_line_highlight", background="#FFFFE0")

        # Notes Style Tags & Attributes
        self.tab_notes_style_active = self.app.notes_style_active
        self._notes_style_highlight_after_id = None

        # Create bold font variant for notes style
        notes_bold_font = tkfont.Font(family=self.app.editor_font.cget("family"),
                                      size=self.app.editor_font.cget("size"),
                                      weight="bold")

        self.text_area.tag_configure("notes_number", foreground="red")
        self.text_area.tag_configure("notes_header", foreground="navy", font=notes_bold_font) # Or "#000080"
        self.text_area.tag_configure("notes_comment", foreground="dark green", font=notes_bold_font) # Or "#006400"
        self.text_area.tag_configure("notes_separator", foreground="orange") # Or "#FFA500"


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

        self.text_area.bind("<KeyPress>", self.on_text_area_keypress_filtered, add="+")

        # Initial current line highlight
        self.update_current_line_highlight()

    def update_current_line_highlight(self, event=None):
        # Remove existing highlight from all lines first
        self.text_area.tag_remove("current_line_highlight", "1.0", tk.END)

        # Get current line based on insert cursor
        try:
            # Ensure widget still exists and INSERT mark is valid
            if not self.text_area.winfo_exists():
                return
            cursor_pos = self.text_area.index(tk.INSERT)
            line_num = cursor_pos.split('.')[0]

            # Apply highlight to the current line
            self.text_area.tag_add("current_line_highlight", f"{line_num}.0", f"{line_num}.end")
        except tk.TclError:
            # Can occur if widget is destroyed or index is somehow invalid during teardown/rapid changes
            pass
        except Exception as e:
            # Catch any other unexpected error during highlight update
            print(f"Error updating current line highlight: {e}")


    def on_text_area_keypress_filtered(self, event):
        if self.is_tab_filtered_view: # Use the new attribute name
            # Ctrl key combinations
            if event.state & 0x0004:  # Control key is pressed
                keysym_lower = event.keysym.lower()
                if keysym_lower == 'x':  # Block Ctrl+X (Cut)
                    # print("DEBUG: Filtered view: Blocking Ctrl+X")
                    return "break"
                if keysym_lower in ['c', 'a']: # Ctrl+C (Copy), Ctrl+A (Select All)
                    # These are handled by TextEditor's bind_all.
                    # This binding should not interfere. Returning None allows bind_all to proceed.
                    # print(f"DEBUG: Filtered view: Allowing Ctrl+{keysym_lower}")
                    return
                # Other Ctrl combinations (like Ctrl+V for paste, Ctrl+Z for undo) will pass through here.
                # TextEditor's global bindings for these will attempt to work.
                # If they perform modifications, they might be confusing in a "read-only" filtered view,
                # but copy/select-all should be fine.
                # For a stricter read-only, one might block Ctrl+V, Ctrl+Z here too.
                # print(f"DEBUG: Filtered view: Passing through Ctrl+{keysym_lower}")
                return

            # Keys that cause direct text modification or unwanted actions
            modifying_keysyms = ["BackSpace", "Delete", "Return", "Tab", "KP_Enter"]
            if event.keysym in modifying_keysyms:
                # print(f"DEBUG: Filtered view: Blocking modifying keysym: {event.keysym}")
                return "break"

            if event.char and event.char.isprintable() and not (event.state & 0x0004): # Printable char without Control
                # print(f"DEBUG: Filtered view: Blocking printable char: '{event.char}'")
                return "break"

            # If we haven't returned "break" or None for a specific Ctrl key,
            # it means it's likely a navigation key (Arrows, Home, End, PageUp, PageDown, Insert),
            # a modifier key press by itself (Shift, Alt, Control), or an unhandled Ctrl combo.
            # These should be allowed to let the Text widget handle navigation & selection by default.
            # print(f"DEBUG: Filtered view: Allowing non-modifying key: {event.keysym}")
            return

        return # Not in filtered view, allow all events by default at this level.


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
            # Only set text_changed flag if not in filtered view and actual user edit occurred
            if not self.is_tab_filtered_view: # Corrected: Use new attribute name
                if self.text_area.edit_modified():
                    if not self.text_changed:
                        self.text_changed = True
                        self.update_tab_title()

            # Always reset the Tkinter internal modified flag after checking it.
            # This is important because programmatic changes (like applying filter)
            # also set this flag, and we need to reset it to correctly detect subsequent user edits.
            self.text_area.edit_modified(False)

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

                # Schedule Notes Style highlighting update (debounced) if active for this tab
                if self.tab_notes_style_active:
                    if self._notes_style_highlight_after_id:
                        self.text_area.after_cancel(self._notes_style_highlight_after_id)
                    self._notes_style_highlight_after_id = self.text_area.after(500, self.apply_notes_style_highlighting)


    def clear_search_highlight_tags(self):
        self.text_area.tag_remove("search_highlight", "1.0", tk.END)
        self.text_area.tag_remove("current_search_highlight", "1.0", tk.END)

    def apply_text_filter(self):
        print(f"DEBUG: apply_text_filter START for tab '{self.current_file or 'Untitled'}'")
        print(f"DEBUG: Initial state: is_tab_filtered_view={self.is_tab_filtered_view}, tab_filter_str='{self.tab_filter_str}'")
        # print(f"DEBUG: Initial original_text_for_filter: '{self.tab_original_text_for_filter[:100] if self.tab_original_text_for_filter else None}...'")

        if not self.tab_filter_str:
            print("DEBUG: Filter string is empty. Restoring original text if needed.")
            if self.is_tab_filtered_view and self.tab_original_text_for_filter is not None:
                print(f"DEBUG: Restoring original text. Length: {len(self.tab_original_text_for_filter)}")
                current_insert = self.text_area.index(tk.INSERT)
                pre_delete_content = self.text_area.get("1.0", tk.END + "-1c")
                print(f"DEBUG: Content BEFORE delete (restore path): '{pre_delete_content[:100]}...'")
                self.text_area.delete("1.0", tk.END)
                content_after_delete = self.text_area.get("1.0", tk.END + "-1c")
                print(f"DEBUG: Content AFTER delete (restore path): '{content_after_delete[:100]}...'")
                self.text_area.insert("1.0", self.tab_original_text_for_filter)
                self.tab_original_text_for_filter = None
                try:
                    self.text_area.mark_set(tk.INSERT, current_insert)
                    self.text_area.see(current_insert)
                except tk.TclError:
                    self.text_area.mark_set(tk.INSERT, "1.0")
            else:
                print("DEBUG: No restoration needed (not in filtered view or no original text).")
            self.is_tab_filtered_view = False
        else:
            print(f"DEBUG: Filter string is '{self.tab_filter_str}'. Applying filter.")
            if not self.is_tab_filtered_view:
                current_text_area_content = self.text_area.get("1.0", tk.END + "-1c")
                print(f"DEBUG: Entering filtered view. Capturing original text. Current text_area content length: {len(current_text_area_content)}")
                # print(f"DEBUG: Content being captured: '{current_text_area_content[:100]}...'")
                self.tab_original_text_for_filter = current_text_area_content

            self.is_tab_filtered_view = True

            if self.tab_original_text_for_filter is None:
                print("CRITICAL WARNING: tab_original_text_for_filter is None in active filter state. This should not happen.")
                # Fallback for safety, though this indicates a logical flaw elsewhere if reached.
                source_text_for_filtering = self.text_area.get("1.0", tk.END + "-1c")
                print(f"DEBUG: Fallback: using current text_area content for filtering. Length: {len(source_text_for_filtering)}")
            else:
                source_text_for_filtering = self.tab_original_text_for_filter

            print(f"DEBUG: Source text for filtering (length {len(source_text_for_filtering)}): '{source_text_for_filtering[:100]}...'")

            lines = source_text_for_filtering.splitlines(keepends=True)
            matching_lines = []
            str_to_find = self.tab_filter_str if self.tab_filter_case_sensitive else self.tab_filter_str.lower()

            for line_content_with_ending in lines:
                line_to_check_in = line_content_with_ending if self.tab_filter_case_sensitive else line_content_with_ending.lower()
                match_found = (str_to_find in line_to_check_in)
                if self.tab_filter_invert:
                    if not match_found: matching_lines.append(line_content_with_ending)
                else:
                    if match_found: matching_lines.append(line_content_with_ending)

            print(f"DEBUG: Found {len(matching_lines)} matching lines.")
            if matching_lines:
                print(f"DEBUG: First matching line: '{matching_lines[0][:100]}...'")

            pre_delete_content_filter = self.text_area.get("1.0", tk.END + "-1c")
            print(f"DEBUG: Content BEFORE delete (filter path): '{pre_delete_content_filter[:100]}...'")
            self.text_area.delete("1.0", tk.END)
            content_after_delete_filter = self.text_area.get("1.0", tk.END + "-1c")
            print(f"DEBUG: Content AFTER delete (filter path): '{content_after_delete_filter[:100]}...'")

            joined_matching_lines = "".join(matching_lines)
            print(f"DEBUG: Text to insert (length {len(joined_matching_lines)}): '{joined_matching_lines[:100]}...'")
            if matching_lines: # Only insert if there's something to insert
                self.text_area.insert("1.0", joined_matching_lines)

        print(f"DEBUG: apply_text_filter END. is_tab_filtered_view={self.is_tab_filtered_view}")
        # print(f"DEBUG: End original_text_for_filter: '{self.tab_original_text_for_filter[:100] if self.tab_original_text_for_filter else None}...'")
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
        if not self.line_numbers_visible or not self.line_numbers_canvas.winfo_ismapped():
            return # Don't draw if not visible or not mapped

        self.line_numbers_canvas.delete("all")

        # Ensure text area is updated for dlineinfo to be accurate
        self.text_area.update_idletasks()

        # Get the index of the first character visible in the text_area
        first_visible_char_index = self.text_area.index("@0,0")

        if not first_visible_char_index:
            return # Should not happen if text_area is valid

        try:
            # Determine the line number of the first visible line
            first_line_num = int(first_visible_char_index.split('.')[0])
        except ValueError:
            return # Invalid index format

        # Get dlineinfo for the first visible line to find its y-offset within the content
        # This y-offset is how much the content has been scrolled up.
        first_visible_line_bbox = self.text_area.dlineinfo(f"{first_line_num}.0")
        if not first_visible_line_bbox:
            # This can happen if the text area is empty or lines are not yet rendered.
            # Try to draw at least line 1 if the text area is empty but focused.
            if self.text_area.index("end-1c") == "1.0": # Empty text area
                 self.line_numbers_canvas.create_text( # Corrected: use self.line_numbers_canvas
                    self.line_numbers_canvas.winfo_width() - 2, 0, # Corrected: use self.line_numbers_canvas
                    anchor=tk.NW, text="1", font=self.line_numbers_font
                )
            return

        y_offset_of_content_top_from_visible_area_top = first_visible_line_bbox[1]

        current_line_to_draw_num = first_line_num
        while True:
            dline_info = self.text_area.dlineinfo(f"{current_line_to_draw_num}.0")

            if dline_info is None:
                # No more lines in the text_area from this number onwards
                break

            # x, y, width, height, baseline of the current line in the text_area's content
            line_x_in_text_content = dline_info[0]
            line_y_in_text_content = dline_info[1]
            line_width_in_text_content = dline_info[2]
            line_height_in_text_content = dline_info[3]
            # line_baseline_in_text_content = dline_info[4] # y + baseline = actual baseline y

            # Calculate the y position for drawing this line number on the canvas.
            # This is the line's y position in the content, minus how much the content is scrolled up.
            # This gives the y-coordinate for the *top* of the line on the canvas.
            canvas_y_for_line_top = line_y_in_text_content - y_offset_of_content_top_from_visible_area_top

            # If we use anchor=tk.NE, the (x,y) is the top-right corner.
            # If we use anchor=tk.NW, the (x,y) is the top-left corner.
            # Let's use anchor=tk.NE for right-alignment.
            # The y-coordinate should be the top of the line.

            # Stop drawing if the top of the line is already below the visible canvas height
            if canvas_y_for_line_top > self.line_numbers_canvas.winfo_height():
                break

            # Only draw if the line is at least partially visible (bottom of line is below canvas top,
            # and top of line is above canvas bottom)
            if (canvas_y_for_line_top + line_height_in_text_content) >= 0 and \
               canvas_y_for_line_top <= self.line_numbers_canvas.winfo_height():

                # The x-coordinate for create_text with anchor=tk.NE should be the right edge of the canvas.
                # Add a small padding (e.g., 2 pixels) from the right edge.
                canvas_x_for_number = self.line_numbers_canvas.winfo_width() - 2

                self.line_numbers_canvas.create_text(
                    canvas_x_for_number,
                    canvas_y_for_line_top, # Use the top of the line for y
                    anchor=tk.NE, # Anchor at the top-right of the text
                    text=str(current_line_to_draw_num),
                    font=self.line_numbers_font
                )

            current_line_to_draw_num += 1
            # Safety break if we somehow get into an excessively long loop (e.g., > 10000 lines drawn)
            # This can happen if text_area.index("end-1c") is huge and dlineinfo keeps returning values.
            if current_line_to_draw_num > first_line_num + 5000: # Limit to drawing 5000 lines per call
                 print(f"DEBUG: redraw_line_numbers breaking early after drawing {5000} lines.")
                 break

            # Break if we are trying to draw a line number greater than the total number of lines.
            # This check is important if the content shrinks while scrolling.
            total_lines_str = self.text_area.index(f"{tk.END}-1c").split('.')[0]
            if total_lines_str.isdigit() and current_line_to_draw_num > int(total_lines_str) + 1: # +1 for safety with empty last line
                break


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
                    # If quitting and this was the last tab, root.destroy will be handled by exit_editor_action.
                    # No need to destroy root here.
                    pass
                else:
                    # Not quitting, but last tab closed, so create a new one.
                    self.app.new_file_action()
            else:
                # Other tabs remain, try to select a sensible one if the app is not quitting.
                if not self.app.quitting_app and len(self.app.notebook.tabs()) > 0:
                    if selected_tab_before_close >= len(self.app.notebook.tabs()): # if last tab was closed
                        self.app.notebook.select(len(self.app.notebook.tabs()) - 1)
                    # else: notebook might auto-select, or current selection is still valid.
                    # on_tab_changed will be triggered if selection changes.
                # If quitting_app is true, no need to select another tab, exit_editor_action handles shutdown.

            # UI updates should only happen if the app is not in the process of quitting.
            if not self.app.quitting_app:
                try:
                    self.app.update_app_title()
                    self.app.update_status_bar()
                except tk.TclError:
                    # If an error occurs here (e.g. root destroyed unexpectedly), just pass.
                    pass

            return True
        except tk.TclError as e: # Catch specific Tcl errors from notebook operations like notebook.forget
            print(f"Error closing tab (TclError): {e}")
            # Fallback or recovery might be needed if notebook is in a bad state
            return False
        except Exception as e: # Catch any other unexpected errors
            print(f"Unexpected error closing tab: {e}")
            return False

    def apply_notes_style_highlighting(self, event=None):
        if not self.tab_notes_style_active:
            self.clear_notes_style_highlighting()
            # If notes style is off, ensure other syntax highlighting is reapplied if necessary
            if self.current_language_name and hasattr(self, 'apply_syntax_highlighting'):
                self.apply_syntax_highlighting()
            if self.app.keyword_highlight_settings.get("active", False) and hasattr(self, 'apply_keyword_highlights'):
                self.apply_keyword_highlights(self.app.keyword_highlight_settings)
            return

        # Notes style is active, clear other types of syntax/keyword highlights first
        if hasattr(self, '_clear_syntax_highlight_tags'):
            self._clear_syntax_highlight_tags()

        # Clearing user keyword highlights:
        if hasattr(self.app, 'pastel_colors'): # Check if keyword system is initialized
            for i in range(len(self.app.pastel_colors) + 5):
                try:
                    self.text_area.tag_remove(f"user_keyword_{i}", "1.0", tk.END)
                except tk.TclError:
                    pass

        self.clear_notes_style_highlighting() # Clear previous notes style highlights before reapplying

        all_text = self.text_area.get("1.0", tk.END)
        if not all_text.strip():
            return

        number_pattern = r'(?<![a-zA-Z_])(?<!\.)-?\b(?:\d+\.?\d*|\.\d+)\b(?!\.)(?![a-zA-Z_])'
        header_pattern = r'^([^:]+):'
        comment_pattern = r'#.*'
        separator_pattern = r'^(?:-{2,}|={2,})$'

        for match in re.finditer(separator_pattern, all_text, re.MULTILINE):
            start_idx = self.text_area.index(f"1.0 + {match.start()} chars")
            end_idx = self.text_area.index(f"1.0 + {match.end()} chars")
            self.text_area.tag_add("notes_separator", start_idx, end_idx)

        for match in re.finditer(header_pattern, all_text, re.MULTILINE):
            start_idx = self.text_area.index(f"1.0 + {match.start(0)} chars") # Use group 0 for full match start
            # end_idx for header should be up to and including the colon
            end_colon_offset = match.group(0).find(':')
            if end_colon_offset != -1:
                actual_end_offset = match.start(0) + end_colon_offset + 1
                end_idx = self.text_area.index(f"1.0 + {actual_end_offset} chars")
            else: # Should not happen with this regex, but as a fallback
                end_idx = self.text_area.index(f"1.0 + {match.end(0)} chars")

            line_text_for_header_check = all_text[match.start() : match.end()]
            if not (line_text_for_header_check.strip().startswith("---") or line_text_for_header_check.strip().startswith("===")):
                self.text_area.tag_add("notes_header", start_idx, end_idx)

        for match in re.finditer(comment_pattern, all_text):
            start_idx = self.text_area.index(f"1.0 + {match.start()} chars")
            end_idx = self.text_area.index(f"1.0 + {match.end()} chars")
            self.text_area.tag_add("notes_comment", start_idx, end_idx)

        for match in re.finditer(number_pattern, all_text):
            match_start_idx = self.text_area.index(f"1.0 + {match.start()} chars")
            match_end_idx = self.text_area.index(f"1.0 + {match.end()} chars")

            tags_at_start = self.text_area.tag_names(match_start_idx)

            is_already_styled_exclusively = False
            for tag_name in tags_at_start:
                if tag_name in ["notes_comment", "notes_separator", "notes_header"]:
                    is_already_styled_exclusively = True
                    break

            if not is_already_styled_exclusively:
                self.text_area.tag_add("notes_number", match_start_idx, match_end_idx)

    def clear_notes_style_highlighting(self):
        self.text_area.tag_remove("notes_number", "1.0", tk.END)
        self.text_area.tag_remove("notes_header", "1.0", tk.END)
        self.text_area.tag_remove("notes_comment", "1.0", tk.END)
        self.text_area.tag_remove("notes_separator", "1.0", tk.END)

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
        self.show_line_numbers = True # Added for toggling line numbers
        self.notes_style_active = False # Added for Notes Style feature
        self._is_updating_filter_bar_from_tab = False # Flag to prevent re-filtering on tab change

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
        self.edit_menu.add_command(label="Strip Clipboard Formatting", command=self.strip_clipboard_formatting_action) # New
        self.edit_menu.add_command(label="Copy File Path", command=self.copy_file_path_action)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", command=self.select_all_action, accelerator="Ctrl+A")

        # Format menu - Restructured
        self.format_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Format", menu=self.format_menu)

        # 1. Trim Sub-menu
        self.trim_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Trim", menu=self.trim_menu)
        self.trim_menu.add_command(label="Leading Whitespace", command=lambda: self.trim_whitespace("leading"))
        self.trim_menu.add_command(label="Trailing Whitespace", command=lambda: self.trim_whitespace("trailing"))
        self.trim_menu.add_command(label="Both Ends Whitespace", command=lambda: self.trim_whitespace("both"))

        # 2. Change Case Sub-menu
        self.case_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Change Case", menu=self.case_menu)
        self.case_menu.add_command(label="To UPPERCASE", command=lambda: self.change_case("upper"))
        self.case_menu.add_command(label="To lowercase", command=lambda: self.change_case("lower"))
        self.case_menu.add_command(label="To Title Case", command=lambda: self.change_case("title"))
        # self.case_menu.add_command(label="To Sentence case", command=self.sentence_case_action) # New, for Phase 2

        # 3. Sort Lines
        self.format_menu.add_command(label="Sort Lines...", command=self.sort_lines_dialog)
        # The dialog itself handles different sort types. Menu labels like "Sort Alphabetically (A → Z)"
        # are covered by options within this dialog.

        # 4. Pad Lines
        self.format_menu.add_command(label="Pad Lines...", command=self.pad_lines_dialog)
        # Dialog handles left, right, center (both sides) padding.

        # 5. Add Prefix/Suffix
        self.format_menu.add_command(label="Add Prefix/Suffix to Lines...", command=self.add_prefix_suffix_dialog)

        self.format_menu.add_separator()

        # 6. Line Spacing Sub-menu
        self.line_spacing_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Line Spacing", menu=self.line_spacing_menu)
        self.line_spacing_menu.add_command(label="Condense Internal Whitespace", command=self.condense_internal_whitespace)
        self.line_spacing_menu.add_command(label="Double Space Lines", command=self.double_space_lines)
        self.line_spacing_menu.add_command(label="Reduce Multiple Blank Lines to One", command=self.reduce_blank_lines)
        # "Remove All Blank Lines" moved to Tools menu

        # 7. Line Alteration Sub-menu
        self.line_alteration_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Line Alteration", menu=self.line_alteration_menu)
        self.line_alteration_menu.add_command(label="Delete Duplicate Consecutive Lines", command=self.delete_duplicate_consecutive_lines)
        self.line_alteration_menu.add_command(label="Reverse Lines", command=self.reverse_lines_action)
        # self.line_alteration_menu.add_command(label="Deduplicate All Lines", command=self.deduplicate_all_lines_action) # New, for Phase 2

        # 8. Join/Split Lines Sub-menu
        self.join_split_lines_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Join/Split Lines", menu=self.join_split_lines_menu)
        self.join_split_lines_menu.add_command(label="Join Lines (with space)", command=self.join_lines_with_space)
        self.join_split_lines_menu.add_command(label="Join Lines (with ', ')", command=self.join_lines_with_comma_space)
        # self.join_split_lines_menu.add_command(label="Join Lines (with |)", command=self.join_lines_with_pipe_action) # New, for Phase 2
        # self.join_split_lines_menu.add_command(label="Split by Delimiter...", command=self.split_by_delimiter_dialog) # New, for Phase 2

        self.format_menu.add_separator()

        # 9. Remove Punctuation
        self.format_menu.add_command(label="Remove Punctuation", command=self.remove_punctuation_action)

        # 10. Shuffle Lines
        self.format_menu.add_command(label="Shuffle Lines", command=self.shuffle_lines_action)

        # 11. Normalize Whitespace (New, for Phase 2)
        # self.format_menu.add_command(label="Normalize Whitespace...", command=self.normalize_whitespace_dialog)


        # Tools Menu - Restructured
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)

        # 1. Word Analysis Sub-menu
        self.word_analysis_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Word Analysis", menu=self.word_analysis_menu)
        self.word_analysis_menu.add_command(label="Count Word Frequency...", command=self.count_word_frequency_action)
        self.word_analysis_menu.add_command(label="Extract Unique Words...", command=self.extract_unique_words_dialog)
        self.word_analysis_menu.add_command(label="Extract UPPERCASE Words...", command=self.extract_uppercase_words_action)
        # New items for Phase 2:
        # self.word_analysis_menu.add_command(label="Extract Longest Words...", command=self.extract_longest_words_action)
        # self.word_analysis_menu.add_command(label="Extract Most Frequent Words...", command=self.extract_most_frequent_words_action)

        # 2. Text Statistics
        # For now, a direct command. Could become a sub-menu if more detailed stats are added.
        self.tools_menu.add_command(label="Text Statistics...", command=self.text_statistics_action)
        # The current self.text_statistics_action shows Character, Word, Line counts.
        # "Average Word Length" would be a new feature or an addition to this dialog.

        self.tools_menu.add_separator()

        # 3. Regex Utilities Sub-menu
        self.regex_utilities_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Regex Utilities", menu=self.regex_utilities_menu)
        self.regex_utilities_menu.add_command(label="Extract by Pattern (Regex)...", command=self.extract_pattern_dialog)
        self.regex_utilities_menu.add_command(label="Keep Lines Matching Regex...", command=lambda: self.filter_lines_by_regex_dialog(action_mode="keep"))
        self.regex_utilities_menu.add_command(label="Remove Lines Matching Regex...", command=lambda: self.filter_lines_by_regex_dialog(action_mode="remove"))
        # New item for Phase 2:
        # self.regex_utilities_menu.add_command(label="Test Regex Pattern...", command=self.test_regex_pattern_dialog)

        self.tools_menu.add_separator()

        # 4. Line Filters Sub-menu
        self.line_filters_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Line Filters", menu=self.line_filters_menu)
        self.line_filters_menu.add_command(label="Extract Lines by Length...", command=self.extract_lines_by_length_dialog) # Moved from Format
        self.line_filters_menu.add_command(label="Remove Blank Lines", command=self.remove_all_blank_lines) # Moved from Format -> Line Spacing
        # New item for Phase 2:
        # self.line_filters_menu.add_command(label="Keep Lines Containing Word...", command=self.keep_lines_containing_word_dialog)

        self.tools_menu.add_separator() # Separator before new direct tool
        self.tools_menu.add_command(label="QuickText Transformer...", command=self.open_quick_text_dialog) # New QuickText Feature
        self.tools_menu.add_command(label="Create Flow Diagram...", command=self.open_flow_diagram_dialog) # New Flow Diagram Feature
        self.tools_menu.add_command(label="View Data as Table (JSON/YAML)...", command=self.view_data_as_table_action) # New Table View Feature
        self.tools_menu.add_command(label="Convert CSV to Text Table", command=self.csv_to_text_table_action)
        self.tools_menu.add_command(label="Compare Two Lists...", command=self.open_compare_lists_dialog) # New Feature
        self.tools_menu.add_separator() # Separator before REST API Client
        self.tools_menu.add_command(label="REST API Client...", command=self.open_rest_api_client_dialog)
        self.tools_menu.add_command(label="SQL Parser...", command=self.open_sql_parser_dialog)
        self.tools_menu.add_command(label="Excel to HTML Site...", command=self.open_excel_to_html_dialog)
        self.tools_menu.add_command(label="Excel to CSVs & Stats...", command=self.open_excel_to_csv_stats_dialog)
        self.tools_menu.add_command(label="URL Manager...", command=self.open_url_manager_dialog) # New URL Manager tool
        self.tools_menu.add_separator() # Separator before Drawing Tool
        self.tools_menu.add_command(label="Drawing Tool...", command=self.open_drawing_tool_action)


        # 5. Compare Text (New, for Phase 2)
        # self.tools_menu.add_separator()
        # self.compare_text_menu = tk.Menu(self.tools_menu, tearoff=0)
        # self.tools_menu.add_cascade(label="Compare Text", menu=self.compare_text_menu)
        # self.compare_text_menu.add_command(label="Diff Two Selections...", command=self.diff_two_selections_action)
        # self.compare_text_menu.add_command(label="Find Common Lines...", command=self.find_common_lines_action)
        # self.compare_text_menu.add_command(label="Find Unique Lines in A/B...", command=self.find_unique_lines_action)


        # Search Menu
        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Search", menu=self.search_menu)
        self.search_menu.add_command(label="Find/Replace in Current File...", command=self.open_find_replace_dialog, accelerator="Ctrl+F")
        self.search_menu.add_command(label="Search in Files...", command=self.open_file_search_dialog, accelerator="Ctrl+Shift+F") # New
        self.search_menu.add_separator()
        self.search_menu.add_command(label="Go to Line...", command=self.prompt_go_to_line, accelerator="Ctrl+G")


        # View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Change Font...", command=self.open_font_dialog)
        self.view_menu.add_command(label="Keyword Highlighting...", command=self.open_keyword_highlight_dialog)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Toggle Line Numbers", command=self.toggle_line_numbers_action)
        self.view_menu.add_command(label="Toggle Notes Style", command=self.toggle_notes_style_action) # New menu item
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Toggle Filter Bar", command=self.toggle_filter_bar, accelerator="Ctrl+Shift+F")


        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Setup Drag & Drop for the notebook
        # The root window (self.root) should be an instance of TkinterDND.Tk()
        # or made DND-aware by the caller of TextEditor.
        self.notebook.drop_target_register(DND_FILES)
        self.notebook.dnd_bind('<<Drop>>', self._handle_drop_files) # Will create this method

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
        self.root.bind_all("<Control-g>", self.prompt_go_to_line) # Added Ctrl+G for Go to Line
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
            # Sync tab's notes style active state with global state before applying
            current_tab.tab_notes_style_active = self.notes_style_active

            if self.notes_style_active:
                # If global notes style is on, apply it to the current tab.
                # This will also clear other syntax/keyword highlights as per its implementation.
                current_tab.apply_notes_style_highlighting()
            else:
                # If global notes style is off, clear notes style from the current tab
                # and reapply other relevant highlights.
                current_tab.clear_notes_style_highlighting()

                # Apply keyword highlighting to newly focused tab if active
                if self.keyword_highlight_settings.get("active", False):
                    current_tab.apply_keyword_highlights(self.keyword_highlight_settings)

                # Apply syntax highlighting to newly focused tab if language is set
                if current_tab.current_language_name:
                    current_tab.apply_syntax_highlighting()
                else: # If no language, ensure syntax highlights are cleared
                    current_tab._clear_syntax_highlight_tags()

            # If filter bar is visible, update its display from the current tab's filter state
            # And re-apply the filter to the tab's view if necessary (e.g. if it wasn't filtered before)
            if self.filter_bar_frame.winfo_ismapped():
                self._is_updating_filter_bar_from_tab = True
                try:
                    self.filter_text_var.set(current_tab.tab_filter_str)
                    self.filter_case_var.set(current_tab.tab_filter_case_sensitive)
                    self.filter_invert_var.set(current_tab.tab_filter_invert)
                finally:
                    self._is_updating_filter_bar_from_tab = False

                # Ensure the tab's view reflects its stored filter state.
                # This is important if the tab was not active and its filter state was changed by other means,
                # or if it's the first time this tab is being shown with its filter.
                # apply_text_filter now reads directly from the tab's properties.
                current_tab.apply_text_filter()
            else:
                # If filter bar is not visible, but the tab has a filter active,
                # ensure its view is correctly filtered.
                if current_tab.is_tab_filtered_view or current_tab.tab_filter_str:
                    current_tab.apply_text_filter()


            # Update Find/Replace button states if dialog is open
            if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists():
                self.update_find_replace_button_states()

            # Update current line highlight for the new tab
            current_tab.update_current_line_highlight()


    def on_filter_settings_changed(self, *args):
        # This method is called when filter text or options in the filter bar change.

        # If the change was triggered by on_tab_changed updating the filter bar, do nothing here.
        if self._is_updating_filter_bar_from_tab:
            return

        current_tab = self.get_current_tab()
        if not current_tab:
            return

        # Update the current tab's specific filter attributes
        current_tab.tab_filter_str = self.filter_text_var.get()
        current_tab.tab_filter_case_sensitive = self.filter_case_var.get()
        current_tab.tab_filter_invert = self.filter_invert_var.get()

        # Apply the filter to the current tab using its newly set attributes
        current_tab.apply_text_filter()

        # Update Find/Replace button states if dialog is open, as filtering might affect editability
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
            if current_tab.is_tab_filtered_view and current_tab.tab_original_text_for_filter is not None:
                content_to_save = current_tab.tab_original_text_for_filter
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
            try:
                # Get plain text from clipboard
                plain_text = self.root.clipboard_get()

                # If there's a selection, delete it first (standard paste behavior)
                if text_area.tag_ranges(tk.SEL):
                    sel_first = text_area.index(tk.SEL_FIRST)
                    sel_last = text_area.index(tk.SEL_LAST)
                    text_area.delete(sel_first, sel_last)

                # Insert the plain text at the cursor
                text_area.insert(tk.INSERT, plain_text)
                text_area.see(tk.INSERT) # Ensure the insert position is visible
                text_area.event_generate("<<Modified>>") # Manually trigger modified
            except tk.TclError:
                # This can happen if clipboard is empty or contains non-text data
                # In this case, we can try to fall back to the default event_generate
                # or simply do nothing / show a status message.
                # For now, let's try event_generate as a fallback,
                # though it might paste formatted text if clipboard_get failed due to format.
                try:
                    text_area.event_generate("<<Paste>>")
                except tk.TclError:
                    pass # Truly nothing to paste or error during event generation
        return "break"

    def select_all_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            text_area.tag_add(tk.SEL, "1.0", tk.END)
            text_area.mark_set(tk.INSERT, "1.0")
            text_area.see(tk.INSERT)
        return "break"

    def copy_file_path_action(self, event=None):
        current_tab = self.get_current_tab()
        if current_tab and current_tab.current_file:
            try:
                filepath = os.path.abspath(current_tab.current_file)
                self.root.clipboard_clear()
                self.root.clipboard_append(filepath)
                # Optionally, provide feedback to the user, e.g., in the status bar
                # For now, no explicit feedback message beyond clipboard change.
                # self.status_label_file_path.config(text=f"Copied: {filepath}") # Example, might need a temporary message mechanism
            except Exception as e:
                # print(f"Error copying file path: {e}")
                # Optionally, show an error message to the user
                pass # Silently fail for now if abspath or clipboard ops fail
        else:
            # No current file or file is untitled, do nothing or provide feedback
            # print("No file path to copy for current tab.")
            pass
        return "break" # Consistent with other actions if bound to event

    def strip_clipboard_formatting_action(self, event=None):
        try:
            plain_text = self.root.clipboard_get()
            # Check if plain_text is not None and is a string,
            # as clipboard_get might return empty string for empty clipboard
            # or could potentially return other types if clipboard has non-text focus (less common for get()).
            if isinstance(plain_text, str): # Ensure it's text
                self.root.clipboard_clear()
                self.root.clipboard_append(plain_text)
                # Optional: Feedback to user, e.g., status bar message
                # self.update_status_bar_temporary_message("Clipboard formatting stripped.")
            # else: Clipboard contained something not convertible to plain text by clipboard_get()
            # or clipboard_get() itself raised TclError for non-text types before returning.
        except tk.TclError:
            # This typically means clipboard is empty or has content that
            # Tkinter cannot interpret as text (e.g., an image).
            # Silently pass, or provide feedback.
            # self.update_status_bar_temporary_message("Clipboard empty or content not text.")
            pass
        return "break" # If bound to an event

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

    def filter_lines_by_regex_dialog(self, action_mode: str, event=None): # Added action_mode
        text_widget = self.get_active_text_area()
        if not text_widget:
            return "break"

        dialog_title = "Keep Lines Matching Regex" if action_mode == "keep" else "Remove Lines Matching Regex"

        dialog = tk.Toplevel(self.root)
        dialog.title(dialog_title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Variables
        regex_var = tk.StringVar()
        case_insensitive_var = tk.BooleanVar(value=False)

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Regex Entry
        ttk.Label(main_frame, text="Regular Expression:").grid(row=0, column=0, sticky=tk.W, pady=2)
        regex_entry = ttk.Entry(main_frame, textvariable=regex_var, width=50)
        regex_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        regex_entry.focus_set()

        main_frame.columnconfigure(1, weight=1) # Make entry expandable

        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5,10))
        ttk.Checkbutton(options_frame, text="Case Insensitive", variable=case_insensitive_var).pack(side=tk.LEFT, anchor=tk.W)

        def on_apply():
            regex_str = regex_var.get()
            if not regex_str.strip():
                messagebox.showerror("Input Error", "Regular expression cannot be empty.", parent=dialog)
                regex_entry.focus_set()
                return

            try:
                re.compile(regex_str) # Validate regex compilation is possible
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid Regular Expression:\n{e}", parent=dialog)
                regex_entry.focus_set()
                return

            self.apply_filter_lines_by_regex( # Call the processing method
                regex_str,
                case_insensitive_var.get(),
                action_mode # Pass the mode ("keep" or "remove")
            )
            dialog.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tk.E, pady=(5,0))

        apply_button = ttk.Button(button_frame, text="Apply", command=on_apply)
        apply_button.pack(side=tk.RIGHT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=(0,5))

        dialog.bind("<Return>", lambda e: on_apply())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break"

    def apply_filter_lines_by_regex(self, regex_str: str, case_insensitive: bool, action_mode: str):
        """
        Filters lines in the current text area based on a regex pattern.
        Lines are either kept or removed based on whether they match the pattern.
        """
        text_widget = self.get_active_text_area()
        if not text_widget:
            return

        flags = 0
        if case_insensitive:
            flags = re.IGNORECASE

        try:
            compiled_regex = re.compile(regex_str, flags)
        except re.error as e:
            # This should ideally be caught by the dialog, but as a safeguard:
            messagebox.showerror("Regex Error", f"Invalid Regular Expression: {e}", parent=self.root)
            return

        def do_filter_lines(text_content):
            lines = text_content.splitlines(keepends=True)
            processed_lines = []
            # The `modified` flag for _process_text is about whether the final text is different from original.
            # Here, we construct the new text. _process_text will compare.

            for line_with_ending in lines:
                # Test the line content (without its newline character) against the regex
                line_content_for_match = line_with_ending.rstrip('\r\n')
                match_found = compiled_regex.search(line_content_for_match)

                if action_mode == "keep":
                    if match_found:
                        processed_lines.append(line_with_ending)
                elif action_mode == "remove":
                    if not match_found:
                        processed_lines.append(line_with_ending)

            return "".join(processed_lines)

        # Use the _process_text helper to handle selection or full document processing
        self._process_text(do_filter_lines)
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
            # Check if the current tab is in a filtered view
            if current_tab and current_tab.is_tab_filtered_view:
                self.find_dialog_replace_btn.config(state=tk.DISABLED)
                self.find_dialog_replace_all_btn.config(state=tk.DISABLED)
            else: # Not filtered or no tab
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

    def extract_lines_by_length_dialog(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area:
            return "break" # Or just return, if not directly from a binding

        dialog = tk.Toplevel(self.root)
        dialog.title("Extract Lines by Length")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Variables
        length_var = tk.IntVar(value=10) # Default length
        mode_var = tk.StringVar(value="longer") # longer, equal, shorter
        keep_empty_var = tk.BooleanVar(value=False) # Default: remove empty lines

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Length Entry
        ttk.Label(main_frame, text="Length:").grid(row=0, column=0, sticky=tk.W, pady=2)
        length_entry = ttk.Spinbox(main_frame, from_=0, to=10000, textvariable=length_var, width=7)
        length_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        length_entry.focus_set()

        # Mode Radio Buttons
        mode_frame = ttk.LabelFrame(main_frame, text="Mode", padding=5)
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
        ttk.Radiobutton(mode_frame, text="Shorter than length", variable=mode_var, value="shorter").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Equal to length", variable=mode_var, value="equal").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Longer than length", variable=mode_var, value="longer").pack(anchor=tk.W)

        # Keep Empty Lines Checkbox
        ttk.Checkbutton(main_frame, text="Keep empty lines (if they meet length criteria for 'equal to 0')", variable=keep_empty_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        def on_apply():
            try:
                length = length_var.get()
                mode = mode_var.get()
                keep_empty = keep_empty_var.get()

                if length < 0:
                    messagebox.showerror("Invalid Length", "Length cannot be negative.", parent=dialog)
                    return

                self.apply_extract_lines_by_length(length, mode, keep_empty)
                dialog.destroy()
            except tk.TclError: # Handles if spinbox has non-integer
                messagebox.showerror("Invalid Input", "Please enter a valid integer for length.", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=dialog)


        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tk.E, pady=(10,0))
        ttk.Button(button_frame, text="Apply", command=on_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)

        dialog.bind("<Return>", lambda e: on_apply())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break" # If called from a key binding

    def apply_extract_lines_by_length(self, length_val: int, mode: str, keep_empty: bool):
        """
        Applies the line extraction based on length criteria.
        mode can be "shorter", "equal", "longer".
        keep_empty: If True, empty lines are kept if they meet the criteria
                    (e.g. mode="equal", length_val=0).
                    If False, empty lines are always removed unless mode="equal",
                    length_val=0, and keep_empty is True.
                    More simply: if keep_empty is False, non-blank lines are processed.
                                 if keep_empty is True, all lines (including blank) are processed.
                                 This interpretation of "keep_empty" might need refinement.
                                 Let's make it simpler: "Process empty lines"
                                 If true, empty lines (length 0) are subject to the filter.
                                 If false, empty lines are discarded UNLESS the filter is specifically for length 0.

        A clearer definition for "keep_empty_lines":
        If False (default): Blank lines (after stripping whitespace) are removed before length filtering,
                            UNLESS the filter is specifically for length 0 (e.g., "equal to 0").
        If True: Blank lines are treated as lines of length 0 and are subject to the length filter.
        """

        def do_extract(text):
            lines = text.splitlines(keepends=True) # Keep original line endings for reconstruction
            processed_lines = []
            for line_with_ending in lines:
                # Determine content for length check (stripping temporary for length, but keep original for output)
                content_for_length_check = line_with_ending.rstrip('\r\n') # Content without any newline
                line_is_blank_after_strip = not content_for_length_check.strip()

                if not keep_empty and line_is_blank_after_strip:
                    # If not keeping empty lines, and this line is blank (after strip),
                    # only consider it if the filter is explicitly for length 0.
                    if not (mode == "equal" and length_val == 0):
                        continue # Skip this blank line

                current_line_length = len(content_for_length_check)
                match = False
                if mode == "shorter":
                    if current_line_length < length_val:
                        match = True
                elif mode == "equal":
                    if current_line_length == length_val:
                        match = True
                elif mode == "longer":
                    if current_line_length > length_val:
                        match = True

                if match:
                    processed_lines.append(line_with_ending)

            return "".join(processed_lines)

        self._process_text(do_extract)

    def pad_lines_dialog(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area:
            return "break" # Or just return, if not directly from a binding

        dialog = tk.Toplevel(self.root)
        dialog.title("Pad Lines")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Variables
        target_length_var = tk.IntVar(value=80)  # Default target length
        pad_char_var = tk.StringVar(value=" ")    # Default padding character
        alignment_var = tk.StringVar(value="right") # "left", "right", "center"

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Target Length Entry
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        ttk.Label(entry_frame, text="Target Length:").pack(side=tk.LEFT, padx=(0,5))
        length_entry = ttk.Spinbox(entry_frame, from_=1, to=10000, textvariable=target_length_var, width=7)
        length_entry.pack(side=tk.LEFT, padx=5)
        length_entry.focus_set()

        # Padding Character Entry
        ttk.Label(entry_frame, text="Padding Character:").pack(side=tk.LEFT, padx=(10,5))
        pad_char_entry = ttk.Entry(entry_frame, textvariable=pad_char_var, width=3)
        pad_char_entry.pack(side=tk.LEFT, padx=5)

        # Alignment Radio Buttons
        align_frame = ttk.LabelFrame(main_frame, text="Alignment", padding=5)
        align_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(align_frame, text="Left Align (Pad Right)", variable=alignment_var, value="left").pack(anchor=tk.W)
        ttk.Radiobutton(align_frame, text="Right Align (Pad Left)", variable=alignment_var, value="right").pack(anchor=tk.W)
        ttk.Radiobutton(align_frame, text="Center Align (Pad Both Sides)", variable=alignment_var, value="center").pack(anchor=tk.W)

        def on_apply():
            try:
                target_length = target_length_var.get()
                pad_char_full = pad_char_var.get()
                alignment = alignment_var.get()

                if target_length < 0: # Spinbox 'from_' should prevent this, but good check
                    messagebox.showerror("Invalid Length", "Target length cannot be negative.", parent=dialog)
                    return

                pad_char = " " # Default if empty
                if len(pad_char_full) > 0:
                    pad_char = pad_char_full[0] # Use only the first character
                    if len(pad_char_full) > 1:
                         pad_char_var.set(pad_char) # Update UI if it was too long
                         messagebox.showwarning("Padding Character Truncated",
                                               "Padding character has been truncated to its first character.",
                                               parent=dialog)
                else: # User cleared the padding character field
                    pad_char_var.set(" ") # Reset to space if empty

                self.apply_pad_lines(target_length, pad_char, alignment)
                dialog.destroy()
            except tk.TclError: # Handles if spinbox has non-integer (though Spinbox should prevent)
                messagebox.showerror("Invalid Input", "Please enter a valid integer for target length.", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=dialog)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0), side=tk.BOTTOM) # Ensure buttons are at the bottom
        ttk.Button(button_frame, text="Apply", command=on_apply).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(0,5))

        dialog.bind("<Return>", lambda e: on_apply())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break"

    def apply_pad_lines(self, target_length: int, pad_char: str, alignment: str):
        """
        Applies padding to lines to meet the target_length.
        alignment can be "left", "right", "center".
        pad_char is a single character used for padding.
        """
        if not pad_char: # Should be caught by dialog, but as a safeguard
            pad_char = " "

        def do_pad(text):
            lines = text.splitlines(keepends=True) # Keep endings for proper reconstruction
            processed_lines = []
            for line_with_ending in lines:
                content_part = line_with_ending.rstrip('\r\n')
                ending_part = line_with_ending[len(content_part):] # Extract the original line ending

                if len(content_part) < target_length:
                    if alignment == "left":
                        padded_content = content_part.ljust(target_length, pad_char)
                    elif alignment == "right":
                        padded_content = content_part.rjust(target_length, pad_char)
                    elif alignment == "center":
                        padded_content = content_part.center(target_length, pad_char)
                    else: # Should not happen if dialog validates alignment
                        padded_content = content_part
                    processed_lines.append(padded_content + ending_part)
                else:
                    processed_lines.append(line_with_ending) # Line is already long enough or longer

            return "".join(processed_lines)

        self._process_text(do_pad)

    def remove_punctuation_action(self, event=None):
        """Removes all standard punctuation from the selected text or the entire document."""

        # Create a translation table that maps each punctuation character to None (for deletion)
        # This is done once, can be a global or class constant if preferred for performance,
        # but defining it here is fine for simplicity.
        translator = str.maketrans('', '', string.punctuation)

        def do_remove_punctuation(text):
            return text.translate(translator)

        self._process_text(do_remove_punctuation)
        return "break" # If called from a binding, though menu items don't need it

    def extract_uppercase_words_action(self, event=None):
        text_widget = self.get_active_text_area()
        if not text_widget:
            return "break"

        try:
            source_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: # No selection, use full text
            source_text = text_widget.get("1.0", tk.END + "-1c")

        if not source_text.strip():
            messagebox.showinfo("Extract UPPERCASE Words", "No text to process.", parent=self.root)
            return "break"

        # Find all words consisting of 2 or more uppercase letters.
        # \b ensures word boundaries. [A-Z] matches any uppercase letter. {2,} means 2 or more occurrences.
        uppercase_words = re.findall(r'\b[A-Z]{2,}\b', source_text)

        if not uppercase_words:
            messagebox.showinfo("Extract UPPERCASE Words", "No uppercase words (2+ chars) found.", parent=self.root)
            return "break"

        # Create a unique, sorted list
        unique_sorted_words = sorted(list(set(uppercase_words)))
        result_text = "\n".join(unique_sorted_words)

        # Display in a new dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Extracted UPPERCASE Words")
        dialog.transient(self.root)
        dialog.grab_set() # Make it modal for now
        dialog.geometry("400x300")

        text_frame = ttk.Frame(dialog, padding=5)
        text_frame.pack(expand=True, fill=tk.BOTH)

        result_display_text = tk.Text(text_frame, wrap=tk.WORD, height=10, width=40)
        result_display_text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, pady=(0,5))

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=result_display_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0,5))
        result_display_text.config(yscrollcommand=scrollbar.set)

        result_display_text.insert(tk.END, result_text)
        result_display_text.config(state=tk.DISABLED) # Make it read-only

        button_frame = ttk.Frame(dialog, padding=(5,0,5,5))
        button_frame.pack(fill=tk.X)

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
            messagebox.showinfo("Copied", "Word list copied to clipboard.", parent=dialog)

        ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break"

    def count_word_frequency_action(self, event=None):
        text_widget = self.get_active_text_area()
        if not text_widget:
            return "break"

        try:
            source_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: # No selection, use full text
            source_text = text_widget.get("1.0", tk.END + "-1c")

        if not source_text.strip():
            messagebox.showinfo("Word Frequency", "No text to process.", parent=self.root)
            return "break"

        # Pre-processing: lowercase and remove punctuation
        processed_text = source_text.lower()
        translator = str.maketrans('', '', string.punctuation)
        processed_text = processed_text.translate(translator)

        # Tokenize into words
        words = re.findall(r'\b\w+\b', processed_text)

        if not words:
            messagebox.showinfo("Word Frequency", "No words found to count.", parent=self.root)
            return "break"

        # Count frequencies
        word_counts = collections.Counter(words)

        # Sort by frequency (descending), then by word (ascending)
        sorted_word_counts = sorted(word_counts.items(), key=lambda item: (-item[1], item[0]))

        result_text_lines = [f"{word}: {count}" for word, count in sorted_word_counts]
        result_text_display = "\n".join(result_text_lines)
        # For clipboard, also include total unique words and total words
        total_words = len(words)
        total_unique_words = len(sorted_word_counts)
        clipboard_header = f"Total Words: {total_words}\nUnique Words: {total_unique_words}\n\nFrequency:\n"
        result_text_clipboard = clipboard_header + result_text_display


        # Display in a new dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Word Frequency Count")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("450x350") # Adjusted size

        text_frame = ttk.Frame(dialog, padding=5)
        text_frame.pack(expand=True, fill=tk.BOTH)

        header_label = ttk.Label(text_frame, text=f"Total Words: {total_words} | Unique Words: {total_unique_words}")
        header_label.pack(pady=(0,5))

        result_display_text_widget = tk.Text(text_frame, wrap=tk.WORD, height=10, width=50)
        result_display_text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, pady=(0,5))

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=result_display_text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0,5))
        result_display_text_widget.config(yscrollcommand=scrollbar.set)

        result_display_text_widget.insert(tk.END, result_text_display)
        result_display_text_widget.config(state=tk.DISABLED)

        button_frame = ttk.Frame(dialog, padding=(5,0,5,5))
        button_frame.pack(fill=tk.X)

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text_clipboard) # Copy the version with header
            messagebox.showinfo("Copied", "Word frequency list copied to clipboard.", parent=dialog)

        ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break"

    def shuffle_lines_action(self, event=None):
        """Randomly shuffles the order of lines in the selected text or the entire document."""

        def do_shuffle_lines(text):
            if not text.strip(): # Avoid shuffling if only whitespace or empty
                return text

            lines = text.splitlines(keepends=True)
            random.shuffle(lines)
            return "".join(lines)

        self._process_text(do_shuffle_lines)
        return "break" # If called from a binding

    def text_statistics_action(self, event=None):
        text_widget = self.get_active_text_area()
        if not text_widget:
            return "break"

        try:
            source_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            selection_info_str = "Selected Text Statistics:"
        except tk.TclError: # No selection, use full text
            source_text = text_widget.get("1.0", tk.END + "-1c")
            selection_info_str = "Full Document Statistics:"

        if not source_text: # Handles empty string (e.g. if selection was empty or document empty)
            messagebox.showinfo("Text Statistics", "No text to analyze.", parent=self.root)
            return "break"

        # Calculations
        char_count_with_spaces_and_newlines = len(source_text)

        # Character count without any whitespace (spaces, tabs, newlines, etc.)
        char_count_no_whitespace = len("".join(source_text.split()))

        # Word count using regex for sequences of word characters
        words = re.findall(r'\b\w+\b', source_text)
        word_count = len(words)

        # Line count: Number of newline characters + 1 if text is not empty and doesn't end with a newline.
        # A more intuitive line count is often len(source_text.splitlines()) if you consider each line by content.
        # Or, for physical lines as they might appear if each \n starts a new line:
        actual_line_count = 0
        if source_text: # Only count lines if there's text
            actual_line_count = source_text.count('\n')
            if not source_text.endswith('\n'):
                actual_line_count += 1

        # Format results
        stats_display_list = [
            selection_info_str,
            f"  Characters (total): {char_count_with_spaces_and_newlines}",
            f"  Characters (no whitespace): {char_count_no_whitespace}",
            f"  Words: {word_count}",
            f"  Lines: {actual_line_count}",
        ]
        stats_display_str = "\n".join(stats_display_list)

        # Display in a new dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Text Statistics")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("400x220")

        text_frame = ttk.Frame(dialog, padding=10)
        text_frame.pack(expand=True, fill=tk.BOTH)

        result_display_text_widget = tk.Text(text_frame, wrap=tk.NONE, height=7, width=45)
        result_display_text_widget.pack(expand=True, fill=tk.BOTH, pady=(0,5))

        result_display_text_widget.insert(tk.END, stats_display_str)
        result_display_text_widget.config(state=tk.DISABLED)

        button_frame = ttk.Frame(dialog, padding=(5,0,5,5))
        button_frame.pack(fill=tk.X)

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(stats_display_str)
            messagebox.showinfo("Copied", "Statistics copied to clipboard.", parent=dialog)

        ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break"

    def extract_unique_words_dialog(self, event=None):
        text_widget = self.get_active_text_area()
        if not text_widget: # Should not happen if menu item is active
            return "break"

        dialog = tk.Toplevel(self.root)
        dialog.title("Extract Unique Words")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Variables
        case_sensitive_var = tk.BooleanVar(value=False) # Default: case-insensitive
        sort_alpha_var = tk.BooleanVar(value=True)    # Default: sort alphabetically
        # Punctuation removal is implied/default for word extraction

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Checkbutton(main_frame, text="Case Sensitive", variable=case_sensitive_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(main_frame, text="Sort Alphabetically", variable=sort_alpha_var).pack(anchor=tk.W, pady=2)

        def on_apply():
            self.apply_extract_unique_words(
                case_sensitive=case_sensitive_var.get(),
                sort_alpha=sort_alpha_var.get()
            )
            dialog.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0), side=tk.BOTTOM)

        apply_button = ttk.Button(button_frame, text="Extract & Show", command=on_apply)
        apply_button.pack(side=tk.RIGHT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=(0,5))

        dialog.bind("<Return>", lambda e: on_apply())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break"

    def apply_extract_unique_words(self, case_sensitive: bool, sort_alpha: bool):
        text_widget = self.get_active_text_area()
        if not text_widget:
            return

        try:
            source_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: # No selection, use full text
            source_text = text_widget.get("1.0", tk.END + "-1c")

        if not source_text.strip():
            messagebox.showinfo("Extract Unique Words", "No text to process.", parent=self.root)
            return

        # Pre-processing: remove punctuation (standard)
        translator = str.maketrans('', '', string.punctuation)
        processed_text = source_text.translate(translator)

        # Case sensitivity
        if not case_sensitive:
            processed_text = processed_text.lower()

        # Tokenize into words
        words = re.findall(r'\b\w+\b', processed_text)

        if not words:
            messagebox.showinfo("Extract Unique Words", "No words found.", parent=self.root)
            return

        # Get unique words
        unique_words = list(set(words))

        # Sort if requested
        if sort_alpha:
            # Sort case-insensitively if the original extraction was case-insensitive,
            # otherwise sort case-sensitively.
            if not case_sensitive:
                unique_words.sort(key=lambda x: x.lower()) # Sorts "a", "B", "c" correctly if input was lowercased
            else:
                unique_words.sort()

        result_text_display = "\n".join(unique_words)

        # For clipboard, also include total unique words
        total_unique_words = len(unique_words)
        clipboard_header = f"Total Unique Words: {total_unique_words}\n\n"
        result_text_clipboard = clipboard_header + result_text_display

        # Display in a new dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Extracted Unique Words")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("400x300")

        text_frame = ttk.Frame(dialog, padding=5)
        text_frame.pack(expand=True, fill=tk.BOTH)

        header_label = ttk.Label(text_frame, text=f"Unique Words Found: {total_unique_words}")
        header_label.pack(pady=(0,5))

        result_display_text_widget = tk.Text(text_frame, wrap=tk.WORD, height=10, width=40)
        result_display_text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, pady=(0,5))

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=result_display_text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0,5))
        result_display_text_widget.config(yscrollcommand=scrollbar.set)

        result_display_text_widget.insert(tk.END, result_text_display)
        result_display_text_widget.config(state=tk.DISABLED)

        button_frame = ttk.Frame(dialog, padding=(5,0,5,5))
        button_frame.pack(fill=tk.X)

        def copy_to_clipboard_unique():
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text_clipboard)
            messagebox.showinfo("Copied", "Unique word list copied to clipboard.", parent=dialog)

        ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard_unique).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')


    def add_prefix_suffix_dialog(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area:
            return "break"

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Prefix/Suffix to Lines")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Variables
        prefix_var = tk.StringVar()
        suffix_var = tk.StringVar()
        skip_empty_var = tk.BooleanVar(value=False) # Default: process all lines

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Prefix Entry
        ttk.Label(main_frame, text="Prefix:").grid(row=0, column=0, sticky=tk.W, pady=2)
        prefix_entry = ttk.Entry(main_frame, textvariable=prefix_var, width=40)
        prefix_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        prefix_entry.focus_set()

        # Suffix Entry
        ttk.Label(main_frame, text="Suffix:").grid(row=1, column=0, sticky=tk.W, pady=2)
        suffix_entry = ttk.Entry(main_frame, textvariable=suffix_var, width=40)
        suffix_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)

        # Skip Empty Lines Checkbox
        ttk.Checkbutton(main_frame, text="Skip empty lines (lines with only whitespace)", variable=skip_empty_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        main_frame.columnconfigure(1, weight=1) # Make entry fields expandable

        def on_apply():
            # No specific validation needed for prefix/suffix (can be empty)
            # skip_empty is boolean
            self.apply_add_prefix_suffix(
                prefix_var.get(),
                suffix_var.get(),
                skip_empty_var.get()
            )
            dialog.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tk.E, pady=(10,0))
        ttk.Button(button_frame, text="Apply", command=on_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)

        dialog.bind("<Return>", lambda e: on_apply())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break"

    def apply_add_prefix_suffix(self, prefix_str: str, suffix_str: str, skip_empty: bool):
        """
        Applies prefix and/or suffix to each line.
        """
        def do_add_prefix_suffix(text):
            lines = text.splitlines(keepends=True)
            processed_lines = []
            for line_with_ending in lines:
                content_part = line_with_ending.rstrip('\r\n')
                ending_part = line_with_ending[len(content_part):] # Extracts the original line ending(s)

                if skip_empty and not content_part.strip():
                    # If skip_empty is true and the line content (sans newline) is blank,
                    # keep the original line with its ending.
                    processed_lines.append(line_with_ending)
                else:
                    modified_content = prefix_str + content_part + suffix_str
                    processed_lines.append(modified_content + ending_part)

            return "".join(processed_lines)

        self._process_text(do_add_prefix_suffix)

    def extract_pattern_dialog(self, event=None):
        text_widget = self.get_active_text_area()
        if not text_widget:
            return "break"

        dialog = tk.Toplevel(self.root)
        dialog.title("Extract by Pattern (Regex)")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False) # Consider allowing resize if custom regex is long

        # Predefined patterns (name: pattern_string)
        # These are examples; more can be added or refined.
        predefined_patterns = {
            "Email Addresses": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "URLs (http/https)": r"https?://[^\s/$.?#].[^\s]*",
            "Phone Numbers (North American basic)": r"\(?\b[2-9][0-9]{2}\b\)?[-. ]?\b[2-9][0-9]{2}\b[-. ]?\b[0-9]{4}\b",
            "Numbers (Integers/Decimals)": r"-?\b\d+(\.\d+)?\b",
            "Dates (YYYY-MM-DD)": r"\b\d{4}-\d{2}-\d{2}\b",
            "Dates (MM/DD/YYYY)": r"\b\d{1,2}/\d{1,2}/\d{4}\b",
            "IP Addresses (IPv4)": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            "-- Custom Regex --": "custom"
        }
        pattern_names = list(predefined_patterns.keys())

        # Variables
        selected_pattern_name_var = tk.StringVar(value=pattern_names[0])
        custom_regex_var = tk.StringVar()
        case_insensitive_var = tk.BooleanVar(value=False)
        unique_only_var = tk.BooleanVar(value=True)

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Pattern Selection
        ttk.Label(main_frame, text="Select Pattern:").grid(row=0, column=0, sticky=tk.W, pady=(0,2))
        pattern_combobox = ttk.Combobox(main_frame, textvariable=selected_pattern_name_var, values=pattern_names, state="readonly", width=40)
        pattern_combobox.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=(0,2))

        # Custom Regex Entry (conditionally visible)
        custom_regex_label = ttk.Label(main_frame, text="Custom Regex:")
        custom_regex_entry = ttk.Entry(main_frame, textvariable=custom_regex_var, width=40)

        def on_pattern_select(event=None):
            if selected_pattern_name_var.get() == "-- Custom Regex --":
                custom_regex_label.grid(row=1, column=0, sticky=tk.W, pady=(5,2))
                custom_regex_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=(5,2))
                custom_regex_entry.focus_set()
            else:
                custom_regex_label.grid_remove()
                custom_regex_entry.grid_remove()

        pattern_combobox.bind("<<ComboboxSelected>>", on_pattern_select)
        on_pattern_select() # Initial call to set visibility

        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Checkbutton(options_frame, text="Case Insensitive", variable=case_insensitive_var).pack(side=tk.LEFT, anchor=tk.W, padx=(0,10))
        ttk.Checkbutton(options_frame, text="Unique Matches Only", variable=unique_only_var).pack(side=tk.LEFT, anchor=tk.W)

        def on_apply():
            pattern_name = selected_pattern_name_var.get()
            regex_to_use = ""
            if pattern_name == "-- Custom Regex --":
                regex_to_use = custom_regex_var.get()
                if not regex_to_use.strip():
                    messagebox.showerror("Input Error", "Custom regex cannot be empty.", parent=dialog)
                    return
            else:
                regex_to_use = predefined_patterns[pattern_name]

            try:
                # Attempt to compile to catch basic regex errors early for custom regex
                re.compile(regex_to_use)
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid Regular Expression: {e}", parent=dialog)
                return

            self.apply_extract_pattern(
                regex_pattern_str=regex_to_use,
                case_insensitive=case_insensitive_var.get(),
                unique_only=unique_only_var.get()
            )
            dialog.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tk.E, pady=(10,0))
        ttk.Button(button_frame, text="Extract & Show", command=on_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)

        dialog.bind("<Return>", lambda e: on_apply())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        main_frame.columnconfigure(1, weight=1)

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        return "break"

    def csv_to_text_table_action(self, event=None):
        """
        Converts selected CSV text or full document content into a
        nicely formatted plain text table.
        """
        import csv
        import io

        def do_csv_to_table(text_content):
            if not text_content.strip():
                return text_content # Return original if empty or only whitespace

            try:
                csv_file = io.StringIO(text_content)
                raw_rows = []
                reader = csv.reader(csv_file, delimiter=',') # Assuming comma delimiter
                try:
                    for row in reader:
                        raw_rows.append(row)
                except csv.Error as e:
                    messagebox.showerror("CSV Parsing Error", f"Could not parse CSV data: {e}\n\nNo changes made.", parent=self.root)
                    return text_content

                if not raw_rows:
                    return text_content

                # Determine column widths
                # Handle potentially empty raw_rows or rows with varying numbers of columns
                if not any(raw_rows): # if all rows are empty or raw_rows itself is empty
                    return text_content

                num_cols = 0
                for row in raw_rows: # Find max number of columns in any row
                    num_cols = max(num_cols, len(row))

                if num_cols == 0: # All rows were empty lists
                    return text_content

                col_widths = [0] * num_cols

                for row in raw_rows:
                    current_row_padded = row + [""] * (num_cols - len(row)) # Pad short rows
                    for i, cell in enumerate(current_row_padded):
                        col_widths[i] = max(col_widths[i], len(str(cell)))

                formatted_table_lines = []

                # Padded content width = width + 2 (for spaces like ' content ')
                padded_col_widths = [w + 2 for w in col_widths]
                separator_line = "+" + "+".join(['-' * pw for pw in padded_col_widths]) + "+"

                # Format rows (including header)
                for row_idx, row_data in enumerate(raw_rows):
                    formatted_row_parts = []
                    current_row_cells = row_data + [""] * (num_cols - len(row_data))

                    for i, cell_content in enumerate(current_row_cells):
                        # Pad with 1 space on each side: " content ".ljust(width+2)
                        padded_cell = (" " + str(cell_content) + " ").ljust(padded_col_widths[i])
                        formatted_row_parts.append(padded_cell)
                    formatted_table_lines.append("|" + "|".join(formatted_row_parts) + "|")

                    if row_idx == 0: # Add separator after the header row
                        formatted_table_lines.append(separator_line)

                return "\n".join(formatted_table_lines)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to convert CSV to table: {e}", parent=self.root)
                return text_content

        self._process_text(do_csv_to_table)

    def apply_extract_pattern(self, regex_pattern_str: str, case_insensitive: bool, unique_only: bool):
        text_widget = self.get_active_text_area()
        if not text_widget:
            return

    def open_compare_lists_dialog(self, event=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Compare Two Lists")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False) # Keep it fixed size for now

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # List 1 Input Area
        ttk.Label(main_frame, text="List 1:").grid(row=0, column=0, sticky=tk.NW, pady=(0, 5))
        list1_text_area = tk.Text(main_frame, width=40, height=10, wrap=tk.WORD, undo=True)
        list1_text_area.grid(row=1, column=0, padx=(0, 5), sticky="nsew")
        list1_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=list1_text_area.yview)
        list1_scrollbar.grid(row=1, column=1, sticky="ns")
        list1_text_area.config(yscrollcommand=list1_scrollbar.set)

        # List 2 Input Area
        ttk.Label(main_frame, text="List 2:").grid(row=0, column=2, sticky=tk.NW, pady=(0, 5), padx=(5,0))
        list2_text_area = tk.Text(main_frame, width=40, height=10, wrap=tk.WORD, undo=True)
        list2_text_area.grid(row=1, column=2, padx=(5, 0), sticky="nsew")
        list2_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=list2_text_area.yview)
        list2_scrollbar.grid(row=1, column=3, sticky="ns")
        list2_text_area.config(yscrollcommand=list2_scrollbar.set)

        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(2, weight=1)

        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=2, column=0, columnspan=4, pady=(10, 5), sticky=tk.W)
        case_sensitive_var = tk.BooleanVar(value=False) # Default: case-insensitive
        case_sensitive_check = ttk.Checkbutton(options_frame, text="Case Sensitive Comparison", variable=case_sensitive_var)
        case_sensitive_check.pack(side=tk.LEFT)

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(10,0), sticky=tk.E)

        def on_compare():
            list1_content = list1_text_area.get("1.0", tk.END + "-1c")
            list2_content = list2_text_area.get("1.0", tk.END + "-1c")
            is_case_sensitive = case_sensitive_var.get()

            dialog.destroy() # Close the input dialog after comparison is initiated
            self._perform_and_show_list_comparison(list1_content, list2_content, is_case_sensitive)

        compare_button = ttk.Button(button_frame, text="Compare", command=on_compare)
        compare_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
        close_button.pack(side=tk.LEFT)

        # Set initial focus (e.g., to the first text area)
        list1_text_area.focus_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

    def _perform_and_show_list_comparison(self, list1_str: str, list2_str: str, case_sensitive: bool):
        # Process List 1
        lines1_raw = list1_str.splitlines()
        processed_lines1 = []
        for line in lines1_raw:
            stripped_line = line.strip()
            if stripped_line: # Ignore empty lines after stripping
                processed_lines1.append(stripped_line if case_sensitive else stripped_line.lower())

        # Process List 2
        lines2_raw = list2_str.splitlines()
        processed_lines2 = []
        for line in lines2_raw:
            stripped_line = line.strip()
            if stripped_line: # Ignore empty lines after stripping
                processed_lines2.append(stripped_line if case_sensitive else stripped_line.lower())

        set1 = set(processed_lines1)
        set2 = set(processed_lines2)

        common_lines = sorted(list(set1.intersection(set2)))
        in_list1_only = sorted(list(set1.difference(set2)))
        in_list2_only = sorted(list(set2.difference(set2)))

        # For display, unique lines should retain their original casing if comparison was case-insensitive
        # Common lines will be shown in the case they were matched (lowercase if case-insensitive)

        in_list1_only_display = []
        in_list2_only_display = []

        if not case_sensitive:
            # Create maps from lowercase to original stripped lines for unique items
            # This helps display the original form of unique lines.
            original_lines1_map = {line.strip().lower(): line.strip() for line in lines1_raw if line.strip()}
            original_lines2_map = {line.strip().lower(): line.strip() for line in lines2_raw if line.strip()}

            for lc_line in in_list1_only:
                in_list1_only_display.append(original_lines1_map.get(lc_line, lc_line)) # Fallback to lc_line if somehow not in map
            for lc_line in in_list2_only:
                in_list2_only_display.append(original_lines2_map.get(lc_line, lc_line))
            # common_lines are already in the correct (lower)case for matching
            in_list1_only_display.sort() # Re-sort after potential case changes from map lookup
            in_list2_only_display.sort()

        else: # Case sensitive, lists already contain original (or relevant) casing.
            in_list1_only_display = in_list1_only
            in_list2_only_display = in_list2_only
            # common_lines are already sorted and in original case

        self._show_list_comparison_results(
            common_lines,
            in_list1_only_display,
            in_list2_only_display,
            case_sensitive # Pass the flag to the results dialog for context
        )

    def _show_list_comparison_results(self, common_lines, list1_unique, list2_unique, case_sensitive_used):
        dialog = tk.Toplevel(self.root)
        dialog.title("List Comparison Results")
        dialog.transient(self.root)
        dialog.grab_set() # Make modal
        dialog.geometry("600x400") # Initial size, can be adjusted

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Status/Info Label
        case_info = "Case Sensitive" if case_sensitive_used else "Case Insensitive"
        info_label_text = f"Comparison Mode: {case_info}"
        ttk.Label(main_frame, text=info_label_text).pack(pady=(0, 5), anchor=tk.W)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True, fill=tk.BOTH, pady=5)

        def create_results_tab(tab_parent, title, lines_list):
            frame = ttk.Frame(tab_parent, padding=5)
            tab_parent.add(frame, text=f"{title} ({len(lines_list)})")

            text_area = tk.Text(frame, wrap=tk.WORD, height=10, width=50, undo=False) # No undo needed for display
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_area.yview)
            text_area.config(yscrollcommand=scrollbar.set)

            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

            if lines_list:
                text_area.insert(tk.END, "\n".join(lines_list))
            else:
                text_area.insert(tk.END, "-- No lines --")
            text_area.config(state=tk.DISABLED) # Read-only
            return text_area # Return for potential use by copy function

        tab1_text = create_results_tab(notebook, "Common Lines", common_lines)
        tab2_text = create_results_tab(notebook, "Only in List 1", list1_unique)
        tab3_text = create_results_tab(notebook, "Only in List 2", list2_unique)

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0))

        def on_copy_all():
            results_summary = []
            results_summary.append(f"Comparison Mode: {case_info}\n")

            results_summary.append(f"--- Common Lines ({len(common_lines)}) ---")
            results_summary.extend(common_lines if common_lines else ["-- No lines --"])
            results_summary.append("\n") # Add a blank line for separation

            results_summary.append(f"--- Only in List 1 ({len(list1_unique)}) ---")
            results_summary.extend(list1_unique if list1_unique else ["-- No lines --"])
            results_summary.append("\n")

            results_summary.append(f"--- Only in List 2 ({len(list2_unique)}) ---")
            results_summary.extend(list2_unique if list2_unique else ["-- No lines --"])

            full_results_str = "\n".join(results_summary)

            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(full_results_str)
                messagebox.showinfo("Results Copied", "All comparison results copied to clipboard.", parent=dialog)
            except tk.TclError:
                messagebox.showerror("Error", "Could not copy results to clipboard.", parent=dialog)

        copy_button = ttk.Button(button_frame, text="Copy All Results", command=on_copy_all)
        copy_button.pack(side=tk.LEFT, padx=(0,5))

        close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
        close_button.pack(side=tk.RIGHT) # Align to right

        dialog.update_idletasks()
        # Center dialog relative to root, or the input dialog if it were still accessible
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        # Ensure the results dialog stays on top until closed.
        dialog.wait_window()

    def apply_extract_pattern(self, regex_pattern_str: str, case_insensitive: bool, unique_only: bool):
        text_widget = self.get_active_text_area()
        if not text_widget:
            return

        try:
            source_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: # No selection, use full text
            source_text = text_widget.get("1.0", tk.END + "-1c")

        if not source_text.strip():
            messagebox.showinfo("Extract by Pattern", "No text to process.", parent=self.root)
            return

        try:
            regex_flags = 0
            if case_insensitive:
                regex_flags = re.IGNORECASE

            compiled_regex = re.compile(regex_pattern_str, flags=regex_flags)
            matches = compiled_regex.findall(source_text)

        except re.error as e:
            messagebox.showerror("Regex Error", f"Error during regex execution: {e}", parent=self.root)
            return
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during pattern matching: {e}", parent=self.root)
            return

        if not matches:
            messagebox.showinfo("Extract by Pattern", "No matches found for the given pattern.", parent=self.root)
            return

        if unique_only:
            # Using dict.fromkeys to preserve order of first appearance for uniques
            # then converting back to list. For simple uniqueness, list(set(matches)) is fine
            # but this preserves order if that's ever a desired nuance.
            processed_matches = list(dict.fromkeys(matches))
        else:
            processed_matches = matches

        # If findall returns tuples (for regexes with capture groups), join them.
        # For now, assume findall returns strings or list of strings directly.
        # If it returns tuples, e.g. for r"(group1)(group2)", matches would be [('g1a','g2a'), ('g1b','g2b')]
        # We might want to display them differently or join tuple elements.
        # For simplicity, if elements are tuples, convert them to strings.
        display_matches = []
        for match in processed_matches:
            if isinstance(match, tuple):
                display_matches.append(" ".join(str(item) for item in match)) # Join tuple elements with space
            else:
                display_matches.append(str(match)) # Ensure it's a string

        result_text_display = "\n".join(display_matches)

        total_matches_found = len(matches)
        total_displayed = len(processed_matches)

        clipboard_header = f"Pattern: {regex_pattern_str}\n"
        if case_insensitive:
            clipboard_header += "Case Insensitive: Yes\n"
        if unique_only:
            clipboard_header += f"Unique Matches Displayed: {total_displayed} (from {total_matches_found} total)\n\n"
        else:
            clipboard_header += f"Total Matches Displayed: {total_displayed}\n\n"

        result_text_clipboard = clipboard_header + result_text_display

        # Display in a new dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Extracted Matches")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("450x350")

        text_frame = ttk.Frame(dialog, padding=5)
        text_frame.pack(expand=True, fill=tk.BOTH)

        info_str = f"Displayed: {total_displayed}"
        if unique_only and total_matches_found != total_displayed:
            info_str += f" (unique from {total_matches_found} total)"
        header_label = ttk.Label(text_frame, text=info_str)
        header_label.pack(pady=(0,5))

        result_display_text_widget = tk.Text(text_frame, wrap=tk.WORD, height=10, width=50)
        result_display_text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, pady=(0,5))

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=result_display_text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0,5))
        result_display_text_widget.config(yscrollcommand=scrollbar.set)

        result_display_text_widget.insert(tk.END, result_text_display)
        result_display_text_widget.config(state=tk.DISABLED)

        button_frame = ttk.Frame(dialog, padding=(5,0,5,5))
        button_frame.pack(fill=tk.X)

        def copy_to_clipboard_pattern():
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text_clipboard)
            messagebox.showinfo("Copied", "Extracted matches copied to clipboard.", parent=dialog)

        ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard_pattern).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')


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
            # If the tab was filtered or had filter text, clear its filter settings
            if current_tab and (current_tab.is_tab_filtered_view or current_tab.tab_filter_str):
                # Setting filter_text_var to "" will trigger on_filter_settings_changed.
                # on_filter_settings_changed will then update current_tab.tab_filter_str,
                # current_tab.tab_filter_case_sensitive, current_tab.tab_filter_invert
                # (though only text changes here, so case/invert remain as they were unless also cleared),
                # and then call current_tab.apply_text_filter().
                # To fully clear the filter state for the tab when hiding the bar,
                # it's better to update the tab's state directly and then apply.
                current_tab.tab_filter_str = ""
                # Optionally reset case/invert for the tab when filter bar is hidden and filter cleared
                # current_tab.tab_filter_case_sensitive = False
                # current_tab.tab_filter_invert = False
                current_tab.apply_text_filter() # Apply the cleared filter

                # Also update the filter bar vars so if it's reshown for another tab, it's clean,
                # though on_tab_changed should handle this.
                self._is_updating_filter_bar_from_tab = True
                try:
                    self.filter_text_var.set("")
                    # self.filter_case_var.set(False) # Optional: reset UI checkboxes too
                    # self.filter_invert_var.set(False)
                finally:
                    self._is_updating_filter_bar_from_tab = False
        else:
            self.filter_bar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,2), before=self.notebook)
            current_tab = self.get_current_tab()
            if current_tab:
                self._is_updating_filter_bar_from_tab = True
                try:
                    self.filter_text_var.set(current_tab.tab_filter_str)
                    self.filter_case_var.set(current_tab.tab_filter_case_sensitive)
                    self.filter_invert_var.set(current_tab.tab_filter_invert)
                finally:
                    self._is_updating_filter_bar_from_tab = False
                # Ensure the tab's view is consistent with its filter state when bar is shown
                current_tab.apply_text_filter()
            self.filter_entry.focus_set()
        return "break" # For key binding

    def toggle_line_numbers_action(self, event=None):
        self.show_line_numbers = not self.show_line_numbers
        for tab in self.tabs:
            tab.line_numbers_visible = self.show_line_numbers
            if tab.line_numbers_visible:
                if not tab.line_numbers_canvas.winfo_ismapped():
                    tab.line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y, before=tab.text_area)
                tab.redraw_line_numbers()
            else:
                if tab.line_numbers_canvas.winfo_ismapped():
                    tab.line_numbers_canvas.pack_forget()
        # Update the current tab's line numbers explicitly if it was just made visible
        current_tab = self.get_current_tab()
        if current_tab and current_tab.line_numbers_visible:
            current_tab.redraw_line_numbers()

    def prompt_go_to_line(self, event=None):
        current_tab = self.get_current_tab()
        if not current_tab:
            return "break"

        text_area = current_tab.text_area

        # Get total lines for validation and dialog prompt
        try:
            total_lines = int(text_area.index(f"{tk.END}-1c").split('.')[0])
        except (ValueError, tk.TclError):
            total_lines = 1 # Default if error or empty

        line_num = simpledialog.askinteger( # Corrected to use imported simpledialog
            "Go to Line",
            f"Enter line number (1-{total_lines}):",
            parent=self.root,
            minvalue=1,
            maxvalue=total_lines
        )

        if line_num is not None: # User entered a number and didn't cancel
            # Validate again, though askinteger should handle min/max.
            # This is more about ensuring it's within the dynamically known total_lines.
            if 1 <= line_num <= total_lines:
                text_area.mark_set(tk.INSERT, f"{line_num}.0")
                text_area.see(f"{line_num}.0")
                text_area.focus_set() # Give focus back to the text area
            else:
                # This case should ideally be prevented by askinteger's maxvalue,
                # but good to have a fallback message.
                messagebox.showwarning("Go to Line",
                                       f"Line number {line_num} is out of range (1-{total_lines}).",
                                       parent=self.root)
        return "break"

    def toggle_notes_style_action(self, event=None):
        self.notes_style_active = not self.notes_style_active
        for tab in self.tabs:
            tab.tab_notes_style_active = self.notes_style_active
            if tab.tab_notes_style_active:
                # If notes style is now active, existing syntax highlighting should be cleared first,
                # then notes style applied.
                if hasattr(tab, '_clear_syntax_highlight_tags'): # Check if method exists
                    tab._clear_syntax_highlight_tags() # Clear general syntax highlighting
                if hasattr(tab, 'clear_keyword_highlight_settings'): # This is on app, not tab.
                                                                    # tab.apply_keyword_highlights({}) might work if it clears
                    # To clear keyword highlights on a tab if Notes Style is active:
                    # Option 1: Add a clear method to EditorTab for user keywords
                    # Option 2: Pass empty settings to apply_keyword_highlights
                    # For now, let notes style overlay, or be potentially overridden by keywords if they run later.
                    # A more robust solution might involve exclusive highlighting modes or priority.
                    # As per plan, Notes Style should take precedence.
                    # So, we should ensure other highlights are cleared or not applied when notes style is on.
                    pass # Keyword clearing needs more thought if they conflict visually.
                         # Let's assume for now that apply_notes_style_highlighting will be dominant.

                if hasattr(tab, 'apply_notes_style_highlighting'): # Check if method exists
                    tab.apply_notes_style_highlighting()
                else:
                    print(f"DEBUG: Tab {tab.current_file or 'Untitled'} missing apply_notes_style_highlighting")
            else:
                # If notes style is now inactive, clear its highlights.
                # Then, reapply original syntax/keyword highlighting if applicable.
                if hasattr(tab, 'clear_notes_style_highlighting'): # Check if method exists
                    tab.clear_notes_style_highlighting()
                else:
                    print(f"DEBUG: Tab {tab.current_file or 'Untitled'} missing clear_notes_style_highlighting")

                # Reapply other active highlights
                if tab.current_language_name and hasattr(tab, 'apply_syntax_highlighting'):
                    tab.apply_syntax_highlighting()
                if self.keyword_highlight_settings.get("active", False) and hasattr(tab, 'apply_keyword_highlights'):
                    tab.apply_keyword_highlights(self.keyword_highlight_settings)

        # Update the current tab's display explicitly after toggling
        current_tab = self.get_current_tab()
        if current_tab:
            if hasattr(current_tab, 'text_area') and current_tab.text_area.winfo_exists():
                current_tab.text_area.update_idletasks() # Ensure UI is responsive
                # The on_text_changed logic or tab.apply_notes_style_highlighting should handle redraw.


    def _handle_drop_files(self, event):
        """
        Handles files dropped onto the notebook widget.
        event.data should contain a string of file paths.
        """
        dropped_files_str = event.data
        if not dropped_files_str:
            return

        # Using re.findall to find either braced content or non-space sequences.
        # This regex finds {anything not a brace} OR any sequence of non-whitespace characters.
        raw_paths = re.findall(r'\{[^{}]+\}|[^\s]+', dropped_files_str)

        files_to_open = []
        for path_candidate in raw_paths:
            path = path_candidate
            if path.startswith('{') and path.endswith('}'):
                path = path[1:-1]

            path = path.strip('"\'') # General precaution for quoted paths

            if os.path.isfile(path):
                files_to_open.append(path)
            elif os.path.isdir(path):
                # Ignoring directories as per current plan
                # print(f"DEBUG: Ignored directory drop: {path}")
                pass

        if files_to_open:
            # This method will be created/adjusted in the next step
            # to handle opening a list of filepaths without dialogs.
            self._open_multiple_files(files_to_open)

    def _open_multiple_files(self, filepaths: list):
        for path in filepaths:
            # Check if file is already open
            already_open = False
            for tab_obj in self.tabs: # Renamed 'tab' to 'tab_obj' to avoid conflict with notebook.select(tab)
                if tab_obj.current_file == path:
                    self.notebook.select(tab_obj.frame_id()) # Select existing tab
                    already_open = True
                    break
            if not already_open:
                # This is the core logic from open_file_action that creates a new tab for a known path
                new_tab = EditorTab(self.notebook, self, file_path=path)
                if new_tab.current_file: # Check if file loading was successful in EditorTab
                    self.tabs.append(new_tab)
                    self.notebook.add(new_tab.frame) # title is set by new_tab.update_tab_title()
                    new_tab.update_tab_title() # Ensure title is set
                    self.notebook.select(new_tab.frame_id())
                    new_tab.text_area.focus_set()
                else:
                    # If new_tab.current_file is None, EditorTab constructor might have failed to load.
                    # It internally calls self.close_tab if load fails, which should remove the frame.
                    # Or, we can explicitly destroy the frame if it wasn't properly handled.
                    if new_tab.frame.winfo_exists(): # Check if frame exists before destroying
                        new_tab.frame.destroy()

        if self.tabs: # If any tabs are open (either new or existing selected)
            self.update_app_title()
            self.update_status_bar()

    def open_quick_text_dialog(self, event=None):
        # This 'self' is the TextEditor instance
        dialog = QuickTextDialog(self) # Pass TextEditor instance as parent
        # Dialog is modal (grab_set) and transient, so execution waits here
        # until dialog is destroyed.
        return "break" # Important for key bindings to prevent further processing

    def open_flow_diagram_dialog(self, event=None):
        dialog = FlowDiagramDialog(self)
        # Dialog handles its own lifecycle (modal)
        return "break" # For key bindings

    def open_file_search_dialog(self, event=None):
        dialog = FileSearchDialog(self)
        # Dialog is designed to be non-modal for now, or will manage its own modality.
        # The search execution and result display are handled via callbacks/methods.
        return "break"

    def _display_search_results(self, results, search_phrase, is_regex, is_case_sensitive):
        if not results: # Should be caught by FileSearchDialog, but double-check
            messagebox.showinfo("Search Results", "No matches found.", parent=self.root)
            return

        # Create a new tab for search results
        results_tab = EditorTab(self.notebook, self)
        self.tabs.append(results_tab)

        # Truncate long search phrases for tab title
        display_phrase = search_phrase[:30] + '...' if len(search_phrase) > 30 else search_phrase
        results_tab_title = f"[Search Results: \"{display_phrase}\"]"

        self.notebook.add(results_tab.frame, text=results_tab_title)
        self.notebook.select(results_tab.frame_id())

        results_text_widget = results_tab.text_area
        results_text_widget.config(state=tk.NORMAL) # Enable for inserting
        results_text_widget.delete("1.0", tk.END)

        # Configure a tag for highlighting the search phrase
        highlight_tag_name = "search_result_highlight"
        results_text_widget.tag_configure(highlight_tag_name, background="yellow", foreground="black")

        # Group results by filepath
        grouped_results = collections.defaultdict(list)
        for result in results:
            grouped_results[result['filepath']].append(result)

        for filepath, file_matches in grouped_results.items():
            results_text_widget.insert(tk.END, f"File: {filepath}\n")
            results_text_widget.insert(tk.END, "================================\n") # Separator for file

            for i, result in enumerate(file_matches):
                results_text_widget.insert(tk.END, f"  Line: {result['line_number']}\n")
                # results_text_widget.insert(tk.END, "  --------------------------------\n") # Sub-separator per match

                for before_line in result['context_before']:
                    results_text_widget.insert(tk.END, f"    {before_line}\n") # Indent context

                # Insert matched line and apply highlighting
                # Need to be careful with indices as we insert.
                # The "> " prefix adds 2 characters + 2 for indentation "  > " = 4 chars
                prefix_for_matched_line = "  > "
                matched_line_display_start_index = results_text_widget.index(tk.END + "-1c") # Before inserting this line
                results_text_widget.insert(tk.END, f"{prefix_for_matched_line}{result['matched_line']}\n")

                highlight_start_tk = f"{matched_line_display_start_index} + {len(prefix_for_matched_line) + result['match_start']} chars"
                highlight_end_tk = f"{matched_line_display_start_index} + {len(prefix_for_matched_line) + result['match_end']} chars"
                results_text_widget.tag_add(highlight_tag_name, highlight_start_tk, highlight_end_tk)

                for after_line in result['context_after']:
                    results_text_widget.insert(tk.END, f"    {after_line}\n") # Indent context

                if i < len(file_matches) - 1: # If not the last match in this file
                    results_text_widget.insert(tk.END, "  --------------------------------\n") # Separator between matches in the same file
                else:
                    results_text_widget.insert(tk.END, "\n") # Extra newline after last match in file before next file's header

            # results_text_widget.insert(tk.END, "\n") # Extra newline after all matches for a file, before next file header

        results_text_widget.config(state=tk.DISABLED) # Make read-only
        results_tab.text_changed = False
        results_tab.current_file = None # This tab doesn't represent a direct file
        results_tab.update_tab_title() # To use the title set above

        self.update_app_title() # Update main window title if it depends on tab name
        self.update_status_bar()
        results_tab.text_area.focus_set()


    def view_data_as_table_action(self, event=None):
        current_tab = self.get_current_tab()
        if not current_tab:
            messagebox.showerror("Error", "No active tab to process.")
            return "break"

        if data_to_table_converter is None:
            messagebox.showerror("Dependency Missing",
                                 "The 'data_to_table_converter' module or 'PyYAML' library is missing. Please ensure PyYAML is installed.",
                                 parent=self.root)
            return "break"

        content = current_tab.get_content()
        if not content.strip():
            messagebox.showinfo("No Content", "Current tab is empty.", parent=self.root)
            return "break"

        try:
            parsed_data, data_type = data_to_table_converter.parse_data(content)
            table_string = data_to_table_converter.format_to_text_table(parsed_data)

            # Create a new tab for the table view
            table_view_tab = EditorTab(self.notebook, self) # Pass self (TextEditor instance)
            self.tabs.append(table_view_tab)

            original_filename = os.path.basename(current_tab.current_file) if current_tab.current_file else "Untitled"
            table_tab_title = f"[Table View] {original_filename} ({data_type})"

            self.notebook.add(table_view_tab.frame, text=table_tab_title)
            self.notebook.select(table_view_tab.frame_id())

            table_view_tab.text_area.insert(tk.END, table_string)
            table_view_tab.text_area.config(state=tk.DISABLED) # Make read-only
            table_view_tab.text_changed = False # Not considered a modification of a file
            table_view_tab.current_file = None # This tab doesn't represent a direct file for saving
            table_view_tab.update_tab_title() # Update title based on new logic

            self.update_app_title()
            self.update_status_bar()
            table_view_tab.text_area.focus_set()

        except DataParsingError as e:
            messagebox.showerror("Data Parsing Error", str(e), parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.root)

        return "break"

    def open_rest_api_client_dialog(self, event=None):
        dialog = RestApiClientDialog(self)
        # Dialog is modal and handles its own lifecycle.
        return "break" # For key bindings if any

    def open_sql_parser_dialog(self, event=None):
        dialog = SqlParserDialog(self)
        # Dialog is modal and handles its own lifecycle.
        return "break" # For key bindings if any

    def open_excel_to_html_dialog(self, event=None):
        dialog = ExcelToHtmlDialog(self)
        # Dialog is modal and handles its own lifecycle.
        return "break" # For key bindings if any

    def open_excel_to_csv_stats_dialog(self, event=None):
        dialog = ExcelToCsvStatsDialog(self)
        # Dialog is modal and handles its own lifecycle
        return "break" # For key bindings if any

    def open_url_manager_dialog(self, event=None):
        dialog = UrlManagerDialog(self)
        # Dialog handles its own lifecycle (e.g. modality via grab_set)
        return "break" # For key bindings

    def open_drawing_tool_action(self, event=None):
        dialog = DrawingDialog(self)
        # DrawingDialog manages its own lifecycle (modal or not via grab_set)
        return "break" # For key bindings

    # --- End of QuickTextDialog and its helper methods in TextEditor ---


class DrawingDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("Drawing Tool")
        self.top.transient(self.root)
        # self.top.grab_set() # Non-modal for now, user might want to see editor
        # self.top.geometry("700x550") # Initial size - let OS/user decide more freely
        self.top.resizable(True, True) # Ensure dialog is resizable

        self.current_brush_size = 5
        self.current_color = "black" # Default color
        self.drawing_mode = "pen" # Modes: "pen", "text", "line"
        self.line_style = "plain" # "plain", "uni_arrow", "bi_arrow"
        self.last_x, self.last_y = None, None # For freehand pen
        self.line_start_x, self.line_start_y = None, None # For line/arrow drawing
        self.temp_line_id = None # For previewing line/arrow during drag

        self.text_tool_button = None
        self.eraser_button = None # Ensure it's initialized before use in activate methods
        self.eraser_button_active = False
        self.plain_line_button = None
        self.uni_arrow_button = None
        self.bi_arrow_button = None


        # --- Main Frame ---
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Controls Frame (for brush size, colors) ---
        controls_frame = ttk.Frame(main_frame, height=50)
        controls_frame.pack(fill=tk.X, pady=(0, 5))

        # Brush Size Control
        ttk.Label(controls_frame, text="Brush Size:").pack(side=tk.LEFT, padx=(5,0))
        self.brush_size_label_var = tk.StringVar(value=str(self.current_brush_size)) # Initialize before scale
        self.brush_size_scale = ttk.Scale(controls_frame, from_=1, to=50, orient=tk.HORIZONTAL,
                                          command=self.set_brush_size_from_scale)
        self.brush_size_scale.set(self.current_brush_size) # Set initial value
        self.brush_size_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(controls_frame, textvariable=self.brush_size_label_var, width=3).pack(side=tk.LEFT, padx=(0,10)) # Increased padding

        # Color Palette
        ttk.Label(controls_frame, text="Color:").pack(side=tk.LEFT, padx=(5,2))
        self.color_palette_frame = ttk.Frame(controls_frame)
        self.color_palette_frame.pack(side=tk.LEFT)

        self.dark_pastel_colors = [
            "#6A5ACD",  # SlateBlue
            "#483D8B",  # DarkSlateBlue
            "#5F9EA0",  # CadetBlue
            "#2F4F4F",  # DarkSlateGray
            "#8B4513",  # SaddleBrown
            "#800000",  # Maroon
            "#4B0082",  # Indigo
            "#006400",  # DarkGreen
            "#556B2F",  # DarkOliveGreen
            "#FF8C00",  # DarkOrange
            "#9932CC",  # DarkOrchid
            "#D2691E",  # Chocolate
            "#FFFFFF",  # White
        ]
        self.active_color_button = None # To track the currently selected color button

        # Ensure default color is one from the palette if current_color is "black" (initial default)
        if self.current_color == "black" and self.dark_pastel_colors:
            self.current_color = self.dark_pastel_colors[0]


        for color_code in self.dark_pastel_colors:
            color_btn = tk.Frame(self.color_palette_frame, width=20, height=20, bg=color_code, relief=tk.RAISED, borderwidth=2)
            color_btn.pack(side=tk.LEFT, padx=2, pady=2)
            # Pass the button widget itself to select_color_button
            color_btn.bind("<Button-1>", lambda e, c=color_code, btn=color_btn: self.select_color_button(c, btn))
            if self.current_color == "black" and color_code == self.dark_pastel_colors[0]: # Initial default selection
                 self.current_color = color_code # Set initial drawing color to the first pastel
                 self.select_color_button(color_code, color_btn)
            elif color_code == self.current_color : # Handles if current_color was already a pastel
                 self.select_color_button(color_code, color_btn)


        # Eraser Button
        self.eraser_button = ttk.Button(controls_frame, text="Eraser", command=self.activate_eraser)
        self.eraser_button.pack(side=tk.LEFT, padx=(10, 2)) # Adjusted padding

        # Text Tool Button
        self.text_tool_button = ttk.Button(controls_frame, text="Text", command=self.activate_text_tool)
        self.text_tool_button.pack(side=tk.LEFT, padx=2)

        # Separator before line tools
        ttk.Separator(controls_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

        # Line Tool Buttons
        self.plain_line_button = ttk.Button(controls_frame, text="Line", command=self.activate_plain_line_mode)
        self.plain_line_button.pack(side=tk.LEFT, padx=2)
        self.uni_arrow_button = ttk.Button(controls_frame, text="→", command=self.activate_uni_arrow_mode) # Uni-directional Arrow
        self.uni_arrow_button.pack(side=tk.LEFT, padx=2)
        self.bi_arrow_button = ttk.Button(controls_frame, text="↔", command=self.activate_bi_arrow_mode) # Bi-directional Arrow
        self.bi_arrow_button.pack(side=tk.LEFT, padx=2)

        # Separator after line tools
        ttk.Separator(controls_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

        # Clear Canvas Button
        clear_button = ttk.Button(controls_frame, text="Clear Canvas", command=self.clear_canvas)
        clear_button.pack(side=tk.LEFT, padx=(2,5)) # Adjusted padding


        # --- Canvas for Drawing ---
        self.canvas = tk.Canvas(main_frame, bg="white", highlightthickness=1, highlightbackground="grey")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        # Center dialog and set initial size (can be overridden by user resize/maximize)
        self.top.update_idletasks()
        initial_width = 700
        initial_height = 550
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (initial_width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (initial_height // 2)
        self.top.geometry(f'{initial_width}x{initial_height}+{x}+{y}')
        self.top.minsize(400, 300)

    def start_draw(self, event):
        if self.drawing_mode == "pen":
            self.last_x, self.last_y = event.x, event.y
            x1 = event.x - self.current_brush_size / 2
            y1 = event.y - self.current_brush_size / 2
            x2 = event.x + self.current_brush_size / 2
            y2 = event.y + self.current_brush_size / 2
            self.canvas.create_oval(x1, y1, x2, y2, fill=self.current_color, outline=self.current_color, width=0)
        elif self.drawing_mode == "text":
            user_text = simpledialog.askstring("Input Text", "Enter text to place on canvas:", parent=self.top)
            if user_text:
                font_size = max(20, int(self.current_brush_size * 3))
                text_font = ("Arial", font_size, "bold")
                self.canvas.create_text(event.x, event.y, text=user_text, fill=self.current_color, font=text_font, anchor=tk.NW)
        elif self.drawing_mode == "line":
            self.line_start_x, self.line_start_y = event.x, event.y
            # No initial dot for line/arrow tool

    def draw(self, event):
        if self.drawing_mode == "pen":
            if self.last_x and self.last_y:
                self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                        width=self.current_brush_size, fill=self.current_color,
                                        capstyle=tk.ROUND, smooth=tk.TRUE, splinesteps=128)
                x1, y1 = (event.x - self.current_brush_size / 2), (event.y - self.current_brush_size / 2)
                x2, y2 = (event.x + self.current_brush_size / 2), (event.y + self.current_brush_size / 2)
                self.canvas.create_oval(x1, y1, x2, y2, fill=self.current_color, outline=self.current_color)
                self.last_x, self.last_y = event.x, event.y
        elif self.drawing_mode == "line":
            if self.line_start_x is not None and self.line_start_y is not None:
                if self.temp_line_id:
                    self.canvas.delete(self.temp_line_id)
                # For preview, draw plain line without arrows yet. Arrows applied on ButtonRelease.
                self.temp_line_id = self.canvas.create_line(self.line_start_x, self.line_start_y, event.x, event.y,
                                                            width=self.current_brush_size, fill=self.current_color,
                                                            capstyle=tk.ROUND) # Using ROUND for consistency with pen

    def stop_draw(self, event):
        if self.drawing_mode == "pen":
            self.last_x, self.last_y = None, None
        elif self.drawing_mode == "line":
            if self.temp_line_id:
                self.canvas.delete(self.temp_line_id)
                self.temp_line_id = None

            if self.line_start_x is not None and self.line_start_y is not None:
                x1, y1 = self.line_start_x, self.line_start_y
                x2, y2 = event.x, event.y

                arrow_option = tk.NONE
                if self.line_style == "uni_arrow":
                    arrow_option = tk.LAST
                elif self.line_style == "bi_arrow":
                    arrow_option = tk.BOTH

                arrow_shape_spec = (10, 12, 5) # Default: (length_of_arrowhead_along_line, full_width_of_arrowhead, indent_of_arrowhead_base)

                self.canvas.create_line(x1, y1, x2, y2,
                                        width=self.current_brush_size,
                                        fill=self.current_color,
                                        arrow=arrow_option,
                                        arrowshape=arrow_shape_spec,
                                        capstyle=tk.ROUND) # Keep capstyle consistent

            self.line_start_x, self.line_start_y = None, None


    def set_brush_size_from_scale(self, value):
        self.current_brush_size = int(float(value))
        self.brush_size_label_var.set(str(self.current_brush_size))

    def select_color_button(self, color_code, button_widget):
        self.current_color = color_code
        if self.active_color_button:
            self.active_color_button.config(relief=tk.RAISED, borderwidth=2) # Deselect old
        button_widget.config(relief=tk.SUNKEN, borderwidth=2) # Select new
        self.active_color_button = button_widget

    def select_color_button(self, color_code, button_widget):
        self.current_color = color_code
        self.drawing_mode = "pen" # Selecting a color implies pen mode
        self._deactivate_all_tools_visual() # Visually deselect all other tools

        # Then, specifically activate the clicked color button
        button_widget.config(relief=tk.SUNKEN, borderwidth=2) # Select new color button
        self.active_color_button = button_widget
        # Note: _deactivate_all_tools_visual already sets self.eraser_button_active = False

    def set_color(self, color): # Called by select_color_button or activate_eraser
        self.current_color = color

    def activate_eraser(self):
        self.set_color("white") # Canvas background color
        self.drawing_mode = "pen" # Eraser is a type of pen
        self._deactivate_all_tools_visual() # Visually deselect all other tools

        # Then, specifically activate the eraser button
        if self.eraser_button and hasattr(self.eraser_button, 'state'):
            self.eraser_button.state(['pressed'])
        self.eraser_button_active = True # Set logical state for eraser

    def activate_text_tool(self):
        self.drawing_mode = "text"
        self._deactivate_all_tools_visual() # Visually deselect all other tools

        # Then, specifically activate the text tool button
        if self.text_tool_button and hasattr(self.text_tool_button, 'state'):
            self.text_tool_button.state(['pressed'])
        # Note: _deactivate_all_tools_visual handles active_color_button relief and eraser_button_active state.

    def _deactivate_all_tools_visual(self):
        """Helper to visually deactivate all tool buttons/swatches."""
        if self.active_color_button:
            self.active_color_button.config(relief=tk.RAISED, borderwidth=2)
            # self.active_color_button = None # Don't nullify, color should be remembered

        if self.eraser_button and hasattr(self.eraser_button, 'state'):
            self.eraser_button.state(['!pressed'])
        self.eraser_button_active = False # Ensure logical state is also reset

        if self.text_tool_button and hasattr(self.text_tool_button, 'state'):
            self.text_tool_button.state(['!pressed'])

        if self.plain_line_button and hasattr(self.plain_line_button, 'state'):
            self.plain_line_button.state(['!pressed'])
        if self.uni_arrow_button and hasattr(self.uni_arrow_button, 'state'):
            self.uni_arrow_button.state(['!pressed'])
        if self.bi_arrow_button and hasattr(self.bi_arrow_button, 'state'):
            self.bi_arrow_button.state(['!pressed'])

    def activate_plain_line_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "plain"
        if hasattr(self.plain_line_button, 'state'):
            self.plain_line_button.state(['pressed'])

    def activate_uni_arrow_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "uni_arrow"
        if hasattr(self.uni_arrow_button, 'state'):
            self.uni_arrow_button.state(['pressed'])

    def activate_bi_arrow_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "bi_arrow"
        if hasattr(self.bi_arrow_button, 'state'):
            self.bi_arrow_button.state(['pressed'])

    def clear_canvas(self):
        if messagebox.askyesno("Clear Canvas", "Are you sure you want to clear the entire canvas?\nThis action cannot be undone (yet!).", parent=self.top):
            self.canvas.delete("all")


class ExcelToCsvStatsDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("Excel to CSVs & Statistics")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(False, False)

        # Variables
        self.input_excel_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()

        # --- Main Frame ---
        main_frame = ttk.Frame(self.top, padding=15)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1) # Allow entry fields to expand

        # Input Excel File
        ttk.Label(main_frame, text="Excel File (.xlsx):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        input_file_entry = ttk.Entry(main_frame, textvariable=self.input_excel_file_var, width=50)
        input_file_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        input_file_button = ttk.Button(main_frame, text="Browse...", command=self._browse_input_file)
        input_file_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        # Output Directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        output_dir_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50)
        output_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        output_dir_button = ttk.Button(main_frame, text="Browse...", command=self._browse_output_dir)
        output_dir_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)

        # Generate Button
        generate_button = ttk.Button(main_frame, text="Generate CSVs & Stats", command=self._generate_files_stub) # Stub for now
        generate_button.grid(row=2, column=0, columnspan=3, pady=15)

        input_file_entry.focus_set()
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        self.top.minsize(550, 180)

    def _browse_input_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx")],
            parent=self.top
        )
        if filepath:
            self.input_excel_file_var.set(filepath)

    def _browse_output_dir(self):
        dirpath = filedialog.askdirectory(
            title="Select Output Directory",
            parent=self.top # Ensure dialog is on top
        )
        if dirpath:
            self.output_dir_var.set(dirpath)

    def _generate_files(self):
        input_file = self.input_excel_file_var.get()
        user_selected_output_dir = self.output_dir_var.get()

        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Input Error", "Please select a valid Excel input file.", parent=self.top)
            return

        if not user_selected_output_dir:
            if messagebox.askyesno("Output Directory", "No output directory selected. Use the input file's directory as the base for output?", parent=self.top):
                base_output_dir = os.path.dirname(input_file)
                self.output_dir_var.set(base_output_dir) # Update UI
            else:
                return # User cancelled
        else:
            base_output_dir = user_selected_output_dir
            if not os.path.isdir(base_output_dir):
                messagebox.showerror("Input Error", "The selected output directory is not valid.", parent=self.top)
                return

        excel_filename_no_ext = os.path.splitext(os.path.basename(input_file))[0]
        sanitized_folder_name = re.sub(r'[^\w\s-]', '', excel_filename_no_ext).strip().replace(' ', '_')
        if not sanitized_folder_name:
            sanitized_folder_name = "excel_csv_stats_output"

        # Create a subfolder like "MyWorkbook_csv_stats"
        final_output_subfolder = os.path.join(base_output_dir, f"{sanitized_folder_name}_csv_stats")

        try:
            os.makedirs(final_output_subfolder, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Output Error", f"Could not create output subfolder: {final_output_subfolder}\nError: {e}", parent=self.top)
            return

        try:
            import openpyxl
            import csv
            import subprocess
        except ImportError as e:
            messagebox.showerror("Dependency Missing",
                                 f"A required library is missing: {e.name}. Please ensure 'openpyxl' and 'csv' (standard library) are available.",
                                 parent=self.top)
            return

        try:
            workbook = openpyxl.load_workbook(input_file, read_only=True)
            sheet_names = workbook.sheetnames

            generated_count = 0
            errors_occurred = []

            for sheet_name in sheet_names:
                ws = workbook[sheet_name]

                # Sanitize sheet name for filename
                sane_sheet_filename_part = re.sub(r'[^\w\s-]', '', sheet_name).strip().replace(' ', '_')
                if not sane_sheet_filename_part:
                    sane_sheet_filename_part = f"sheet_{generated_count + 1}" # Fallback if name is all special chars

                csv_filename = f"{sane_sheet_filename_part}.csv"
                csv_filepath = os.path.join(final_output_subfolder, csv_filename)

                stats_txt_filename = f"{csv_filename}.txt"
                stats_txt_filepath = os.path.join(final_output_subfolder, stats_txt_filename)

                try:
                    # Write CSV
                    with open(csv_filepath, 'w', newline='', encoding='utf-8') as f_csv:
                        writer = csv.writer(f_csv)
                        for row in ws.iter_rows():
                            writer.writerow([cell.value for cell in row])

                    # Run csvstat
                    try:
                        # Try to find csvstat. On Windows, subprocess might need shell=True if csvstat is a .bat or not directly in PATH in some setups.
                        # However, shell=True is a security risk if command parts are from untrusted input. Here, csv_filepath is constructed.
                        # For broader compatibility, direct executable path or ensuring PATH is set is better.
                        # If `csvstat` is a script, it might need `python -m csvkit.utilities.csvstat` or similar if not installed as direct executable.
                        # For now, assume `csvstat` is in PATH.
                        process_result = subprocess.run(['csvstat', csv_filepath], capture_output=True, text=True, check=False, encoding='utf-8')

                        if process_result.returncode == 0:
                            with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt:
                                f_txt.write(process_result.stdout)
                            generated_count += 1
                        else:
                            error_detail = f"Error running csvstat on {csv_filename}:\n{process_result.stderr}"
                            if process_result.stdout: # Sometimes errors also print to stdout
                                error_detail += f"\nStdout:\n{process_result.stdout}"
                            with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt: # Write error to the txt file
                                f_txt.write(error_detail)
                            errors_occurred.append(error_detail)

                    except FileNotFoundError:
                        error_msg = "Error: 'csvstat' command not found. Please ensure csvkit is installed and 'csvstat' is in your system's PATH."
                        messagebox.showerror("csvstat Error", error_msg, parent=self.top)
                        # Write this error to the stats file for this sheet as well
                        with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt:
                            f_txt.write(error_msg)
                        errors_occurred.append(f"csvstat not found for {csv_filename}.")
                        # We should probably stop trying for other sheets if csvstat is not found once.
                        # For now, let it try per sheet and accumulate errors. Or, break here.
                        # To stop for all: raise an exception or return after this messagebox.
                        # For this implementation, let's report it once and stop processing further csvstat calls.
                        # This requires a flag or early exit.
                        # For simplicity of this step, we'll let it report per file if FileNotFoundError happens multiple times.
                        # A better approach would be a pre-check for csvstat.

                except Exception as e_file:
                    errors_occurred.append(f"Failed to process sheet '{sheet_name}': {e_file}")

            if errors_occurred:
                error_summary = "\n\n".join(errors_occurred)
                messagebox.showwarning("Processing Issues",
                                     f"{generated_count} sheet(s) processed with stats. Some errors occurred:\n\n{error_summary}\n\nCheck files in {final_output_subfolder}",
                                     parent=self.top)
            elif generated_count > 0:
                messagebox.showinfo("Success",
                                    f"Successfully generated {generated_count} CSV file(s) and their statistics in:\n{final_output_subfolder}",
                                    parent=self.top)
            else: # No sheets or all failed before csvstat
                 messagebox.showinfo("No Data", "No sheets were processed or found in the Excel file.", parent=self.top)


        except FileNotFoundError: # For input_file itself
            messagebox.showerror("Error", f"Input Excel file not found: {input_file}", parent=self.top)
        except openpyxl.utils.exceptions.InvalidFileException:
            messagebox.showerror("Error", "Invalid Excel file format. Please provide a .xlsx file.", parent=self.top)
        except Exception as e:
            messagebox.showerror("Generation Error", f"An unexpected error occurred: {e}", parent=self.top)

    # Bind the actual method to the button in __init__
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("Excel to CSVs & Statistics")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(False, False)

        # Variables
        self.input_excel_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()

        # --- Main Frame ---
        main_frame = ttk.Frame(self.top, padding=15)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1) # Allow entry fields to expand

        # Input Excel File
        ttk.Label(main_frame, text="Excel File (.xlsx):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        input_file_entry = ttk.Entry(main_frame, textvariable=self.input_excel_file_var, width=50)
        input_file_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        input_file_button = ttk.Button(main_frame, text="Browse...", command=self._browse_input_file)
        input_file_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        # Output Directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        output_dir_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50)
        output_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        output_dir_button = ttk.Button(main_frame, text="Browse...", command=self._browse_output_dir)
        output_dir_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)

        # Generate Button
        generate_button = ttk.Button(main_frame, text="Generate CSVs & Stats", command=self._generate_files) # Changed to actual method
        generate_button.grid(row=2, column=0, columnspan=3, pady=15)

        input_file_entry.focus_set()
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        self.top.minsize(550, 180)

class UrlManagerDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("URL Manager")
        self.top.transient(self.root)
        # self.top.grab_set() # Making it non-modal for now
        self.top.geometry("700x500")
        self.top.resizable(True, True) # Make window resizable
        self.top.minsize(500, 350) # Adjusted minsize slightly for potential new widgets

        self.bookmarks_data = {}  # For the currently selected single file
        self.all_bookmark_sets_data = {} # For global search cache
        self.current_ini_file = None

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        top_controls_frame = ttk.Frame(main_frame)
        top_controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        # Configure columns for the top_controls_frame to allow combobox and label to share space
        # Order: ComboLabel, Combo, LoadOtherButton, StatusLabel(expand), SearchLabel, SearchEntry
        top_controls_frame.grid_columnconfigure(0, weight=0)  # Combobox Label
        top_controls_frame.grid_columnconfigure(1, weight=0)  # Combobox
        top_controls_frame.grid_columnconfigure(2, weight=0)  # Load Other INI button
        top_controls_frame.grid_columnconfigure(3, weight=1)  # Loaded file label (this should expand)
        top_controls_frame.grid_columnconfigure(4, weight=0)  # Search Label
        top_controls_frame.grid_columnconfigure(5, weight=0)  # Search Entry


        # --- New Combobox for bookmark sets ---
        self.bookmark_files_map = {} # To map display names to full paths
        self.selected_bookmark_file_var = tk.StringVar()

        self.bookmarks_combobox_label = ttk.Label(top_controls_frame, text="Set:")
        self.bookmarks_combobox_label.grid(row=0, column=0, padx=(0,2), pady=(0,5), sticky=tk.W)

        self.bookmarks_combobox = ttk.Combobox(top_controls_frame, textvariable=self.selected_bookmark_file_var, state="readonly", width=20)
        self.bookmarks_combobox.grid(row=0, column=1, padx=(0,10), pady=(0,5), sticky=tk.W)
        self.bookmarks_combobox.bind("<<ComboboxSelected>>", self._on_bookmark_set_selected)

        self.load_button = ttk.Button(top_controls_frame, text="Load Other INI...", command=lambda: self._load_ini_file(filepath_arg=None))
        self.load_button.grid(row=0, column=2, padx=(0,10), pady=(0,5), sticky=tk.W)

        self.loaded_file_label_var = tk.StringVar(value="No file loaded.")
        loaded_file_label = ttk.Label(top_controls_frame, textvariable=self.loaded_file_label_var, anchor=tk.W)
        loaded_file_label.grid(row=0, column=3, padx=(0,10), pady=(0,5), sticky=tk.EW)

        search_label = ttk.Label(top_controls_frame, text="Search:")
        search_label.grid(row=0, column=4, padx=(5,0), pady=(0,5), sticky=tk.E)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_controls_frame, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=5, padx=(0,0), pady=(0,5), sticky=tk.E) # Removed right padx for checkbox
        self.search_var.trace_add("write", self._filter_display)

        self.global_search_var = tk.BooleanVar(value=False)
        global_search_checkbox = ttk.Checkbutton(top_controls_frame, text="Global", variable=self.global_search_var)
        global_search_checkbox.grid(row=0, column=6, padx=(5,0), pady=(0,5), sticky=tk.E)
        self.global_search_var.trace_add("write", self._filter_display)


        # Adjust column weights for top_controls_frame to include new checkbox
        top_controls_frame.grid_columnconfigure(0, weight=0) # Label for combobox
        top_controls_frame.grid_columnconfigure(1, weight=0) # Combobox
        top_controls_frame.grid_columnconfigure(2, weight=0) # Load Other INI button
        top_controls_frame.grid_columnconfigure(3, weight=1) # Loaded file label (this should expand)
        top_controls_frame.grid_columnconfigure(4, weight=0) # Search Label
        top_controls_frame.grid_columnconfigure(5, weight=0) # Search Entry
        top_controls_frame.grid_columnconfigure(6, weight=0) # Global Search Checkbox


        columns = ("description", "url")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="tree headings", height=15) # show tree for groups

        self.tree.heading("#0", text="Group")
        self.tree.column("#0", width=150, stretch=tk.NO, anchor=tk.W)
        # For description and url columns, we will achieve left padding by adding spaces to the values themselves
        # rather than trying to manipulate column properties for padding, as it's more direct.
        # The width here should accommodate the text *plus* the desired visual padding.
        # We'll add 3 spaces to the text content.
        self.tree.heading("description", text="Description / Name")
        self.tree.column("description", width=250 + 20, anchor=tk.W) # Increased width to allow for spaces
        self.tree.heading("url", text="URL")
        self.tree.column("url", width=300 + 20, anchor=tk.W) # Increased width

        tree_scrollbar_y = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        tree_scrollbar_y.grid(row=1, column=1, sticky="ns")

        bottom_controls_frame = ttk.Frame(main_frame, padding=(0,10,0,0))
        bottom_controls_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.open_url_button = ttk.Button(bottom_controls_frame, text="Open Selected URL", command=self._open_selected_url, state=tk.DISABLED) # Fixed: Use actual method
        self.open_url_button.pack(side=tk.LEFT)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select) # Fixed: Use actual method
        self.tree.bind("<Double-1>", self._open_selected_url) # Fixed: Use actual method

        self.top.update_idletasks()
        x_pos = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y_pos = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'{self.top.winfo_width()}x{self.top.winfo_height()}+{x_pos}+{y_pos}')

        # After all widgets are created:
        self._populate_bookmarks_dropdown()
        self._load_all_bookmark_sets_data() # Load all data for global search
        self._try_load_default_ini()

    def _load_all_bookmark_sets_data(self):
        """Loads data from all .ini files found in the bookmarks directory."""
        self.all_bookmark_sets_data.clear()
        # self.bookmark_files_map is populated by _populate_bookmarks_dropdown
        # It maps display names (filenames) to full filepaths.

        if not self.bookmark_files_map:
            # print("Debug: No bookmark files found to load for global search.")
            return

        import configparser # Keep import local to methods that use it or move to top if widely used

        for filename, filepath in self.bookmark_files_map.items():
            parser = configparser.ConfigParser()
            try:
                parsed_files = parser.read(filepath, encoding='utf-8')
                if parsed_files:
                    current_file_data = {}
                    for section in parser.sections():
                        current_file_data[section] = {}
                        for description_key, url_value in parser.items(section):
                            current_file_data[section][description_key] = url_value
                    self.all_bookmark_sets_data[filename] = current_file_data
                else:
                    print(f"Warning: Could not read or parse '{filename}' for global search cache.")
            except configparser.Error as e:
                print(f"Warning: Error parsing INI file '{filename}' for global search cache: {e}")
            except Exception as e:
                print(f"Warning: Unexpected error loading '{filename}' for global search cache: {e}")

        # print(f"Debug: Loaded {len(self.all_bookmark_sets_data)} files into global search cache.")

    def _find_bookmark_files(self):
        """Scans for .ini files in 'bookmarks' subdirectories (CWD then script path)."""
        filenames_paths = []
        seen_filenames = set() # To handle potential name clashes if script dir is subdir of CWD etc.

        # Define potential 'bookmarks' subdirectories
        bookmarks_dirname = "bookmarks"
        possible_base_paths = [
            os.getcwd(),
            os.path.dirname(os.path.abspath(__file__))
        ]

        unique_base_paths = []
        for p in possible_base_paths:
            if p not in unique_base_paths:
                unique_base_paths.append(p)

        for base_path in unique_base_paths:
            bookmarks_path = os.path.join(base_path, bookmarks_dirname)
            if os.path.isdir(bookmarks_path):
                try:
                    for entry in os.listdir(bookmarks_path):
                        if entry.lower().endswith(".ini") and entry not in seen_filenames:
                            full_path = os.path.join(bookmarks_path, entry)
                            if os.path.isfile(full_path):
                                filenames_paths.append((entry, full_path)) # Store (display name, full path)
                                seen_filenames.add(entry)
                except OSError as e:
                    print(f"Error accessing bookmarks directory {bookmarks_path}: {e}")

        filenames_paths.sort(key=lambda x: x[0].lower()) # Sort by filename, case-insensitive
        return filenames_paths

    def _populate_bookmarks_dropdown(self):
        found_files_with_paths = self._find_bookmark_files()
        self.bookmark_files_map.clear()
        display_names = []

        if not found_files_with_paths:
            self.bookmarks_combobox_label.config(text="Set (None found):")
            self.bookmarks_combobox.set("")
            self.bookmarks_combobox.config(values=[], state=tk.DISABLED)
            return

        self.bookmarks_combobox_label.config(text="Set:")
        for display_name, full_path in found_files_with_paths:
            self.bookmark_files_map[display_name] = full_path
            display_names.append(display_name)

        self.bookmarks_combobox.config(values=display_names, state="readonly")
        # Default selection will be handled by _try_load_default_ini

    def _on_bookmark_set_selected(self, event=None):
        selected_display_name = self.selected_bookmark_file_var.get()
        if selected_display_name and selected_display_name in self.bookmark_files_map:
            filepath_to_load = self.bookmark_files_map[selected_display_name]
            self._load_ini_file(filepath_arg=filepath_to_load)

    def _try_load_default_ini(self):
        """Attempts to load a default bookmark file based on Combobox content."""
        available_files = self.bookmarks_combobox.cget("values")
        if not available_files:
            # No files found in bookmarks/ directory, so nothing to load by default here.
            # The dialog will open with "No file loaded."
            self.loaded_file_label_var.set("No bookmark sets found in 'bookmarks/' directory.")
            return

        file_to_load_display_name = None
        default_ini_name = "default.ini"

        if default_ini_name in available_files:
            file_to_load_display_name = default_ini_name
        elif available_files: # If default.ini not found, but others exist
            file_to_load_display_name = available_files[0] # Load the first one in the sorted list

        if file_to_load_display_name:
            self.selected_bookmark_file_var.set(file_to_load_display_name) # Set combobox selection
            # Get the full path from our map
            filepath_to_load = self.bookmark_files_map.get(file_to_load_display_name)
            if filepath_to_load:
                self._load_ini_file(filepath_arg=filepath_to_load)
            else:
                # This case should ideally not happen if map is populated correctly
                print(f"Error: Display name '{file_to_load_display_name}' not found in bookmark_files_map.")
                self.loaded_file_label_var.set(f"Error finding path for {file_to_load_display_name}.")
        else:
            # This means available_files was empty, already handled at the start.
            # Or, if logic changes, could mean no suitable default.
            self.loaded_file_label_var.set("Select a bookmark set.") # Prompt if no default auto-loaded

    def _load_ini_file(self, filepath_arg=None): # Renamed parameter for clarity
        actual_filepath_to_load = None
        is_default_load_attempt = False

        if filepath_arg and os.path.isfile(filepath_arg):
            actual_filepath_to_load = filepath_arg
            is_default_load_attempt = True
        else:
            # No valid filepath_arg provided (or button was clicked), open file dialog
            selected_via_dialog = filedialog.askopenfilename(
                title="Open INI File",
                filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
                parent=self.top
            )
            if not selected_via_dialog: # User cancelled dialog
                return
            actual_filepath_to_load = selected_via_dialog
            is_default_load_attempt = False # User explicitly selected this one

        import configparser
        parser = configparser.ConfigParser()
        try:
            # Read with UTF-8 encoding
            parsed_files = parser.read(actual_filepath_to_load, encoding='utf-8')
            if not parsed_files:
                if is_default_load_attempt and self.current_ini_file and self.current_ini_file != actual_filepath_to_load:
                    # Default load failed, but a user-loaded file is active.
                    print(f"Debug: Default INI file '{os.path.basename(actual_filepath_to_load)}' not found or failed to parse. Keeping '{os.path.basename(self.current_ini_file) if self.current_ini_file else 'None'}'.")
                else:
                    # User-selected file failed, or it was the current file that failed, or no file previously loaded.
                    messagebox.showerror("Error", f"Could not read or parse INI file: {os.path.basename(actual_filepath_to_load)}", parent=self.top)
                    self._handle_load_error()
                return

            # Successfully parsed, now update state
            self.bookmarks_data.clear()
            for section in parser.sections():
                self.bookmarks_data[section] = {}
                for description_key, url_value in parser.items(section):
                    self.bookmarks_data[section][description_key] = url_value

            self.current_ini_file = actual_filepath_to_load
            self.loaded_file_label_var.set(f"Loaded: {os.path.basename(actual_filepath_to_load)}")
            self._populate_treeview()
            self.open_url_button.config(state=tk.DISABLED) # Reset button state on new load

        except configparser.Error as e:
            if is_default_load_attempt and self.current_ini_file and self.current_ini_file != actual_filepath_to_load:
                 print(f"Debug: Error parsing default INI file '{os.path.basename(actual_filepath_to_load)}': {e}. Keeping previously loaded file.")
            else:
                messagebox.showerror("INI Parsing Error", f"Error parsing INI file '{os.path.basename(actual_filepath_to_load)}':\n{e}", parent=self.top)
                self._handle_load_error()
        except Exception as e:
            if is_default_load_attempt and self.current_ini_file and self.current_ini_file != actual_filepath_to_load:
                print(f"Debug: Unexpected error loading default INI file '{os.path.basename(actual_filepath_to_load)}': {e}. Keeping previously loaded file.")
            else:
                messagebox.showerror("Error", f"An unexpected error occurred while loading '{os.path.basename(actual_filepath_to_load)}':\n{e}", parent=self.top)
                self._handle_load_error()

    def _handle_load_error(self):
        self.bookmarks_data.clear()
        self.current_ini_file = None
        self.loaded_file_label_var.set("Error loading file or no file loaded.")
        self._clear_treeview()

    def _clear_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _populate_treeview(self): # For single-file display
        self._clear_treeview()
        # This method now explicitly uses self.bookmarks_data (the currently loaded single file)
        if not self.bookmarks_data:
            # Potentially set a message in Treeview if it's empty, or rely on status label
            return

        padding_spaces = "   "

        for group_name, items in sorted(self.bookmarks_data.items()): # Sort groups
            group_node_id = self.tree.insert("", tk.END, text=group_name, open=True, tags=('group',))

            sorted_items = sorted(items.items())

            for description, url in sorted_items:
                padded_description = padding_spaces + description
                padded_url = padding_spaces + url
                self.tree.insert(group_node_id, tk.END, values=(padded_description, padded_url), tags=('item',))

        self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
        self.tree.tag_configure('item') # Ensure 'item' tag is configured for selection logic

    def _filter_display(self, *args):
        search_term = self.search_var.get().lower()
        self._clear_treeview()
        padding_spaces = "   "

        is_global = self.global_search_var.get()

        if not search_term and not is_global:
            # No search term and local search: show current file
            self._populate_treeview()
            return

        if not search_term and is_global:
            # No search term and global search: show all items from all files
            # Ensure all_bookmark_sets_data is iterated in a sorted order of filenames for consistency
            for ini_filename, file_data in sorted(self.all_bookmark_sets_data.items()):
                file_node_id = self.tree.insert("", tk.END, text=ini_filename, open=True, tags=('file_header',))
                for group_name, items in sorted(file_data.items()): # Sort groups within each file
                    group_node_id = self.tree.insert(file_node_id, tk.END, text=group_name, open=True, tags=('group',))
                    for description, url in sorted(items.items()): # Sort items within each group
                        padded_description = padding_spaces + description
                        padded_url = padding_spaces + url
                        self.tree.insert(group_node_id, tk.END, values=(padded_description, padded_url), tags=('item',))
            self.tree.tag_configure('file_header', font=tkfont.Font(weight='bold', slant='italic'))
            self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
            self.tree.tag_configure('item')
            return

        # If there IS a search term:
        if is_global:
            # Global Search with a search term
            # Ensure all_bookmark_sets_data is iterated in a sorted order of filenames
            for ini_filename, file_data in sorted(self.all_bookmark_sets_data.items()):
                file_node_id_for_this_file = None
                for group_name, items in sorted(file_data.items()): # Sort groups
                    group_node_id_for_this_group = None
                    for description, url in sorted(items.items()): # Sort items
                        if search_term in description.lower() or search_term in url.lower():
                            if file_node_id_for_this_file is None:
                                file_node_id_for_this_file = self.tree.insert("", tk.END, text=ini_filename, open=True, tags=('file_header',))
                            if group_node_id_for_this_group is None:
                                group_node_id_for_this_group = self.tree.insert(file_node_id_for_this_file, tk.END, text=group_name, open=True, tags=('group',))

                            padded_description = padding_spaces + description
                            padded_url = padding_spaces + url
                            self.tree.insert(group_node_id_for_this_group, tk.END, values=(padded_description, padded_url), tags=('item',))
            self.tree.tag_configure('file_header', font=tkfont.Font(weight='bold', slant='italic'))
            self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
            self.tree.tag_configure('item')
        else:
            # Local Search with a search term (current file only)
            if not self.bookmarks_data:
                return

            for group_name, items in sorted(self.bookmarks_data.items()): # Sort groups
                group_node_id_for_this_group = None
                for description, url in sorted(items.items()): # Sort items
                    if search_term in description.lower() or search_term in url.lower():
                        if group_node_id_for_this_group is None:
                            group_node_id_for_this_group = self.tree.insert("", tk.END, text=group_name, open=True, tags=('group',))

                        padded_description = padding_spaces + description
                        padded_url = padding_spaces + url
                        self.tree.insert(group_node_id_for_this_group, tk.END, values=(padded_description, padded_url), tags=('item',))
            self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
            self.tree.tag_configure('item')


    def _open_selected_url(self, event=None):
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            return

        item_tags = self.tree.item(selected_item_id, "tags")

        # Only proceed if it's a bookmark item
        if 'item' not in item_tags:
            # Optionally, if it's a group or file_header and event is double-click, toggle open/close state
            # Double-click binding <Double-1> passes an event. Simple select might not.
            if event and hasattr(event, 'type') and str(event.type) == "ButtonPress" and event.num == 1:
                 # Check if it's a node that can be opened/closed
                 if 'group' in item_tags or 'file_header' in item_tags:
                     try: # Defensive: item might not exist if tree changes rapidly
                        self.tree.item(selected_item_id, open=not self.tree.item(selected_item_id, "open"))
                     except tk.TclError:
                        pass
            return

        try:
            item_values = self.tree.item(selected_item_id, "values")
            # Values are (padded_description, padded_url)
            if item_values and len(item_values) >= 2:
                padded_url = item_values[1]
                # Remove the leading padding spaces before opening
                url_to_open = padded_url.lstrip() # Remove leading spaces

                if url_to_open:
                    import webbrowser
                    try:
                        webbrowser.open_new_tab(url_to_open)
                    except Exception as e:
                        messagebox.showerror("Error Opening URL", f"Could not open URL: {url_to_open}\nError: {e}", parent=self.top)
                else:
                    messagebox.showwarning("No URL", "Selected item does not have a valid URL after stripping padding.", parent=self.top)
            else:
                messagebox.showwarning("No URL Data", "Could not retrieve URL for the selected item.", parent=self.top)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while trying to open URL: {e}", parent=self.top)


    def _on_tree_select(self, event=None):
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            self.open_url_button.config(state=tk.DISABLED)
            return

        item_tags = self.tree.item(selected_item_id, "tags")

        # Enable button only if it's an actual bookmark item
        if 'item' in item_tags:
            self.open_url_button.config(state=tk.NORMAL)
        else:
            self.open_url_button.config(state=tk.DISABLED)


class ExcelToHtmlDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("Excel to HTML Site Generator")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(False, False)

        # Variables
        self.input_excel_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.site_title_var = tk.StringVar(value="Excel Data Site")

        # --- Main Frame ---
        main_frame = ttk.Frame(self.top, padding=15)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1) # Allow entry fields to expand

        # Input Excel File
        ttk.Label(main_frame, text="Excel File (.xlsx):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        input_file_entry = ttk.Entry(main_frame, textvariable=self.input_excel_file_var, width=50)
        input_file_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        input_file_button = ttk.Button(main_frame, text="Browse...", command=self._browse_input_file)
        input_file_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        # Output Directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        output_dir_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50)
        output_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        output_dir_button = ttk.Button(main_frame, text="Browse...", command=self._browse_output_dir)
        output_dir_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)

        # Site Title
        ttk.Label(main_frame, text="Site Title (Optional):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        site_title_entry = ttk.Entry(main_frame, textvariable=self.site_title_var, width=50)
        site_title_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        # Generate Button
        generate_button = ttk.Button(main_frame, text="Generate HTML Site", command=self._generate_html_site) # Changed command
        generate_button.grid(row=3, column=0, columnspan=3, pady=15)

        # Progress Bar (Optional - for future use or simple feedback)
        # self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        # self.progress_bar.grid(row=4, column=0, columnspan=3, pady=10)


        # Set initial focus and center dialog
        input_file_entry.focus_set()
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        self.top.minsize(550, 220) # Adjusted minsize
        # self.top.resizable(True, True) # Keep resizable if progressbar or more info added later

    def _browse_input_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx")],
            parent=self.top
        )
        if filepath:
            self.input_excel_file_var.set(filepath)

    def _browse_output_dir(self):
        dirpath = filedialog.askdirectory(
            title="Select Output Directory",
            parent=self.top
        )
        if dirpath:
            self.output_dir_var.set(dirpath)

    # def _generate_html_site_stub(self): # Stub is no longer needed
    #     # Placeholder for core logic
    #     # messagebox.showinfo("Not Implemented", "HTML site generation logic not yet implemented.", parent=self.top)
    #     # Basic validation example:
    #     # if not self.input_excel_file_var.get() or not self.output_dir_var.get():
    #     #     messagebox.showerror("Input Missing", "Please select an input Excel file and an output directory.", parent=self.top)
    #     #     return
    #     # print(f"Input File: {self.input_excel_file_var.get()}")
    #     # print(f"Output Dir: {self.output_dir_var.get()}")
    #     # print(f"Site Title: {self.site_title_var.get()}")
    #     self._generate_html_site() # Call the actual generation method

    def _generate_html_site(self):
        input_file = self.input_excel_file_var.get()
        user_selected_output_dir = self.output_dir_var.get()
        site_title = self.site_title_var.get().strip()

        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Input Error", "Please select a valid Excel input file.", parent=self.top)
            return

        # Determine base output directory
        if not user_selected_output_dir:
            # Default to same directory as input file
            base_output_dir = os.path.dirname(input_file)
            self.output_dir_var.set(base_output_dir) # Update UI for user info, though not strictly necessary for logic
        else:
            base_output_dir = user_selected_output_dir
            if not os.path.isdir(base_output_dir):
                messagebox.showerror("Input Error", "The selected output directory is not valid.", parent=self.top)
                return

        # Create subfolder named after the Excel file
        excel_filename_no_ext = os.path.splitext(os.path.basename(input_file))[0]
        # Basic sanitization for folder name (can be more robust if needed)
        sanitized_folder_name = re.sub(r'[^\w\s-]', '', excel_filename_no_ext).strip().replace(' ', '_')
        if not sanitized_folder_name: # Handle case where filename was all special chars
            sanitized_folder_name = "excel_site_output"

        final_output_path = os.path.join(base_output_dir, sanitized_folder_name)

        try:
            os.makedirs(final_output_path, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Output Error", f"Could not create output subfolder: {final_output_path}\nError: {e}", parent=self.top)
            return

        try:
            import openpyxl
        except ImportError:
            messagebox.showerror("Dependency Missing",
                                 "The 'openpyxl' library is not installed. Please install it (e.g., pip install openpyxl).",
                                 parent=self.top)
            return

        # Basic CSS for styling
        # More advanced styling could involve a separate CSS file.
        basic_css = """
        <style>
            body {
                font-family: sans-serif;
                margin: 0;
                background-color: #f4f4f4;
                color: #333;
                display: flex; /* For sidebar layout */
                min-height: 100vh;
            }
            .sidebar {
                width: 220px; /* Width of the sidebar */
                background-color: #333;
                color: #fff;
                padding: 15px;
                height: 100vh; /* Full height */
                position: fixed; /* Fixed Sidebar (stay in place on scroll) */
                overflow-y: auto; /* Scrollable if content overflows */
            }
            .sidebar h2 {
                text-align: center;
                color: #fff;
                margin-top: 0;
            }
            .sidebar ul {
                list-style-type: none;
                padding: 0;
            }
            .sidebar ul li a {
                display: block;
                color: #fff;
                padding: 8px 10px;
                text-decoration: none;
                border-radius: 4px;
            }
            .sidebar ul li a:hover, .sidebar ul li a.active {
                background-color: #555;
            }
            .main-content {
                margin-left: 240px; /* Same as sidebar width + some padding */
                padding: 20px;
                flex-grow: 1; /* Takes remaining space */
                background-color: #fff;
                /* Removed container style, main-content is the container now */
            }
            header {
                /* Header is now part of main-content or can be global if needed */
                /* For this layout, let's assume header is part of main-content page title */
                text-align: center;
                margin-bottom:20px;
            }
            /* nav ul - old styles removed/adapted to .sidebar ul */
            /* .container - old styles removed/adapted to .main-content */
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f0f0f0; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f1f1f1; }
            h1, h2 { color: #333; }
            a { color: #007bff; }
            a:hover { color: #0056b3; }
            /* Filter input and button styling */
            #filterInput {
                padding: 8px;
                margin-bottom: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                width: calc(100% - 120px); /* Adjust width considering the button */
                box-sizing: border-box;
            }
            button {
                padding: 8px 12px;
                background-color: #5cb85c;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin-left: 5px;
            }
            button:hover {
                background-color: #4cae4c;
            }
        </style>
        """

        def sanitize_filename(name):
            # Basic sanitization for filenames
            name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
            return name if name else "untitled_sheet"

        try:
            workbook = openpyxl.load_workbook(input_file, read_only=True) # read_only for performance
            sheet_names = workbook.sheetnames

            generated_files_info = [] # To store (sheet_name, html_filename, row_count, col_count)

            # Prepare sheet info and sort alphabetically by sheet name for navigation
            # This loop also gathers row/column counts needed for the overview page.
            for sheet_name in sheet_names:
                ws = workbook[sheet_name]
                html_filename = sanitize_filename(sheet_name) + ".html"
                generated_files_info.append({
                    "name": sheet_name,
                    "file": html_filename,
                    "original_name": sheet_name,
                    "row_count": ws.max_row,
                    "col_count": ws.max_column
                })

            generated_files_info.sort(key=lambda x: x["name"])

            # --- Generate index.html (which is now the overview page) ---
            index_html_path = os.path.join(final_output_path, "index.html")
            with open(index_html_path, "w", encoding="utf-8") as f_index:
                f_index.write(f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n")
                index_page_title = f"{site_title if site_title else excel_filename_no_ext} - Overview"
                f_index.write(f"<title>{index_page_title}</title>\n{basic_css}\n</head>\n<body>\n")

                # Sidebar Navigation for index.html (overview page)
                f_index.write("<div class=\"sidebar\">\n")
                f_index.write(f"  <h2>{site_title if site_title else 'Navigation'}</h2>\n  <ul>\n")
                f_index.write(f"    <li><a href=\"index.html\" class=\"active\">Home (Overview)</a></li>\n")
                for sheet_info_nav in generated_files_info:
                    f_index.write(f"    <li><a href=\"{sheet_info_nav['file']}\">{sheet_info_nav['name']}</a></li>\n")
                f_index.write("  </ul>\n</div>\n") # End sidebar

                # Main content for index.html (overview page)
                f_index.write("<div class=\"main-content\">\n")
                main_header_text = f"{site_title} Overview" if site_title else "Excel Data Overview"
                f_index.write(f"  <header><h1>{main_header_text}</h1></header>\n")
                f_index.write("  <h2>Sheet Summary:</h2>\n  <table>\n")
                f_index.write("    <tr><th>Sheet Name</th><th>Number of Rows</th><th>Number of Columns</th></tr>\n")
                for sheet_info in generated_files_info:
                    f_index.write(f"    <tr>\n")
                    f_index.write(f"      <td><a href=\"{sheet_info['file']}\">{sheet_info['name']}</a></td>\n")
                    f_index.write(f"      <td>{sheet_info['row_count']}</td>\n")
                    f_index.write(f"      <td>{sheet_info['col_count']}</td>\n")
                    f_index.write(f"    </tr>\n")
                f_index.write("  </table>\n")
                f_index.write("</div>\n") # End main-content
                f_index.write("</body>\n</html>")

            # --- Generate HTML for each sheet ---
            for current_sheet_info in generated_files_info:
                sheet_name = current_sheet_info["original_name"]
                html_filename = current_sheet_info["file"]
                sheet_html_path = os.path.join(final_output_path, html_filename)
                ws = workbook[sheet_name] # ws was already fetched for row/col count, could optimize if memory is a concern for huge files.

                with open(sheet_html_path, "w", encoding="utf-8") as f_sheet:
                    f_sheet.write(f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n")
                    page_specific_title = f"{sheet_name} - {site_title}" if site_title else sheet_name
                    f_sheet.write(f"<title>{page_specific_title}</title>\n{basic_css}\n</head>\n<body>\n")

                    # Sidebar Navigation for sheet pages
                    f_sheet.write("<div class=\"sidebar\">\n")
                    f_sheet.write(f"  <h2>{site_title if site_title else 'Navigation'}</h2>\n  <ul>\n")
                    f_sheet.write(f"    <li><a href=\"index.html\">Home (Overview)</a></li>\n") # Link to the new index/overview
                    for other_sheet_info in generated_files_info:
                        active_class = ' class="active"' if other_sheet_info["file"] == html_filename else ''
                        f_sheet.write(f"    <li><a href=\"{other_sheet_info['file']}\"{active_class}>{other_sheet_info['name']}</a></li>\n")
                    f_sheet.write("  </ul>\n</div>\n") # End sidebar

                    # Main content for sheet pages
                    f_sheet.write("<div class=\"main-content\">\n")
                    f_sheet.write(f"  <header><h1>{sheet_name}</h1></header>\n") # Sheet name as header
                    f_sheet.write("  <h2>Sheet Data:</h2>\n")

                    # Add filter input and button
                    f_sheet.write("  <div>\n")
                    f_sheet.write(f"    <input type=\"text\" id=\"filterInput\" onkeyup=\"filterTable()\" placeholder=\"Filter table content...\" title=\"Type in a name to filter the table\">\n")
                    f_sheet.write(f"    <button onclick=\"clearFilter()\">Clear Filter</button>\n")
                    f_sheet.write("  </div>\n")

                    f_sheet.write("  <table id=\"sheetTable\">\n") # Add id to table

                    first_row = True
                    for row_idx, row in enumerate(ws.iter_rows()):
                        f_sheet.write("  <tr>\n")
                        for cell in row:
                            cell_value = cell.value if cell.value is not None else ""
                            if first_row: # This is the header row
                                f_sheet.write(f"    <th>{str(cell_value)}</th>\n")
                            else: # These are data rows
                                f_sheet.write(f"    <td>{str(cell_value)}</td>\n")
                        f_sheet.write("  </tr>\n")
                        if first_row:
                            first_row = False
                    f_sheet.write("  </table>\n")
                    f_sheet.write("</div>\n") # End main-content

                    # Add JavaScript for filtering
                    filter_script = """
                    <script>
                    function filterTable() {
                      // Declare variables
                      var input, filter, table, tr, td, i, j, txtValue;
                      input = document.getElementById("filterInput");
                      filter = input.value.toUpperCase();
                      table = document.getElementById("sheetTable");
                      tr = table.getElementsByTagName("tr");

                      // Loop through all table rows (starting from 1 to skip header row 'th')
                      for (i = 1; i < tr.length; i++) {
                        let rowContainsFilterText = false;
                        // Loop through all cells in the current row
                        td = tr[i].getElementsByTagName("td");
                        for (j = 0; j < td.length; j++) {
                          if (td[j]) {
                            txtValue = td[j].textContent || td[j].innerText;
                            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                              rowContainsFilterText = true;
                              break; // Found filter text in this row, no need to check other cells
                            }
                          }
                        }
                        if (rowContainsFilterText) {
                          tr[i].style.display = "";
                        } else {
                          tr[i].style.display = "none";
                        }
                      }
                    }

                    function clearFilter() {
                      var input, table, tr, i;
                      input = document.getElementById("filterInput");
                      input.value = ""; // Clear the input field
                      table = document.getElementById("sheetTable");
                      tr = table.getElementsByTagName("tr");

                      // Loop through all table rows (starting from 1 to skip header row) and display them
                      for (i = 1; i < tr.length; i++) {
                        tr[i].style.display = "";
                      }
                    }
                    </script>
                    """
                    f_sheet.write(filter_script)
                    f_sheet.write("</body>\n</html>")

            messagebox.showinfo("Success",
                                f"HTML site generated successfully in:\n{final_output_path}\n\nOpen 'index.html' inside this folder to view.",
                                parent=self.top)

        except FileNotFoundError:
            messagebox.showerror("Error", f"Input Excel file not found: {input_file}", parent=self.top)
        except openpyxl.utils.exceptions.InvalidFileException: # Ensure openpyxl is imported for this exception
            messagebox.showerror("Error", f"Invalid Excel file format. Please provide a .xlsx file.", parent=self.top)
        except Exception as e:
            messagebox.showerror("Generation Error", f"An error occurred: {e}", parent=self.top)


class SqlParserDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("SQL Parser")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(False, False)

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.grid_rowconfigure(1, weight=1) # SQL input text
        main_frame.grid_rowconfigure(3, weight=1) # JSON output text
        main_frame.grid_columnconfigure(0, weight=1)


        # SQL Input Area
        ttk.Label(main_frame, text="SQL Query:").grid(row=0, column=0, sticky=tk.W, pady=(0,2))

        sql_input_frame = ttk.Frame(main_frame)
        sql_input_frame.grid(row=1, column=0, sticky="nsew", pady=(0,5))
        sql_input_frame.rowconfigure(0, weight=1)
        sql_input_frame.columnconfigure(0, weight=1)

        self.sql_input_text = tk.Text(sql_input_frame, height=8, width=70, wrap=tk.WORD, undo=True)
        sql_input_scrollbar = ttk.Scrollbar(sql_input_frame, orient=tk.VERTICAL, command=self.sql_input_text.yview)
        self.sql_input_text.config(yscrollcommand=sql_input_scrollbar.set)
        self.sql_input_text.grid(row=0, column=0, sticky="nsew")
        sql_input_scrollbar.grid(row=0, column=1, sticky="ns")
        self.sql_input_text.focus_set()
        self.sql_input_text.insert("1.0", "SELECT column1, column2\nFROM table_name\nWHERE column1 = 'value';")


        # JSON Output Area
        ttk.Label(main_frame, text="Parsed JSON Output:").grid(row=2, column=0, sticky=tk.W, pady=(5,2))

        json_output_frame = ttk.Frame(main_frame)
        json_output_frame.grid(row=3, column=0, sticky="nsew", pady=(0,10))
        json_output_frame.rowconfigure(0, weight=1)
        json_output_frame.columnconfigure(0, weight=1)

        self.json_output_text = tk.Text(json_output_frame, height=12, width=70, wrap=tk.WORD, undo=False)
        json_output_scrollbar = ttk.Scrollbar(json_output_frame, orient=tk.VERTICAL, command=self.json_output_text.yview)
        self.json_output_text.config(yscrollcommand=json_output_scrollbar.set)
        self.json_output_text.grid(row=0, column=0, sticky="nsew")
        json_output_scrollbar.grid(row=0, column=1, sticky="ns")
        self.json_output_text.config(state=tk.DISABLED) # Read-only


        # Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=tk.E, pady=(5,0))

        self.parse_sql_button = ttk.Button(button_frame, text="Parse SQL", command=self._parse_sql_query_stub)
        self.parse_sql_button.pack(side=tk.LEFT, padx=(0,5))

        self.copy_json_button = ttk.Button(button_frame, text="Copy JSON", command=self._copy_json_output_stub, state=tk.DISABLED)
        self.copy_json_button.pack(side=tk.LEFT)

        # Center dialog
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        # Ensure width is reasonable before centering
        min_width = 500
        min_height = 450
        current_width = self.top.winfo_width()
        current_height = self.top.winfo_height()
        final_width = max(current_width, min_width)
        final_height = max(current_height, min_height)
        self.top.geometry(f"{final_width}x{final_height}+{x}+{y}")
        self.top.minsize(min_width, min_height)
        self.top.resizable(True, True)

        # Bind Parse SQL button to the actual parsing method
        self.parse_sql_button.config(command=self._parse_sql_query)
        # Bind Copy JSON button to the actual copy method (will be implemented later)
        # self.copy_json_button.config(command=self._copy_json_output)


    def _parse_sql_query(self):
        try:
            from mo_sql_parsing import parse as parse_sql
            from mo_sql_parsing.exceptions import MoSQLError
            import json
        except ImportError:
            messagebox.showerror("Dependency Missing",
                                 "The 'mo-sql-parsing' library is not installed. Please install it (e.g., pip install mo-sql-parsing).",
                                 parent=self.top)
            self.json_output_text.config(state=tk.NORMAL)
            self.json_output_text.delete("1.0", tk.END)
            self.json_output_text.insert("1.0", "Error: 'mo-sql-parsing' library not found.")
            self.json_output_text.config(state=tk.DISABLED)
            self.copy_json_button.config(state=tk.DISABLED)
            return

        sql_query = self.sql_input_text.get("1.0", tk.END + "-1c").strip()

        self.json_output_text.config(state=tk.NORMAL)
        self.json_output_text.delete("1.0", tk.END)

        if not sql_query:
            messagebox.showwarning("Input Empty", "SQL query input is empty.", parent=self.top)
            self.json_output_text.config(state=tk.DISABLED)
            self.copy_json_button.config(state=tk.DISABLED)
            return

        try:
            parsed_dict = parse_sql(sql_query)
            json_output_str = json.dumps(parsed_dict, indent=2)
            self.json_output_text.insert("1.0", json_output_str)
            self.copy_json_button.config(state=tk.NORMAL)
        except MoSQLError as e:
            error_message = f"Error parsing SQL (MoSQLError):\n{str(e)}"
            self.json_output_text.insert("1.0", error_message)
            self.copy_json_button.config(state=tk.NORMAL) # Allow copying of error message
        except Exception as e:
            error_message = f"An unexpected error occurred during parsing:\n{str(e)}"
            self.json_output_text.insert("1.0", error_message)
            self.copy_json_button.config(state=tk.NORMAL) # Allow copying of error message
        finally:
            self.json_output_text.config(state=tk.DISABLED)


    def _copy_json_output(self):
        json_content = self.json_output_text.get("1.0", tk.END + "-1c")
        if json_content.strip(): # Check if there's actual content (not just whitespace)
            try:
                self.top.clipboard_clear()
                self.top.clipboard_append(json_content)
                messagebox.showinfo("Copied", "JSON output copied to clipboard.", parent=self.top)
            except tk.TclError:
                messagebox.showerror("Error", "Could not copy to clipboard. TclError occurred.", parent=self.top)
        else:
            messagebox.showwarning("Empty Output", "There is no JSON output to copy.", parent=self.top)

    # Ensure the button command is updated from the stub name
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("SQL Parser")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(False, False)

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.grid_rowconfigure(1, weight=1) # SQL input text
        main_frame.grid_rowconfigure(3, weight=1) # JSON output text
        main_frame.grid_columnconfigure(0, weight=1)


        # SQL Input Area
        ttk.Label(main_frame, text="SQL Query:").grid(row=0, column=0, sticky=tk.W, pady=(0,2))

        sql_input_frame = ttk.Frame(main_frame)
        sql_input_frame.grid(row=1, column=0, sticky="nsew", pady=(0,5))
        sql_input_frame.rowconfigure(0, weight=1)
        sql_input_frame.columnconfigure(0, weight=1)

        self.sql_input_text = tk.Text(sql_input_frame, height=8, width=70, wrap=tk.WORD, undo=True)
        sql_input_scrollbar = ttk.Scrollbar(sql_input_frame, orient=tk.VERTICAL, command=self.sql_input_text.yview)
        self.sql_input_text.config(yscrollcommand=sql_input_scrollbar.set)
        self.sql_input_text.grid(row=0, column=0, sticky="nsew")
        sql_input_scrollbar.grid(row=0, column=1, sticky="ns")
        self.sql_input_text.focus_set()
        self.sql_input_text.insert("1.0", "SELECT column1, column2\nFROM table_name\nWHERE column1 = 'value';")


        # JSON Output Area
        ttk.Label(main_frame, text="Parsed JSON Output:").grid(row=2, column=0, sticky=tk.W, pady=(5,2))

        json_output_frame = ttk.Frame(main_frame)
        json_output_frame.grid(row=3, column=0, sticky="nsew", pady=(0,10))
        json_output_frame.rowconfigure(0, weight=1)
        json_output_frame.columnconfigure(0, weight=1)

        self.json_output_text = tk.Text(json_output_frame, height=12, width=70, wrap=tk.WORD, undo=False)
        json_output_scrollbar = ttk.Scrollbar(json_output_frame, orient=tk.VERTICAL, command=self.json_output_text.yview)
        self.json_output_text.config(yscrollcommand=json_output_scrollbar.set)
        self.json_output_text.grid(row=0, column=0, sticky="nsew")
        json_output_scrollbar.grid(row=0, column=1, sticky="ns")
        self.json_output_text.config(state=tk.DISABLED) # Read-only


        # Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=tk.E, pady=(5,0))

        self.parse_sql_button = ttk.Button(button_frame, text="Parse SQL", command=self._parse_sql_query) # Already updated
        self.parse_sql_button.pack(side=tk.LEFT, padx=(0,5))

        self.copy_json_button = ttk.Button(button_frame, text="Copy JSON", command=self._copy_json_output, state=tk.DISABLED) # Update command here
        self.copy_json_button.pack(side=tk.LEFT)

        # Center dialog
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        # Ensure width is reasonable before centering
        min_width = 500
        min_height = 450
        current_width = self.top.winfo_width()
        current_height = self.top.winfo_height()
        final_width = max(current_width, min_width)
        final_height = max(current_height, min_height)
        self.top.geometry(f"{final_width}x{final_height}+{x}+{y}")
        self.top.minsize(min_width, min_height)
        self.top.resizable(True, True)

        # Bind Parse SQL button to the actual parsing method
        # self.parse_sql_button.config(command=self._parse_sql_query) # Already done above
        # Bind Copy JSON button to the actual copy method
        # self.copy_json_button.config(command=self._copy_json_output) # Done at button creation


class RestApiClientDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root # Parent window for dialog transience
        self.top = tk.Toplevel(self.root)
        self.top.title("REST API Client")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(False, False) # Start with non-resizable

        # --- Variables ---
        self.url_var = tk.StringVar(value="https://jsonplaceholder.typicode.com/todos/1") # Sample URL
        self.method_var = tk.StringVar(value="GET")
        self.http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

        self.body_type_var = tk.StringVar(value="JSON")
        self.body_types = ["JSON", "XML", "Plain Text", "None"]

        # --- Main Frame ---
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        # main_frame.grid_rowconfigure(1, weight=1) # For request_notebook
        # main_frame.grid_rowconfigure(3, weight=1) # For response_notebook
        # main_frame.grid_columnconfigure(0, weight=1)


        # --- Request Top Section (URL, Method) ---
        request_setup_frame = ttk.Frame(main_frame)
        request_setup_frame.pack(fill=tk.X, pady=(0,10)) # Changed to pack

        ttk.Label(request_setup_frame, text="URL:").pack(side=tk.LEFT, padx=(0,5))
        url_entry = ttk.Entry(request_setup_frame, textvariable=self.url_var, width=70)
        url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,10))
        url_entry.focus_set()

        ttk.Label(request_setup_frame, text="Method:").pack(side=tk.LEFT, padx=(0,5))
        method_combobox = ttk.Combobox(request_setup_frame, textvariable=self.method_var,
                                       values=self.http_methods, state="readonly", width=10)
        method_combobox.pack(side=tk.LEFT)
        method_combobox.bind("<<ComboboxSelected>>", self._on_method_change)


        # --- Request Details Notebook (Headers, Body) ---
        request_notebook = ttk.Notebook(main_frame)
        request_notebook.pack(expand=True, fill=tk.BOTH, pady=(0,10)) # Changed to pack

        # Request Headers Tab
        req_headers_frame = ttk.Frame(request_notebook, padding=5)
        request_notebook.add(req_headers_frame, text="Headers")
        ttk.Label(req_headers_frame, text="Enter headers (HeaderName: HeaderValue), one per line:").pack(anchor=tk.W, pady=(0,2))
        self.req_headers_text = tk.Text(req_headers_frame, height=5, width=80, wrap=tk.WORD, undo=True)
        self.req_headers_text.pack(expand=True, fill=tk.BOTH)
        self.req_headers_text.insert("1.0", "User-Agent: JulesTextEditor/1.0\nAccept: */*")


        # Request Body Tab
        self.req_body_frame = ttk.Frame(request_notebook, padding=5) # Store as self for enable/disable
        request_notebook.add(self.req_body_frame, text="Body")

        body_options_frame = ttk.Frame(self.req_body_frame)
        body_options_frame.pack(fill=tk.X, pady=(0,5))
        ttk.Label(body_options_frame, text="Body Type:").pack(side=tk.LEFT, padx=(0,5))
        self.body_type_combo = ttk.Combobox(body_options_frame, textvariable=self.body_type_var,
                                       values=self.body_types, state="readonly", width=15)
        self.body_type_combo.pack(side=tk.LEFT)
        self.body_type_combo.bind("<<ComboboxSelected>>", self._on_body_type_change)

        self.req_body_text = tk.Text(self.req_body_frame, height=8, width=80, wrap=tk.WORD, undo=True)
        self.req_body_text.pack(expand=True, fill=tk.BOTH)
        self.req_body_text.insert("1.0", "{\n  \"key\": \"value\",\n  \"example\": true\n}")


        # --- Action Button (Send) ---
        send_button = ttk.Button(main_frame, text="Send Request", command=self._send_request)
        send_button.pack(pady=5) # Changed to pack


        # --- Response Status Display ---
        self.status_label_var = tk.StringVar(value="Status: -")
        status_display_label = ttk.Label(main_frame, textvariable=self.status_label_var, font=("TkDefaultFont", 10, "bold"))
        status_display_label.pack(anchor=tk.W, pady=(5,2)) # Changed to pack


        # --- Response Details Notebook (Body, Headers) ---
        response_notebook = ttk.Notebook(main_frame)
        response_notebook.pack(expand=True, fill=tk.BOTH, pady=(0,10)) # Changed to pack

        # Response Body Tab
        resp_body_frame = ttk.Frame(response_notebook, padding=5)
        response_notebook.add(resp_body_frame, text="Response Body")
        self.resp_body_text = tk.Text(resp_body_frame, height=10, width=80, wrap=tk.WORD, undo=False)
        self.resp_body_text.pack(expand=True, fill=tk.BOTH)
        self.resp_body_text.config(state=tk.DISABLED) # Read-only

        # Response Headers Tab
        resp_headers_frame = ttk.Frame(response_notebook, padding=5)
        response_notebook.add(resp_headers_frame, text="Response Headers")
        self.resp_headers_text = tk.Text(resp_headers_frame, height=8, width=80, wrap=tk.WORD, undo=False)
        self.resp_headers_text.pack(expand=True, fill=tk.BOTH)
        self.resp_headers_text.config(state=tk.DISABLED) # Read-only


        # --- Copy Button ---
        copy_button_frame = ttk.Frame(main_frame)
        copy_button_frame.pack(fill=tk.X, pady=(5,0)) # Changed to pack
        self.copy_resp_body_button = ttk.Button(copy_button_frame, text="Copy Response Body", command=self._copy_response_body, state=tk.DISABLED)
        self.copy_resp_body_button.pack(side=tk.LEFT)

        # Initial UI state based on method
        self._on_method_change()

        # Center dialog
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f"{self.top.winfo_width()}x{self.top.winfo_height()}+{x}+{y}")
        self.top.minsize(500, 600) # Set a minsize after initial geometry
        self.top.resizable(True, True) # Allow resizing

        self.top.bind("<Escape>", lambda e: self.top.destroy())

    def _on_method_change(self, event=None):
        method = self.method_var.get()
        # Methods that typically don't have a request body
        no_body_methods = ["GET", "HEAD", "DELETE", "OPTIONS"] # DELETE can have body, but often doesn't. OPTIONS usually not.

        if method in no_body_methods:
            self.req_body_text.config(state=tk.DISABLED)
            self.body_type_combo.config(state=tk.DISABLED)
            # Optionally clear body text or set body type to None
            # self.body_type_var.set("None")
            # self.req_body_text.delete("1.0", tk.END)
        else: # POST, PUT, PATCH
            self.req_body_text.config(state=tk.NORMAL)
            self.body_type_combo.config(state=tk.NORMAL)

    def _on_body_type_change(self, event=None):
        # This could be used in the future to auto-set Content-Type header
        # or provide sample body structures.
        # Removed automatic header update from here; it's handled in _send_request.
        pass

    def _parse_headers_text(self, headers_str):
        headers = {}
        for line in headers_str.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        return headers

    def _update_headers_text(self, key_to_update, new_value):
        """Updates or adds a header in the req_headers_text widget."""
        current_headers_content = self.req_headers_text.get("1.0", tk.END + "-1c")
        lines = current_headers_content.splitlines()
        found = False
        new_lines = []
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                if key.strip().lower() == key_to_update.lower():
                    new_lines.append(f"{key_to_update}: {new_value}")
                    found = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line) # Keep non-header lines as is (e.g. blank lines)

        if not found:
            new_lines.append(f"{key_to_update}: {new_value}")
            if not current_headers_content.strip(): # If was empty, don't add extra newline at start
                 self.req_headers_text.delete("1.0", tk.END)
                 self.req_headers_text.insert("1.0", "\n".join(new_lines).strip())
            elif not current_headers_content.endswith('\n'): # if no trailing newline, add one before new header
                 self.req_headers_text.insert(tk.END, f"\n{key_to_update}: {new_value}")
            else:
                 self.req_headers_text.insert(tk.END, f"{key_to_update}: {new_value}\n")

        else:
            self.req_headers_text.delete("1.0", tk.END)
            self.req_headers_text.insert("1.0", "\n".join(new_lines))

        # Ensure a trailing newline if there's content, for easier subsequent additions
        final_content = self.req_headers_text.get("1.0", tk.END + "-1c")
        if final_content.strip() and not final_content.endswith('\n'):
            self.req_headers_text.insert(tk.END, "\n")


    def _send_request(self):
        try:
            import requests # Ensure requests is imported
            import json # For pretty printing JSON
        except ImportError:
            messagebox.showerror("Dependency Missing",
                                 "The 'requests' library is not installed. Please install it (e.g., pip install requests).",
                                 parent=self.top)
            self.status_label_var.set("Status: Error - 'requests' library missing")
            return

        url = self.url_var.get()
        method = self.method_var.get()
        headers_str = self.req_headers_text.get("1.0", tk.END + "-1c")
        body_str = self.req_body_text.get("1.0", tk.END + "-1c") if self.req_body_text.cget("state") == tk.NORMAL else None

        if not url:
            messagebox.showerror("Input Error", "URL cannot be empty.", parent=self.top)
            return

        headers = self._parse_headers_text(headers_str)

        # Auto-set Content-Type if body is present and type is specified, and not already in headers
        if body_str and 'content-type' not in (k.lower() for k in headers):
            body_type = self.body_type_var.get()
            if body_type == "JSON":
                headers['Content-Type'] = 'application/json'
            elif body_type == "XML":
                headers['Content-Type'] = 'application/xml'
            elif body_type == "Plain Text":
                headers['Content-Type'] = 'text/plain'
            # Update header text widget if we auto-added
            if 'Content-Type' in headers and not any(h.lower().startswith("content-type:") for h in headers_str.splitlines()):
                 self._update_headers_text("Content-Type", headers['Content-Type'])


        self.status_label_var.set(f"Status: Sending {method} request to {url}...")
        self.top.update_idletasks() # Refresh UI to show "Sending..."

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body_str.encode('utf-8') if body_str else None, # Encode body to bytes
                timeout=10 # Basic timeout
            )

            # --- Response Handling (moved here from placeholder) ---
            self.status_label_var.set(f"Status: {response.status_code} {response.reason}")

            # Display Response Headers
            self.resp_headers_text.config(state=tk.NORMAL)
            self.resp_headers_text.delete("1.0", tk.END)
            for key, value in response.headers.items():
                self.resp_headers_text.insert(tk.END, f"{key}: {value}\n")
            self.resp_headers_text.config(state=tk.DISABLED)

            # Display Response Body
            self.resp_body_text.config(state=tk.NORMAL)
            self.resp_body_text.delete("1.0", tk.END)

            response_content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in response_content_type:
                try:
                    json_body = response.json()
                    pretty_json = json.dumps(json_body, indent=2, sort_keys=True)
                    self.resp_body_text.insert(tk.END, pretty_json)
                except json.JSONDecodeError:
                    self.resp_body_text.insert(tk.END, response.text) # Fallback to raw text
            else:
                self.resp_body_text.insert(tk.END, response.text) # Display raw text for other types

            self.resp_body_text.config(state=tk.DISABLED)
            self.copy_resp_body_button.config(state=tk.NORMAL if response.text else tk.DISABLED)

        except requests.exceptions.Timeout:
            messagebox.showerror("Request Error", "Request timed out.", parent=self.top)
            self.status_label_var.set("Status: Error - Timeout")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Request Error", "Could not connect to the server. Check the URL and network connection.", parent=self.top)
            self.status_label_var.set("Status: Error - Connection Failed")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Request Error", f"An error occurred: {e}", parent=self.top)
            self.status_label_var.set(f"Status: Error - {type(e).__name__}")
            # Clear response areas on major error
            self.resp_headers_text.config(state=tk.NORMAL); self.resp_headers_text.delete("1.0", tk.END); self.resp_headers_text.config(state=tk.DISABLED)
            self.resp_body_text.config(state=tk.NORMAL); self.resp_body_text.delete("1.0", tk.END); self.resp_body_text.config(state=tk.DISABLED)
            self.copy_resp_body_button.config(state=tk.DISABLED)


    def _copy_response_body(self):
        response_body_content = self.resp_body_text.get("1.0", tk.END + "-1c")
        if response_body_content:
            try:
                self.top.clipboard_clear()
                self.top.clipboard_append(response_body_content)
                messagebox.showinfo("Copied", "Response body copied to clipboard.", parent=self.top)
            except tk.TclError:
                messagebox.showerror("Error", "Could not copy to clipboard. TclError occurred.", parent=self.top)
        else:
            messagebox.showwarning("Empty Response", "There is no response body to copy.", parent=self.top)


if __name__ == "__main__":
    # root = tk.Tk() # Old way
    root = TkinterDnD.Tk() # New way for tkinterdnd2 - Corrected Case
    app = TextEditor(root)
    root.mainloop()
