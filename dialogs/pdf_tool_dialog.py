import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import os # Added for os.path operations

# Attempt to import fitz (PyMuPDF), will be checked before use in specific functions
try:
    import fitz  # PyMuPDF
except ImportError: # Specifically for when the package isn't found
    fitz = None
except RuntimeError as e: # For issues like the 'static/' directory not found
    fitz = None
    print(f"RuntimeError during PyMuPDF (fitz) import: {e}. PDF features will be disabled.")
except Exception as e: # Catch any other unexpected import-time errors
    fitz = None
    print(f"Unexpected error during PyMuPDF (fitz) import: {e}. PDF features will be disabled.")

# Attempt to import Pillow, will be checked before use
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

class PdfToolDialog(tk.Toplevel):
    def __init__(self, parent_editor):
        super().__init__(parent_editor.root)
        self.parent_editor = parent_editor
        self.title("PDF Tools")
        self.transient(parent_editor.root) # Keep on top of parent
        # self.grab_set() # Make modal if strictly necessary, for now allowing interaction with editor
        self.geometry("750x600") # Initial size, can be adjusted
        self.resizable(True, True)
        self.minsize(600, 450)

        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Notebook for different PDF features
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        # Initialize tabs for each feature - will be populated in later steps
        self._create_pdf_to_images_tab()
        self._create_delete_pages_tab()
        self._create_split_pdf_tab()
        self._create_merge_pdfs_tab()
        self._create_images_to_pdf_tab()

        self.protocol("WM_DELETE_WINDOW", self.destroy) # Ensure proper cleanup if needed

    def _create_pdf_to_images_tab(self):
        tab_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_frame, text="PDF to Images")

        # PDF File Selection
        file_frame = ttk.Frame(tab_frame)
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(file_frame, text="PDF File:").pack(side=tk.LEFT, padx=(0, 5))
        self.pdf_to_img_file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.pdf_to_img_file_var, width=60)
        file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        browse_btn = ttk.Button(file_frame, text="Browse...", command=lambda: self._browse_pdf_file(self.pdf_to_img_file_var))
        browse_btn.pack(side=tk.LEFT)

        # Output Directory Selection
        dir_frame = ttk.Frame(tab_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dir_frame, text="Output Dir:").pack(side=tk.LEFT, padx=(0, 5))
        self.pdf_to_img_dir_var = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.pdf_to_img_dir_var, width=60)
        dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        browse_dir_btn = ttk.Button(dir_frame, text="Browse...", command=lambda: self._browse_directory(self.pdf_to_img_dir_var))
        browse_dir_btn.pack(side=tk.LEFT)

        # DPI Selection
        dpi_frame = ttk.Frame(tab_frame)
        dpi_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dpi_frame, text="Image DPI:").pack(side=tk.LEFT, padx=(0, 5))
        self.pdf_to_img_dpi_var = tk.IntVar(value=150) # Default DPI
        dpi_values = [72, 150, 300, 600]
        dpi_combo = ttk.Combobox(dpi_frame, textvariable=self.pdf_to_img_dpi_var, values=dpi_values, width=10, state="readonly")
        dpi_combo.pack(side=tk.LEFT)

        # Export Button
        export_btn = ttk.Button(tab_frame, text="Export Pages to PNGs", command=self._export_pdf_to_png_action)
        export_btn.pack(pady=10)

        # Status Label (optional, for feedback within the tab)
        self.pdf_to_img_status_var = tk.StringVar()
        status_label = ttk.Label(tab_frame, textvariable=self.pdf_to_img_status_var)
        status_label.pack(pady=5)

    def _browse_pdf_file(self, string_var):
        filepath = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
            parent=self
        )
        if filepath:
            string_var.set(filepath)

    def _browse_directory(self, string_var):
        dirpath = filedialog.askdirectory(
            title="Select Directory",
            parent=self
        )
        if dirpath:
            string_var.set(dirpath)

    def _export_pdf_to_png_action(self):
        if fitz is None:
            messagebox.showerror("Dependency Error", "PyMuPDF (fitz) library failed to load. Please check its installation. PDF features are unavailable.", parent=self)
            return

        pdf_path = self.pdf_to_img_file_var.get()
        output_dir = self.pdf_to_img_dir_var.get()
        dpi = self.pdf_to_img_dpi_var.get()

        if not pdf_path or not os.path.isfile(pdf_path):
            messagebox.showerror("Input Error", "Please select a valid PDF file.", parent=self)
            return
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Input Error", "Please select a valid output directory.", parent=self)
            return
        if not dpi > 0:
            messagebox.showerror("Input Error", "Please select a valid DPI.", parent=self)
            return

        self.pdf_to_img_status_var.set("Processing...")
        self.update_idletasks()

        try:
            doc = fitz.open(pdf_path)
            num_pages = doc.page_count
            base_filename = os.path.splitext(os.path.basename(pdf_path))[0]

            for i in range(num_pages):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=dpi)
                output_image_path = os.path.join(output_dir, f"{base_filename}_page_{i + 1:03d}.png")
                pix.save(output_image_path)
                self.pdf_to_img_status_var.set(f"Exported page {i+1}/{num_pages}...")
                self.update_idletasks()

            doc.close()
            self.pdf_to_img_status_var.set("") # Clear status
            messagebox.showinfo("Success", f"Successfully exported {num_pages} page(s) to PNGs in:\n{output_dir}", parent=self)
        except Exception as e:
            self.pdf_to_img_status_var.set("Error.")
            messagebox.showerror("Export Error", f"An error occurred during PDF to PNG export:\n{e}", parent=self)


    def _create_delete_pages_tab(self):
        tab_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_frame, text="Delete Pages")

        # Input PDF File Selection
        in_file_frame = ttk.Frame(tab_frame)
        in_file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(in_file_frame, text="Input PDF:").pack(side=tk.LEFT, padx=(0, 5))
        self.del_pages_input_file_var = tk.StringVar()
        in_file_entry = ttk.Entry(in_file_frame, textvariable=self.del_pages_input_file_var, width=60)
        in_file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        in_browse_btn = ttk.Button(in_file_frame, text="Browse...", command=lambda: self._browse_pdf_file(self.del_pages_input_file_var))
        in_browse_btn.pack(side=tk.LEFT)

        # Page Numbers/Ranges Input
        pages_frame = ttk.Frame(tab_frame)
        pages_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pages_frame, text="Pages to Delete:").pack(side=tk.LEFT, padx=(0, 5))
        self.del_pages_ranges_var = tk.StringVar()
        ttk.Entry(pages_frame, textvariable=self.del_pages_ranges_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Label(pages_frame, text="(e.g., 1, 3-5, 7)").pack(side=tk.LEFT, padx=(5,0))


        # Output PDF File Selection
        out_file_frame = ttk.Frame(tab_frame)
        out_file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(out_file_frame, text="Output PDF:").pack(side=tk.LEFT, padx=(0, 5))
        self.del_pages_output_file_var = tk.StringVar()
        out_file_entry = ttk.Entry(out_file_frame, textvariable=self.del_pages_output_file_var, width=60)
        out_file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        out_browse_btn = ttk.Button(out_file_frame, text="Save As...", command=lambda: self._browse_save_pdf_file(self.del_pages_output_file_var))
        out_browse_btn.pack(side=tk.LEFT)

        # Delete Button
        delete_btn = ttk.Button(tab_frame, text="Delete Pages & Save PDF", command=self._delete_pdf_pages_action)
        delete_btn.pack(pady=10)

        self.del_pages_status_var = tk.StringVar()
        status_label = ttk.Label(tab_frame, textvariable=self.del_pages_status_var)
        status_label.pack(pady=5)

    def _browse_save_pdf_file(self, string_var):
        filepath = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
            parent=self
        )
        if filepath:
            string_var.set(filepath)

    def _parse_page_ranges(self, ranges_str, max_pages):
        """Parses a string like '1,3-5,7' into a sorted list of unique 0-indexed page numbers."""
        pages_to_delete = set()
        if not ranges_str.strip():
            return []
        try:
            parts = ranges_str.split(',')
            for part in parts:
                part = part.strip()
                if not part: continue
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    if start <= 0 or end <= 0 or start > end or end > max_pages :
                        raise ValueError(f"Invalid page range: {part}. Page numbers must be between 1 and {max_pages}.")
                    for i in range(start, end + 1):
                        pages_to_delete.add(i - 1) # 0-indexed
                else:
                    page_num = int(part)
                    if page_num <= 0 or page_num > max_pages:
                        raise ValueError(f"Invalid page number: {page_num}. Page numbers must be between 1 and {max_pages}.")
                    pages_to_delete.add(page_num - 1) # 0-indexed
        except ValueError as e:
            raise ValueError(f"Invalid page range format: {ranges_str}. Error: {e}") from e

        return sorted(list(pages_to_delete))


    def _delete_pdf_pages_action(self):
        if fitz is None:
            messagebox.showerror("Dependency Error", "PyMuPDF (fitz) library failed to load. Please check its installation. PDF features are unavailable.", parent=self)
            return

        input_pdf = self.del_pages_input_file_var.get()
        output_pdf = self.del_pages_output_file_var.get()
        ranges_str = self.del_pages_ranges_var.get()

        if not input_pdf or not os.path.isfile(input_pdf):
            messagebox.showerror("Input Error", "Please select a valid input PDF file.", parent=self)
            return
        if not output_pdf:
            messagebox.showerror("Input Error", "Please specify an output PDF file path.", parent=self)
            return
        if not ranges_str.strip():
            messagebox.showwarning("Input Warning", "No pages specified for deletion. The PDF will be saved unchanged.", parent=self)
            # Optionally, just copy the file or do nothing. For now, save it.
            # os.system(f'cp "{input_pdf}" "{output_pdf}"') # This is system dependent, better to use fitz to save
            try:
                doc = fitz.open(input_pdf)
                doc.save(output_pdf, garbage=4, deflate=True)
                doc.close()
                messagebox.showinfo("Success", f"PDF saved (no pages deleted) to:\n{output_pdf}", parent=self)
            except Exception as e:
                 messagebox.showerror("Save Error", f"Could not save PDF: {e}", parent=self)
            return


        self.del_pages_status_var.set("Processing...")
        self.update_idletasks()

        try:
            doc = fitz.open(input_pdf)
            max_doc_pages = doc.page_count

            pages_to_delete_indices = self._parse_page_ranges(ranges_str, max_doc_pages)

            if not pages_to_delete_indices: # Should be caught by earlier empty string check, but good to have
                self.del_pages_status_var.set("")
                messagebox.showinfo("No Action", "No valid pages selected for deletion.", parent=self)
                doc.close()
                return

            # fitz.delete_pages expects a list of 0-indexed page numbers.
            # The list should be in increasing order for some versions, though modern fitz might handle it.
            # It's safer to provide them sorted. _parse_page_ranges already sorts them.
            doc.delete_pages(pages_to_delete_indices)

            # Save the modified document
            # garbage=4 performs thorough garbage collection, deflate=True compresses
            doc.save(output_pdf, garbage=4, deflate=True)
            doc.close()

            self.del_pages_status_var.set("")
            messagebox.showinfo("Success", f"Successfully deleted pages and saved PDF to:\n{output_pdf}", parent=self)

        except ValueError as ve: # Catch parsing errors from _parse_page_ranges
            self.del_pages_status_var.set("Error.")
            messagebox.showerror("Input Error", str(ve), parent=self)
        except Exception as e:
            self.del_pages_status_var.set("Error.")
            messagebox.showerror("Processing Error", f"An error occurred while deleting pages:\n{e}", parent=self)


    def _create_split_pdf_tab(self):
        tab_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_frame, text="Split PDF")

        # Input PDF File Selection
        in_file_frame = ttk.Frame(tab_frame)
        in_file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(in_file_frame, text="Input PDF:").pack(side=tk.LEFT, padx=(0, 5))
        self.split_pdf_input_file_var = tk.StringVar()
        in_file_entry = ttk.Entry(in_file_frame, textvariable=self.split_pdf_input_file_var, width=60)
        in_file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        in_browse_btn = ttk.Button(in_file_frame, text="Browse...", command=lambda: self._browse_pdf_file(self.split_pdf_input_file_var))
        in_browse_btn.pack(side=tk.LEFT)

        # Output Directory Selection
        dir_frame = ttk.Frame(tab_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dir_frame, text="Output Dir:").pack(side=tk.LEFT, padx=(0, 5))
        self.split_pdf_output_dir_var = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.split_pdf_output_dir_var, width=60)
        dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        browse_dir_btn = ttk.Button(dir_frame, text="Browse...", command=lambda: self._browse_directory(self.split_pdf_output_dir_var))
        browse_dir_btn.pack(side=tk.LEFT)

        # Split Button
        split_btn = ttk.Button(tab_frame, text="Split PDF into Single Pages", command=self._split_pdf_action)
        split_btn.pack(pady=10)

        self.split_pdf_status_var = tk.StringVar()
        status_label = ttk.Label(tab_frame, textvariable=self.split_pdf_status_var)
        status_label.pack(pady=5)

    def _split_pdf_action(self):
        if fitz is None:
            messagebox.showerror("Dependency Error", "PyMuPDF (fitz) library failed to load. Please check its installation. PDF features are unavailable.", parent=self)
            return

        input_pdf_path = self.split_pdf_input_file_var.get()
        output_dir = self.split_pdf_output_dir_var.get()

        if not input_pdf_path or not os.path.isfile(input_pdf_path):
            messagebox.showerror("Input Error", "Please select a valid input PDF file.", parent=self)
            return
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Input Error", "Please select a valid output directory.", parent=self)
            return

        self.split_pdf_status_var.set("Splitting PDF...")
        self.update_idletasks()

        try:
            source_doc = fitz.open(input_pdf_path)
            num_pages = source_doc.page_count
            base_filename = os.path.splitext(os.path.basename(input_pdf_path))[0]

            if num_pages == 0:
                messagebox.showinfo("Info", "The selected PDF has no pages to split.", parent=self)
                self.split_pdf_status_var.set("")
                source_doc.close()
                return

            for i in range(num_pages):
                self.split_pdf_status_var.set(f"Processing page {i + 1}/{num_pages}...")
                self.update_idletasks()

                new_doc = fitz.open() # Create a new empty PDF for each page
                new_doc.insert_pdf(source_doc, from_page=i, to_page=i) # Insert just the current page

                output_filename = f"{base_filename}_page_{i + 1:03d}.pdf"
                output_filepath = os.path.join(output_dir, output_filename)

                new_doc.save(output_filepath, garbage=4, deflate=True)
                new_doc.close()

            source_doc.close()
            self.split_pdf_status_var.set("")
            messagebox.showinfo("Success", f"Successfully split PDF into {num_pages} single-page PDF(s) in:\n{output_dir}", parent=self)

        except Exception as e:
            self.split_pdf_status_var.set("Error.")
            messagebox.showerror("Splitting Error", f"An error occurred while splitting the PDF:\n{e}", parent=self)


    def _create_merge_pdfs_tab(self):
        tab_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_frame, text="Merge PDFs")
        tab_frame.columnconfigure(0, weight=1) # Allow listbox/button frame to expand

        # Frame for Listbox and its Scrollbar
        listbox_frame = ttk.Frame(tab_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        listbox_frame.rowconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)

        self.merge_pdf_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED, width=70, height=10)
        self.merge_pdf_listbox.grid(row=0, column=0, sticky="nsew")

        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.merge_pdf_listbox.yview)
        listbox_scrollbar.grid(row=0, column=1, sticky="ns")
        self.merge_pdf_listbox.configure(yscrollcommand=listbox_scrollbar.set)

        # Frame for Listbox control buttons (Add, Remove, Move Up/Down)
        listbox_buttons_frame = ttk.Frame(tab_frame)
        listbox_buttons_frame.pack(fill=tk.X, pady=(0,5))

        add_btn = ttk.Button(listbox_buttons_frame, text="Add PDF(s)", command=self._add_pdfs_to_merge_list)
        add_btn.pack(side=tk.LEFT, padx=2)
        remove_btn = ttk.Button(listbox_buttons_frame, text="Remove Selected", command=self._remove_selected_pdfs_from_merge_list)
        remove_btn.pack(side=tk.LEFT, padx=2)
        move_up_btn = ttk.Button(listbox_buttons_frame, text="Move Up", command=self._move_pdf_in_merge_list_up)
        move_up_btn.pack(side=tk.LEFT, padx=2)
        move_down_btn = ttk.Button(listbox_buttons_frame, text="Move Down", command=self._move_pdf_in_merge_list_down)
        move_down_btn.pack(side=tk.LEFT, padx=2)

        # Output PDF File Selection
        out_file_frame = ttk.Frame(tab_frame)
        out_file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(out_file_frame, text="Output Merged PDF:").pack(side=tk.LEFT, padx=(0, 5))
        self.merge_output_file_var = tk.StringVar()
        out_file_entry = ttk.Entry(out_file_frame, textvariable=self.merge_output_file_var, width=50)
        out_file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        out_browse_btn = ttk.Button(out_file_frame, text="Save As...", command=lambda: self._browse_save_pdf_file(self.merge_output_file_var))
        out_browse_btn.pack(side=tk.LEFT)

        # Merge Button
        merge_btn = ttk.Button(tab_frame, text="Merge PDFs & Save", command=self._merge_pdfs_action)
        merge_btn.pack(pady=10)

        self.merge_pdfs_status_var = tk.StringVar()
        status_label = ttk.Label(tab_frame, textvariable=self.merge_pdfs_status_var)
        status_label.pack(pady=5)

    def _add_pdfs_to_merge_list(self):
        filepaths = filedialog.askopenfilenames(
            title="Select PDF files to merge",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
            parent=self
        )
        if filepaths:
            for fp in filepaths:
                if fp not in self.merge_pdf_listbox.get(0, tk.END): # Avoid duplicates
                    self.merge_pdf_listbox.insert(tk.END, fp)

    def _remove_selected_pdfs_from_merge_list(self):
        selected_indices = self.merge_pdf_listbox.curselection()
        # Iterate in reverse to avoid index shifting issues when deleting
        for i in sorted(selected_indices, reverse=True):
            self.merge_pdf_listbox.delete(i)

    def _move_pdf_in_merge_list_up(self):
        selected_indices = self.merge_pdf_listbox.curselection()
        if not selected_indices: return

        for i in selected_indices: # Process one by one for simplicity, though only first matters for single selection
            if i > 0:
                text = self.merge_pdf_listbox.get(i)
                self.merge_pdf_listbox.delete(i)
                self.merge_pdf_listbox.insert(i - 1, text)
                self.merge_pdf_listbox.selection_set(i - 1) # Keep it selected

    def _move_pdf_in_merge_list_down(self):
        selected_indices = self.merge_pdf_listbox.curselection()
        if not selected_indices: return

        # Process in reverse order of selection to handle multiple items moving down correctly
        for i in sorted(selected_indices, reverse=True):
            if i < self.merge_pdf_listbox.size() - 1:
                text = self.merge_pdf_listbox.get(i)
                self.merge_pdf_listbox.delete(i)
                self.merge_pdf_listbox.insert(i + 1, text)
                self.merge_pdf_listbox.selection_set(i + 1)

    def _merge_pdfs_action(self):
        if fitz is None:
            messagebox.showerror("Dependency Error", "PyMuPDF (fitz) library failed to load. Please check its installation. PDF features are unavailable.", parent=self)
            return

        pdf_files_to_merge = self.merge_pdf_listbox.get(0, tk.END)
        output_pdf_path = self.merge_output_file_var.get()

        if len(pdf_files_to_merge) < 1: # Changed from < 2 to allow "saving" a single PDF (effectively a copy)
            messagebox.showerror("Input Error", "Please add at least one PDF file to the list to merge/save.", parent=self)
            return
        if not output_pdf_path:
            messagebox.showerror("Input Error", "Please specify an output file path for the merged PDF.", parent=self)
            return

        self.merge_pdfs_status_var.set("Merging PDFs...")
        self.update_idletasks()

        try:
            result_doc = fitz.open() # Create new empty PDF

            for idx, pdf_path in enumerate(pdf_files_to_merge):
                self.merge_pdfs_status_var.set(f"Processing file {idx + 1}/{len(pdf_files_to_merge)}: {os.path.basename(pdf_path)}...")
                self.update_idletasks()
                if not os.path.isfile(pdf_path):
                    raise ValueError(f"File not found: {pdf_path}")

                source_doc = fitz.open(pdf_path)
                result_doc.insert_pdf(source_doc) # Appends all pages from source_doc
                source_doc.close()

            result_doc.save(output_pdf_path, garbage=4, deflate=True)
            result_doc.close()

            self.merge_pdfs_status_var.set("")
            messagebox.showinfo("Success", f"Successfully merged {len(pdf_files_to_merge)} PDF(s) into:\n{output_pdf_path}", parent=self)

        except Exception as e:
            self.merge_pdfs_status_var.set("Error.")
            messagebox.showerror("Merging Error", f"An error occurred while merging PDFs:\n{e}", parent=self)


    def _create_images_to_pdf_tab(self):
        tab_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_frame, text="Images to PDF")
        tab_frame.columnconfigure(0, weight=1) # Main column for listbox and controls

        # Frame for Listbox and its Scrollbar
        img_listbox_frame = ttk.Frame(tab_frame)
        img_listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        img_listbox_frame.rowconfigure(0, weight=1)
        img_listbox_frame.columnconfigure(0, weight=1)

        self.img_to_pdf_listbox = tk.Listbox(img_listbox_frame, selectmode=tk.EXTENDED, width=70, height=8)
        self.img_to_pdf_listbox.grid(row=0, column=0, sticky="nsew")

        img_listbox_scrollbar = ttk.Scrollbar(img_listbox_frame, orient=tk.VERTICAL, command=self.img_to_pdf_listbox.yview)
        img_listbox_scrollbar.grid(row=0, column=1, sticky="ns")
        self.img_to_pdf_listbox.configure(yscrollcommand=img_listbox_scrollbar.set)

        # Frame for Listbox control buttons
        img_listbox_buttons_frame = ttk.Frame(tab_frame)
        img_listbox_buttons_frame.pack(fill=tk.X, pady=(0,5))

        add_img_btn = ttk.Button(img_listbox_buttons_frame, text="Add Image(s)", command=self._add_images_to_convert_list)
        add_img_btn.pack(side=tk.LEFT, padx=2)
        remove_img_btn = ttk.Button(img_listbox_buttons_frame, text="Remove Selected", command=self._remove_selected_images_from_convert_list)
        remove_img_btn.pack(side=tk.LEFT, padx=2)
        move_img_up_btn = ttk.Button(img_listbox_buttons_frame, text="Move Up", command=self._move_image_in_convert_list_up)
        move_img_up_btn.pack(side=tk.LEFT, padx=2)
        move_img_down_btn = ttk.Button(img_listbox_buttons_frame, text="Move Down", command=self._move_image_in_convert_list_down)
        move_img_down_btn.pack(side=tk.LEFT, padx=2)

        # PDF Options Frame (Page Size, Orientation, Fit)
        options_frame = ttk.Frame(tab_frame)
        options_frame.pack(fill=tk.X, pady=5)

        ttk.Label(options_frame, text="Page Size:").pack(side=tk.LEFT, padx=(0,2))
        self.img_to_pdf_page_size_var = tk.StringVar(value="A4")
        page_size_combo = ttk.Combobox(options_frame, textvariable=self.img_to_pdf_page_size_var, values=["A4", "Letter"], width=8, state="readonly")
        page_size_combo.pack(side=tk.LEFT, padx=(0,10))

        ttk.Label(options_frame, text="Orientation:").pack(side=tk.LEFT, padx=(0,2))
        self.img_to_pdf_orientation_var = tk.StringVar(value="Portrait")
        orientation_combo = ttk.Combobox(options_frame, textvariable=self.img_to_pdf_orientation_var, values=["Portrait", "Landscape"], width=10, state="readonly")
        orientation_combo.pack(side=tk.LEFT, padx=(0,10))

        ttk.Label(options_frame, text="Output DPI:").pack(side=tk.LEFT, padx=(0,2))
        self.img_to_pdf_output_dpi_var = tk.IntVar(value=300)
        dpi_values = [150, 300, 600]
        output_dpi_combo = ttk.Combobox(options_frame, textvariable=self.img_to_pdf_output_dpi_var, values=dpi_values, width=5, state="readonly")
        output_dpi_combo.pack(side=tk.LEFT, padx=(0,10))

        # self.img_to_pdf_fit_var = tk.BooleanVar(value=True) # Replaced by radio buttons
        # fit_check = ttk.Checkbutton(options_frame, text="Fit image to page (maintain aspect ratio)", variable=self.img_to_pdf_fit_var)
        # fit_check.pack(side=tk.LEFT, padx=(0,5))

        # Fitting options frame
        fitting_frame = ttk.LabelFrame(tab_frame, text="Image Fitting Mode", padding=5)
        fitting_frame.pack(fill=tk.X, pady=5)

        self.img_to_pdf_fitting_mode_var = tk.StringVar(value="fit_aspect") # Default

        rb_fit_aspect = ttk.Radiobutton(fitting_frame, text="Fit (maintain aspect ratio)", variable=self.img_to_pdf_fitting_mode_var, value="fit_aspect")
        rb_fit_aspect.pack(anchor=tk.W, padx=5)

        rb_stretch_fill = ttk.Radiobutton(fitting_frame, text="Stretch to fill page (distort)", variable=self.img_to_pdf_fitting_mode_var, value="stretch_fill")
        rb_stretch_fill.pack(anchor=tk.W, padx=5)

        rb_original_size = ttk.Radiobutton(fitting_frame, text="Original image size", variable=self.img_to_pdf_fitting_mode_var, value="original_size")
        rb_original_size.pack(anchor=tk.W, padx=5)

        # Output PDF File Selection
        out_file_frame = ttk.Frame(tab_frame)
        out_file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(out_file_frame, text="Output PDF:").pack(side=tk.LEFT, padx=(0, 5))
        self.img_to_pdf_output_file_var = tk.StringVar()
        out_file_entry = ttk.Entry(out_file_frame, textvariable=self.img_to_pdf_output_file_var, width=50)
        out_file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        out_browse_btn = ttk.Button(out_file_frame, text="Save As...", command=lambda: self._browse_save_pdf_file(self.img_to_pdf_output_file_var))
        out_browse_btn.pack(side=tk.LEFT)

        # Convert Button
        convert_btn = ttk.Button(tab_frame, text="Convert Images to PDF", command=self._convert_images_to_pdf_action)
        convert_btn.pack(pady=10)

        self.img_to_pdf_status_var = tk.StringVar()
        status_label = ttk.Label(tab_frame, textvariable=self.img_to_pdf_status_var)
        status_label.pack(pady=5)

    def _add_images_to_convert_list(self):
        # Common image file types
        filetypes = [
            ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
            ("All Files", "*.*")
        ]
        filepaths = filedialog.askopenfilenames(
            title="Select image files",
            filetypes=filetypes,
            parent=self
        )
        if filepaths:
            for fp in filepaths:
                if fp not in self.img_to_pdf_listbox.get(0, tk.END):
                    self.img_to_pdf_listbox.insert(tk.END, fp)

    def _remove_selected_images_from_convert_list(self):
        selected_indices = self.img_to_pdf_listbox.curselection()
        for i in sorted(selected_indices, reverse=True):
            self.img_to_pdf_listbox.delete(i)

    def _move_image_in_convert_list_up(self):
        selected_indices = self.img_to_pdf_listbox.curselection()
        if not selected_indices: return
        for i in selected_indices:
            if i > 0:
                text = self.img_to_pdf_listbox.get(i)
                self.img_to_pdf_listbox.delete(i)
                self.img_to_pdf_listbox.insert(i - 1, text)
                self.img_to_pdf_listbox.selection_set(i - 1)

    def _move_image_in_convert_list_down(self):
        selected_indices = self.img_to_pdf_listbox.curselection()
        if not selected_indices: return
        for i in sorted(selected_indices, reverse=True):
            if i < self.img_to_pdf_listbox.size() - 1:
                text = self.img_to_pdf_listbox.get(i)
                self.img_to_pdf_listbox.delete(i)
                self.img_to_pdf_listbox.insert(i + 1, text)
                self.img_to_pdf_listbox.selection_set(i + 1)

    def _get_page_dimensions_pixels(self, page_size_str, orientation_str, dpi=72):
        # Standard page sizes in points (1/72 inch)
        sizes_points = {
            "A4": (595, 842),
            "Letter": (612, 792)
        }
        width_pt, height_pt = sizes_points.get(page_size_str, sizes_points["A4"])

        if orientation_str == "Landscape":
            width_pt, height_pt = height_pt, width_pt

        # Convert points to pixels
        return int(width_pt * dpi / 72), int(height_pt * dpi / 72)


    def _convert_images_to_pdf_action(self):
        if Image is None or ImageTk is None:
            messagebox.showerror("Dependency Missing", "Pillow library is not installed. Please install it to use this feature (pip install Pillow).", parent=self)
            return

        image_paths = self.img_to_pdf_listbox.get(0, tk.END)
        output_pdf_path = self.img_to_pdf_output_file_var.get()

        page_size_str = self.img_to_pdf_page_size_var.get()
        orientation_str = self.img_to_pdf_orientation_var.get()
        # fit_to_page = self.img_to_pdf_fit_var.get() # Old variable
        fitting_mode = self.img_to_pdf_fitting_mode_var.get()


        if not image_paths:
            messagebox.showerror("Input Error", "Please add at least one image to the list.", parent=self)
            return
        if not output_pdf_path:
            messagebox.showerror("Input Error", "Please specify an output file path for the PDF.", parent=self)
            return

        self.img_to_pdf_status_var.set("Converting images to PDF...")
        self.update_idletasks()

        processed_pil_images = []
        try:
            # Standard DPI for PDF page dimension calculations if not fitting
            # When fitting, we use this to create the blank page, then fit image into it.
            # Pillow's PDF save doesn't directly use DPI in the same way as image rendering.
            # We define page dimensions in pixels based on common paper sizes at a reference DPI (e.g., 72 or 300).
            # For simplicity, using 72 DPI for page size calculation, image itself retains its resolution.
            # MODIFIED: Use a higher DPI for better quality when fitting to page.
            output_dpi = self.img_to_pdf_output_dpi_var.get() # User selected DPI

            for idx, img_path in enumerate(image_paths):
                self.img_to_pdf_status_var.set(f"Processing image {idx + 1}/{len(image_paths)}: {os.path.basename(img_path)}...")
                self.update_idletasks()

                img = Image.open(img_path)

                if img.mode == 'RGBA' or img.mode == 'LA' or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGB')

                if fitting_mode == "fit_aspect" or fitting_mode == "stretch_fill":
                    # Calculate page dimensions in pixels using the selected output_dpi
                    page_width_px, page_height_px = self._get_page_dimensions_pixels(page_size_str, orientation_str, dpi=output_dpi)
                    page_image = Image.new('RGB', (page_width_px, page_height_px), (255, 255, 255))

                    if fitting_mode == "fit_aspect":
                        img_copy = img.copy()
                        img_copy.thumbnail((page_width_px, page_height_px), Image.Resampling.LANCZOS)
                        x_offset = (page_width_px - img_copy.width) // 2
                        y_offset = (page_height_px - img_copy.height) // 2
                        page_image.paste(img_copy, (x_offset, y_offset))
                    elif fitting_mode == "stretch_fill":
                        img_resized = img.resize((page_width_px, page_height_px), Image.Resampling.LANCZOS)
                        page_image.paste(img_resized, (0,0))

                    processed_pil_images.append(page_image)

                elif fitting_mode == "original_size":
                    processed_pil_images.append(img)

            if not processed_pil_images:
                self.img_to_pdf_status_var.set("No images processed.")
                messagebox.showwarning("Warning", "No images were successfully processed.", parent=self)
                return

            first_image = processed_pil_images[0]
            other_images = processed_pil_images[1:]

            if fitting_mode == "fit_aspect" or fitting_mode == "stretch_fill":
                save_resolution = self.img_to_pdf_output_dpi_var.get()
            else: # original_size
                save_resolution = 100.0 # Default for original size, or could try to get from image if available

            first_image.save(output_pdf_path, save_all=True, append_images=other_images, resolution=save_resolution)

            self.img_to_pdf_status_var.set("")
            messagebox.showinfo("Success", f"Successfully converted {len(processed_pil_images)} image(s) to PDF:\n{output_pdf_path}", parent=self)

        except FileNotFoundError as fnf_e:
            self.img_to_pdf_status_var.set("Error: File not found.")
            messagebox.showerror("File Error", f"Image file not found: {fnf_e.filename}", parent=self)
        except Exception as e:
            self.img_to_pdf_status_var.set("Error.")
            messagebox.showerror("Conversion Error", f"An error occurred while converting images to PDF:\n{e}", parent=self)


    # Placeholder for methods related to each feature, to be implemented later
    # def _export_pdf_to_png(self): pass # Already implemented
    # def _delete_pdf_pages(self): pass
    # def _split_pdf_pages(self): pass
    # def _merge_pdfs(self): pass
    # def _convert_images_to_pdf(self): pass

if __name__ == '__main__':
    # This is for testing the dialog independently
    # You would typically run editor.py
    root = tk.Tk()
    root.withdraw() # Hide the main root window for dialog-only testing

    # Mock parent editor for testing
    class MockEditor:
        def __init__(self, root_window):
            self.root = root_window
            # Add any other attributes/methods PdfToolDialog might expect from parent_editor
            # For now, only self.root is used by PdfToolDialog constructor

    mock_editor_app = MockEditor(root)
    dialog = PdfToolDialog(mock_editor_app)
    dialog.mainloop()
