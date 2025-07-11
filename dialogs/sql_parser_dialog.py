import tkinter as tk
from tkinter import ttk, messagebox
import json # For formatting output

try:
    from mo_sql_parsing import parse as parse_sql
    from mo_sql_parsing.exceptions import MoSQLError
except ImportError:
    parse_sql = None # Will be checked in _parse_sql_query
    MoSQLError = None # Will be checked in _parse_sql_query


class SqlParserDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("SQL Parser")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(True, True) # Allow resizing

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.grid_rowconfigure(1, weight=1) # SQL input text area
        main_frame.grid_rowconfigure(3, weight=1) # JSON output text area
        main_frame.grid_columnconfigure(0, weight=1) # Make column expandable

        # SQL Input Area
        ttk.Label(main_frame, text="SQL Query:").grid(row=0, column=0, sticky=tk.W, pady=(0,2))
        sql_input_frame = ttk.Frame(main_frame) # Frame for text and scrollbar
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
        json_output_frame = ttk.Frame(main_frame) # Frame for text and scrollbar
        json_output_frame.grid(row=3, column=0, sticky="nsew", pady=(0,10))
        json_output_frame.rowconfigure(0, weight=1)
        json_output_frame.columnconfigure(0, weight=1)
        self.json_output_text = tk.Text(json_output_frame, height=12, width=70, wrap=tk.WORD, undo=False) # Output, so undo=False
        json_output_scrollbar = ttk.Scrollbar(json_output_frame, orient=tk.VERTICAL, command=self.json_output_text.yview)
        self.json_output_text.config(yscrollcommand=json_output_scrollbar.set)
        self.json_output_text.grid(row=0, column=0, sticky="nsew")
        json_output_scrollbar.grid(row=0, column=1, sticky="ns")
        self.json_output_text.config(state=tk.DISABLED) # Read-only

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=tk.E, pady=(5,0))
        self.parse_sql_button = ttk.Button(button_frame, text="Parse SQL", command=self._parse_sql_query)
        self.parse_sql_button.pack(side=tk.LEFT, padx=(0,5))
        self.copy_json_button = ttk.Button(button_frame, text="Copy JSON", command=self._copy_json_output, state=tk.DISABLED)
        self.copy_json_button.pack(side=tk.LEFT)

        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)

        min_width = 500 # Define minimums for better usability
        min_height = 450
        current_width = self.top.winfo_width()
        current_height = self.top.winfo_height()
        final_width = max(current_width, min_width)
        final_height = max(current_height, min_height)

        self.top.geometry(f"{final_width}x{final_height}+{x}+{y}")
        self.top.minsize(min_width, min_height)


    def _parse_sql_query(self):
        if parse_sql is None or MoSQLError is None:
            messagebox.showerror("Dependency Missing", "The 'mo-sql-parsing' library is not installed. Please install it (e.g., pip install mo-sql-parsing).", parent=self.top)
            self.json_output_text.config(state=tk.NORMAL)
            self.json_output_text.delete("1.0", tk.END)
            self.json_output_text.insert("1.0", "Error: 'mo-sql-parsing' library not found.")
            self.json_output_text.config(state=tk.DISABLED)
            self.copy_json_button.config(state=tk.DISABLED)
            return

        sql_query = self.sql_input_text.get("1.0", tk.END + "-1c").strip()
        self.json_output_text.config(state=tk.NORMAL) # Enable for editing
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
            self.copy_json_button.config(state=tk.NORMAL) # Enable copy if successful
        except MoSQLError as e: # Specific error from the parser
            error_message = f"Error parsing SQL (MoSQLError):\n{str(e)}"
            self.json_output_text.insert("1.0", error_message)
            self.copy_json_button.config(state=tk.NORMAL) # Allow copying error message
        except Exception as e: # Catch any other unexpected errors
            error_message = f"An unexpected error occurred during parsing:\n{str(e)}"
            self.json_output_text.insert("1.0", error_message)
            self.copy_json_button.config(state=tk.NORMAL) # Allow copying error message
        finally:
            self.json_output_text.config(state=tk.DISABLED) # Disable editing again

    def _copy_json_output(self):
        json_content = self.json_output_text.get("1.0", tk.END + "-1c")
        if json_content.strip(): # Check if there's anything to copy
            try:
                self.top.clipboard_clear()
                self.top.clipboard_append(json_content)
                messagebox.showinfo("Copied", "JSON output copied to clipboard.", parent=self.top)
            except tk.TclError: # Handle potential clipboard errors
                messagebox.showerror("Error", "Could not copy to clipboard. TclError occurred.", parent=self.top)
        else:
            messagebox.showwarning("Empty Output", "There is no JSON output to copy.", parent=self.top)
