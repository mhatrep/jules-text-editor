import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading # Added missing import

class DocumentConverterDialog(tk.Toplevel):
    """
    A dialog for converting various document types (.docx, .pdf, .html, .txt)
    into cleaned plain text files.
    """
    def __init__(self, master):
        """
        Initializes the DocumentConverterDialog.

        Args:
            master: The parent widget (typically the main TextEditor instance).
        """
        super().__init__(master.root)
        self.title("Document to Text Converter")
        self.geometry("700x550")
        self.master_app = master

        self.file_list = [] # Store full paths of files to convert
        self.supported_formats = {
            ".txt": "Text",
            ".docx": "Word Document",
            ".pdf": "PDF Document",
            ".html": "HTML File",
            ".htm": "HTML File",
            ".pptx": "PowerPoint Presentation"
        }

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Input Files Frame ---
        input_frame = ttk.LabelFrame(main_frame, text="Input Files/Directories", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        input_frame.columnconfigure(0, weight=1) # Listbox column

        self.listbox_frame = ttk.Frame(input_frame)
        self.listbox_frame.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(0,5))
        self.listbox_frame.rowconfigure(0, weight=1)
        self.listbox_frame.columnconfigure(0, weight=1)

        self.files_listbox = tk.Listbox(self.listbox_frame, selectmode=tk.EXTENDED, width=70, height=10)
        self.files_listbox.grid(row=0, column=0, sticky="nsew")

        list_scrollbar_y = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        list_scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.files_listbox.config(yscrollcommand=list_scrollbar_y.set)

        list_scrollbar_x = ttk.Scrollbar(self.listbox_frame, orient=tk.HORIZONTAL, command=self.files_listbox.xview)
        list_scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.files_listbox.config(xscrollcommand=list_scrollbar_x.set)

        # Buttons for listbox management
        list_buttons_frame = ttk.Frame(input_frame)
        list_buttons_frame.grid(row=0, column=1, rowspan=4, sticky="ns", padx=(5,0))

        add_files_button = ttk.Button(list_buttons_frame, text="Add File(s)...", command=self._add_files)
        add_files_button.pack(fill=tk.X, pady=2)
        add_dir_button = ttk.Button(list_buttons_frame, text="Add Directory...", command=self._add_directory)
        add_dir_button.pack(fill=tk.X, pady=2)
        remove_selected_button = ttk.Button(list_buttons_frame, text="Remove Selected", command=self._remove_selected)
        remove_selected_button.pack(fill=tk.X, pady=2)
        clear_list_button = ttk.Button(list_buttons_frame, text="Clear List", command=self._clear_list)
        clear_list_button.pack(fill=tk.X, pady=2)

        # --- Output Options Frame ---
        output_options_frame = ttk.LabelFrame(main_frame, text="Output Options", padding="10")
        output_options_frame.pack(fill=tk.X, pady=5)
        output_options_frame.columnconfigure(1, weight=1)

        self.output_dir_choice = tk.StringVar(value="same") # 'same' or 'specific'

        same_dir_radio = ttk.Radiobutton(output_options_frame, text="Save in same directory as input",
                                         variable=self.output_dir_choice, value="same", command=self._toggle_output_dir_entry)
        same_dir_radio.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=2)

        specific_dir_radio = ttk.Radiobutton(output_options_frame, text="Save in specific directory:",
                                             variable=self.output_dir_choice, value="specific", command=self._toggle_output_dir_entry)
        specific_dir_radio.grid(row=1, column=0, sticky=tk.W, pady=2)

        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(output_options_frame, textvariable=self.output_dir_var, width=50, state=tk.DISABLED)
        self.output_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)

        browse_output_button = ttk.Button(output_options_frame, text="Browse...", command=self._browse_output_dir, state=tk.DISABLED)
        browse_output_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.browse_output_button_ref = browse_output_button # Keep a reference

        # --- Conversion Control & Status ---
        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        self.convert_button = ttk.Button(action_frame, text="Start Conversion", command=self._start_conversion)
        self.convert_button.pack(side=tk.RIGHT, padx=5)

        self.cancel_button = ttk.Button(action_frame, text="Cancel", command=self._cancel_conversion, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)

        self.status_label_var = tk.StringVar(value="Status: Idle")
        status_label = ttk.Label(action_frame, textvariable=self.status_label_var)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)
        add_files_button.focus_set()

    def _update_listbox(self):
        """Refreshes the listbox display based on the content of self.file_list."""
        self.files_listbox.delete(0, tk.END)
        for item_path in self.file_list:
            self.files_listbox.insert(tk.END, item_path)

    def _add_files(self):
        """
        Opens a file dialog for the user to select one or more document files.
        Selected files are added to the internal list and displayed in the listbox.
        """
        file_types_for_dialog = []
        for ext, desc in self.supported_formats.items():
            # Ensure correct glob pattern, e.g., *.txt
            file_types_for_dialog.append((f"{desc} (*{ext})", f"*{ext}"))
        file_types_for_dialog.append(("All files", "*.*"))

        filepaths = filedialog.askopenfilenames(
            parent=self,
            title="Select Document Files",
            filetypes=file_types_for_dialog
        )
        if filepaths:
            for f_path in filepaths:
                if f_path not in self.file_list: # Avoid duplicates
                    self.file_list.append(f_path)
            self._update_listbox()

    def _add_directory(self):
        """
        Opens a directory dialog for the user to select a folder.
        Recursively finds all supported document types within that folder
        and adds them to the internal list and listbox display.
        """
        dir_path = filedialog.askdirectory(parent=self, title="Select Directory Containing Documents")
        if dir_path:
            added_count = 0
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in self.supported_formats:
                        full_path = os.path.join(root, file)
                        if full_path not in self.file_list: # Avoid duplicates
                            self.file_list.append(full_path)
                            added_count +=1
            if added_count > 0:
                self._update_listbox()
            else:
                messagebox.showinfo("Info", f"No new supported document files found in '{os.path.basename(dir_path)}' or its subdirectories.", parent=self)


    def _remove_selected(self):
        """Removes selected files from the conversion list."""
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "No files selected to remove.", parent=self)
            return

        # Remove in reverse order to maintain correct indices
        for index in sorted(selected_indices, reverse=True):
            del self.file_list[index]
        self._update_listbox()

    def _clear_list(self):
        """Clears all files from the conversion list."""
        if not self.file_list:
            return # Nothing to clear
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all files from the list?", parent=self):
            self.file_list.clear()
            self._update_listbox()

    def _toggle_output_dir_entry(self):
        if self.output_dir_choice.get() == "specific":
            self.output_dir_entry.config(state=tk.NORMAL)
            self.browse_output_button_ref.config(state=tk.NORMAL)
        else:
            self.output_dir_entry.config(state=tk.DISABLED)
            self.browse_output_button_ref.config(state=tk.DISABLED)
            self.output_dir_var.set("") # Clear if "same as input"

    def _browse_output_dir(self):
        """Opens a dialog for the user to select a specific output directory."""
        directory = filedialog.askdirectory(parent=self, title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)

    def _start_conversion(self):
        """
        Validates inputs and initiates the file conversion process in a separate thread.
        Disables UI elements during conversion and re-enables them upon completion.
        """
        if not self.file_list:
            messagebox.showwarning("Warning", "No files to convert. Please add files or directories.", parent=self)
            return

        output_dir = self.output_dir_var.get()
        if self.output_dir_choice.get() == "specific" and not (output_dir and os.path.isdir(output_dir)):
            messagebox.showerror("Error", "Please select a valid specific output directory.", parent=self)
            return

        self.convert_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.status_label_var.set("Status: Starting conversion...")

        # Run the conversion in a separate thread to avoid freezing the UI
        self.conversion_thread = threading.Thread(target=self._conversion_worker, daemon=True)
        self.conversion_thread.start()

    def _cancel_conversion(self):
        if self.conversion_thread and self.conversion_thread.is_alive():
            self.status_label_var.set("Status: Cancellation requested...")
            self.cancel_requested = True

    def _conversion_worker(self):
        """The actual worker process for converting files."""
        self.cancel_requested = False
        total_files = len(self.file_list)
        errors = []

        for i, filepath in enumerate(self.file_list):
            if self.cancel_requested:
                self.status_label_var.set("Status: Conversion cancelled.")
                break
            self.status_label_var.set(f"Status: Processing {i+1}/{total_files}: {os.path.basename(filepath)}")

            file_ext = os.path.splitext(filepath)[1].lower()
            raw_text = ""

            if file_ext == '.txt':
                raw_text = self._extract_text_from_txt(filepath)
            elif file_ext == '.docx':
                raw_text = self._extract_text_from_docx(filepath)
            elif file_ext == '.pdf':
                raw_text = self._extract_text_from_pdf(filepath)
            elif file_ext in ['.html', '.htm']:
                raw_text = self._extract_text_from_html(filepath)
            elif file_ext == '.pptx':
                raw_text = self._extract_text_from_pptx(filepath)
            else:
                # This case should ideally not be reached if listbox is populated correctly
                errors.append(f"Unsupported file type: {os.path.basename(filepath)}")
                continue

            if raw_text.startswith("[Error:"): # Check if extraction failed
                errors.append(f"{os.path.basename(filepath)} - {raw_text}")
                continue

            processed_text = self._process_text_content(raw_text)

            # Determine output path
            base_filename = os.path.splitext(os.path.basename(filepath))[0]
            output_filename = f"{base_filename}.txt"

            output_dir = ""
            if self.output_dir_choice.get() == "same":
                output_dir = os.path.dirname(filepath)
            else: # 'specific'
                output_dir = self.output_dir_var.get()

            output_path = os.path.join(output_dir, output_filename)

            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(processed_text)
            except Exception as e:
                errors.append(f"Could not save {output_filename}: {e}")

        # Final status update after loop finishes
        if not errors:
            self.status_label_var.set(f"Status: Conversion complete! {total_files} file(s) processed.")
        else:
            error_summary = f"Status: Conversion finished with {len(errors)} error(s). See details below."
            self.status_label_var.set(error_summary)
            # Optionally, show errors in a new window/dialog
            error_details_str = "\n".join(errors)
            messagebox.showerror("Conversion Errors", f"The following errors occurred:\n\n{error_details_str}", parent=self)

        self.convert_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)


    def on_close(self, event=None):
        # Placeholder for any cleanup if needed (e.g., stop running conversion thread)
        self.destroy()

    # --- Text Extraction Methods ---
    def _extract_text_from_txt(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            # print(f"Error reading txt file {filepath}: {e}")
            return f"[Error reading TXT: {e}]"

    def _extract_text_from_docx(self, filepath):
        try:
            import docx # python-docx library
            doc = docx.Document(filepath)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\n'.join(full_text)
        except ImportError:
            # print("python-docx library not found. Please install it.")
            return "[Error: python-docx library not installed]"
        except Exception as e:
            # print(f"Error reading docx file {filepath}: {e}")
            return f"[Error reading DOCX: {e}]"

    def _extract_text_from_pdf(self, filepath):
        try:
            import fitz  # PyMuPDF
            text = ""
            with fitz.open(filepath) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except ImportError:
            # print("PyMuPDF (fitz) library not found. It should be in requirements.")
            return "[Error: PyMuPDF (fitz) library not installed]"
        except Exception as e:
            # print(f"Error reading pdf file {filepath}: {e}")
            return f"[Error reading PDF: {e}]"

    def _extract_text_from_pptx(self, filepath):
        try:
            from pptx import Presentation
            prs = Presentation(filepath)
            full_text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        full_text.append(shape.text)
            return '\n'.join(full_text)
        except ImportError:
            return "[Error: python-pptx library not installed]"
        except Exception as e:
            return f"[Error reading PPTX: {e}]"

    def _extract_text_from_html(self, filepath):
        try:
            from bs4 import BeautifulSoup, Comment
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'lxml')

            # Tags to remove completely
            tags_to_remove = ['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'button', 'input', 'textarea', 'label', 'select', 'option']
            for tag in soup(tags_to_remove):
                tag.decompose()

            # Remove comments
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()

            # Replace some block-level elements with newlines for better formatting
            for tag in soup(['p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr', 'blockquote']):
                tag.append('\n')

            # Get text, which now includes the added newlines
            text = soup.get_text(separator=' ', strip=False) # Use space separator to handle inline tags better initially

            # Post-processing to clean up whitespace
            lines = (line.strip() for line in text.splitlines()) # Process each line
            chunks = (phrase.strip() for line in lines for phrase in line.split("  ")) # Split on multiple spaces to condense them
            text = '\n'.join(chunk for chunk in chunks if chunk) # Rejoin non-empty parts with single newlines

            return text
        except ImportError:
            return "[Error: beautifulsoup4 or lxml library not installed]"
        except Exception as e:
            return f"[Error reading HTML: {e}]"

    # --- Text Processing Method ---
    def _process_text_content(self, raw_text: str) -> str:
        """
        Cleans the raw extracted text according to specified rules:
        - Trims leading/trailing whitespace from each line.
        - Replaces multiple consecutive blank lines with a single blank line.
        - Removes non-printable characters (excluding space, tab, CR, LF).
        """
        if not isinstance(raw_text, str):
            return "" # Or handle error appropriately

        lines = raw_text.splitlines()
        processed_lines = []

        # 1. Trim whitespace from each line and remove non-printable characters
        cleaned_lines = []
        for line in lines:
            stripped_line = line.strip()
            # Remove non-printable characters, but keep common whitespace (space, tab)
            # and allow actual newlines handled by splitlines/join.
            # Characters to keep: string.printable includes letters, digits, punctuation, whitespace.
            # We want to be a bit more selective for "non-printable" in this context.
            # A common approach is to filter out characters not in a whitelist of "good" characters
            # or specifically target ranges of control characters (excluding \t, \n, \r).

            # Keep ASCII printable and \t, \n, \r.
            # This will remove things like form feed, vertical tab, bell, nulls, etc.
            # string.printable includes digits, ascii_letters, punctuation, and whitespace (space, tab, linefeed, formfeed, carriage return, vertical tab)
            # We want to remove formfeed, vertical tab from string.whitespace for this definition.

            # More targeted removal of C0 and C1 control characters except HT, LF, CR
            # C0 controls: 0x00-0x1F. C1 controls: 0x7F-0x9F (0x7F is DEL)
            def is_char_printable_custom(char):
                # Allow standard printable ASCII, tab, LF, CR
                return (' ' <= char <= '~') or (char in ('\t', '\n', '\r'))

            printable_line = "".join(filter(is_char_printable_custom, stripped_line))
            cleaned_lines.append(printable_line)

        # 2. Replace multiple blank lines with a single one
        last_line_was_blank = False
        for line in cleaned_lines:
            if not line: # Current line is blank (empty after strip)
                if not last_line_was_blank:
                    processed_lines.append("") # Add one blank line
                last_line_was_blank = True
            else: # Current line has content
                processed_lines.append(line)
                last_line_was_blank = False

        # Ensure there's a newline at the end if the original text likely had one
        # or if the last processed line wasn't blank.
        final_text = "\n".join(processed_lines)

        # One final pass to ensure no leading/trailing newlines on the whole text block,
        # unless it's just a single newline for an empty file.
        # The join above handles this well, but strip() can clean up any extra.
        if final_text == "\n" and not processed_lines: # if only a single newline from empty processing
             return ""

        return final_text


if __name__ == '__main__':
    # Example usage for testing the dialog independently
    root = tk.Tk()
    root.title("Main Test Window")

    # Mock TextEditor class or pass relevant parts if dialog needs them
    class MockEditor:
        def __init__(self, root_window):
            self.root = root_window
            # Add any other attributes the dialog might expect from its master

    mock_master_app = MockEditor(root)

    def open_dialog():
        dialog = DocumentConverterDialog(mock_master_app)
        # dialog.grab_set() # Make it modal for testing if desired

    ttk.Button(root, text="Open Document Converter", command=open_dialog).pack(padx=20, pady=20)
    root.mainloop()
