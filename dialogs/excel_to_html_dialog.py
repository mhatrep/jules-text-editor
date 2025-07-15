import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re

try:
    import openpyxl
except ImportError:
    openpyxl = None # Will be checked in _generate_html_site

class ExcelToHtmlDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("Excel to HTML Site Generator")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(False, False) # Dialog is not complex enough to need resizing

        self.input_excel_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.site_title_var = tk.StringVar(value="Excel Data Site") # Default site title

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

        # Site Title (Optional)
        ttk.Label(main_frame, text="Site Title (Optional):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        site_title_entry = ttk.Entry(main_frame, textvariable=self.site_title_var, width=50)
        site_title_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)


        # Generate Button
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=3, pady=15)
        self.generate_button = ttk.Button(action_frame, text="Generate HTML Site", command=self._generate_html_site)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(action_frame, text="Cancel", command=self._cancel_generation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        input_file_entry.focus_set() # Focus on the first input field
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        self.top.minsize(550, 220) # Set a minimum size for the dialog

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

    def _generate_html_site(self):
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
        site_title = self.site_title_var.get().strip() # Get and strip site title

        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Input Error", "Please select a valid Excel input file.", parent=self.top)
            self.generate_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return

        if not user_selected_output_dir: # If no output dir, use input file's dir
            base_output_dir = os.path.dirname(input_file)
            self.output_dir_var.set(base_output_dir) # Update for consistency
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
        if not sanitized_folder_name: # Handle cases where sanitization results in empty string
            sanitized_folder_name = "excel_site_output"

        final_output_path = os.path.join(base_output_dir, sanitized_folder_name)

        try:
            os.makedirs(final_output_path, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Output Error", f"Could not create output subfolder: {final_output_path}\nError: {e}", parent=self.top)
            self.generate_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return

        if openpyxl is None:
            messagebox.showerror("Dependency Missing", "The 'openpyxl' library is not installed. Please install it (e.g., pip install openpyxl).", parent=self.top)
            self.generate_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return

        basic_css = """<style>body {font-family: sans-serif;margin: 0;background-color: #f4f4f4;color: #333;display: flex;min-height: 100vh;}.sidebar {width: 220px;background-color: #333;color: #fff;padding: 15px;height: 100vh;position: fixed;overflow-y: auto;}.sidebar h2 {text-align: center;color: #fff;margin-top: 0;}.sidebar ul {list-style-type: none;padding: 0;}.sidebar ul li a {display: block;color: #fff;padding: 8px 10px;text-decoration: none;border-radius: 4px;}.sidebar ul li a:hover, .sidebar ul li a.active {background-color: #555;}.main-content {margin-left: 240px;padding: 20px;flex-grow: 1;background-color: #fff;}header {text-align: center;margin-bottom:20px;}table { border-collapse: collapse; width: 100%; margin-top: 20px; }th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }th { background-color: #f0f0f0; }tr:nth-child(even) { background-color: #f9f9f9; }tr:hover { background-color: #f1f1f1; }h1, h2 { color: #333; }a { color: #007bff; }a:hover { color: #0056b3; }#filterInput {padding: 8px;margin-bottom: 10px;border: 1px solid #ccc;border-radius: 4px;width: calc(100% - 120px);box-sizing: border-box;}button {padding: 8px 12px;background-color: #5cb85c;color: white;border: none;border-radius: 4px;cursor: pointer;margin-left: 5px;}button:hover {background-color: #4cae4c;}</style>"""

        def sanitize_filename(name):
            name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
            return name if name else "untitled_sheet"

        try:
            workbook = openpyxl.load_workbook(input_file, read_only=True)
            sheet_names = workbook.sheetnames
            generated_files_info = [] # To store info for index.html and navigation

            for sheet_name in sheet_names:
                if self.cancel_requested:
                    messagebox.showinfo("Cancelled", "Operation cancelled by user.", parent=self.top)
                    break
                ws = workbook[sheet_name]
                html_filename = sanitize_filename(sheet_name) + ".html"
                generated_files_info.append({
                    "name": sheet_name, # For display in navigation
                    "file": html_filename,
                    "original_name": sheet_name, # To access the sheet in workbook
                    "row_count": ws.max_row,
                    "col_count": ws.max_column
                })

            if not self.cancel_requested:
                generated_files_info.sort(key=lambda x: x["name"]) # Sort for consistent nav order

                # Create index.html (Overview page)
                index_html_path = os.path.join(final_output_path, "index.html")
                with open(index_html_path, "w", encoding="utf-8") as f_index:
                    f_index.write(f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n")
                    index_page_title = f"{site_title if site_title else excel_filename_no_ext} - Overview"
                    f_index.write(f"<title>{index_page_title}</title>\n{basic_css}\n</head>\n<body>\n")

                    # Sidebar for index.html
                    f_index.write("<div class=\"sidebar\">\n")
                    f_index.write(f"  <h2>{site_title if site_title else 'Navigation'}</h2>\n  <ul>\n")
                    f_index.write(f"    <li><a href=\"index.html\" class=\"active\">Home (Overview)</a></li>\n")
                    for sheet_info_nav in generated_files_info:
                        f_index.write(f"    <li><a href=\"{sheet_info_nav['file']}\">{sheet_info_nav['name']}</a></li>\n")
                    f_index.write("  </ul>\n</div>\n") # Close sidebar

                    # Main content for index.html
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
                    f_index.write("  </table>\n</div>\n</body>\n</html>") # Close main-content, body, html

                # Create individual HTML files for each sheet
                for current_sheet_info in generated_files_info:
                    if self.cancel_requested:
                        break
                    sheet_name = current_sheet_info["original_name"]
                    html_filename = current_sheet_info["file"]
                    sheet_html_path = os.path.join(final_output_path, html_filename)
                    ws = workbook[sheet_name]

                    with open(sheet_html_path, "w", encoding="utf-8") as f_sheet:
                        f_sheet.write(f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n")
                        page_specific_title = f"{sheet_name} - {site_title}" if site_title else sheet_name
                        f_sheet.write(f"<title>{page_specific_title}</title>\n{basic_css}\n</head>\n<body>\n")

                        # Sidebar for individual sheet pages
                        f_sheet.write("<div class=\"sidebar\">\n")
                        f_sheet.write(f"  <h2>{site_title if site_title else 'Navigation'}</h2>\n  <ul>\n")
                        f_sheet.write(f"    <li><a href=\"index.html\">Home (Overview)</a></li>\n")
                        for other_sheet_info in generated_files_info:
                            active_class = ' class="active"' if other_sheet_info["file"] == html_filename else ''
                            f_sheet.write(f"    <li><a href=\"{other_sheet_info['file']}\"{active_class}>{other_sheet_info['name']}</a></li>\n")
                        f_sheet.write("  </ul>\n</div>\n") # Close sidebar

                        # Main content for sheet page
                        f_sheet.write("<div class=\"main-content\">\n")
                        f_sheet.write(f"  <header><h1>{sheet_name}</h1></header>\n")
                        f_sheet.write("  <h2>Sheet Data:</h2>\n")
                        # Filter input
                        f_sheet.write("  <div>\n") # Filter controls container
                        f_sheet.write(f"    <input type=\"text\" id=\"filterInput\" onkeyup=\"filterTable()\" placeholder=\"Filter table content...\" title=\"Type in a name to filter the table\">\n")
                        f_sheet.write(f"    <button onclick=\"clearFilter()\">Clear Filter</button>\n")
                        f_sheet.write("  </div>\n")

                        f_sheet.write("  <table id=\"sheetTable\">\n") # Add ID for JS filtering
                        first_row = True
                        for row_idx, row in enumerate(ws.iter_rows()):
                            f_sheet.write("  <tr>\n")
                            for cell in row:
                                cell_value = cell.value if cell.value is not None else ""
                                if first_row: # Use <th> for header row
                                    f_sheet.write(f"    <th>{str(cell_value)}</th>\n")
                                else:
                                    f_sheet.write(f"    <td>{str(cell_value)}</td>\n")
                            f_sheet.write("  </tr>\n")
                            if first_row: first_row = False
                        f_sheet.write("  </table>\n</div>\n") # Close main-content

                        # JavaScript for filtering
                        filter_script = """<script>function filterTable() {var input, filter, table, tr, td, i, j, txtValue;input = document.getElementById("filterInput");filter = input.value.toUpperCase();table = document.getElementById("sheetTable");tr = table.getElementsByTagName("tr");for (i = 1; i < tr.length; i++) {let rowContainsFilterText = false;td = tr[i].getElementsByTagName("td");for (j = 0; j < td.length; j++) {if (td[j]) {txtValue = td[j].textContent || td[j].innerText;if (txtValue.toUpperCase().indexOf(filter) > -1) {rowContainsFilterText = true;break;}}}if (rowContainsFilterText) {tr[i].style.display = "";} else {tr[i].style.display = "none";}}}function clearFilter() {var input, table, tr, i;input = document.getElementById("filterInput");input.value = "";table = document.getElementById("sheetTable");tr = table.getElementsByTagName("tr");for (i = 1; i < tr.length; i++) {tr[i].style.display = "";}}</script>"""
                        f_sheet.write(filter_script)
                        f_sheet.write("</body>\n</html>") # Close body, html

                if not self.cancel_requested:
                    messagebox.showinfo("Success", f"HTML site generated successfully in:\n{final_output_path}\n\nOpen 'index.html' inside this folder to view.", parent=self.top)

        except FileNotFoundError:
            messagebox.showerror("Error", f"Input Excel file not found: {input_file}", parent=self.top)
        except openpyxl.utils.exceptions.InvalidFileException:
             messagebox.showerror("Error", f"Invalid Excel file format. Please provide a .xlsx file.", parent=self.top)
        except Exception as e:
            messagebox.showerror("Generation Error", f"An error occurred: {e}", parent=self.top)
        finally:
            self.generate_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
