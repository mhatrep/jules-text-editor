import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import threading

class ExcelToCsvDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master.root)
        self.title("Excel to CSV Converter")
        self.geometry("500x200")
        self.master_app = master

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Input File ---
        ttk.Label(main_frame, text="Excel File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.excel_file_var = tk.StringVar()
        self.excel_file_entry = ttk.Entry(main_frame, textvariable=self.excel_file_var, width=50)
        self.excel_file_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(main_frame, text="Browse...", command=self._browse_excel_file).grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)

        # --- Output Directory ---
        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(main_frame, text="Browse...", command=self._browse_output_dir).grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)

        # --- Conversion Control & Status ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, columnspan=3, pady=10)

        self.convert_button = ttk.Button(action_frame, text="Convert", command=self._start_conversion)
        self.convert_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(action_frame, text="Cancel", command=self._cancel_conversion, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.status_label_var = tk.StringVar(value="Status: Idle")
        status_label = ttk.Label(action_frame, textvariable=self.status_label_var)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)

    def _browse_excel_file(self):
        filepath = filedialog.askopenfilename(
            parent=self,
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if filepath:
            self.excel_file_var.set(filepath)

    def _browse_output_dir(self):
        directory = filedialog.askdirectory(parent=self, title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)

    def _start_conversion(self):
        excel_file = self.excel_file_var.get()
        output_dir = self.output_dir_var.get()

        if not excel_file or not os.path.isfile(excel_file):
            messagebox.showerror("Error", "Please select a valid Excel file.", parent=self)
            return

        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Please select a valid output directory.", parent=self)
            return

        self.convert_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.status_label_var.set("Status: Starting conversion...")

        self.conversion_thread = threading.Thread(target=self._conversion_worker, args=(excel_file, output_dir), daemon=True)
        self.conversion_thread.start()

    def _cancel_conversion(self):
        if self.conversion_thread and self.conversion_thread.is_alive():
            self.status_label_var.set("Status: Cancellation requested...")
            self.cancel_requested = True

    def _conversion_worker(self, excel_file, output_dir):
        self.cancel_requested = False
        try:
            xls = pd.ExcelFile(excel_file)
            for sheet_name in xls.sheet_names:
                if self.cancel_requested:
                    self.status_label_var.set("Status: Conversion cancelled.")
                    break
                df = pd.read_excel(xls, sheet_name)
                csv_filename = f"{os.path.splitext(os.path.basename(excel_file))[0]}_{sheet_name}.csv"
                csv_filepath = os.path.join(output_dir, csv_filename)
                df.to_csv(csv_filepath, index=False)
                self.status_label_var.set(f"Status: Converted {sheet_name}...")
            if not self.cancel_requested:
                self.status_label_var.set(f"Status: Conversion complete! {len(xls.sheet_names)} sheet(s) converted.")
        except Exception as e:
            self.status_label_var.set(f"Status: Error - {e}")

        self.convert_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

    def on_close(self, event=None):
        self.destroy()
