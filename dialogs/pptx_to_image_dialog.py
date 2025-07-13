import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from pptx import Presentation
from PIL import Image

class PptxToImageDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master.root)
        self.title("PowerPoint to Image Converter")
        self.geometry("500x250")
        self.master_app = master

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Input File ---
        ttk.Label(main_frame, text="PowerPoint File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.pptx_file_var = tk.StringVar()
        self.pptx_file_entry = ttk.Entry(main_frame, textvariable=self.pptx_file_var, width=50)
        self.pptx_file_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(main_frame, text="Browse...", command=self._browse_pptx_file).grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)

        # --- Output Directory ---
        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(main_frame, text="Browse...", command=self._browse_output_dir).grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)

        # --- Options ---
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=2, column=0, columnspan=3, pady=10)

        ttk.Label(options_frame, text="Image Format:").pack(side=tk.LEFT, padx=(0, 5))
        self.image_format_var = tk.StringVar(value="png")
        self.image_format_combo = ttk.Combobox(options_frame, textvariable=self.image_format_var, values=["png", "jpeg", "bmp", "tiff"], state="readonly")
        self.image_format_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(options_frame, text="DPI:").pack(side=tk.LEFT, padx=(10, 5))
        self.dpi_var = tk.StringVar(value="300")
        self.dpi_entry = ttk.Entry(options_frame, textvariable=self.dpi_var, width=10)
        self.dpi_entry.pack(side=tk.LEFT, padx=5)

        # --- Conversion Control & Status ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.convert_button = ttk.Button(action_frame, text="Convert", command=self._start_conversion)
        self.convert_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(action_frame, text="Cancel", command=self._cancel_conversion, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.status_label_var = tk.StringVar(value="Status: Idle")
        status_label = ttk.Label(action_frame, textvariable=self.status_label_var)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)

    def _browse_pptx_file(self):
        filepath = filedialog.askopenfilename(
            parent=self,
            title="Select PowerPoint File",
            filetypes=[("PowerPoint Files", "*.pptx"), ("All Files", "*.*")]
        )
        if filepath:
            self.pptx_file_var.set(filepath)

    def _browse_output_dir(self):
        directory = filedialog.askdirectory(parent=self, title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)

    def _start_conversion(self):
        pptx_file = self.pptx_file_var.get()
        output_dir = self.output_dir_var.get()
        image_format = self.image_format_var.get()
        try:
            dpi = int(self.dpi_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for DPI.", parent=self)
            return

        if not pptx_file or not os.path.isfile(pptx_file):
            messagebox.showerror("Error", "Please select a valid PowerPoint file.", parent=self)
            return

        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Please select a valid output directory.", parent=self)
            return

        self.convert_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.status_label_var.set("Status: Starting conversion...")

        self.conversion_thread = threading.Thread(target=self._conversion_worker, args=(pptx_file, output_dir, image_format, dpi), daemon=True)
        self.conversion_thread.start()

    def _cancel_conversion(self):
        if self.conversion_thread and self.conversion_thread.is_alive():
            # This is a bit tricky with comtypes, as it's a blocking call.
            # We can't easily interrupt the thread. The best we can do is
            # set a flag and check it between slides.
            self.status_label_var.set("Status: Cancellation requested...")
            self.cancel_requested = True

    def _conversion_worker(self, pptx_file, output_dir, image_format, dpi):
        self.cancel_requested = False
        if os.name != 'nt':
            messagebox.showerror("Unsupported OS", "This feature is only available on Windows with PowerPoint installed.", parent=self)
            self.status_label_var.set("Status: Unsupported OS")
            self.convert_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return
        try:
            import comtypes.client
            powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
            presentation = powerpoint.Presentations.Open(pptx_file)
            for i, slide in enumerate(presentation.Slides):
                if self.cancel_requested:
                    self.status_label_var.set("Status: Conversion cancelled.")
                    break
                slide_filename = f"{os.path.splitext(os.path.basename(pptx_file))[0]}_slide_{i+1}.{image_format}"
                slide_filepath = os.path.join(output_dir, slide_filename)
                slide.Export(slide_filepath, image_format.upper(), dpi, dpi)
                self.status_label_var.set(f"Status: Converted slide {i+1}/{len(presentation.Slides)}")
            presentation.Close()
            powerpoint.Quit()
            if not self.cancel_requested:
                self.status_label_var.set(f"Status: Conversion complete! {len(presentation.Slides)} slide(s) converted.")
        except Exception as e:
            self.status_label_var.set(f"Status: Error - {e}")

        self.convert_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

    def on_close(self, event=None):
        self.destroy()
