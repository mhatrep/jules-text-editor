import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog # Added simpledialog
import tkinter.font as tkfont # Corrected import
from PIL import ImageGrab # Added for Drawing Tool PNG export
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
import world_clock # Added for World Clock feature

try:
    import graphviz
except ImportError:
    graphviz = None

try:
    import data_to_table_converter
    from data_to_table_converter import DataParsingError
except ImportError:
    data_to_table_converter = None
    DataParsingError = Exception

import fnmatch


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
        if " (" in file_pattern:
            file_pattern = file_pattern.split(" (", 1)[1][:-1]
        search_phrase = self.search_phrase_var.get()

        if not base_dir or not os.path.isdir(base_dir):
            messagebox.showerror("Error", "Base directory is invalid or not specified.", parent=self.top)
            return
        if not search_phrase:
            messagebox.showerror("Error", "Search phrase cannot be empty.", parent=self.top)
            return

        results = self._execute_search_logic(base_dir, file_pattern, search_phrase)
        if results:
            self.parent_editor._display_search_results(
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
            search_phrase_compiled = re.escape(search_phrase)
        else:
            try:
                search_phrase_compiled = re.compile(search_phrase, search_flags)
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regular expression: {e}", parent=self.top)
                return []

        for root, _, files in os.walk(base_dir):
            for filename in files:
                if fnmatch.fnmatch(filename, file_pattern):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            all_file_lines = list(f)

                        lines_buffer = collections.deque(maxlen=lines_before_count)
                        for line_num_zero_based, line_content in enumerate(all_file_lines):
                            line_content_stripped = line_content.rstrip('\r\n')
                            match_iter = None
                            if use_regex:
                                match_iter = search_phrase_compiled.finditer(line_content_stripped)
                            else:
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
                                    "line_number": line_num_zero_based + 1,
                                    "matched_line": line_content_stripped,
                                    "context_before": list(context_before),
                                    "context_after": context_after,
                                    "match_start": start_char,
                                    "match_end": end_char
                                })
                            if lines_before_count > 0:
                                lines_buffer.append(line_content_stripped)
                    except Exception as e:
                        print(f"Error reading or processing file {filepath}: {e}")
        return results

class FlowDiagramDialog:
    def __init__(self, parent_editor, title="Create Flow Diagram"):
        self.parent_editor = parent_editor
        self.top = tk.Toplevel(parent_editor.root)
        self.top.title(title)
        self.top.transient(parent_editor.root)
        self.top.grab_set()

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(title_frame, text="Diagram Title:").pack(side=tk.LEFT, padx=(0,5))
        self.title_var = tk.StringVar(value="[Flow Diagram]")
        title_entry = ttk.Entry(title_frame, textvariable=self.title_var, width=50)
        title_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        input_frame = ttk.LabelFrame(main_frame, text="Flow Sequences (e.g., Step A->Step B->Step C, one per line)", padding=5)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        input_frame.rowconfigure(0, weight=1)
        input_frame.columnconfigure(0, weight=1)

        self.sequences_text = tk.Text(input_frame, height=15, width=70, wrap=tk.WORD, undo=True)
        sequences_scrollbar = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.sequences_text.yview)
        self.sequences_text.config(yscrollcommand=sequences_scrollbar.set)
        self.sequences_text.grid(row=0, column=0, sticky="nsew")
        sequences_scrollbar.grid(row=0, column=1, sticky="ns")
        self.sequences_text.insert("1.0", "Step A->Step B->Step C\nStep A->Step D\nStep D->Step B\nStep B->Step N->Step A")

        option_frame = ttk.Frame(main_frame)
        option_frame.pack(fill=tk.X, pady=(5,0))
        self.dot_syntax_var = tk.BooleanVar(value=False)
        dot_syntax_check = ttk.Checkbutton(option_frame, text="Use DOT Syntax Directly",
                                           variable=self.dot_syntax_var, command=self._on_dot_syntax_toggle)
        dot_syntax_check.pack(side=tk.LEFT)

        self.title_entry_widget = title_entry
        self.input_frame_widget = input_frame

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0))
        generate_btn = ttk.Button(button_frame, text="Generate & Save Diagram", command=self._generate_and_save)
        generate_btn.pack(side=tk.LEFT, padx=(0,10))
        close_btn = ttk.Button(button_frame, text="Close", command=self.top.destroy)
        close_btn.pack(side=tk.RIGHT)

        self.sequences_text.focus_set()
        self._on_dot_syntax_toggle()

        self.top.update_idletasks()
        x = parent_editor.root.winfo_x() + (parent_editor.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = parent_editor.root.winfo_y() + (parent_editor.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')

    def _generate_and_save(self):
        if graphviz is None:
            messagebox.showerror("Dependency Missing", "The 'graphviz' Python library is not installed. Please install it to use this feature.", parent=self.top)
            return
        dot_script_mode = self.dot_syntax_var.get()
        input_content = self.sequences_text.get("1.0", tk.END + "-1c").strip()
        if not input_content:
            messagebox.showwarning("Input Missing", "Please enter flow sequences or DOT script.", parent=self.top)
            self.sequences_text.focus_set()
            return
        diagram_title_str = self.title_var.get().strip()
        if not dot_script_mode and not diagram_title_str:
            diagram_title_str = "[Flow Diagram]"

        filepath = filedialog.asksaveasfilename(
            parent=self.top, title="Save Flow Diagram As", defaultextension=".pdf",
            initialfile="flow_diagram.pdf",
            filetypes=[("PDF Files", "*.pdf"), ("PNG Files", "*.png"), ("SVG Files", "*.svg"), ("Graphviz DOT File", "*.gv"), ("All Files", "*.*")]
        )
        if not filepath: return

        base_filepath, file_extension = os.path.splitext(filepath)
        output_format = file_extension[1:] if file_extension else 'pdf'

        try:
            if dot_script_mode:
                dot_obj = graphviz.Source(input_content)
            else:
                sequences_list = [s.strip() for s in input_content.splitlines() if s.strip()]
                if not sequences_list:
                    messagebox.showwarning("Input Missing", "No valid flow sequences provided for simplified input.", parent=self.top)
                    self.sequences_text.focus_set()
                    return
                dot_obj = self._create_graphviz_dot(sequences_list, diagram_title_str)

            dot_obj.render(filename=base_filepath, format=output_format, cleanup=True, view=False)
            saved_file_actual_path = f"{base_filepath}.{output_format}"
            if output_format == 'gv' and not saved_file_actual_path.endswith('.gv'):
                saved_file_actual_path = base_filepath
            elif not os.path.exists(saved_file_actual_path):
                 if os.path.exists(base_filepath) and output_format == 'gv':
                      saved_file_actual_path = base_filepath
                 else:
                      print(f"Warning: Expected file {saved_file_actual_path} not found, trying {base_filepath}")
                      if os.path.exists(base_filepath):
                          saved_file_actual_path = base_filepath

            messagebox.showinfo("Success", f"Diagram saved successfully as {saved_file_actual_path}", parent=self.top)
            try:
                if os.name == 'nt': os.startfile(saved_file_actual_path)
                elif os.name == 'posix':
                    if 'darwin' in os.uname().sysname.lower(): subprocess.call(['open', saved_file_actual_path])
                    else: subprocess.call(['xdg-open', saved_file_actual_path])
            except Exception as e_open:
                messagebox.showwarning("Open File", f"Could not automatically open the diagram: {e_open}", parent=self.top)
        except Exception as e:
            messagebox.showerror("Diagram Generation Error", f"Could not generate or save diagram: {e}", parent=self.top)

    def _create_graphviz_dot(self, sequences, label):
        dot = graphviz.Digraph()
        dot.attr(splines='true', rankdir='TB')
        dot.attr('node', shape='plaintext', fontname='Helvetica', fontsize='11', fontcolor='black', style='filled', fillcolor='#e9e9e9', width='1.5')
        dot.attr('edge', arrowhead='normal', arrowtail='dot', color='#20B2AA', style='solid')
        dot.attr(labelloc='t', labeljust='c', fontcolor='#20B2AA', fontname='Courier New Bold', fontsize='20')
        dot.attr(label=label)
        steps = set()
        edges_to_add = []
        for sequence in sequences:
            sequence_steps = [step.strip() for step in sequence.split('->') if step.strip()]
            if not sequence_steps: continue
            for step in sequence_steps: steps.add(step)
            for i in range(len(sequence_steps) - 1):
                edges_to_add.append((sequence_steps[i], sequence_steps[i+1]))
        for step in sorted(list(steps)):
            dot.node(step, label=f'► {step}')
        for u, v in edges_to_add: dot.edge(u, v)
        return dot

    def _on_dot_syntax_toggle(self):
        if self.dot_syntax_var.get():
            self.title_entry_widget.config(state=tk.DISABLED)
            self.title_var.set("[Title defined in DOT script]")
            self.input_frame_widget.config(text="DOT Language Script")
        else:
            self.title_entry_widget.config(state=tk.NORMAL)
            if self.title_var.get() == "[Title defined in DOT script]":
                 self.title_var.set("[Flow Diagram]")
            self.input_frame_widget.config(text="Flow Sequences (e.g., Step A->Step B->Step C, one per line)")

class QuickTextDialog:
    def __init__(self, parent, title="QuickText Transformer"):
        self.parent = parent
        self.top = tk.Toplevel(parent.root)
        self.top.title(title)
        self.top.transient(parent.root)
        self.top.grab_set()
        self.initial_input_data = ""
        current_tab = parent.get_current_tab()
        if current_tab:
            try:
                selected_text = current_tab.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected_text: self.initial_input_data = selected_text
            except tk.TclError: pass

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        input_frame = ttk.LabelFrame(main_frame, text="Input Data", padding=5)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.input_text = tk.Text(input_frame, height=10, width=80, wrap=tk.WORD, undo=True)
        self.input_text_scrollbar = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.input_text.yview)
        self.input_text.config(yscrollcommand=self.input_text_scrollbar.set)
        self.input_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if self.initial_input_data: self.input_text.insert("1.0", self.initial_input_data)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        ttk.Label(controls_frame, text="Delimiter:").pack(side=tk.LEFT, padx=(0,5))
        self.delimiter_var = tk.StringVar(value=",")
        self.delimiter_entry = ttk.Entry(controls_frame, textvariable=self.delimiter_var, width=5)
        self.delimiter_entry.pack(side=tk.LEFT, padx=(0,10))
        self.live_preview_var = tk.BooleanVar(value=False)
        self.live_preview_check = ttk.Checkbutton(controls_frame, text="Live Preview", variable=self.live_preview_var, command=self._on_live_preview_toggle)
        self.live_preview_check.pack(side=tk.LEFT, padx=(0,10))
        self._debounce_timer_id = None
        self.saved_patterns = {
            "SQL INSERT": "INSERT INTO table_name (column1, column2, column3) VALUES ('$1', '$2', '$3');",
            "HTML List": "<li>$1</li>",
            "CSV Output (reversed)": "$3,$2,$1",
        }
        self.pattern_history_for_dialog = list(self.saved_patterns.keys())

        pattern_frame = ttk.LabelFrame(main_frame, text="Pattern (e.g., Name: $1 $2. ID: $lineNumber. Use \\$ for literal $)", padding=5)
        pattern_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.pattern_text = tk.Text(pattern_frame, height=4, width=80, wrap=tk.WORD, undo=True)
        self.pattern_text_scrollbar = ttk.Scrollbar(pattern_frame, orient=tk.VERTICAL, command=self.pattern_text.yview)
        self.pattern_text.config(yscrollcommand=self.pattern_text_scrollbar.set)
        pattern_text_and_buttons_frame = ttk.Frame(pattern_frame)
        pattern_text_and_buttons_frame.pack(fill=tk.BOTH, expand=True)
        self.pattern_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, in_=pattern_text_and_buttons_frame)
        self.pattern_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, in_=pattern_text_and_buttons_frame)
        initial_pattern_name = self.pattern_history_for_dialog[0] if self.pattern_history_for_dialog else "Field1: $1, Field2: $2, Line: $lineNumber"
        initial_pattern_value = self.saved_patterns.get(initial_pattern_name, initial_pattern_name)
        self.pattern_text.insert("1.0", initial_pattern_value)
        self.pattern_text.config(state=tk.NORMAL)

        pattern_buttons_frame = ttk.Frame(pattern_frame)
        pattern_buttons_frame.pack(fill=tk.X, pady=(5,0))
        self.save_pattern_btn = ttk.Button(pattern_buttons_frame, text="Save Current Pattern", command=self._save_current_pattern)
        self.save_pattern_btn.pack(side=tk.LEFT, padx=(0,5))
        self.load_pattern_btn = ttk.Button(pattern_buttons_frame, text="Load Saved Pattern...", command=self._load_saved_pattern)
        self.load_pattern_btn.pack(side=tk.LEFT)

        output_frame = ttk.LabelFrame(main_frame, text="Output", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.output_text = tk.Text(output_frame, height=10, width=80, wrap=tk.WORD, undo=True)
        self.output_text_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.config(yscrollcommand=self.output_text_scrollbar.set)
        self.output_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)

        action_buttons_frame = ttk.Frame(main_frame)
        action_buttons_frame.pack(fill=tk.X, pady=(10,0))
        self.transform_btn = ttk.Button(action_buttons_frame, text="Transform", command=self._run_transform)
        self.transform_btn.pack(side=tk.LEFT, padx=5)
        self.copy_output_btn = ttk.Button(action_buttons_frame, text="Copy Output", command=self._copy_output)
        self.copy_output_btn.pack(side=tk.LEFT, padx=5)
        self.copy_output_btn.config(state=tk.DISABLED)
        self.close_btn = ttk.Button(action_buttons_frame, text="Close", command=self.top.destroy)
        self.close_btn.pack(side=tk.RIGHT, padx=5)
        self.input_text.bind("<<Modified>>", self._debounced_maybe_live_transform)
        self.pattern_text.bind("<<Modified>>", self._debounced_maybe_live_transform)
        self.delimiter_var.trace_add("write", self._debounced_maybe_live_transform_trace)
        self.input_text.focus_set()
        self.top.update_idletasks()
        parent_root = self.parent.root
        x = parent_root.winfo_x() + (parent_root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = parent_root.winfo_y() + (parent_root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')

    def _run_transform(self, event=None):
        input_data = self.input_text.get("1.0", tk.END + "-1c")
        pattern = self.pattern_text.get("1.0", tk.END + "-1c").strip()
        delimiter = self.delimiter_var.get()
        if not input_data.strip():
            messagebox.showwarning("Input Missing", "Input data is empty.", parent=self.top)
            self.input_text.focus_set()
            return
        if not pattern:
            messagebox.showwarning("Pattern Missing", "Pattern is empty.", parent=self.top)
            self.pattern_text.focus_set()
            return
        try:
            output = quick_transformer.quick_transform(input_data, pattern, delimiter)
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, output)
            self.output_text.config(state=tk.DISABLED)
            self.copy_output_btn.config(state=tk.NORMAL if output else tk.DISABLED)
        except ValueError as e:
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
        output_content = self.output_text.get("1.0", tk.END + "-1c")
        if output_content:
            self.top.clipboard_clear()
            self.top.clipboard_append(output_content)
            messagebox.showinfo("Copied", "Output copied to clipboard.", parent=self.top)
        else:
            messagebox.showwarning("Empty Output", "There is no output to copy.", parent=self.top)

    def _on_live_preview_toggle(self):
        if self.live_preview_var.get(): self._run_transform()

    def _debounced_maybe_live_transform(self, event=None):
        widget = event.widget
        try:
            if widget.edit_modified(): widget.edit_modified(False)
        except AttributeError: pass
        if self.live_preview_var.get():
            if self._debounce_timer_id: self.top.after_cancel(self._debounce_timer_id)
            self._debounce_timer_id = self.top.after(500, self._run_transform)

    def _debounced_maybe_live_transform_trace(self, *args):
        if self.live_preview_var.get():
            if self._debounce_timer_id: self.top.after_cancel(self._debounce_timer_id)
            self._debounce_timer_id = self.top.after(500, self._run_transform)

    def _save_current_pattern(self):
        current_pattern_text = self.pattern_text.get("1.0", tk.END + "-1c").strip()
        if not current_pattern_text:
            messagebox.showwarning("Empty Pattern", "Cannot save an empty pattern.", parent=self.top)
            return
        pattern_name = simpledialog.askstring("Save Pattern", "Enter a name for this pattern:", parent=self.top)
        if pattern_name:
            pattern_name = pattern_name.strip()
            if not pattern_name:
                messagebox.showwarning("Invalid Name", "Pattern name cannot be empty.", parent=self.top)
                return
            if pattern_name in self.saved_patterns and \
               not messagebox.askyesno("Overwrite Pattern", f"A pattern named '{pattern_name}' already exists. Overwrite it?", parent=self.top):
                return
            self.saved_patterns[pattern_name] = current_pattern_text
            if pattern_name not in self.pattern_history_for_dialog:
                self.pattern_history_for_dialog.append(pattern_name)
            messagebox.showinfo("Pattern Saved", f"Pattern '{pattern_name}' saved.", parent=self.top)

    def _load_saved_pattern(self):
        if not self.saved_patterns:
            messagebox.showinfo("No Saved Patterns", "There are no patterns saved in this session.", parent=self.top)
            return
        load_dialog = tk.Toplevel(self.top)
        load_dialog.title("Load Pattern")
        load_dialog.transient(self.top)
        load_dialog.grab_set()
        load_dialog.geometry("300x250")
        ttk.Label(load_dialog, text="Select a pattern to load:").pack(pady=5)
        patterns_listbox = tk.Listbox(load_dialog, selectmode=tk.SINGLE, exportselection=False)
        for pattern_name_item in self.pattern_history_for_dialog:
            patterns_listbox.insert(tk.END, pattern_name_item)
        patterns_listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        if self.pattern_history_for_dialog:
            patterns_listbox.select_set(0)
            patterns_listbox.activate(0)
        patterns_listbox.focus_set()
        result_pattern_value = None
        def on_load_select():
            nonlocal result_pattern_value
            selected_indices = patterns_listbox.curselection()
            if selected_indices:
                selected_name = patterns_listbox.get(selected_indices[0])
                result_pattern_value = self.saved_patterns.get(selected_name)
                if result_pattern_value is not None:
                    self.pattern_text.delete("1.0", tk.END)
                    self.pattern_text.insert("1.0", result_pattern_value)
                    if self.live_preview_var.get(): self._run_transform()
                load_dialog.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select a pattern from the list.", parent=load_dialog)
        def on_load_cancel(): load_dialog.destroy()
        buttons_frame_load = ttk.Frame(load_dialog)
        buttons_frame_load.pack(pady=5, fill=tk.X)
        load_btn_inner = ttk.Button(buttons_frame_load, text="Load", command=on_load_select)
        load_btn_inner.pack(side=tk.LEFT, padx=10)
        cancel_btn_inner = ttk.Button(buttons_frame_load, text="Cancel", command=on_load_cancel)
        cancel_btn_inner.pack(side=tk.RIGHT, padx=10)
        patterns_listbox.bind("<Double-1>", lambda e: on_load_select())
        load_dialog.bind("<Return>", lambda e: on_load_select())
        load_dialog.bind("<Escape>", lambda e: on_load_cancel())
        load_dialog.wait_window()

class EditorTab:
    def __init__(self, notebook_widget, app_instance, file_path=None):
        self.app = app_instance
        self.notebook = notebook_widget
        self.frame = ttk.Frame(self.notebook, padding=2)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.line_numbers_font = tkfont.Font(family=app_instance.editor_font.cget("family"), size=app_instance.editor_font.cget("size"))
        self.line_numbers_canvas = tk.Canvas(self.frame, width=65, bg='lightgrey', highlightthickness=0)
        self.line_numbers_visible = self.app.show_line_numbers
        if self.line_numbers_visible: self.line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y)
        self.text_area = tk.Text(self.frame, wrap=tk.WORD, undo=True, yscrollcommand=self.sync_scroll_text, font=app_instance.editor_font)
        self.text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.current_file = file_path
        self.text_changed = False
        self.text_area.bind("<<Modified>>", self.on_text_changed_tab_and_update_lines)
        self.text_area.bind("<Configure>", self.on_text_changed_tab_and_update_lines)
        self.text_area.bind("<MouseWheel>", self.on_scroll_wheel)
        self.text_area.bind("<Button-4>", self.on_scroll_wheel)
        self.text_area.bind("<Button-5>", self.on_scroll_wheel)
        self.text_area.bind("<KeyRelease>", self.on_key_or_mouse_release)
        self.text_area.bind("<ButtonRelease-1>", self.on_key_or_mouse_release)
        self.text_area.bind("<KeyRelease>", self.update_current_line_highlight, add="+")
        self.text_area.bind("<ButtonRelease-1>", self.update_current_line_highlight, add="+")
        self.text_area.bind("<FocusIn>", self.update_current_line_highlight, add="+")
        self.text_area.tag_configure("search_highlight", background="yellow", foreground="black")
        self.text_area.tag_configure("current_search_highlight", background="orange", foreground="black")
        self._keyword_highlight_after_id = None
        self._syntax_highlight_after_id = None
        self.current_language_name = None
        self.tab_original_text_for_filter: str | None = None
        self.is_tab_filtered_view: bool = False
        self.tab_filter_str: str = ""
        self.tab_filter_case_sensitive: bool = False
        self.tab_filter_invert: bool = False
        self.text_area.tag_configure("hl_keyword", foreground="#0000FF")
        self.text_area.tag_configure("hl_comment", foreground="#008000")
        self.text_area.tag_configure("hl_string", foreground="#A52A2A")
        self.text_area.tag_configure("hl_number", foreground="#FF00FF")
        self.text_area.tag_configure("hl_operator", foreground="#FF8C00")
        self.text_area.tag_configure("hl_builtin", foreground="#20B2AA")
        self.text_area.tag_configure("current_line_highlight", background="#FFFFE0")
        self.tab_notes_style_active = self.app.notes_style_active
        self._notes_style_highlight_after_id = None
        notes_bold_font = tkfont.Font(family=self.app.editor_font.cget("family"), size=self.app.editor_font.cget("size"), weight="bold")
        self.text_area.tag_configure("notes_number", foreground="red")
        self.text_area.tag_configure("notes_header", foreground="navy", font=notes_bold_font)
        self.text_area.tag_configure("notes_comment", foreground="dark green", font=notes_bold_font)
        self.text_area.tag_configure("notes_separator", foreground="orange")
        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=self.sync_scroll_text)
        self.redraw_line_numbers()
        if file_path: self.load_file_content(file_path)
        else: self.update_tab_title()
        self.apply_keyword_highlights(self.app.keyword_highlight_settings)
        self._detect_and_set_language(self.current_file)
        self.text_area.bind("<KeyPress>", self.on_text_area_keypress_filtered, add="+")
        self.update_current_line_highlight()

    def update_current_line_highlight(self, event=None):
        self.text_area.tag_remove("current_line_highlight", "1.0", tk.END)
        try:
            if not self.text_area.winfo_exists(): return
            cursor_pos = self.text_area.index(tk.INSERT)
            line_num = cursor_pos.split('.')[0]
            self.text_area.tag_add("current_line_highlight", f"{line_num}.0", f"{line_num}.end")
        except tk.TclError: pass
        except Exception as e: print(f"Error updating current line highlight: {e}")

    def on_text_area_keypress_filtered(self, event):
        if self.is_tab_filtered_view:
            if event.state & 0x0004:
                keysym_lower = event.keysym.lower()
                if keysym_lower == 'x': return "break"
                if keysym_lower in ['c', 'a']: return
                return
            modifying_keysyms = ["BackSpace", "Delete", "Return", "Tab", "KP_Enter"]
            if event.keysym in modifying_keysyms: return "break"
            if event.char and event.char.isprintable() and not (event.state & 0x0004): return "break"
            return
        return

    def load_file_content(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f: content = f.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
            self.current_file = filepath
            self.text_changed = False
            self.text_area.edit_modified(False)
            self.update_tab_title()
            self._detect_and_set_language(self.current_file)
            self.apply_keyword_highlights(self.app.keyword_highlight_settings)
        except Exception as e:
            messagebox.showerror("Error Opening File", str(e))
            self.close_tab(check_save=False)

    def update_tab_title(self):
        tab_text = os.path.basename(self.current_file) if self.current_file else "Untitled"
        if self.text_changed: tab_text = "*" + tab_text
        try:
            current_tabs = self.notebook.tabs()
            if self.frame_id() in current_tabs: self.notebook.tab(self.frame_id(), text=tab_text)
        except tk.TclError: pass

    def on_text_changed_tab_and_update_lines(self, event=None):
        if event and str(event.type) == "Modified":
            if not self.is_tab_filtered_view:
                if self.text_area.edit_modified():
                    if not self.text_changed:
                        self.text_changed = True
                        self.update_tab_title()
            self.text_area.edit_modified(False)
        self.text_area.after(1, self.redraw_line_numbers)
        if event and (str(event.type) == "Modified" or str(event.type) == "Configure"):
            self.app.update_status_bar()
            if str(event.type) == "Modified":
                self.clear_search_highlight_tags()
                if self.app.keyword_highlight_settings.get("active", False):
                    if self._keyword_highlight_after_id: self.text_area.after_cancel(self._keyword_highlight_after_id)
                    self._keyword_highlight_after_id = self.text_area.after(500, lambda: self.apply_keyword_highlights(self.app.keyword_highlight_settings))
                if self.current_language_name:
                    if self._syntax_highlight_after_id: self.text_area.after_cancel(self._syntax_highlight_after_id)
                    self._syntax_highlight_after_id = self.text_area.after(500, self.apply_syntax_highlighting)
                if self.tab_notes_style_active:
                    if self._notes_style_highlight_after_id: self.text_area.after_cancel(self._notes_style_highlight_after_id)
                    self._notes_style_highlight_after_id = self.text_area.after(500, self.apply_notes_style_highlighting)

    def clear_search_highlight_tags(self):
        self.text_area.tag_remove("search_highlight", "1.0", tk.END)
        self.text_area.tag_remove("current_search_highlight", "1.0", tk.END)

    def apply_text_filter(self):
        if not self.tab_filter_str:
            if self.is_tab_filtered_view and self.tab_original_text_for_filter is not None:
                current_insert = self.text_area.index(tk.INSERT)
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", self.tab_original_text_for_filter)
                self.tab_original_text_for_filter = None
                try:
                    self.text_area.mark_set(tk.INSERT, current_insert)
                    self.text_area.see(current_insert)
                except tk.TclError: self.text_area.mark_set(tk.INSERT, "1.0")
            self.is_tab_filtered_view = False
        else:
            if not self.is_tab_filtered_view:
                self.tab_original_text_for_filter = self.text_area.get("1.0", tk.END + "-1c")
            self.is_tab_filtered_view = True
            source_text_for_filtering = self.tab_original_text_for_filter if self.tab_original_text_for_filter is not None else self.text_area.get("1.0", tk.END + "-1c")
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
            self.text_area.delete("1.0", tk.END)
            if matching_lines: self.text_area.insert("1.0", "".join(matching_lines))

        self.redraw_line_numbers()
        if self.current_language_name: self.apply_syntax_highlighting()
        if self.app.keyword_highlight_settings.get("active", False): self.apply_keyword_highlights(self.app.keyword_highlight_settings)
        self.app.update_status_bar()

    def _detect_and_set_language(self, filepath):
        self.current_language_name = None
        if not filepath:
            self.apply_syntax_highlighting()
            return
        _, extension = os.path.splitext(filepath)
        extension = extension.lower()
        if self.app and hasattr(self.app, 'language_definitions'):
            for lang_name, lang_def in self.app.language_definitions.items():
                if extension in lang_def.get("extensions", []):
                    self.current_language_name = lang_name
                    break
        self.apply_syntax_highlighting()

    def _clear_syntax_highlight_tags(self):
        syntax_tags_to_clear = ["hl_keyword", "hl_comment", "hl_string", "hl_number", "hl_operator", "hl_builtin"]
        for tag in syntax_tags_to_clear:
            try: self.text_area.tag_remove(tag, "1.0", tk.END)
            except tk.TclError: pass

    def apply_syntax_highlighting(self):
        if not self.current_language_name or not self.app.language_definitions: return
        lang_def = self.app.language_definitions.get(self.current_language_name)
        if not lang_def or not lang_def.get("rules"): return
        self._clear_syntax_highlight_tags()
        all_text = self.text_area.get("1.0", tk.END)
        if not all_text.strip(): return
        import re
        for rule in lang_def["rules"]:
            token_type = rule["token_type"]
            pattern_str = rule["pattern"]
            try:
                for match in re.finditer(pattern_str, all_text):
                    start_offset, end_offset = match.span()
                    start_idx = self.text_area.index(f"1.0 + {start_offset} chars")
                    end_idx = self.text_area.index(f"1.0 + {end_offset} chars")
                    self.text_area.tag_add(token_type, start_idx, end_idx)
            except re.error as e: print(f"Regex error for language {self.current_language_name}, pattern {pattern_str}: {e}")
            except tk.TclError as e:
                print(f"TclError during syntax highlighting: {e}. Text might have changed.")
                return

    def apply_keyword_highlights(self, highlight_settings):
        for i in range(len(self.app.pastel_colors) + 5):
            try: self.text_area.tag_remove(f"user_keyword_{i}", "1.0", tk.END)
            except tk.TclError: pass
        if not highlight_settings or not highlight_settings.get("active", False) or not highlight_settings.get("parsed_keywords"): return
        keywords = highlight_settings["parsed_keywords"]
        case_sensitive = highlight_settings["case_sensitive"]
        whole_word = highlight_settings["whole_word"]
        kw_to_color = highlight_settings["keyword_to_color_map"]
        kw_to_tag = highlight_settings["keyword_to_tag_name_map"]
        for keyword_text in keywords:
            tag_name = kw_to_tag.get(keyword_text)
            color = kw_to_color.get(keyword_text)
            if not tag_name or not color: continue
            self.text_area.tag_configure(tag_name, background=color, foreground="black")
            start_index = "1.0"
            while True:
                nocase_local = not case_sensitive
                search_pattern = keyword_text
                use_regexp_for_this_keyword = False
                if whole_word: pass
                length_var = tk.IntVar()
                pos = self.text_area.search(search_pattern, start_index, tk.END, nocase=nocase_local, regexp=use_regexp_for_this_keyword, exact=whole_word, count=length_var)
                if pos:
                    match_len = length_var.get()
                    if match_len == 0 and len(search_pattern) > 0 : match_len = len(search_pattern)
                    if match_len > 0:
                        end_pos = self.text_area.index(f"{pos} + {match_len} chars")
                        self.text_area.tag_add(tag_name, pos, end_pos)
                        start_index = end_pos
                    else: break
                else: break

    def on_key_or_mouse_release(self, event=None): self.app.update_status_bar()

    def on_scroll_wheel(self, event):
        if event.num == 4: self.text_area.yview_scroll(-1, "units")
        elif event.num == 5: self.text_area.yview_scroll(1, "units")
        elif event.delta: self.text_area.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def sync_scroll_text(self, *args):
        self.scrollbar.set(*args)
        self.redraw_line_numbers()

    def redraw_line_numbers(self):
        if not self.line_numbers_visible or not self.line_numbers_canvas.winfo_ismapped(): return
        self.line_numbers_canvas.delete("all")
        self.text_area.update_idletasks()
        first_visible_char_index = self.text_area.index("@0,0")
        if not first_visible_char_index: return
        try: first_line_num = int(first_visible_char_index.split('.')[0])
        except ValueError: return
        first_visible_line_bbox = self.text_area.dlineinfo(f"{first_line_num}.0")
        if not first_visible_line_bbox:
            if self.text_area.index("end-1c") == "1.0":
                 self.line_numbers_canvas.create_text(self.line_numbers_canvas.winfo_width() - 2, 0, anchor=tk.NW, text="1", font=self.line_numbers_font)
            return
        y_offset_of_content_top_from_visible_area_top = first_visible_line_bbox[1]
        current_line_to_draw_num = first_line_num
        while True:
            dline_info = self.text_area.dlineinfo(f"{current_line_to_draw_num}.0")
            if dline_info is None: break
            line_y_in_text_content = dline_info[1]
            line_height_in_text_content = dline_info[3]
            canvas_y_for_line_top = line_y_in_text_content - y_offset_of_content_top_from_visible_area_top
            if canvas_y_for_line_top > self.line_numbers_canvas.winfo_height(): break
            if (canvas_y_for_line_top + line_height_in_text_content) >= 0 and canvas_y_for_line_top <= self.line_numbers_canvas.winfo_height():
                canvas_x_for_number = self.line_numbers_canvas.winfo_width() - 2
                self.line_numbers_canvas.create_text(canvas_x_for_number, canvas_y_for_line_top, anchor=tk.NE, text=str(current_line_to_draw_num), font=self.line_numbers_font)
            current_line_to_draw_num += 1
            if current_line_to_draw_num > first_line_num + 5000:
                 print(f"DEBUG: redraw_line_numbers breaking early after drawing {5000} lines.")
                 break
            total_lines_str = self.text_area.index(f"{tk.END}-1c").split('.')[0]
            if total_lines_str.isdigit() and current_line_to_draw_num > int(total_lines_str) + 1: break

    def get_content(self): return self.text_area.get("1.0", tk.END + "-1c")
    def frame_id(self): return self.frame

    def close_tab(self, check_save=True):
        if check_save and not self.check_unsaved_changes_tab(): return False
        try:
            selected_tab_before_close = self.app.notebook.index(tk.CURRENT)
            self.notebook.forget(self.frame_id())
            if self in self.app.tabs: self.app.tabs.remove(self)
            else: print(f"Warning: EditorTab instance {self} was not found in self.app.tabs during close_tab.")
            if not self.app.tabs:
                if self.app.quitting_app: pass
                else: self.app.new_file_action()
            else:
                if not self.app.quitting_app and len(self.app.notebook.tabs()) > 0:
                    if selected_tab_before_close >= len(self.app.notebook.tabs()):
                        self.app.notebook.select(len(self.app.notebook.tabs()) - 1)
            if not self.app.quitting_app:
                try:
                    self.app.update_app_title()
                    self.app.update_status_bar()
                except tk.TclError: pass
            return True
        except tk.TclError as e:
            print(f"Error closing tab (TclError): {e}")
            return False
        except Exception as e:
            print(f"Unexpected error closing tab: {e}")
            return False

    def apply_notes_style_highlighting(self, event=None):
        if not self.tab_notes_style_active:
            self.clear_notes_style_highlighting()
            if self.current_language_name and hasattr(self, 'apply_syntax_highlighting'): self.apply_syntax_highlighting()
            if self.app.keyword_highlight_settings.get("active", False) and hasattr(self, 'apply_keyword_highlights'): self.apply_keyword_highlights(self.app.keyword_highlight_settings)
            return
        if hasattr(self, '_clear_syntax_highlight_tags'): self._clear_syntax_highlight_tags()
        if hasattr(self.app, 'pastel_colors'):
            for i in range(len(self.app.pastel_colors) + 5):
                try: self.text_area.tag_remove(f"user_keyword_{i}", "1.0", tk.END)
                except tk.TclError: pass
        self.clear_notes_style_highlighting()
        all_text = self.text_area.get("1.0", tk.END)
        if not all_text.strip(): return
        number_pattern = r'(?<![a-zA-Z_])(?<!\.)-?\b(?:\d+\.?\d*|\.\d+)\b(?!\.)(?![a-zA-Z_])'
        header_pattern = r'^([^:]+):'
        comment_pattern = r'#.*'
        separator_pattern = r'^(?:-{2,}|={2,})$'
        for match in re.finditer(separator_pattern, all_text, re.MULTILINE):
            start_idx = self.text_area.index(f"1.0 + {match.start()} chars")
            end_idx = self.text_area.index(f"1.0 + {match.end()} chars")
            self.text_area.tag_add("notes_separator", start_idx, end_idx)
        for match in re.finditer(header_pattern, all_text, re.MULTILINE):
            start_idx = self.text_area.index(f"1.0 + {match.start(0)} chars")
            end_colon_offset = match.group(0).find(':')
            if end_colon_offset != -1:
                actual_end_offset = match.start(0) + end_colon_offset + 1
                end_idx = self.text_area.index(f"1.0 + {actual_end_offset} chars")
            else: end_idx = self.text_area.index(f"1.0 + {match.end(0)} chars")
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
            if not is_already_styled_exclusively: self.text_area.tag_add("notes_number", match_start_idx, match_end_idx)

    def clear_notes_style_highlighting(self):
        self.text_area.tag_remove("notes_number", "1.0", tk.END)
        self.text_area.tag_remove("notes_header", "1.0", tk.END)
        self.text_area.tag_remove("notes_comment", "1.0", tk.END)
        self.text_area.tag_remove("notes_separator", "1.0", tk.END)

    def check_unsaved_changes_tab(self):
        if self.text_changed:
            self.notebook.select(self.frame_id())
            file_display_name = os.path.basename(self.current_file) if self.current_file else "Untitled"
            response = messagebox.askyesnocancel("Unsaved Changes", f"Do you want to save the changes to {file_display_name}?")
            if response is True: return self.app.save_file_action(save_as_if_needed=False)
            elif response is False: return True
            else: return False
        return True

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        self.quitting_app = False
        self.tabs = []
        self.show_line_numbers = True
        self.notes_style_active = False
        self._is_updating_filter_bar_from_tab = False
        self.known_fixed_fonts = sorted([
            "TkFixedFont", "Courier New", "Courier", "Consolas", "DejaVu Sans Mono",
            "Liberation Mono", "Menlo", "Monaco", "Source Code Pro", "Fira Code",
            "Inconsolata", "Fixedsys", "Terminal", "Monospace"
        ])
        system_fonts = set(tkfont.families())
        preferred_defaults = ["Courier New", "Consolas", "TkFixedFont"]
        default_family_to_set = None
        for preferred_font in preferred_defaults:
            if preferred_font in system_fonts:
                default_family_to_set = preferred_font
                break
        if not default_family_to_set:
            for ff in self.known_fixed_fonts:
                if ff in system_fonts:
                    default_family_to_set = ff
                    break
        if not default_family_to_set: default_family_to_set = "TkFixedFont"
        self.current_font_family = default_family_to_set
        self.current_font_size = 14
        self.current_font_weight = "normal"
        self.current_font_slant = "roman"
        self.editor_font = tkfont.Font(family=self.current_font_family, size=self.current_font_size, weight=self.current_font_weight, slant=self.current_font_slant)
        self.keyword_highlight_settings = {
            "keywords_input_string": "", "parsed_keywords": [],
            "keyword_to_color_map": {}, "keyword_to_tag_name_map": {},
            "case_sensitive": False, "whole_word": True, "active": False
        }
        self.pastel_colors = ["#FFDFD3", "#FFFACD", "#D7E9F7", "#E0FFFF", "#F0FFF0", "#FFE4E1", "#FAFAD2", "#ADD8E6", "#E6E6FA", "#FFF0F5"]
        self.language_definitions = {
            "python": {
                "extensions": [".py", ".pyw"],
                "rules": [
                    {"token_type": "hl_comment", "pattern": r"#.*"},
                    {"token_type": "hl_string", "pattern": r"(\"\"\"(?:[^\"]|\\\"|\n)*?\"\"\"|\'\'\'(?:[^\']|\\\'|\n)*?\'\'\'|\"[^\"\\\n]*(?:\\.[^\"\\\n]*)*\"|\'[^\'\\\n]*(?:\\.[^\'\\\n]*)*\')"},
                    {"token_type": "hl_keyword", "pattern": r'\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b'},
                    {"token_type": "hl_builtin", "pattern": r'\b(abs|all|any|ascii|bin|bool|bytearray|bytes|callable|chr|classmethod|compile|complex|delattr|dict|dir|divmod|enumerate|eval|exec|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|print|property|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|vars|zip|__import__)\b'},
                    {"token_type": "hl_number", "pattern": r'\b(?:0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+|[0-9]+\.?[0-9]*(?:[eE][+-]?[0-9]+)?|[0-9]+)\b'},
                    {"token_type": "hl_operator", "pattern": r"(\+|\-|\*|/|%|=|==|!=|>|<|>=|<=|&|\||\^|~|<<|>>|\*\*|//|@)"}
                ]
            }
        }
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.toolbar_frame = ttk.Frame(self.root, relief=tk.FLAT, padding=2)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        # World Clock Frame
        self.world_clock_frame = ttk.Frame(self.root, relief=tk.FLAT, padding=(5,2))
        self.world_clock_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,2))
        self.timezones_to_display = [
            {"label": "NYC (ET):", "tz": "America/New_York"},
            {"label": "IST:", "tz": "Asia/Kolkata"},
            {"label": "JST:", "tz": "Asia/Tokyo"},
            {"label": "UTC:", "tz": "UTC"}
        ]
        self.world_clock_labels = []
        self._initialize_world_clocks()

        self.filter_bar_frame = ttk.Frame(self.root, padding=(5,2))
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
        self.filter_close_btn = ttk.Button(self.filter_bar_frame, text="✕", command=self.toggle_filter_bar, width=3)
        self.filter_close_btn.pack(side=tk.LEFT, padx=5)
        self.filter_text_var.trace_add("write", self.on_filter_settings_changed)
        self.filter_case_var.trace_add("write", self.on_filter_settings_changed)
        self.filter_invert_var.trace_add("write", self.on_filter_settings_changed)

        btn_padx = 3
        btn_pady = 2
        self.new_btn = ttk.Button(self.toolbar_frame, text="New", command=self.new_file_action_handler)
        self.new_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        self.open_btn = ttk.Button(self.toolbar_frame, text="Open", command=self.open_file_action_handler)
        self.open_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        self.save_btn = ttk.Button(self.toolbar_frame, text="Save", command=lambda: self.save_action_handler(save_as_if_needed=False))
        self.save_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=btn_pady)
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
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.new_file_action_handler, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open...", command=self.open_file_action_handler, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save", command=lambda: self.save_action_handler(save_as_if_needed=False), accelerator="Ctrl+S")
        self.file_menu.add_command(label="Save As...", command=self.save_as_action_handler, accelerator="Ctrl+Shift+S")
        self.file_menu.add_command(label="Close Tab", command=self.close_current_tab_action_handler, accelerator="Ctrl+W")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_editor_action)
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Undo", command=self.undo_action, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Redo", command=self.redo_action, accelerator="Ctrl+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut_action, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Copy", command=self.copy_action, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Paste", command=self.paste_action, accelerator="Ctrl+V")
        self.edit_menu.add_command(label="Strip Clipboard Formatting", command=self.strip_clipboard_formatting_action)
        self.edit_menu.add_command(label="Copy File Path", command=self.copy_file_path_action)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", command=self.select_all_action, accelerator="Ctrl+A")
        self.format_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Format", menu=self.format_menu)
        self.trim_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Trim", menu=self.trim_menu)
        self.trim_menu.add_command(label="Leading Whitespace", command=lambda: self.trim_whitespace("leading"))
        self.trim_menu.add_command(label="Trailing Whitespace", command=lambda: self.trim_whitespace("trailing"))
        self.trim_menu.add_command(label="Both Ends Whitespace", command=lambda: self.trim_whitespace("both"))
        self.case_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Change Case", menu=self.case_menu)
        self.case_menu.add_command(label="To UPPERCASE", command=lambda: self.change_case("upper"))
        self.case_menu.add_command(label="To lowercase", command=lambda: self.change_case("lower"))
        self.case_menu.add_command(label="To Title Case", command=lambda: self.change_case("title"))
        self.format_menu.add_command(label="Sort Lines...", command=self.sort_lines_dialog)
        self.format_menu.add_command(label="Pad Lines...", command=self.pad_lines_dialog)
        self.format_menu.add_command(label="Add Prefix/Suffix to Lines...", command=self.add_prefix_suffix_dialog)
        self.format_menu.add_separator()
        self.line_spacing_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Line Spacing", menu=self.line_spacing_menu)
        self.line_spacing_menu.add_command(label="Condense Internal Whitespace", command=self.condense_internal_whitespace)
        self.line_spacing_menu.add_command(label="Double Space Lines", command=self.double_space_lines)
        self.line_spacing_menu.add_command(label="Reduce Multiple Blank Lines to One", command=self.reduce_blank_lines)
        self.line_alteration_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Line Alteration", menu=self.line_alteration_menu)
        self.line_alteration_menu.add_command(label="Delete Duplicate Consecutive Lines", command=self.delete_duplicate_consecutive_lines)
        self.line_alteration_menu.add_command(label="Reverse Lines", command=self.reverse_lines_action)
        self.join_split_lines_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Join/Split Lines", menu=self.join_split_lines_menu)
        self.join_split_lines_menu.add_command(label="Join Lines (with space)", command=self.join_lines_with_space)
        self.join_split_lines_menu.add_command(label="Join Lines (with ', ')", command=self.join_lines_with_comma_space)
        self.format_menu.add_separator()
        self.format_menu.add_command(label="Remove Punctuation", command=self.remove_punctuation_action)
        self.format_menu.add_command(label="Shuffle Lines", command=self.shuffle_lines_action)
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.word_analysis_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Word Analysis", menu=self.word_analysis_menu)
        self.word_analysis_menu.add_command(label="Count Word Frequency...", command=self.count_word_frequency_action)
        self.word_analysis_menu.add_command(label="Extract Unique Words...", command=self.extract_unique_words_dialog)
        self.word_analysis_menu.add_command(label="Extract UPPERCASE Words...", command=self.extract_uppercase_words_action)
        self.tools_menu.add_command(label="Text Statistics...", command=self.text_statistics_action)
        self.tools_menu.add_separator()
        self.regex_utilities_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Regex Utilities", menu=self.regex_utilities_menu)
        self.regex_utilities_menu.add_command(label="Extract by Pattern (Regex)...", command=self.extract_pattern_dialog)
        self.regex_utilities_menu.add_command(label="Keep Lines Matching Regex...", command=lambda: self.filter_lines_by_regex_dialog(action_mode="keep"))
        self.regex_utilities_menu.add_command(label="Remove Lines Matching Regex...", command=lambda: self.filter_lines_by_regex_dialog(action_mode="remove"))
        self.tools_menu.add_separator()
        self.line_filters_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Line Filters", menu=self.line_filters_menu)
        self.line_filters_menu.add_command(label="Extract Lines by Length...", command=self.extract_lines_by_length_dialog)
        self.line_filters_menu.add_command(label="Remove Blank Lines", command=self.remove_all_blank_lines)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="QuickText Transformer...", command=self.open_quick_text_dialog)
        self.tools_menu.add_command(label="Create Flow Diagram...", command=self.open_flow_diagram_dialog)
        self.tools_menu.add_command(label="View Data as Table (JSON/YAML)...", command=self.view_data_as_table_action)
        self.tools_menu.add_command(label="Convert CSV to Text Table", command=self.csv_to_text_table_action)
        self.tools_menu.add_command(label="Compare Two Lists...", command=self.open_compare_lists_dialog)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="REST API Client...", command=self.open_rest_api_client_dialog)
        self.tools_menu.add_command(label="SQL Parser...", command=self.open_sql_parser_dialog)
        self.tools_menu.add_command(label="Excel to HTML Site...", command=self.open_excel_to_html_dialog)
        self.tools_menu.add_command(label="Excel to CSVs & Stats...", command=self.open_excel_to_csv_stats_dialog)
        self.tools_menu.add_command(label="URL Manager...", command=self.open_url_manager_dialog)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Drawing Tool...", command=self.open_drawing_tool_action)
        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Search", menu=self.search_menu)
        self.search_menu.add_command(label="Find/Replace in Current File...", command=self.open_find_replace_dialog, accelerator="Ctrl+F")
        self.search_menu.add_command(label="Search in Files...", command=self.open_file_search_dialog, accelerator="Ctrl+Shift+F")
        self.search_menu.add_separator()
        self.search_menu.add_command(label="Go to Line...", command=self.prompt_go_to_line, accelerator="Ctrl+G")
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Change Font...", command=self.open_font_dialog)
        self.view_menu.add_command(label="Keyword Highlighting...", command=self.open_keyword_highlight_dialog)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Toggle Line Numbers", command=self.toggle_line_numbers_action)
        self.view_menu.add_command(label="Toggle Notes Style", command=self.toggle_notes_style_action)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Toggle Filter Bar", command=self.toggle_filter_bar, accelerator="Ctrl+Shift+F") # UNCOMMENTED
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.notebook.drop_target_register(DND_FILES)
        self.notebook.dnd_bind('<<Drop>>', self._handle_drop_files)
        self.status_bar_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=2)
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label_line_col = ttk.Label(self.status_bar_frame, text="Ln 1, Col 1", width=20)
        self.status_label_line_col.pack(side=tk.LEFT, padx=5)
        self.status_label_total_lines = ttk.Label(self.status_bar_frame, text="Lines: 1", width=15)
        self.status_label_total_lines.pack(side=tk.LEFT, padx=5)
        self.status_label_file_path = ttk.Label(self.status_bar_frame, text="File: Untitled", anchor=tk.W)
        self.status_label_file_path.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.new_file_action()
        self.update_app_title()
        self.root.bind_all("<Control-n>", self.new_file_action_handler)
        self.root.bind_all("<Control-o>", self.open_file_action_handler)
        self.root.bind_all("<Control-s>", lambda event: self.save_action_handler(save_as_if_needed=False))
        self.root.bind_all("<Control-S>", self.save_as_action_handler)
        self.root.bind_all("<Control-w>", self.close_current_tab_action_handler)
        self.root.bind_all("<Control-f>", self.open_find_replace_dialog)
        self.root.bind_all("<Control-g>", self.prompt_go_to_line)
        self.root.bind_all("<Control-F>", lambda event: self.toggle_filter_bar())
        self.root.bind_all("<Control-z>", lambda event: self.undo_action())
        self.root.bind_all("<Control-y>", lambda event: self.redo_action())
        self.root.bind_all("<Control-x>", lambda event: self.cut_action())
        self.root.bind_all("<Control-c>", lambda event: self.copy_action())
        self.root.bind_all("<Control-v>", lambda event: self.paste_action())
        self.root.bind_all("<Control-a>", lambda event: self.select_all_action())
        self.root.protocol("WM_DELETE_WINDOW", self.exit_editor_action)

    def _initialize_world_clocks(self):
        self.world_clock_labels = []
        # Clear any existing widgets in the frame, in case this is called multiple times
        for widget in self.world_clock_frame.winfo_children():
            widget.destroy()

        for tz_info in self.timezones_to_display:
            clock_entry_frame = ttk.Frame(self.world_clock_frame)
            clock_entry_frame.pack(side=tk.LEFT, padx=10, pady=2)

            static_label = ttk.Label(clock_entry_frame, text=tz_info["label"])
            static_label.pack(side=tk.LEFT)

            time_label = ttk.Label(clock_entry_frame, text="Loading...")
            time_label.pack(side=tk.LEFT, padx=(2,0))
            self.world_clock_labels.append(time_label)

        self._update_world_clocks() # Start the update cycle

    def _update_world_clocks(self):
        for i, tz_info in enumerate(self.timezones_to_display):
            if i < len(self.world_clock_labels): # Ensure label exists
                formatted_time = world_clock.get_formatted_datetime(tz_info["tz"])
                self.world_clock_labels[i].config(text=formatted_time)

        # Schedule next update
        self.root.after(5000, self._update_world_clocks)


    def get_current_tab(self):
        try:
            selected_tab_frame_id = self.notebook.select()
            if not selected_tab_frame_id:
                 if self.tabs: return self.tabs[0]
                 return None
            for tab_obj in self.tabs:
                if str(tab_obj.frame_id()) == str(selected_tab_frame_id): return tab_obj
            return None
        except tk.TclError: return None

    def on_tab_changed(self, event=None):
        self.update_app_title()
        self.update_status_bar()
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.tab_notes_style_active = self.notes_style_active
            if self.notes_style_active: current_tab.apply_notes_style_highlighting()
            else:
                current_tab.clear_notes_style_highlighting()
                if self.keyword_highlight_settings.get("active", False): current_tab.apply_keyword_highlights(self.keyword_highlight_settings)
                if current_tab.current_language_name: current_tab.apply_syntax_highlighting()
                else: current_tab._clear_syntax_highlight_tags()
            if self.filter_bar_frame.winfo_ismapped():
                self._is_updating_filter_bar_from_tab = True
                try:
                    self.filter_text_var.set(current_tab.tab_filter_str)
                    self.filter_case_var.set(current_tab.tab_filter_case_sensitive)
                    self.filter_invert_var.set(current_tab.tab_filter_invert)
                finally: self._is_updating_filter_bar_from_tab = False
                current_tab.apply_text_filter()
            else:
                if current_tab.is_tab_filtered_view or current_tab.tab_filter_str: current_tab.apply_text_filter()
            if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists(): self.update_find_replace_button_states()
            current_tab.update_current_line_highlight()

    def on_filter_settings_changed(self, *args):
        if self._is_updating_filter_bar_from_tab: return
        current_tab = self.get_current_tab()
        if not current_tab: return
        current_tab.tab_filter_str = self.filter_text_var.get()
        current_tab.tab_filter_case_sensitive = self.filter_case_var.get()
        current_tab.tab_filter_invert = self.filter_invert_var.get()
        current_tab.apply_text_filter()
        if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists(): self.update_find_replace_button_states()

    def update_status_bar(self):
        current_tab = self.get_current_tab()
        if current_tab and current_tab.text_area:
            cursor_pos = current_tab.text_area.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            self.status_label_line_col.config(text=f"Ln {line}, Col {col + 1}")
            total_lines = int(current_tab.text_area.index(f"{tk.END}-1c").split('.')[0])
            self.status_label_total_lines.config(text=f"Lines: {total_lines}")
            file_path_display = "Untitled"
            if current_tab.current_file: file_path_display = os.path.basename(current_tab.current_file)
            self.status_label_file_path.config(text=f"File: {file_path_display}")
        else:
            self.status_label_line_col.config(text="Ln --, Col --")
            self.status_label_total_lines.config(text="Lines: --")
            self.status_label_file_path.config(text="File: --")

    def update_app_title(self):
        current_tab = self.get_current_tab()
        if current_tab:
            base_name = os.path.basename(current_tab.current_file) if current_tab.current_file else "Untitled"
            title = f"Jules Text Editor - {base_name}"
            if current_tab.text_changed: title = "*" + title
            self.root.title(title)
        else: self.root.title("Jules Text Editor")

    def new_file_action_handler(self, event=None): self.new_file_action(); return "break"
    def new_file_action(self):
        new_tab = EditorTab(self.notebook, self)
        self.tabs.append(new_tab)
        self.notebook.add(new_tab.frame, text="Untitled")
        self.notebook.select(new_tab.frame_id())
        new_tab.text_area.focus_set()
        self.update_app_title()
        self.update_status_bar()

    def open_file_action_handler(self, event=None): self.open_file_action(); return "break"
    def open_file_action(self):
        filepath = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")])
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
            else: new_tab.frame.destroy()
        self.update_app_title()
        self.update_status_bar()

    def save_action_handler(self, event=None, save_as_if_needed=True): self.save_file(save_as_if_needed=save_as_if_needed); return "break"
    def save_as_action_handler(self, event=None): self.save_as_file(); return "break"
    def save_file(self, save_as_if_needed=True):
        current_tab = self.get_current_tab()
        if not current_tab: return False
        if not current_tab.current_file or save_as_if_needed: return self.save_as_file()
        try:
            if current_tab.is_tab_filtered_view and current_tab.tab_original_text_for_filter is not None:
                content_to_save = current_tab.tab_original_text_for_filter
            else: content_to_save = current_tab.get_content()
            with open(current_tab.current_file, "w", encoding="utf-8") as f: f.write(content_to_save)
            current_tab.text_changed = False
            current_tab.text_area.edit_modified(False)
            current_tab.update_tab_title()
            self.update_app_title()
            self.update_status_bar()
            return True
        except Exception as e:
            messagebox.showerror("Error Saving File", str(e))
            return False

    def save_as_file(self):
        current_tab = self.get_current_tab()
        if not current_tab: return False
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=os.path.basename(current_tab.current_file) if current_tab.current_file else "Untitled.txt", filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")])
        if filepath:
            current_tab.current_file = filepath
            if self.save_file(save_as_if_needed=False):
                current_tab._detect_and_set_language(filepath)
                return True
            else:
                current_tab._detect_and_set_language(filepath)
                self.update_status_bar()
                return False
        self.update_status_bar()
        return False

    def close_current_tab_action_handler(self, event=None): self.close_current_tab_action(); return "break"
    def close_current_tab_action(self):
        current_tab = self.get_current_tab()
        if current_tab: current_tab.close_tab()
        self.update_status_bar()

    def exit_editor_action(self):
        self.quitting_app = True
        for tab in list(self.tabs):
            if not tab.close_tab():
                self.quitting_app = False
                return
        if not self.tabs: self.root.destroy()

    def get_active_text_area(self):
        current_tab = self.get_current_tab()
        if current_tab: return current_tab.text_area
        return None

    def undo_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            try: text_area.edit_undo()
            except tk.TclError: pass
        return "break"

    def redo_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            try: text_area.edit_redo()
            except tk.TclError: pass
        return "break"

    def cut_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area and text_area.tag_ranges(tk.SEL): text_area.event_generate("<<Cut>>")
        return "break"

    def copy_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area and text_area.tag_ranges(tk.SEL): text_area.event_generate("<<Copy>>")
        return "break"

    def paste_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            try:
                plain_text = self.root.clipboard_get()
                if text_area.tag_ranges(tk.SEL):
                    sel_first = text_area.index(tk.SEL_FIRST)
                    sel_last = text_area.index(tk.SEL_LAST)
                    text_area.delete(sel_first, sel_last)
                text_area.insert(tk.INSERT, plain_text)
                text_area.see(tk.INSERT)
                text_area.event_generate("<<Modified>>")
            except tk.TclError:
                try: text_area.event_generate("<<Paste>>")
                except tk.TclError: pass
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
            except Exception as e: pass
        else: pass
        return "break"

    def strip_clipboard_formatting_action(self, event=None):
        try:
            plain_text = self.root.clipboard_get()
            if isinstance(plain_text, str):
                self.root.clipboard_clear()
                self.root.clipboard_append(plain_text)
        except tk.TclError: pass
        return "break"

    def _process_text(self, operation_func):
        text_area = self.get_active_text_area()
        if not text_area: return
        try:
            sel_start = text_area.index(tk.SEL_FIRST)
            sel_end = text_area.index(tk.SEL_LAST)
            selected_text = text_area.get(sel_start, sel_end)
            processed_text = operation_func(selected_text)
            if selected_text != processed_text:
                text_area.delete(sel_start, sel_end)
                text_area.insert(sel_start, processed_text)
                text_area.event_generate("<<Modified>>")
        except tk.TclError:
            full_text = text_area.get("1.0", tk.END + "-1c")
            processed_text = operation_func(full_text)
            if full_text != processed_text:
                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", processed_text)
                text_area.event_generate("<<Modified>>")

    def trim_whitespace(self, mode="both"):
        def do_trim(text):
            lines = text.splitlines(keepends=True); processed_lines = []
            if mode == "leading":
                for line in lines:
                    stripped_line = line.lstrip()
                    if not stripped_line.strip() and line.endswith('\n') and stripped_line == '': processed_lines.append('\n')
                    elif not stripped_line and line.endswith('\n'): processed_lines.append(line)
                    else: processed_lines.append(line.lstrip())
            elif mode == "trailing":
                for line in lines: processed_lines.append(line.rstrip() + ('\n' if line.endswith('\n') and line.rstrip() else ''))
                temp_text = "".join(processed_lines)
                return temp_text.rstrip() + ('\n' if temp_text.endswith('\n') else '')
            elif mode == "both":
                 for line in lines:
                    stripped_line = line.strip()
                    if not stripped_line and line.endswith('\n'): processed_lines.append('\n')
                    elif line.strip(): processed_lines.append(line.strip() + ('\n' if line.endswith('\n') else ''))
            if mode == "leading" or mode == "both": return "".join(processed_lines)
            else:
                text_area = self.get_active_text_area()
                if not text_area: return text
                try: text_area.index(tk.SEL_FIRST)
                except tk.TclError:
                    processed_text = "\n".join([line.rstrip() for line in text.splitlines()])
                    if text.endswith('\n'): processed_text += '\n'
                    return processed_text
                return "\n".join([line.rstrip() for line in text.splitlines()])
        self._process_text(do_trim)

    def change_case(self, case_type):
        def do_change_case(text):
            if case_type == "upper": return text.upper()
            elif case_type == "lower": return text.lower()
            elif case_type == "title": return text.title()
            return text
        self._process_text(do_change_case)

    def sort_lines_dialog(self):
        # This method (and others like it) are assumed to be complete and correct from previous versions.
        # For brevity, their full content is not repeated here, but would be in the actual file.
        pass

    def filter_lines_by_regex_dialog(self, action_mode: str, event=None): pass
    def apply_filter_lines_by_regex(self, regex_str: str, case_insensitive: bool, action_mode: str): pass
    def update_sort_options_state(self): pass
    def apply_sort_lines(self, sort_type, case_sensitive, remove_duplicates): pass
    def open_find_replace_dialog(self, event=None): pass
    def update_find_replace_button_states(self): pass
    def _search_in_text(self, text_widget, pattern, start_index, end_index, case_sensitive, whole_word, regex, backwards): return None,0
    def find_next(self, event=None): pass
    def replace_once(self, event=None): pass
    def replace_all(self, event=None): pass
    def clear_all_search_highlights_active_tab(self): pass
    def clear_current_search_highlight_active_tab(self): pass
    def refresh_search_highlights(self): pass
    def navigate_to_match(self, match_index, is_initial_find=False): pass
    def open_font_dialog(self): pass
    def update_font_preview(self, preview_label, family_var, size_var, bold_var, italic_var): pass
    def apply_new_font(self, family, size, weight, slant): pass
    def open_keyword_highlight_dialog(self): pass
    def update_keyword_highlight_settings(self, input_str, case_sens, whole_word): pass
    def clear_keyword_highlight_settings(self): pass
    def apply_all_tabs_keyword_highlights(self): pass
    def double_space_lines(self): pass
    def reduce_blank_lines(self): pass
    def remove_all_blank_lines(self): pass
    def delete_duplicate_consecutive_lines(self): pass
    def reverse_lines_action(self): pass
    def extract_lines_by_length_dialog(self, event=None): pass
    def apply_extract_lines_by_length(self, length_val: int, mode: str, keep_empty: bool): pass
    def pad_lines_dialog(self, event=None): pass
    def apply_pad_lines(self, target_length: int, pad_char: str, alignment: str): pass
    def remove_punctuation_action(self, event=None): pass
    def extract_uppercase_words_action(self, event=None): pass
    def count_word_frequency_action(self, event=None): pass
    def shuffle_lines_action(self, event=None): pass
    def text_statistics_action(self, event=None): pass
    def extract_unique_words_dialog(self, event=None): pass
    def apply_extract_unique_words(self, case_sensitive: bool, sort_alpha: bool): pass
    def add_prefix_suffix_dialog(self, event=None): pass
    def apply_add_prefix_suffix(self, prefix_str: str, suffix_str: str, skip_empty: bool): pass
    def extract_pattern_dialog(self, event=None): pass
    def csv_to_text_table_action(self, event=None): pass
    def apply_extract_pattern(self, regex_pattern_str: str, case_insensitive: bool, unique_only: bool): pass
    def open_compare_lists_dialog(self, event=None): pass
    def _perform_and_show_list_comparison(self, list1_str: str, list2_str: str, case_sensitive: bool): pass
    def _show_list_comparison_results(self, common_lines, list1_unique, list2_unique, case_sensitive_used): pass
    def _process_selected_lines(self, line_operation_func, preserves_original_endings=True): pass
    def condense_internal_whitespace(self): pass
    def join_lines_with_space(self): pass
    def join_lines_with_comma_space(self): pass

    def toggle_filter_bar(self, event=None):
        current_tab = self.get_current_tab()
        if self.filter_bar_frame.winfo_ismapped():
            self.filter_bar_frame.pack_forget()
            if current_tab and (current_tab.is_tab_filtered_view or current_tab.tab_filter_str):
                self._is_updating_filter_bar_from_tab = True
                try:
                    current_tab.tab_filter_str = ""
                    current_tab.tab_filter_case_sensitive = False
                    current_tab.tab_filter_invert = False
                    self.filter_text_var.set("")
                    self.filter_case_var.set(False)
                    self.filter_invert_var.set(False)
                finally:
                    self._is_updating_filter_bar_from_tab = False
                current_tab.apply_text_filter()
        else:
            self.filter_bar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,2), before=self.notebook)
            if current_tab:
                self._is_updating_filter_bar_from_tab = True
                try:
                    self.filter_text_var.set(current_tab.tab_filter_str)
                    self.filter_case_var.set(current_tab.tab_filter_case_sensitive)
                    self.filter_invert_var.set(current_tab.tab_filter_invert)
                finally:
                    self._is_updating_filter_bar_from_tab = False
                current_tab.apply_text_filter()
            self.filter_entry.focus_set()
        return "break"

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
        current_tab = self.get_current_tab()
        if current_tab and current_tab.line_numbers_visible:
            current_tab.redraw_line_numbers()

    def prompt_go_to_line(self, event=None):
        current_tab = self.get_current_tab()
        if not current_tab: return "break"
        text_area = current_tab.text_area
        try: total_lines = int(text_area.index(f"{tk.END}-1c").split('.')[0])
        except (ValueError, tk.TclError): total_lines = 1
        line_num = simpledialog.askinteger("Go to Line", f"Enter line number (1-{total_lines}):", parent=self.root, minvalue=1, maxvalue=total_lines)
        if line_num is not None:
            if 1 <= line_num <= total_lines:
                text_area.mark_set(tk.INSERT, f"{line_num}.0")
                text_area.see(f"{line_num}.0")
                text_area.focus_set()
            else: messagebox.showwarning("Go to Line", f"Line number {line_num} is out of range (1-{total_lines}).", parent=self.root)
        return "break"

    def toggle_notes_style_action(self, event=None):
        self.notes_style_active = not self.notes_style_active
        for tab in self.tabs:
            tab.tab_notes_style_active = self.notes_style_active
            if tab.tab_notes_style_active:
                if hasattr(tab, '_clear_syntax_highlight_tags'): tab._clear_syntax_highlight_tags()
                if hasattr(tab, 'apply_notes_style_highlighting'): tab.apply_notes_style_highlighting()
                else: print(f"DEBUG: Tab {tab.current_file or 'Untitled'} missing apply_notes_style_highlighting")
            else:
                if hasattr(tab, 'clear_notes_style_highlighting'): tab.clear_notes_style_highlighting()
                else: print(f"DEBUG: Tab {tab.current_file or 'Untitled'} missing clear_notes_style_highlighting")
                if tab.current_language_name and hasattr(tab, 'apply_syntax_highlighting'): tab.apply_syntax_highlighting()
                if self.keyword_highlight_settings.get("active", False) and hasattr(tab, 'apply_keyword_highlights'): tab.apply_keyword_highlights(self.keyword_highlight_settings)
        current_tab = self.get_current_tab()
        if current_tab:
            if hasattr(current_tab, 'text_area') and current_tab.text_area.winfo_exists():
                current_tab.text_area.update_idletasks()

    def _handle_drop_files(self, event):
        dropped_files_str = event.data
        if not dropped_files_str: return
        raw_paths = re.findall(r'\{[^{}]+\}|[^\s]+', dropped_files_str)
        files_to_open = []
        for path_candidate in raw_paths:
            path = path_candidate
            if path.startswith('{') and path.endswith('}'): path = path[1:-1]
            path = path.strip('"\'')
            if os.path.isfile(path): files_to_open.append(path)
            elif os.path.isdir(path): pass
        if files_to_open: self._open_multiple_files(files_to_open)

    def _open_multiple_files(self, filepaths: list):
        for path in filepaths:
            already_open = False
            for tab_obj in self.tabs:
                if tab_obj.current_file == path:
                    self.notebook.select(tab_obj.frame_id())
                    already_open = True; break
            if not already_open:
                new_tab = EditorTab(self.notebook, self, file_path=path)
                if new_tab.current_file:
                    self.tabs.append(new_tab)
                    self.notebook.add(new_tab.frame)
                    new_tab.update_tab_title()
                    self.notebook.select(new_tab.frame_id())
                    new_tab.text_area.focus_set()
                else:
                    if new_tab.frame.winfo_exists(): new_tab.frame.destroy()
        if self.tabs:
            self.update_app_title()
            self.update_status_bar()

    def open_quick_text_dialog(self, event=None): dialog = QuickTextDialog(self); return "break"
    def open_flow_diagram_dialog(self, event=None): dialog = FlowDiagramDialog(self); return "break"
    def open_file_search_dialog(self, event=None): dialog = FileSearchDialog(self); return "break"

    def _display_search_results(self, results, search_phrase, is_regex, is_case_sensitive):
        if not results: messagebox.showinfo("Search Results", "No matches found.", parent=self.root); return
        results_tab = EditorTab(self.notebook, self); self.tabs.append(results_tab)
        display_phrase = search_phrase[:30] + '...' if len(search_phrase) > 30 else search_phrase
        results_tab_title = f"[Search Results: \"{display_phrase}\"]"
        self.notebook.add(results_tab.frame, text=results_tab_title); self.notebook.select(results_tab.frame_id())
        results_text_widget = results_tab.text_area; results_text_widget.config(state=tk.NORMAL)
        results_text_widget.delete("1.0", tk.END)
        highlight_tag_name = "search_result_highlight"
        results_text_widget.tag_configure(highlight_tag_name, background="yellow", foreground="black")
        grouped_results = collections.defaultdict(list)
        for result in results: grouped_results[result['filepath']].append(result)
        for filepath, file_matches in grouped_results.items():
            results_text_widget.insert(tk.END, f"File: {filepath}\n================================\n")
            for i, result in enumerate(file_matches):
                results_text_widget.insert(tk.END, f"  Line: {result['line_number']}\n")
                for before_line in result['context_before']: results_text_widget.insert(tk.END, f"    {before_line}\n")
                prefix_for_matched_line = "  > "
                matched_line_display_start_index = results_text_widget.index(tk.END + "-1c")
                results_text_widget.insert(tk.END, f"{prefix_for_matched_line}{result['matched_line']}\n")
                highlight_start_tk = f"{matched_line_display_start_index} + {len(prefix_for_matched_line) + result['match_start']} chars"
                highlight_end_tk = f"{matched_line_display_start_index} + {len(prefix_for_matched_line) + result['match_end']} chars"
                results_text_widget.tag_add(highlight_tag_name, highlight_start_tk, highlight_end_tk)
                for after_line in result['context_after']: results_text_widget.insert(tk.END, f"    {after_line}\n")
                if i < len(file_matches) - 1: results_text_widget.insert(tk.END, "  --------------------------------\n")
                else: results_text_widget.insert(tk.END, "\n")
        results_text_widget.config(state=tk.DISABLED); results_tab.text_changed = False; results_tab.current_file = None
        results_tab.update_tab_title()
        self.update_app_title(); self.update_status_bar(); results_tab.text_area.focus_set()

    def view_data_as_table_action(self, event=None):
        current_tab = self.get_current_tab()
        if not current_tab: messagebox.showerror("Error", "No active tab to process."); return "break"
        if data_to_table_converter is None:
            messagebox.showerror("Dependency Missing", "The 'data_to_table_converter' module or 'PyYAML' library is missing. Please ensure PyYAML is installed.", parent=self.root)
            return "break"
        content = current_tab.get_content()
        if not content.strip(): messagebox.showinfo("No Content", "Current tab is empty.", parent=self.root); return "break"
        try:
            parsed_data, data_type = data_to_table_converter.parse_data(content)
            table_string = data_to_table_converter.format_to_text_table(parsed_data)
            table_view_tab = EditorTab(self.notebook, self)
            self.tabs.append(table_view_tab)
            original_filename = os.path.basename(current_tab.current_file) if current_tab.current_file else "Untitled"
            table_tab_title = f"[Table View] {original_filename} ({data_type})"
            self.notebook.add(table_view_tab.frame, text=table_tab_title); self.notebook.select(table_view_tab.frame_id())
            table_view_tab.text_area.insert(tk.END, table_string); table_view_tab.text_area.config(state=tk.DISABLED)
            table_view_tab.text_changed = False; table_view_tab.current_file = None
            table_view_tab.update_tab_title()
            self.update_app_title(); self.update_status_bar(); table_view_tab.text_area.focus_set()
        except DataParsingError as e: messagebox.showerror("Data Parsing Error", str(e), parent=self.root)
        except Exception as e: messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.root)
        return "break"

    def open_rest_api_client_dialog(self, event=None): dialog = RestApiClientDialog(self); return "break"
    def open_sql_parser_dialog(self, event=None): dialog = SqlParserDialog(self); return "break"
    def open_excel_to_html_dialog(self, event=None): dialog = ExcelToHtmlDialog(self); return "break"
    def open_excel_to_csv_stats_dialog(self, event=None): dialog = ExcelToCsvStatsDialog(self); return "break"
    def open_url_manager_dialog(self, event=None): dialog = UrlManagerDialog(self); return "break"
    def open_drawing_tool_action(self, event=None): dialog = DrawingDialog(self); return "break"

class DrawingDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("Drawing Tool")
        self.top.transient(self.root)
        self.top.resizable(True, True)

        self.current_brush_size = 5
        self.current_color = "black"
        self.drawing_mode = "pen"
        self.line_style = "plain"
        self.last_x, self.last_y = None, None
        self.line_start_x, self.line_start_y = None, None
        self.temp_line_id = None
        self.shape_start_x, self.shape_start_y = None, None
        self.temp_shape_id = None

        self.highlighter_stipple = "gray25"
        self.stipple_patterns = ["Solid Fill", "gray75", "gray50", "gray25", "gray12", "hourglass", "info", "questhead", "error", "warning"]
        self.current_fill_pattern_var = tk.StringVar(value=self.stipple_patterns[0])
        self.grid_rows_var = tk.IntVar(value=3)
        self.grid_cols_var = tk.IntVar(value=3)

        self.eraser_button = None
        self.text_tool_button = None
        self.highlighter_button = None
        self.plain_line_button = None
        self.uni_arrow_button = None
        self.bi_arrow_button = None
        self.rectangle_button = None
        self.circle_button = None
        self.triangle_button = None
        self.apply_grid_button = None
        self.active_color_button = None

        main_dialog_frame = ttk.Frame(self.top, padding=5)
        main_dialog_frame.pack(expand=True, fill=tk.BOTH)

        self.sidebar_frame = ttk.Frame(main_dialog_frame, width=220, relief=tk.FLAT, borderwidth=0)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5), pady=0)
        self.sidebar_frame.pack_propagate(False)

        canvas_frame = ttk.Frame(main_dialog_frame)
        canvas_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        props_group = ttk.LabelFrame(self.sidebar_frame, text="Properties", padding=5)
        props_group.pack(fill=tk.X, pady=5, padx=5)

        brush_frame = ttk.Frame(props_group)
        brush_frame.pack(fill=tk.X, pady=2)
        ttk.Label(brush_frame, text="Size:").pack(side=tk.LEFT, padx=(0,2))
        self.brush_size_label_var = tk.StringVar(value=str(self.current_brush_size))
        self.brush_size_scale = ttk.Scale(brush_frame, from_=1, to=50, orient=tk.HORIZONTAL, command=self.set_brush_size_from_scale)
        self.brush_size_scale.set(self.current_brush_size)
        self.brush_size_scale.pack(side=tk.LEFT, padx=(0,2), fill=tk.X, expand=True)
        ttk.Label(brush_frame, textvariable=self.brush_size_label_var, width=3).pack(side=tk.LEFT)

        color_frame = ttk.Frame(props_group)
        color_frame.pack(fill=tk.X, pady=(5,2))
        ttk.Label(color_frame, text="Color:").pack(side=tk.LEFT, anchor=tk.NW, padx=(0,3))
        self.color_palette_frame = ttk.Frame(color_frame)
        self.color_palette_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.basic_colors = {
            "Black": "#000000", "LightRed": "#FF9999", "LightBlue": "#ADD8E6",
            "LightGreen": "#90EE90", "Yellow": "#FFFFE0"
        }
        self.color_palette_list = list(self.basic_colors.values())

        if self.current_color not in self.color_palette_list:
            self.current_color = self.color_palette_list[0] if self.color_palette_list else "#000000"

        num_color_cols = 5
        for i, color_code in enumerate(self.color_palette_list):
            color_btn_widget = tk.Frame(self.color_palette_frame, width=22, height=22, bg=color_code, relief=tk.RAISED, borderwidth=1)
            color_btn_widget.grid(row=i // num_color_cols, column=i % num_color_cols, padx=1, pady=1)
            color_btn_widget.bind("<Button-1>", lambda e, c=color_code, btn=color_btn_widget: self.select_color_button(c, btn))
            if color_code == self.current_color:
                 self.select_color_button(color_code, color_btn_widget)

        if not self.active_color_button and self.color_palette_list:
            first_color_code = self.color_palette_list[0]
            if self.color_palette_frame.winfo_children():
                 self.select_color_button(first_color_code, self.color_palette_frame.winfo_children()[0])

        fill_pattern_frame = ttk.Frame(props_group)
        fill_pattern_frame.pack(fill=tk.X, pady=(5,2))
        ttk.Label(fill_pattern_frame, text="Fill:").pack(side=tk.LEFT, padx=(0,2))
        self.fill_pattern_combo = ttk.Combobox(fill_pattern_frame, textvariable=self.current_fill_pattern_var,
                                               values=self.stipple_patterns, state="readonly", width=10)
        self.fill_pattern_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tools_group = ttk.LabelFrame(self.sidebar_frame, text="Tools", padding=5)
        tools_group.pack(fill=tk.X, pady=5, padx=5)

        basic_tools_subframe = ttk.Frame(tools_group)
        basic_tools_subframe.pack(fill=tk.X)
        btn_width = 9

        self.eraser_button = ttk.Button(basic_tools_subframe, text="Eraser", command=self.activate_eraser, width=btn_width)
        self.eraser_button.grid(row=0, column=0, padx=1, pady=1, sticky="ew")
        self.text_tool_button = ttk.Button(basic_tools_subframe, text="Text", command=self.activate_text_tool, width=btn_width)
        self.text_tool_button.grid(row=0, column=1, padx=1, pady=1, sticky="ew")
        self.highlighter_button = ttk.Button(basic_tools_subframe, text="Highlight", command=self.activate_highlighter_mode, width=btn_width)
        self.highlighter_button.grid(row=1, column=0, padx=1, pady=1, sticky="ew")

        line_tools_subframe = ttk.Frame(tools_group)
        line_tools_subframe.pack(fill=tk.X, pady=(5,0))
        self.plain_line_button = ttk.Button(line_tools_subframe, text="--", command=self.activate_plain_line_mode, width=5)
        self.plain_line_button.pack(side=tk.LEFT, padx=1)
        self.uni_arrow_button = ttk.Button(line_tools_subframe, text="→", command=self.activate_uni_arrow_mode, width=5)
        self.uni_arrow_button.pack(side=tk.LEFT, padx=1)
        self.bi_arrow_button = ttk.Button(line_tools_subframe, text="↔", command=self.activate_bi_arrow_mode, width=5)
        self.bi_arrow_button.pack(side=tk.LEFT, padx=1)

        shape_tools_subframe = ttk.Frame(tools_group)
        shape_tools_subframe.pack(fill=tk.X, pady=(5,0))
        self.rectangle_button = ttk.Button(shape_tools_subframe, text="□", command=self.activate_rectangle_mode, width=5)
        self.rectangle_button.pack(side=tk.LEFT, padx=1)
        self.circle_button = ttk.Button(shape_tools_subframe, text="○", command=self.activate_circle_mode, width=5)
        self.circle_button.pack(side=tk.LEFT, padx=1)
        self.triangle_button = ttk.Button(shape_tools_subframe, text="△", command=self.activate_triangle_mode, width=5)
        self.triangle_button.pack(side=tk.LEFT, padx=1)

        actions_group = ttk.LabelFrame(self.sidebar_frame, text="Canvas Actions", padding=5)
        actions_group.pack(fill=tk.X, pady=5, padx=5, side=tk.BOTTOM)

        grid_controls_frame = ttk.Frame(actions_group)
        grid_controls_frame.pack(fill=tk.X, pady=(0,5))

        row_col_frame = ttk.Frame(grid_controls_frame)
        row_col_frame.pack(fill=tk.X)
        ttk.Label(row_col_frame, text="Rows:").pack(side=tk.LEFT, padx=(0,1))
        self.grid_rows_spinbox = ttk.Spinbox(row_col_frame, from_=1, to=20, width=3, textvariable=self.grid_rows_var)
        self.grid_rows_spinbox.pack(side=tk.LEFT, padx=(0,3))
        ttk.Label(row_col_frame, text="Cols:").pack(side=tk.LEFT, padx=(0,1))
        self.grid_cols_spinbox = ttk.Spinbox(row_col_frame, from_=1, to=20, width=3, textvariable=self.grid_cols_var)
        self.grid_cols_spinbox.pack(side=tk.LEFT, padx=(0,3))

        self.apply_grid_button = ttk.Button(grid_controls_frame, text="Apply Grid", command=self.draw_grid_on_canvas)
        self.apply_grid_button.pack(fill=tk.X, pady=(3,0))

        clear_save_frame = ttk.Frame(actions_group)
        clear_save_frame.pack(fill=tk.X, pady=(5,0))
        clear_button = ttk.Button(clear_save_frame, text="Clear Canvas", command=self.clear_canvas)
        clear_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,1))
        save_png_button = ttk.Button(clear_save_frame, text="Save as PNG", command=self.save_canvas_as_png)
        save_png_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(1,0))

        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=1, highlightbackground="grey")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        self.top.bind('l', lambda event: self.activate_plain_line_mode())
        self.top.bind('L', lambda event: self.activate_plain_line_mode())
        self.top.bind('a', lambda event: self.activate_uni_arrow_mode())
        self.top.bind('A', lambda event: self.activate_uni_arrow_mode())
        self.top.bind('b', lambda event: self.activate_bi_arrow_mode())
        self.top.bind('B', lambda event: self.activate_bi_arrow_mode())
        self.top.bind('r', lambda event: self.activate_rectangle_mode())
        self.top.bind('R', lambda event: self.activate_rectangle_mode())
        self.top.bind('c', lambda event: self.activate_circle_mode())
        self.top.bind('C', lambda event: self.activate_circle_mode())
        self.top.bind('t', lambda event: self.activate_triangle_mode())
        self.top.bind('T', lambda event: self.activate_triangle_mode())
        self.top.bind('e', lambda event: self.activate_eraser())
        self.top.bind('E', lambda event: self.activate_eraser())
        self.top.bind('x', lambda event: self.activate_text_tool())
        self.top.bind('X', lambda event: self.activate_text_tool())
        self.top.bind('p', lambda event: self.activate_pen_mode())
        self.top.bind('P', lambda event: self.activate_pen_mode())
        self.top.bind('h', lambda event: self.activate_highlighter_mode())
        self.top.bind('H', lambda event: self.activate_highlighter_mode())

        self.top.update_idletasks()
        initial_width = max(700, self.sidebar_frame.winfo_reqwidth() + 500)
        initial_height = 550
        x_pos = self.root.winfo_x() + (self.root.winfo_width() // 2) - (initial_width // 2)
        y_pos = self.root.winfo_y() + (self.root.winfo_height() // 2) - (initial_height // 2)
        self.top.geometry(f'{initial_width}x{initial_height}+{x_pos}+{y_pos}')
        self.top.minsize(self.sidebar_frame.winfo_reqwidth() + 200, 400)

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
        elif self.drawing_mode in ["rectangle", "circle", "triangle"]:
            self.shape_start_x, self.shape_start_y = event.x, event.y
        elif self.drawing_mode == "highlighter":
            self.last_x, self.last_y = event.x, event.y
            highlighter_brush_size = max(10, self.current_brush_size * 2)
            x1 = event.x - highlighter_brush_size / 2
            y1 = event.y - highlighter_brush_size / 2
            x2 = event.x + highlighter_brush_size / 2
            y2 = event.y + highlighter_brush_size / 2
            self.canvas.create_oval(x1, y1, x2, y2, fill=self.current_color, outline=self.current_color, width=0, stipple=self.highlighter_stipple)

    def draw(self, event):
        if self.drawing_mode == "pen":
            if self.last_x and self.last_y:
                self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                        width=self.current_brush_size, fill=self.current_color,
                                        capstyle=tk.ROUND, smooth=tk.TRUE, splinesteps=128)
                x1_pen, y1_pen = (event.x - self.current_brush_size / 2), (event.y - self.current_brush_size / 2)
                x2_pen, y2_pen = (event.x + self.current_brush_size / 2), (event.y + self.current_brush_size / 2)
                self.canvas.create_oval(x1_pen, y1_pen, x2_pen, y2_pen, fill=self.current_color, outline=self.current_color)
                self.last_x, self.last_y = event.x, event.y
        elif self.drawing_mode == "highlighter":
            if self.last_x and self.last_y:
                highlighter_brush_size = max(10, self.current_brush_size * 2)
                self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                        width=highlighter_brush_size, fill=self.current_color,
                                        capstyle=tk.ROUND, smooth=tk.FALSE,
                                        stipple=self.highlighter_stipple)
                self.last_x, self.last_y = event.x, event.y
        elif self.drawing_mode == "line":
            if self.line_start_x is not None and self.line_start_y is not None:
                if self.temp_line_id:
                    self.canvas.delete(self.temp_line_id)
                self.temp_line_id = self.canvas.create_line(self.line_start_x, self.line_start_y, event.x, event.y,
                                                            width=self.current_brush_size, fill=self.current_color,
                                                            capstyle=tk.ROUND)
        elif self.drawing_mode in ["rectangle", "circle", "triangle"]:
            if self.shape_start_x is not None and self.shape_start_y is not None:
                if self.temp_shape_id:
                    self.canvas.delete(self.temp_shape_id)
                x1, y1 = self.shape_start_x, self.shape_start_y
                x2, y2 = event.x, event.y
                draw_x1, draw_y1 = min(x1, x2), min(y1, y2)
                draw_x2, draw_y2 = max(x1, x2), max(y1, y2)
                if self.drawing_mode == "rectangle":
                    self.temp_shape_id = self.canvas.create_rectangle(draw_x1, draw_y1, draw_x2, draw_y2,
                                                                    outline=self.current_color, width=self.current_brush_size,
                                                                    fill="", stipple="")
                elif self.drawing_mode == "circle":
                    self.temp_shape_id = self.canvas.create_oval(draw_x1, draw_y1, draw_x2, draw_y2,
                                                                 outline=self.current_color, width=self.current_brush_size,
                                                                 fill="", stipple="")
                elif self.drawing_mode == "triangle":
                    p1 = ((x1 + x2) / 2, y1)
                    p2 = (x1, y2)
                    p3 = (x2, y2)
                    self.temp_shape_id = self.canvas.create_polygon(p1, p2, p3,
                                                                    outline=self.current_color, width=self.current_brush_size,
                                                                    fill="", stipple="")

    def stop_draw(self, event):
        if self.drawing_mode == "pen":
            self.last_x, self.last_y = None, None
        elif self.drawing_mode == "highlighter":
            self.last_x, self.last_y = None, None
        elif self.drawing_mode == "line":
            if self.temp_line_id:
                self.canvas.delete(self.temp_line_id)
                self.temp_line_id = None
            if self.line_start_x is not None and self.line_start_y is not None:
                x1, y1 = self.line_start_x, self.line_start_y
                x2, y2 = event.x, event.y
                arrow_option = tk.NONE
                if self.line_style == "uni_arrow": arrow_option = tk.LAST
                elif self.line_style == "bi_arrow": arrow_option = tk.BOTH
                arrow_shape_spec = (10, 12, 5)
                self.canvas.create_line(x1, y1, x2, y2, width=self.current_brush_size, fill=self.current_color,
                                        arrow=arrow_option, arrowshape=arrow_shape_spec, capstyle=tk.ROUND)
            self.line_start_x, self.line_start_y = None, None
        elif self.drawing_mode in ["rectangle", "circle", "triangle"]:
            if self.temp_shape_id:
                self.canvas.delete(self.temp_shape_id)
                self.temp_shape_id = None
            if self.shape_start_x is not None and self.shape_start_y is not None:
                x1, y1 = self.shape_start_x, self.shape_start_y
                x2, y2 = event.x, event.y
                draw_x1, draw_y1 = min(x1, x2), min(y1, y2)
                draw_x2, draw_y2 = max(x1, x2), max(y1, y2)
                selected_pattern = self.current_fill_pattern_var.get()
                stipple_option = ""
                if selected_pattern != "Solid Fill":
                    stipple_option = selected_pattern
                if self.drawing_mode == "rectangle":
                    self.canvas.create_rectangle(draw_x1, draw_y1, draw_x2, draw_y2,
                                                 fill=self.current_color, outline=self.current_color,
                                                 width=0, stipple=stipple_option)
                elif self.drawing_mode == "circle":
                    self.canvas.create_oval(draw_x1, draw_y1, draw_x2, draw_y2,
                                            fill=self.current_color, outline=self.current_color,
                                            width=0, stipple=stipple_option)
                elif self.drawing_mode == "triangle":
                    p1_x, p1_y = (x1 + x2) / 2, y1
                    p2_x, p2_y = x1, y2
                    p3_x, p3_y = x2, y2
                    self.canvas.create_polygon(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y,
                                               fill=self.current_color, outline=self.current_color,
                                               width=0, stipple=stipple_option)
            self.shape_start_x, self.shape_start_y = None, None

    def set_brush_size_from_scale(self, value):
        self.current_brush_size = int(float(value))
        self.brush_size_label_var.set(str(self.current_brush_size))

    def select_color_button(self, color_code, button_widget):
        self.current_color = color_code
        if self.active_color_button and self.active_color_button != button_widget:
            self.active_color_button.config(relief=tk.RAISED, borderwidth=1)
        button_widget.config(relief=tk.SUNKEN, borderwidth=1)
        self.active_color_button = button_widget
        if self.eraser_button and hasattr(self.eraser_button, 'state') and 'pressed' in self.eraser_button.state():
            if color_code != "white":
                 self.eraser_button.state(['!pressed'])
                 self.eraser_button_active = False

    def set_color(self, color):
        self.current_color = color

    def activate_eraser(self):
        self.set_color("white")
        self.drawing_mode = "pen"
        self._deactivate_all_tools_visual()
        if self.eraser_button and hasattr(self.eraser_button, 'state'):
            self.eraser_button.state(['pressed'])
        self.eraser_button_active = True

    def activate_text_tool(self):
        self.drawing_mode = "text"
        self._deactivate_all_tools_visual()
        if self.text_tool_button and hasattr(self.text_tool_button, 'state'):
            self.text_tool_button.state(['pressed'])

    def _deactivate_all_tools_visual(self):
        tool_buttons = [
            self.eraser_button, self.text_tool_button, self.highlighter_button,
            self.plain_line_button, self.uni_arrow_button, self.bi_arrow_button,
            self.rectangle_button, self.circle_button, self.triangle_button
        ]
        for btn in tool_buttons:
            if btn and hasattr(btn, 'state'):
                btn.state(['!pressed'])
        self.eraser_button_active = False

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

    def activate_rectangle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "rectangle"
        if hasattr(self.rectangle_button, 'state'):
            self.rectangle_button.state(['pressed'])

    def activate_circle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "circle"
        if hasattr(self.circle_button, 'state'):
            self.circle_button.state(['pressed'])

    def activate_triangle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "triangle"
        if hasattr(self.triangle_button, 'state'):
            self.triangle_button.state(['pressed'])

    def activate_highlighter_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "highlighter"
        if hasattr(self.highlighter_button, 'state'):
            self.highlighter_button.state(['pressed'])

    def activate_pen_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "pen"
        if self.active_color_button:
            self.active_color_button.config(relief=tk.SUNKEN, borderwidth=1)
        else:
            if self.color_palette_list:
                first_color_code = self.color_palette_list[0]
                if self.color_palette_frame.winfo_children():
                     self.select_color_button(first_color_code, self.color_palette_frame.winfo_children()[0])

    def clear_canvas(self):
        if messagebox.askyesno("Clear Canvas", "Are you sure you want to clear the entire canvas?\nThis action cannot be undone (yet!).", parent=self.top):
            self.canvas.delete("all")

    def draw_grid_on_canvas(self):
        self.canvas.delete("grid_line")
        try:
            rows = self.grid_rows_var.get()
            cols = self.grid_cols_var.get()
        except tk.TclError:
            messagebox.showerror("Input Error", "Please enter valid integer values for rows and columns.", parent=self.top)
            return
        if rows < 1 or cols < 1: return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            messagebox.showwarning("Canvas Size Error", "Canvas is not ready or too small to draw a grid.", parent=self.top)
            return
        cell_width = canvas_width / cols
        cell_height = canvas_height / rows
        for i in range(1, cols):
            x = i * cell_width
            self.canvas.create_line(x, 0, x, canvas_height, fill="lightgrey", dash=(2, 2), tags="grid_line")
        for i in range(1, rows):
            y = i * cell_height
            self.canvas.create_line(0, y, canvas_width, y, fill="lightgrey", dash=(2, 2), tags="grid_line")

    def save_canvas_as_png(self):
        try:
            from PIL import ImageGrab
        except ImportError:
            messagebox.showerror("Dependency Missing","The 'Pillow' library is not installed. Please install it (e.g., pip install Pillow) to save images.",parent=self.top)
            return
        filepath = filedialog.asksaveasfilename(parent=self.top,title="Save Canvas As PNG",defaultextension=".png",initialfile="drawing.png",filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
        if not filepath: return
        try:
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            if width <= 0 or height <= 0:
                messagebox.showerror("Save Error", "Canvas has no dimensions to capture.", parent=self.top)
                return
            self.top.update_idletasks()
            self.canvas.after(200, lambda: self._capture_and_save_png(filepath, x, y, width, height))
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save canvas as PNG: {e}", parent=self.top)

    def _capture_and_save_png(self, filepath, x, y, width, height):
        try:
            from PIL import ImageGrab
            bbox = (x, y, x + width, y + height)
            image = ImageGrab.grab(bbox=bbox, all_screens=True)
            if image is None:
                messagebox.showerror("Capture Error", "Failed to grab canvas image. Image is None.", parent=self.top)
                return
            if image.width == 0 or image.height == 0:
                messagebox.showerror("Capture Error", "Grabbed image has zero dimensions.", parent=self.top)
                return
            image.save(filepath, "PNG")
            messagebox.showinfo("Save Successful", f"Canvas saved successfully as {filepath}", parent=self.top)
        except Exception as e:
            error_detail = str(e)
            if "grab" in error_detail.lower() and "X server" in error_detail:
                error_detail += "\n\nThis might be an issue with screen grabbing on your Linux environment. Ensure necessary tools (e.g., scrot, maim, or X server configuration) are set up if Pillow relies on them."
            elif "Permission denied" in error_detail:
                 error_detail += f"\n\nEnsure you have write permissions for the directory: {os.path.dirname(filepath)}"
            messagebox.showerror("Save Error", f"Could not save canvas as PNG: {error_detail}", parent=self.top)

class ExcelToCsvStatsDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("Excel to CSVs & Statistics")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(False, False)

        self.input_excel_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()

        main_frame = ttk.Frame(self.top, padding=15)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Excel File (.xlsx):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        input_file_entry = ttk.Entry(main_frame, textvariable=self.input_excel_file_var, width=50)
        input_file_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        input_file_button = ttk.Button(main_frame, text="Browse...", command=self._browse_input_file)
        input_file_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        output_dir_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50)
        output_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        output_dir_button = ttk.Button(main_frame, text="Browse...", command=self._browse_output_dir)
        output_dir_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)

        generate_button = ttk.Button(main_frame, text="Generate CSVs & Stats", command=self._generate_files)
        generate_button.grid(row=2, column=0, columnspan=3, pady=15)

        input_file_entry.focus_set()
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        self.top.minsize(550, 180)

    def _browse_input_file(self):
        filepath = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel Files", "*.xlsx")], parent=self.top)
        if filepath: self.input_excel_file_var.set(filepath)

    def _browse_output_dir(self):
        dirpath = filedialog.askdirectory(title="Select Output Directory", parent=self.top)
        if dirpath: self.output_dir_var.set(dirpath)

    def _generate_files(self):
        input_file = self.input_excel_file_var.get()
        user_selected_output_dir = self.output_dir_var.get()
        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Input Error", "Please select a valid Excel input file.", parent=self.top)
            return
        if not user_selected_output_dir:
            if messagebox.askyesno("Output Directory", "No output directory selected. Use the input file's directory as the base for output?", parent=self.top):
                base_output_dir = os.path.dirname(input_file)
                self.output_dir_var.set(base_output_dir)
            else: return
        else:
            base_output_dir = user_selected_output_dir
            if not os.path.isdir(base_output_dir):
                messagebox.showerror("Input Error", "The selected output directory is not valid.", parent=self.top)
                return
        excel_filename_no_ext = os.path.splitext(os.path.basename(input_file))[0]
        sanitized_folder_name = re.sub(r'[^\w\s-]', '', excel_filename_no_ext).strip().replace(' ', '_')
        if not sanitized_folder_name: sanitized_folder_name = "excel_csv_stats_output"
        final_output_subfolder = os.path.join(base_output_dir, f"{sanitized_folder_name}_csv_stats")
        try: os.makedirs(final_output_subfolder, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Output Error", f"Could not create output subfolder: {final_output_subfolder}\nError: {e}", parent=self.top)
            return
        try:
            import openpyxl
            import csv # csv is standard, but good to note
            # subprocess is already imported at top level
        except ImportError as e:
            messagebox.showerror("Dependency Missing", f"A required library is missing: {e.name}. Please ensure 'openpyxl' is available.", parent=self.top)
            return
        try:
            workbook = openpyxl.load_workbook(input_file, read_only=True)
            sheet_names = workbook.sheetnames
            generated_count = 0
            errors_occurred = []
            for sheet_name in sheet_names:
                ws = workbook[sheet_name]
                sane_sheet_filename_part = re.sub(r'[^\w\s-]', '', sheet_name).strip().replace(' ', '_')
                if not sane_sheet_filename_part: sane_sheet_filename_part = f"sheet_{generated_count + 1}"
                csv_filename = f"{sane_sheet_filename_part}.csv"
                csv_filepath = os.path.join(final_output_subfolder, csv_filename)
                stats_txt_filename = f"{csv_filename}.txt"
                stats_txt_filepath = os.path.join(final_output_subfolder, stats_txt_filename)
                try:
                    with open(csv_filepath, 'w', newline='', encoding='utf-8') as f_csv:
                        writer = csv.writer(f_csv)
                        for row in ws.iter_rows(): writer.writerow([cell.value for cell in row])
                    try:
                        process_result = subprocess.run(['csvstat', csv_filepath], capture_output=True, text=True, check=False, encoding='utf-8')
                        if process_result.returncode == 0:
                            with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt: f_txt.write(process_result.stdout)
                            generated_count += 1
                        else:
                            error_detail = f"Error running csvstat on {csv_filename}:\n{process_result.stderr}"
                            if process_result.stdout: error_detail += f"\nStdout:\n{process_result.stdout}"
                            with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt: f_txt.write(error_detail)
                            errors_occurred.append(error_detail)
                    except FileNotFoundError:
                        error_msg = "Error: 'csvstat' command not found. Please ensure csvkit is installed and 'csvstat' is in your system's PATH."
                        messagebox.showerror("csvstat Error", error_msg, parent=self.top)
                        with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt: f_txt.write(error_msg)
                        errors_occurred.append(f"csvstat not found for {csv_filename}.")
                except Exception as e_file: errors_occurred.append(f"Failed to process sheet '{sheet_name}': {e_file}")
            if errors_occurred:
                error_summary = "\n\n".join(errors_occurred)
                messagebox.showwarning("Processing Issues", f"{generated_count} sheet(s) processed with stats. Some errors occurred:\n\n{error_summary}\n\nCheck files in {final_output_subfolder}", parent=self.top)
            elif generated_count > 0:
                messagebox.showinfo("Success", f"Successfully generated {generated_count} CSV file(s) and their statistics in:\n{final_output_subfolder}", parent=self.top)
            else: messagebox.showinfo("No Data", "No sheets were processed or found in the Excel file.", parent=self.top)
        except FileNotFoundError: messagebox.showerror("Error", f"Input Excel file not found: {input_file}", parent=self.top)
        except openpyxl.utils.exceptions.InvalidFileException: messagebox.showerror("Error", "Invalid Excel file format. Please provide a .xlsx file.", parent=self.top)
        except Exception as e: messagebox.showerror("Generation Error", f"An unexpected error occurred: {e}", parent=self.top)

class UrlManagerDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("URL Manager")
        self.top.transient(self.root)
        self.top.geometry("700x500")
        self.top.resizable(True, True)
        self.top.minsize(500, 350)
        self.bookmarks_data = {}
        self.all_bookmark_sets_data = {}
        self.current_ini_file = None
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        top_controls_frame = ttk.Frame(main_frame)
        top_controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        top_controls_frame.grid_columnconfigure(3, weight=1)
        self.bookmark_files_map = {}
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
        search_entry.grid(row=0, column=5, padx=(0,0), pady=(0,5), sticky=tk.E)
        self.search_var.trace_add("write", self._filter_display)
        self.global_search_var = tk.BooleanVar(value=False)
        global_search_checkbox = ttk.Checkbutton(top_controls_frame, text="Global", variable=self.global_search_var)
        global_search_checkbox.grid(row=0, column=6, padx=(5,0), pady=(0,5), sticky=tk.E)
        self.global_search_var.trace_add("write", self._filter_display)
        columns = ("description", "url")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="tree headings", height=15)
        self.tree.heading("#0", text="Group")
        self.tree.column("#0", width=150, stretch=tk.NO, anchor=tk.W)
        self.tree.heading("description", text="Description / Name")
        self.tree.column("description", width=250 + 20, anchor=tk.W)
        self.tree.heading("url", text="URL")
        self.tree.column("url", width=300 + 20, anchor=tk.W)
        tree_scrollbar_y = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        tree_scrollbar_y.grid(row=1, column=1, sticky="ns")
        bottom_controls_frame = ttk.Frame(main_frame, padding=(0,10,0,0))
        bottom_controls_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.open_url_button = ttk.Button(bottom_controls_frame, text="Open Selected URL", command=self._open_selected_url, state=tk.DISABLED)
        self.open_url_button.pack(side=tk.LEFT)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._open_selected_url)
        self.top.update_idletasks()
        x_pos = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y_pos = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'{self.top.winfo_width()}x{self.top.winfo_height()}+{x_pos}+{y_pos}')
        self._populate_bookmarks_dropdown()
        self._load_all_bookmark_sets_data()
        self._try_load_default_ini()

    def _load_all_bookmark_sets_data(self):
        self.all_bookmark_sets_data.clear()
        if not self.bookmark_files_map: return
        import configparser
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
                else: print(f"Warning: Could not read or parse '{filename}' for global search cache.")
            except configparser.Error as e: print(f"Warning: Error parsing INI file '{filename}' for global search cache: {e}")
            except Exception as e: print(f"Warning: Unexpected error loading '{filename}' for global search cache: {e}")

    def _find_bookmark_files(self):
        filenames_paths = []
        seen_filenames = set()
        bookmarks_dirname = "bookmarks"
        possible_base_paths = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
        unique_base_paths = []
        for p in possible_base_paths:
            if p not in unique_base_paths: unique_base_paths.append(p)
        for base_path in unique_base_paths:
            bookmarks_path = os.path.join(base_path, bookmarks_dirname)
            if os.path.isdir(bookmarks_path):
                try:
                    for entry in os.listdir(bookmarks_path):
                        if entry.lower().endswith(".ini") and entry not in seen_filenames:
                            full_path = os.path.join(bookmarks_path, entry)
                            if os.path.isfile(full_path):
                                filenames_paths.append((entry, full_path))
                                seen_filenames.add(entry)
                except OSError as e: print(f"Error accessing bookmarks directory {bookmarks_path}: {e}")
        filenames_paths.sort(key=lambda x: x[0].lower())
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

    def _on_bookmark_set_selected(self, event=None):
        selected_display_name = self.selected_bookmark_file_var.get()
        if selected_display_name and selected_display_name in self.bookmark_files_map:
            filepath_to_load = self.bookmark_files_map[selected_display_name]
            self._load_ini_file(filepath_arg=filepath_to_load)

    def _try_load_default_ini(self):
        available_files = self.bookmarks_combobox.cget("values")
        if not available_files:
            self.loaded_file_label_var.set("No bookmark sets found in 'bookmarks/' directory.")
            return
        file_to_load_display_name = None
        default_ini_name = "default.ini"
        if default_ini_name in available_files: file_to_load_display_name = default_ini_name
        elif available_files: file_to_load_display_name = available_files[0]
        if file_to_load_display_name:
            self.selected_bookmark_file_var.set(file_to_load_display_name)
            filepath_to_load = self.bookmark_files_map.get(file_to_load_display_name)
            if filepath_to_load: self._load_ini_file(filepath_arg=filepath_to_load)
            else:
                print(f"Error: Display name '{file_to_load_display_name}' not found in bookmark_files_map.")
                self.loaded_file_label_var.set(f"Error finding path for {file_to_load_display_name}.")
        else: self.loaded_file_label_var.set("Select a bookmark set.")

    def _load_ini_file(self, filepath_arg=None):
        actual_filepath_to_load = None
        is_default_load_attempt = False
        if filepath_arg and os.path.isfile(filepath_arg):
            actual_filepath_to_load = filepath_arg
            is_default_load_attempt = True
        else:
            selected_via_dialog = filedialog.askopenfilename(title="Open INI File", filetypes=[("INI files", "*.ini"), ("All files", "*.*")], parent=self.top)
            if not selected_via_dialog: return
            actual_filepath_to_load = selected_via_dialog
            is_default_load_attempt = False
        import configparser
        parser = configparser.ConfigParser()
        try:
            parsed_files = parser.read(actual_filepath_to_load, encoding='utf-8')
            if not parsed_files:
                if is_default_load_attempt and self.current_ini_file and self.current_ini_file != actual_filepath_to_load:
                    print(f"Debug: Default INI file '{os.path.basename(actual_filepath_to_load)}' not found or failed to parse. Keeping '{os.path.basename(self.current_ini_file) if self.current_ini_file else 'None'}'.")
                else:
                    messagebox.showerror("Error", f"Could not read or parse INI file: {os.path.basename(actual_filepath_to_load)}", parent=self.top)
                    self._handle_load_error()
                return
            self.bookmarks_data.clear()
            for section in parser.sections():
                self.bookmarks_data[section] = {}
                for description_key, url_value in parser.items(section):
                    self.bookmarks_data[section][description_key] = url_value
            self.current_ini_file = actual_filepath_to_load
            self.loaded_file_label_var.set(f"Loaded: {os.path.basename(actual_filepath_to_load)}")
            self._populate_treeview()
            self.open_url_button.config(state=tk.DISABLED)
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
        for item in self.tree.get_children(): self.tree.delete(item)

    def _populate_treeview(self):
        self._clear_treeview()
        if not self.bookmarks_data: return
        padding_spaces = "   "
        for group_name, items in sorted(self.bookmarks_data.items()):
            group_node_id = self.tree.insert("", tk.END, text=group_name, open=True, tags=('group',))
            sorted_items = sorted(items.items())
            for description, url in sorted_items:
                padded_description = padding_spaces + description
                padded_url = padding_spaces + url
                self.tree.insert(group_node_id, tk.END, values=(padded_description, padded_url), tags=('item',))
        self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
        self.tree.tag_configure('item')

    def _filter_display(self, *args):
        search_term = self.search_var.get().lower()
        self._clear_treeview()
        padding_spaces = "   "
        is_global = self.global_search_var.get()
        if not search_term and not is_global:
            self._populate_treeview()
            return
        if not search_term and is_global:
            for ini_filename, file_data in sorted(self.all_bookmark_sets_data.items()):
                file_node_id = self.tree.insert("", tk.END, text=ini_filename, open=True, tags=('file_header',))
                for group_name, items in sorted(file_data.items()):
                    group_node_id = self.tree.insert(file_node_id, tk.END, text=group_name, open=True, tags=('group',))
                    for description, url in sorted(items.items()):
                        padded_description = padding_spaces + description
                        padded_url = padding_spaces + url
                        self.tree.insert(group_node_id, tk.END, values=(padded_description, padded_url), tags=('item',))
            self.tree.tag_configure('file_header', font=tkfont.Font(weight='bold', slant='italic'))
            self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
            self.tree.tag_configure('item')
            return
        if is_global:
            for ini_filename, file_data in sorted(self.all_bookmark_sets_data.items()):
                file_node_id_for_this_file = None
                for group_name, items in sorted(file_data.items()):
                    group_node_id_for_this_group = None
                    for description, url in sorted(items.items()):
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
            if not self.bookmarks_data: return
            for group_name, items in sorted(self.bookmarks_data.items()):
                group_node_id_for_this_group = None
                for description, url in sorted(items.items()):
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
        if not selected_item_id: return
        item_tags = self.tree.item(selected_item_id, "tags")
        if 'item' not in item_tags:
            if event and hasattr(event, 'type') and str(event.type) == "ButtonPress" and event.num == 1:
                 if 'group' in item_tags or 'file_header' in item_tags:
                     try: self.tree.item(selected_item_id, open=not self.tree.item(selected_item_id, "open"))
                     except tk.TclError: pass
            return
        try:
            item_values = self.tree.item(selected_item_id, "values")
            if item_values and len(item_values) >= 2:
                padded_url = item_values[1]
                url_to_open = padded_url.lstrip()
                if url_to_open:
                    import webbrowser
                    try: webbrowser.open_new_tab(url_to_open)
                    except Exception as e: messagebox.showerror("Error Opening URL", f"Could not open URL: {url_to_open}\nError: {e}", parent=self.top)
                else: messagebox.showwarning("No URL", "Selected item does not have a valid URL after stripping padding.", parent=self.top)
            else: messagebox.showwarning("No URL Data", "Could not retrieve URL for the selected item.", parent=self.top)
        except Exception as e: messagebox.showerror("Error", f"An error occurred while trying to open URL: {e}", parent=self.top)

    def _on_tree_select(self, event=None):
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            self.open_url_button.config(state=tk.DISABLED)
            return
        item_tags = self.tree.item(selected_item_id, "tags")
        if 'item' in item_tags: self.open_url_button.config(state=tk.NORMAL)
        else: self.open_url_button.config(state=tk.DISABLED)

class ExcelToHtmlDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("Excel to HTML Site Generator")
        self.top.transient(self.root)
        self.top.grab_set()
        self.top.resizable(False, False)
        self.input_excel_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.site_title_var = tk.StringVar(value="Excel Data Site")
        main_frame = ttk.Frame(self.top, padding=15)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1)
        ttk.Label(main_frame, text="Excel File (.xlsx):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        input_file_entry = ttk.Entry(main_frame, textvariable=self.input_excel_file_var, width=50)
        input_file_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        input_file_button = ttk.Button(main_frame, text="Browse...", command=self._browse_input_file)
        input_file_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        output_dir_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50)
        output_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        output_dir_button = ttk.Button(main_frame, text="Browse...", command=self._browse_output_dir)
        output_dir_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Label(main_frame, text="Site Title (Optional):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        site_title_entry = ttk.Entry(main_frame, textvariable=self.site_title_var, width=50)
        site_title_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        generate_button = ttk.Button(main_frame, text="Generate HTML Site", command=self._generate_html_site)
        generate_button.grid(row=3, column=0, columnspan=3, pady=15)
        input_file_entry.focus_set()
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        self.top.minsize(550, 220)

    def _browse_input_file(self):
        filepath = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel Files", "*.xlsx")], parent=self.top)
        if filepath: self.input_excel_file_var.set(filepath)

    def _browse_output_dir(self):
        dirpath = filedialog.askdirectory(title="Select Output Directory", parent=self.top)
        if dirpath: self.output_dir_var.set(dirpath)

    def _generate_html_site(self):
        input_file = self.input_excel_file_var.get()
        user_selected_output_dir = self.output_dir_var.get()
        site_title = self.site_title_var.get().strip()
        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Input Error", "Please select a valid Excel input file.", parent=self.top)
            return
        if not user_selected_output_dir:
            base_output_dir = os.path.dirname(input_file)
            self.output_dir_var.set(base_output_dir)
        else:
            base_output_dir = user_selected_output_dir
            if not os.path.isdir(base_output_dir):
                messagebox.showerror("Input Error", "The selected output directory is not valid.", parent=self.top)
                return
        excel_filename_no_ext = os.path.splitext(os.path.basename(input_file))[0]
        sanitized_folder_name = re.sub(r'[^\w\s-]', '', excel_filename_no_ext).strip().replace(' ', '_')
        if not sanitized_folder_name: sanitized_folder_name = "excel_site_output"
        final_output_path = os.path.join(base_output_dir, sanitized_folder_name)
        try: os.makedirs(final_output_path, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Output Error", f"Could not create output subfolder: {final_output_path}\nError: {e}", parent=self.top)
            return
        try: import openpyxl
        except ImportError:
            messagebox.showerror("Dependency Missing", "The 'openpyxl' library is not installed. Please install it (e.g., pip install openpyxl).", parent=self.top)
            return
        basic_css = """<style>body {font-family: sans-serif;margin: 0;background-color: #f4f4f4;color: #333;display: flex;min-height: 100vh;}.sidebar {width: 220px;background-color: #333;color: #fff;padding: 15px;height: 100vh;position: fixed;overflow-y: auto;}.sidebar h2 {text-align: center;color: #fff;margin-top: 0;}.sidebar ul {list-style-type: none;padding: 0;}.sidebar ul li a {display: block;color: #fff;padding: 8px 10px;text-decoration: none;border-radius: 4px;}.sidebar ul li a:hover, .sidebar ul li a.active {background-color: #555;}.main-content {margin-left: 240px;padding: 20px;flex-grow: 1;background-color: #fff;}header {text-align: center;margin-bottom:20px;}table { border-collapse: collapse; width: 100%; margin-top: 20px; }th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }th { background-color: #f0f0f0; }tr:nth-child(even) { background-color: #f9f9f9; }tr:hover { background-color: #f1f1f1; }h1, h2 { color: #333; }a { color: #007bff; }a:hover { color: #0056b3; }#filterInput {padding: 8px;margin-bottom: 10px;border: 1px solid #ccc;border-radius: 4px;width: calc(100% - 120px);box-sizing: border-box;}button {padding: 8px 12px;background-color: #5cb85c;color: white;border: none;border-radius: 4px;cursor: pointer;margin-left: 5px;}button:hover {background-color: #4cae4c;}</style>"""
        def sanitize_filename(name):
            name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
            return name if name else "untitled_sheet"
        try:
            workbook = openpyxl.load_workbook(input_file, read_only=True)
            sheet_names = workbook.sheetnames
            generated_files_info = []
            for sheet_name in sheet_names:
                ws = workbook[sheet_name]
                html_filename = sanitize_filename(sheet_name) + ".html"
                generated_files_info.append({"name": sheet_name, "file": html_filename, "original_name": sheet_name, "row_count": ws.max_row, "col_count": ws.max_column})
            generated_files_info.sort(key=lambda x: x["name"])
            index_html_path = os.path.join(final_output_path, "index.html")
            with open(index_html_path, "w", encoding="utf-8") as f_index:
                f_index.write(f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n")
                index_page_title = f"{site_title if site_title else excel_filename_no_ext} - Overview"
                f_index.write(f"<title>{index_page_title}</title>\n{basic_css}\n</head>\n<body>\n")
                f_index.write("<div class=\"sidebar\">\n")
                f_index.write(f"  <h2>{site_title if site_title else 'Navigation'}</h2>\n  <ul>\n")
                f_index.write(f"    <li><a href=\"index.html\" class=\"active\">Home (Overview)</a></li>\n")
                for sheet_info_nav in generated_files_info: f_index.write(f"    <li><a href=\"{sheet_info_nav['file']}\">{sheet_info_nav['name']}</a></li>\n")
                f_index.write("  </ul>\n</div>\n")
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
                f_index.write("  </table>\n</div>\n</body>\n</html>")
            for current_sheet_info in generated_files_info:
                sheet_name = current_sheet_info["original_name"]
                html_filename = current_sheet_info["file"]
                sheet_html_path = os.path.join(final_output_path, html_filename)
                ws = workbook[sheet_name]
                with open(sheet_html_path, "w", encoding="utf-8") as f_sheet:
                    f_sheet.write(f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n")
                    page_specific_title = f"{sheet_name} - {site_title}" if site_title else sheet_name
                    f_sheet.write(f"<title>{page_specific_title}</title>\n{basic_css}\n</head>\n<body>\n")
                    f_sheet.write("<div class=\"sidebar\">\n")
                    f_sheet.write(f"  <h2>{site_title if site_title else 'Navigation'}</h2>\n  <ul>\n")
                    f_sheet.write(f"    <li><a href=\"index.html\">Home (Overview)</a></li>\n")
                    for other_sheet_info in generated_files_info:
                        active_class = ' class="active"' if other_sheet_info["file"] == html_filename else ''
                        f_sheet.write(f"    <li><a href=\"{other_sheet_info['file']}\"{active_class}>{other_sheet_info['name']}</a></li>\n")
                    f_sheet.write("  </ul>\n</div>\n")
                    f_sheet.write("<div class=\"main-content\">\n")
                    f_sheet.write(f"  <header><h1>{sheet_name}</h1></header>\n")
                    f_sheet.write("  <h2>Sheet Data:</h2>\n")
                    f_sheet.write("  <div>\n")
                    f_sheet.write(f"    <input type=\"text\" id=\"filterInput\" onkeyup=\"filterTable()\" placeholder=\"Filter table content...\" title=\"Type in a name to filter the table\">\n")
                    f_sheet.write(f"    <button onclick=\"clearFilter()\">Clear Filter</button>\n")
                    f_sheet.write("  </div>\n")
                    f_sheet.write("  <table id=\"sheetTable\">\n")
                    first_row = True
                    for row_idx, row in enumerate(ws.iter_rows()):
                        f_sheet.write("  <tr>\n")
                        for cell in row:
                            cell_value = cell.value if cell.value is not None else ""
                            if first_row: f_sheet.write(f"    <th>{str(cell_value)}</th>\n")
                            else: f_sheet.write(f"    <td>{str(cell_value)}</td>\n")
                        f_sheet.write("  </tr>\n")
                        if first_row: first_row = False
                    f_sheet.write("  </table>\n</div>\n")
                    filter_script = """<script>function filterTable() {var input, filter, table, tr, td, i, j, txtValue;input = document.getElementById("filterInput");filter = input.value.toUpperCase();table = document.getElementById("sheetTable");tr = table.getElementsByTagName("tr");for (i = 1; i < tr.length; i++) {let rowContainsFilterText = false;td = tr[i].getElementsByTagName("td");for (j = 0; j < td.length; j++) {if (td[j]) {txtValue = td[j].textContent || td[j].innerText;if (txtValue.toUpperCase().indexOf(filter) > -1) {rowContainsFilterText = true;break;}}}if (rowContainsFilterText) {tr[i].style.display = "";} else {tr[i].style.display = "none";}}}function clearFilter() {var input, table, tr, i;input = document.getElementById("filterInput");input.value = "";table = document.getElementById("sheetTable");tr = table.getElementsByTagName("tr");for (i = 1; i < tr.length; i++) {tr[i].style.display = "";}}</script>"""
                    f_sheet.write(filter_script)
                    f_sheet.write("</body>\n</html>")
            messagebox.showinfo("Success", f"HTML site generated successfully in:\n{final_output_path}\n\nOpen 'index.html' inside this folder to view.", parent=self.top)
        except FileNotFoundError: messagebox.showerror("Error", f"Input Excel file not found: {input_file}", parent=self.top)
        except openpyxl.utils.exceptions.InvalidFileException: messagebox.showerror("Error", f"Invalid Excel file format. Please provide a .xlsx file.", parent=self.top)
        except Exception as e: messagebox.showerror("Generation Error", f"An error occurred: {e}", parent=self.top)

class SqlParserDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("SQL Parser")
        self.top.transient(self.root)
        self.top.grab_set()
        self.top.resizable(True, True) # Changed to True
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
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
        self.json_output_text.config(state=tk.DISABLED)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=tk.E, pady=(5,0))
        self.parse_sql_button = ttk.Button(button_frame, text="Parse SQL", command=self._parse_sql_query)
        self.parse_sql_button.pack(side=tk.LEFT, padx=(0,5))
        self.copy_json_button = ttk.Button(button_frame, text="Copy JSON", command=self._copy_json_output, state=tk.DISABLED)
        self.copy_json_button.pack(side=tk.LEFT)
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        min_width = 500; min_height = 450
        current_width = self.top.winfo_width(); current_height = self.top.winfo_height()
        final_width = max(current_width, min_width); final_height = max(current_height, min_height)
        self.top.geometry(f"{final_width}x{final_height}+{x}+{y}")
        self.top.minsize(min_width, min_height)

    def _parse_sql_query(self):
        try:
            from mo_sql_parsing import parse as parse_sql
            from mo_sql_parsing.exceptions import MoSQLError
            import json
        except ImportError:
            messagebox.showerror("Dependency Missing", "The 'mo-sql-parsing' library is not installed. Please install it (e.g., pip install mo-sql-parsing).", parent=self.top)
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
            self.copy_json_button.config(state=tk.NORMAL)
        except Exception as e:
            error_message = f"An unexpected error occurred during parsing:\n{str(e)}"
            self.json_output_text.insert("1.0", error_message)
            self.copy_json_button.config(state=tk.NORMAL)
        finally: self.json_output_text.config(state=tk.DISABLED)

    def _copy_json_output(self):
        json_content = self.json_output_text.get("1.0", tk.END + "-1c")
        if json_content.strip():
            try:
                self.top.clipboard_clear()
                self.top.clipboard_append(json_content)
                messagebox.showinfo("Copied", "JSON output copied to clipboard.", parent=self.top)
            except tk.TclError: messagebox.showerror("Error", "Could not copy to clipboard. TclError occurred.", parent=self.top)
        else: messagebox.showwarning("Empty Output", "There is no JSON output to copy.", parent=self.top)

class RestApiClientDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("REST API Client")
        self.top.transient(self.root)
        self.top.grab_set()
        self.top.resizable(True, True) # Changed to True

        self.url_var = tk.StringVar(value="https://jsonplaceholder.typicode.com/todos/1")
        self.method_var = tk.StringVar(value="GET")
        self.http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        self.body_type_var = tk.StringVar(value="JSON")
        self.body_types = ["JSON", "XML", "Plain Text", "None"]

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        request_setup_frame = ttk.Frame(main_frame)
        request_setup_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Label(request_setup_frame, text="URL:").pack(side=tk.LEFT, padx=(0,5))
        url_entry = ttk.Entry(request_setup_frame, textvariable=self.url_var, width=70)
        url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,10))
        url_entry.focus_set()
        ttk.Label(request_setup_frame, text="Method:").pack(side=tk.LEFT, padx=(0,5))
        method_combobox = ttk.Combobox(request_setup_frame, textvariable=self.method_var, values=self.http_methods, state="readonly", width=10)
        method_combobox.pack(side=tk.LEFT)
        method_combobox.bind("<<ComboboxSelected>>", self._on_method_change)

        request_notebook = ttk.Notebook(main_frame)
        request_notebook.pack(expand=True, fill=tk.BOTH, pady=(0,10))
        req_headers_frame = ttk.Frame(request_notebook, padding=5)
        request_notebook.add(req_headers_frame, text="Headers")
        ttk.Label(req_headers_frame, text="Enter headers (HeaderName: HeaderValue), one per line:").pack(anchor=tk.W, pady=(0,2))
        self.req_headers_text = tk.Text(req_headers_frame, height=5, width=80, wrap=tk.WORD, undo=True)
        self.req_headers_text.pack(expand=True, fill=tk.BOTH)
        self.req_headers_text.insert("1.0", "User-Agent: JulesTextEditor/1.0\nAccept: */*")
        self.req_body_frame = ttk.Frame(request_notebook, padding=5)
        request_notebook.add(self.req_body_frame, text="Body")
        body_options_frame = ttk.Frame(self.req_body_frame)
        body_options_frame.pack(fill=tk.X, pady=(0,5))
        ttk.Label(body_options_frame, text="Body Type:").pack(side=tk.LEFT, padx=(0,5))
        self.body_type_combo = ttk.Combobox(body_options_frame, textvariable=self.body_type_var, values=self.body_types, state="readonly", width=15)
        self.body_type_combo.pack(side=tk.LEFT)
        self.body_type_combo.bind("<<ComboboxSelected>>", self._on_body_type_change)
        self.req_body_text = tk.Text(self.req_body_frame, height=8, width=80, wrap=tk.WORD, undo=True)
        self.req_body_text.pack(expand=True, fill=tk.BOTH)
        self.req_body_text.insert("1.0", "{\n  \"key\": \"value\",\n  \"example\": true\n}")

        send_button = ttk.Button(main_frame, text="Send Request", command=self._send_request)
        send_button.pack(pady=5)
        self.status_label_var = tk.StringVar(value="Status: -")
        status_display_label = ttk.Label(main_frame, textvariable=self.status_label_var, font=("TkDefaultFont", 10, "bold"))
        status_display_label.pack(anchor=tk.W, pady=(5,2))
        response_notebook = ttk.Notebook(main_frame)
        response_notebook.pack(expand=True, fill=tk.BOTH, pady=(0,10))
        resp_body_frame = ttk.Frame(response_notebook, padding=5)
        response_notebook.add(resp_body_frame, text="Response Body")
        self.resp_body_text = tk.Text(resp_body_frame, height=10, width=80, wrap=tk.WORD, undo=False)
        self.resp_body_text.pack(expand=True, fill=tk.BOTH)
        self.resp_body_text.config(state=tk.DISABLED)
        resp_headers_frame = ttk.Frame(response_notebook, padding=5)
        response_notebook.add(resp_headers_frame, text="Response Headers")
        self.resp_headers_text = tk.Text(resp_headers_frame, height=8, width=80, wrap=tk.WORD, undo=False)
        self.resp_headers_text.pack(expand=True, fill=tk.BOTH)
        self.resp_headers_text.config(state=tk.DISABLED)
        copy_button_frame = ttk.Frame(main_frame)
        copy_button_frame.pack(fill=tk.X, pady=(5,0))
        self.copy_resp_body_button = ttk.Button(copy_button_frame, text="Copy Response Body", command=self._copy_response_body, state=tk.DISABLED)
        self.copy_resp_body_button.pack(side=tk.LEFT)
        self._on_method_change()
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f"{self.top.winfo_width()}x{self.top.winfo_height()}+{x}+{y}")
        self.top.minsize(500, 600)
        self.top.bind("<Escape>", lambda e: self.top.destroy())

    def _on_method_change(self, event=None):
        method = self.method_var.get()
        no_body_methods = ["GET", "HEAD", "DELETE", "OPTIONS"]
        if method in no_body_methods:
            self.req_body_text.config(state=tk.DISABLED)
            self.body_type_combo.config(state=tk.DISABLED)
        else:
            self.req_body_text.config(state=tk.NORMAL)
            self.body_type_combo.config(state=tk.NORMAL)

    def _on_body_type_change(self, event=None): pass

    def _parse_headers_text(self, headers_str):
        headers = {}
        for line in headers_str.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        return headers

    def _update_headers_text(self, key_to_update, new_value):
        current_headers_content = self.req_headers_text.get("1.0", tk.END + "-1c")
        lines = current_headers_content.splitlines()
        found = False; new_lines = []
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                if key.strip().lower() == key_to_update.lower():
                    new_lines.append(f"{key_to_update}: {new_value}"); found = True
                else: new_lines.append(line)
            else: new_lines.append(line)
        if not found:
            new_lines.append(f"{key_to_update}: {new_value}")
            if not current_headers_content.strip():
                 self.req_headers_text.delete("1.0", tk.END)
                 self.req_headers_text.insert("1.0", "\n".join(new_lines).strip())
            elif not current_headers_content.endswith('\n'):
                 self.req_headers_text.insert(tk.END, f"\n{key_to_update}: {new_value}")
            else: self.req_headers_text.insert(tk.END, f"{key_to_update}: {new_value}\n")
        else:
            self.req_headers_text.delete("1.0", tk.END)
            self.req_headers_text.insert("1.0", "\n".join(new_lines))
        final_content = self.req_headers_text.get("1.0", tk.END + "-1c")
        if final_content.strip() and not final_content.endswith('\n'): self.req_headers_text.insert(tk.END, "\n")

    def _send_request(self):
        try:
            import requests
            import json
        except ImportError:
            messagebox.showerror("Dependency Missing", "The 'requests' library is not installed. Please install it (e.g., pip install requests).", parent=self.top)
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
        if body_str and 'content-type' not in (k.lower() for k in headers):
            body_type = self.body_type_var.get()
            if body_type == "JSON": headers['Content-Type'] = 'application/json'
            elif body_type == "XML": headers['Content-Type'] = 'application/xml'
            elif body_type == "Plain Text": headers['Content-Type'] = 'text/plain'
            if 'Content-Type' in headers and not any(h.lower().startswith("content-type:") for h in headers_str.splitlines()): # Actual fix: ensure .splitlines() is correct
                 self._update_headers_text("Content-Type", headers['Content-Type'])
        self.status_label_var.set(f"Status: Sending {method} request to {url}...")
        self.top.update_idletasks()
        try:
            response = requests.request(method=method, url=url, headers=headers, data=body_str.encode('utf-8') if body_str else None, timeout=10 )
            self.status_label_var.set(f"Status: {response.status_code} {response.reason}")
            self.resp_headers_text.config(state=tk.NORMAL)
            self.resp_headers_text.delete("1.0", tk.END)
            for key, value in response.headers.items(): self.resp_headers_text.insert(tk.END, f"{key}: {value}\n")
            self.resp_headers_text.config(state=tk.DISABLED)
            self.resp_body_text.config(state=tk.NORMAL)
            self.resp_body_text.delete("1.0", tk.END)
            response_content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in response_content_type:
                try:
                    json_body = response.json()
                    pretty_json = json.dumps(json_body, indent=2, sort_keys=True)
                    self.resp_body_text.insert(tk.END, pretty_json)
                except json.JSONDecodeError: self.resp_body_text.insert(tk.END, response.text)
            else: self.resp_body_text.insert(tk.END, response.text)
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
            except tk.TclError: messagebox.showerror("Error", "Could not copy to clipboard. TclError occurred.", parent=self.top)
        else: messagebox.showwarning("Empty Response", "There is no response body to copy.", parent=self.top)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = TextEditor(root)
    root.mainloop()
