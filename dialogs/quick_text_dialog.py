import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import quick_transformer # Assuming quick_transformer.py is in the same directory or accessible via PYTHONPATH

class QuickTextDialog:
    def __init__(self, parent, title="QuickText Transformer"):
        self.parent = parent # parent is the TextEditor instance
        self.top = tk.Toplevel(parent.root)
        self.top.title(title)
        self.top.transient(parent.root)
        self.top.grab_set() # Make it modal

        self.initial_input_data = ""
        current_tab = parent.get_current_tab()
        if current_tab:
            try:
                selected_text = current_tab.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected_text:
                    self.initial_input_data = selected_text
            except tk.TclError: # No selection
                pass

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Input Data Frame
        input_frame = ttk.LabelFrame(main_frame, text="Input Data", padding=5)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.input_text = tk.Text(input_frame, height=10, width=80, wrap=tk.WORD, undo=True)
        self.input_text_scrollbar = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.input_text.yview)
        self.input_text.config(yscrollcommand=self.input_text_scrollbar.set)
        self.input_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if self.initial_input_data:
            self.input_text.insert("1.0", self.initial_input_data)

        # Controls (Delimiter, Live Preview)
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
            # Add more default patterns here if desired
        }
        self.pattern_history_for_dialog = list(self.saved_patterns.keys()) # Used for populating the load dialog

        # Pattern Frame
        pattern_frame = ttk.LabelFrame(main_frame, text="Pattern (e.g., Name: $1 $2. ID: $lineNumber. Use \\$ for literal $)", padding=5)
        pattern_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.pattern_text = tk.Text(pattern_frame, height=4, width=80, wrap=tk.WORD, undo=True)
        self.pattern_text_scrollbar = ttk.Scrollbar(pattern_frame, orient=tk.VERTICAL, command=self.pattern_text.yview)
        self.pattern_text.config(yscrollcommand=self.pattern_text_scrollbar.set)

        pattern_text_and_buttons_frame = ttk.Frame(pattern_frame) # New frame to hold text and scrollbar together
        pattern_text_and_buttons_frame.pack(fill=tk.BOTH, expand=True)

        self.pattern_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, in_=pattern_text_and_buttons_frame) # pack scrollbar inside this new frame
        self.pattern_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, in_=pattern_text_and_buttons_frame) # pack text area inside

        initial_pattern_name = self.pattern_history_for_dialog[0] if self.pattern_history_for_dialog else "Field1: $1, Field2: $2, Line: $lineNumber"
        initial_pattern_value = self.saved_patterns.get(initial_pattern_name, initial_pattern_name)
        self.pattern_text.insert("1.0", initial_pattern_value)
        self.pattern_text.config(state=tk.NORMAL) # Ensure it's editable

        pattern_buttons_frame = ttk.Frame(pattern_frame) # Buttons below the text area
        pattern_buttons_frame.pack(fill=tk.X, pady=(5,0))
        self.save_pattern_btn = ttk.Button(pattern_buttons_frame, text="Save Current Pattern", command=self._save_current_pattern)
        self.save_pattern_btn.pack(side=tk.LEFT, padx=(0,5))
        self.load_pattern_btn = ttk.Button(pattern_buttons_frame, text="Load Saved Pattern...", command=self._load_saved_pattern)
        self.load_pattern_btn.pack(side=tk.LEFT)


        # Output Frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.output_text = tk.Text(output_frame, height=10, width=80, wrap=tk.WORD, undo=True)
        self.output_text_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.config(yscrollcommand=self.output_text_scrollbar.set)
        self.output_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED) # Output is not directly editable

        # Action Buttons (Transform, Copy, Close)
        action_buttons_frame = ttk.Frame(main_frame)
        action_buttons_frame.pack(fill=tk.X, pady=(10,0))
        self.transform_btn = ttk.Button(action_buttons_frame, text="Transform", command=self._run_transform)
        self.transform_btn.pack(side=tk.LEFT, padx=5)
        self.copy_output_btn = ttk.Button(action_buttons_frame, text="Copy Output", command=self._copy_output)
        self.copy_output_btn.pack(side=tk.LEFT, padx=5)
        self.copy_output_btn.config(state=tk.DISABLED) # Enabled when there's output
        self.close_btn = ttk.Button(action_buttons_frame, text="Close", command=self.top.destroy)
        self.close_btn.pack(side=tk.RIGHT, padx=5)

        # Bindings for live preview
        self.input_text.bind("<<Modified>>", self._debounced_maybe_live_transform)
        self.pattern_text.bind("<<Modified>>", self._debounced_maybe_live_transform)
        self.delimiter_var.trace_add("write", self._debounced_maybe_live_transform_trace)

        self.input_text.focus_set()
        self.top.update_idletasks() # Ensure window dimensions are calculated
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
        except ValueError as e: # Specific error from quick_transformer
            messagebox.showerror("Transformation Error", str(e), parent=self.top)
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, f"Error: {str(e)}")
            self.output_text.config(state=tk.DISABLED)
            self.copy_output_btn.config(state=tk.DISABLED)
        except Exception as e: # Catch any other unexpected errors
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
        if self.live_preview_var.get():
            self._run_transform()

    def _debounced_maybe_live_transform(self, event=None):
        # This is called when input_text or pattern_text is modified
        widget = event.widget
        try: # Clear the modified flag to prevent re-triggering
            if widget.edit_modified():
                widget.edit_modified(False)
        except AttributeError: # Might be called by trace, which doesn't have edit_modified
            pass

        if self.live_preview_var.get():
            if self._debounce_timer_id:
                self.top.after_cancel(self._debounce_timer_id)
            self._debounce_timer_id = self.top.after(500, self._run_transform) # 500ms delay

    def _debounced_maybe_live_transform_trace(self, *args):
        # This is called when delimiter_var changes via trace
        if self.live_preview_var.get():
            if self._debounce_timer_id:
                self.top.after_cancel(self._debounce_timer_id)
            self._debounce_timer_id = self.top.after(500, self._run_transform)


    def _save_current_pattern(self):
        current_pattern_text = self.pattern_text.get("1.0", tk.END + "-1c").strip()
        if not current_pattern_text:
            messagebox.showwarning("Empty Pattern", "Cannot save an empty pattern.", parent=self.top)
            return

        pattern_name = simpledialog.askstring("Save Pattern", "Enter a name for this pattern:", parent=self.top)
        if pattern_name: # User entered a name and clicked OK
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

    def _load_saved_pattern(self):
        if not self.saved_patterns:
            messagebox.showinfo("No Saved Patterns", "There are no patterns saved in this session.", parent=self.top)
            return

        load_dialog = tk.Toplevel(self.top)
        load_dialog.title("Load Pattern")
        load_dialog.transient(self.top)
        load_dialog.grab_set()
        load_dialog.geometry("300x250") # Adjust size as needed

        ttk.Label(load_dialog, text="Select a pattern to load:").pack(pady=5)

        patterns_listbox = tk.Listbox(load_dialog, selectmode=tk.SINGLE, exportselection=False)
        for pattern_name_item in self.pattern_history_for_dialog: # Use the history for display order
            patterns_listbox.insert(tk.END, pattern_name_item)
        patterns_listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        if self.pattern_history_for_dialog: # Pre-select the first item if list is not empty
            patterns_listbox.select_set(0)
            patterns_listbox.activate(0)

        patterns_listbox.focus_set()

        result_pattern_value = None # To store the selection

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

        patterns_listbox.bind("<Double-1>", lambda e: on_load_select())
        load_dialog.bind("<Return>", lambda e: on_load_select())
        load_dialog.bind("<Escape>", lambda e: on_load_cancel())

        load_dialog.wait_window() # Wait for the dialog to be closed
