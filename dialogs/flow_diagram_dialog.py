import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess

try:
    import graphviz
except ImportError:
    graphviz = None

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
            if output_format == 'gv' and not saved_file_actual_path.endswith('.gv'): # if DOT output, render() might not add .gv if filename already has it or similar
                saved_file_actual_path = base_filepath
            elif not os.path.exists(saved_file_actual_path): # Double check if render added the extension or not
                 if os.path.exists(base_filepath) and output_format == 'gv': # For DOT output, sometimes it's just the base_filepath
                      saved_file_actual_path = base_filepath
                 else:
                      print(f"Warning: Expected file {saved_file_actual_path} not found, trying {base_filepath}")
                      if os.path.exists(base_filepath): # Fallback if extension was not added by render
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
        dot.attr(splines='true', rankdir='TB') # Changed rankdir to TB (Top to Bottom)
        dot.attr('node', shape='plaintext', fontname='Helvetica', fontsize='11', fontcolor='black', style='filled', fillcolor='#e9e9e9', width='1.5') # Standardized node style
        dot.attr('edge', arrowhead='normal', arrowtail='dot', color='#20B2AA', style='solid') # Standardized edge style
        dot.attr(labelloc='t', labeljust='c', fontcolor='#20B2AA', fontname='Courier New Bold', fontsize='20')
        dot.attr(label=label) # Set diagram title
        steps = set()
        edges_to_add = []
        for sequence in sequences:
            sequence_steps = [step.strip() for step in sequence.split('->') if step.strip()]
            if not sequence_steps: continue
            for step in sequence_steps: steps.add(step)
            for i in range(len(sequence_steps) - 1):
                edges_to_add.append((sequence_steps[i], sequence_steps[i+1]))
        for step in sorted(list(steps)): # Ensure nodes are created consistently
            dot.node(step, label=f'► {step}') # Add a small arrow/icon for visual cue
        for u, v in edges_to_add: dot.edge(u, v)
        return dot

    def _on_dot_syntax_toggle(self):
        if self.dot_syntax_var.get():
            self.title_entry_widget.config(state=tk.DISABLED)
            self.title_var.set("[Title defined in DOT script]")
            self.input_frame_widget.config(text="DOT Language Script")
        else:
            self.title_entry_widget.config(state=tk.NORMAL)
            if self.title_var.get() == "[Title defined in DOT script]": # Restore default only if it was the placeholder
                 self.title_var.set("[Flow Diagram]")
            self.input_frame_widget.config(text="Flow Sequences (e.g., Step A->Step B->Step C, one per line)")
