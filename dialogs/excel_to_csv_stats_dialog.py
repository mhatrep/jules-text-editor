import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import subprocess # For csvstat
import csv # For writing CSVs

try:
    import openpyxl
except ImportError:
    openpyxl = None # Handled in _generate_files

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

        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, columnspan=3, pady=15)
        self.generate_button = ttk.Button(action_frame, text="Generate CSVs & Stats", command=self._generate_files)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(action_frame, text="Cancel", command=self._cancel_generation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        input_file_entry.focus_set()
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        self.top.minsize(550, 180)

    def _browse_input_file(self):
        filepath = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel Files", "*.xlsx")], parent=self.top)
        if filepath:
            self.input_excel_file_var.set(filepath)

    def _browse_output_dir(self):
        dirpath = filedialog.askdirectory(title="Select Output Directory", parent=self.top)
        if dirpath:
            self.output_dir_var.set(dirpath)

    def _generate_files(self):
        self.generate_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.cancel_requested = False

        self.generation_thread = threading.Thread(target=self._generation_worker, daemon=True)
        self.generation_thread.start()

    def _cancel_generation(self):
        if self.generation_thread and self.generation_thread.is_alive():
            self.cancel_requested = True

    def _generation_worker(self):
        input_file = self.input_excel_file_var.get()
        user_selected_output_dir = self.output_dir_var.get()

        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Input Error", "Please select a valid Excel input file.", parent=self.top)
            self.generate_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return

        if not user_selected_output_dir:
            if messagebox.askyesno("Output Directory", "No output directory selected. Use the input file's directory as the base for output?", parent=self.top):
                base_output_dir = os.path.dirname(input_file)
                self.output_dir_var.set(base_output_dir) # Update var for consistency
            else:
                self.generate_button.config(state=tk.NORMAL)
                self.cancel_button.config(state=tk.DISABLED)
                return # User cancelled
        else:
            base_output_dir = user_selected_output_dir
            if not os.path.isdir(base_output_dir):
                messagebox.showerror("Input Error", "The selected output directory is not valid.", parent=self.top)
                self.generate_button.config(state=tk.NORMAL)
                self.cancel_button.config(state=tk.DISABLED)
                return

        excel_filename_no_ext = os.path.splitext(os.path.basename(input_file))[0]
        # Sanitize folder name from Excel filename
        sanitized_folder_name = re.sub(r'[^\w\s-]', '', excel_filename_no_ext).strip().replace(' ', '_')
        if not sanitized_folder_name: # Handle empty string after sanitization
            sanitized_folder_name = "excel_csv_stats_output"

        final_output_subfolder = os.path.join(base_output_dir, f"{sanitized_folder_name}_csv_stats")

        try:
            os.makedirs(final_output_subfolder, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Output Error", f"Could not create output subfolder: {final_output_subfolder}\nError: {e}", parent=self.top)
            self.generate_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return

        if openpyxl is None:
            messagebox.showerror("Dependency Missing", "The 'openpyxl' library is not installed. Please install it (e.g., pip install openpyxl).", parent=self.top)
            self.generate_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return

        try:
            workbook = openpyxl.load_workbook(input_file, read_only=True)
            sheet_names = workbook.sheetnames
            generated_count = 0
            errors_occurred = []

            for sheet_name in sheet_names:
                if self.cancel_requested:
                    messagebox.showinfo("Cancelled", "Operation cancelled by user.", parent=self.top)
                    break
                ws = workbook[sheet_name]
                # Sanitize sheet name for filename
                sane_sheet_filename_part = re.sub(r'[^\w\s-]', '', sheet_name).strip().replace(' ', '_')
                if not sane_sheet_filename_part: # Handle empty string after sanitization
                    sane_sheet_filename_part = f"sheet_{generated_count + 1}" # Use a generic name

                csv_filename = f"{sane_sheet_filename_part}.csv"
                csv_filepath = os.path.join(final_output_subfolder, csv_filename)
                stats_txt_filename = f"{csv_filename}.txt" # Stats filename based on CSV filename
                stats_txt_filepath = os.path.join(final_output_subfolder, stats_txt_filename)

                try:
                    # Write CSV
                    with open(csv_filepath, 'w', newline='', encoding='utf-8') as f_csv:
                        writer = csv.writer(f_csv)
                        for row in ws.iter_rows():
                            writer.writerow([cell.value for cell in row])

                    # Generate stats using csvstat
                    try:
                        # Use subprocess.run for better control and error handling
                        process_result = subprocess.run(
                            ['csvstat', csv_filepath],
                            capture_output=True, text=True, check=False, encoding='utf-8' # check=False to handle non-zero exit codes manually
                        )
                        if process_result.returncode == 0:
                            with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt:
                                f_txt.write(process_result.stdout)
                            generated_count += 1
                        else:
                            error_detail = f"Error running csvstat on {csv_filename}:\n{process_result.stderr}"
                            if process_result.stdout: # Include stdout if any, might contain useful info
                                error_detail += f"\nStdout:\n{process_result.stdout}"
                            with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt: # Write error to the stats file
                                f_txt.write(error_detail)
                            errors_occurred.append(error_detail)
                    except FileNotFoundError:
                        # csvstat command not found
                        error_msg = "Error: 'csvstat' command not found. Please ensure csvkit is installed and 'csvstat' is in your system's PATH."
                        messagebox.showerror("csvstat Error", error_msg, parent=self.top)
                        with open(stats_txt_filepath, 'w', encoding='utf-8') as f_txt: # Write error to stats file
                            f_txt.write(error_msg)
                        errors_occurred.append(f"csvstat not found for {csv_filename}.")
                        # Optionally break or continue based on desired behavior if csvstat is critical
                except Exception as e_file:
                    errors_occurred.append(f"Failed to process sheet '{sheet_name}': {e_file}")

            if errors_occurred:
                error_summary = "\n\n".join(errors_occurred)
                messagebox.showwarning("Processing Issues", f"{generated_count} sheet(s) processed with stats. Some errors occurred:\n\n{error_summary}\n\nCheck files in {final_output_subfolder}", parent=self.top)
            elif generated_count > 0 and not self.cancel_requested:
                messagebox.showinfo("Success", f"Successfully generated {generated_count} CSV file(s) and their statistics in:\n{final_output_subfolder}", parent=self.top)
            elif not self.cancel_requested:
                messagebox.showinfo("No Data", "No sheets were processed or found in the Excel file.", parent=self.top)

        except FileNotFoundError:
            messagebox.showerror("Error", f"Input Excel file not found: {input_file}", parent=self.top)
        except openpyxl.utils.exceptions.InvalidFileException: # More specific openpyxl error
            messagebox.showerror("Error", "Invalid Excel file format. Please provide a .xlsx file.", parent=self.top)
        except Exception as e:
            messagebox.showerror("Generation Error", f"An unexpected error occurred: {e}", parent=self.top)
        finally:
            self.generate_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
