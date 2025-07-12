import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image, ImageTk, ImageDraw, ImageFont # Added ImageDraw, ImageFont

class ImageSearchDialog:
    def __init__(self, parent_editor, title="Image Search by Name"):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title(title)
        self.top.transient(self.root)
        self.top.grab_set()
        self.top.resizable(True, True)

        self._image_references = []
        self._current_image_paths_for_redisplay = []

        self._setup_ui()

        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)

        initial_width = max(self.top.winfo_width(), 600)
        initial_height = max(self.top.winfo_height(), 500)
        self.top.geometry(f'{initial_width}x{initial_height}+{x}+{y}')
        self.top.minsize(550, 450)

        self.top.bind("<Escape>", lambda e: self.top.destroy())


    def _setup_ui(self):
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(0, weight=1)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=0, column=0, sticky=tk.EW, pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)

        ttk.Label(controls_frame, text="Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.dir_var = tk.StringVar()
        current_tab = self.parent_editor.get_current_tab()
        if current_tab and current_tab.current_file:
            self.dir_var.set(os.path.dirname(current_tab.current_file))
        else:
            self.dir_var.set(os.path.expanduser("~"))

        dir_entry = ttk.Entry(controls_frame, textvariable=self.dir_var, width=60)
        dir_entry.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(0, 5))

        browse_button = ttk.Button(controls_frame, text="Browse...", command=self._browse_directory)
        browse_button.grid(row=0, column=2, sticky=tk.W, pady=2)

        ttk.Label(controls_frame, text="Filename contains (comma-sep):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.search_terms_var = tk.StringVar()
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_terms_var, width=60)
        search_entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=2)
        search_entry.bind("<Return>", self._start_search)

        search_button = ttk.Button(controls_frame, text="Search Images", command=self._start_search)
        search_button.grid(row=2, column=0, columnspan=2, pady=(10, 5), sticky=tk.EW)

        self.export_pdf_button = ttk.Button(controls_frame, text="Export to PDF", command=self._export_images_to_pdf, state=tk.DISABLED)
        self.export_pdf_button.grid(row=2, column=2, pady=(10, 5), padx=(5,0), sticky=tk.EW)

        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=0)

        pdf_options_outer_frame = ttk.Frame(controls_frame)
        pdf_options_outer_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(10,0))

        self.pdf_options_frame = ttk.LabelFrame(pdf_options_outer_frame, text="PDF Export Options", padding=5)
        self.pdf_options_frame.pack(fill=tk.X, expand=True)


        self.pdf_orientation_var = tk.StringVar(value="Portrait")
        ttk.Label(self.pdf_options_frame, text="Orientation:").pack(side=tk.LEFT, padx=(0,5), pady=2)
        ttk.Radiobutton(self.pdf_options_frame, text="Portrait", variable=self.pdf_orientation_var, value="Portrait").pack(side=tk.LEFT, pady=2)
        ttk.Radiobutton(self.pdf_options_frame, text="Landscape", variable=self.pdf_orientation_var, value="Landscape").pack(side=tk.LEFT, padx=(0,10), pady=2)

        self.pdf_fit_to_page_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.pdf_options_frame, text="Fit image to page", variable=self.pdf_fit_to_page_var).pack(side=tk.LEFT, padx=(0,10), pady=2)

        self.pdf_page_numbers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.pdf_options_frame, text="Add page numbers", variable=self.pdf_page_numbers_var).pack(side=tk.LEFT, pady=2)


        self.image_area_frame = ttk.LabelFrame(main_frame, text="Results", padding=5)
        self.image_area_frame.grid(row=1, column=0, sticky="nsew")
        self.image_area_frame.rowconfigure(0, weight=1)
        self.image_area_frame.columnconfigure(0, weight=1)

        main_frame.rowconfigure(1, weight=1)

        self.canvas = tk.Canvas(self.image_area_frame, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.image_area_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux_up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux_down)

        self.top.bind("<Configure>", self._on_dialog_resize)


    def _on_dialog_resize(self, event=None):
        if hasattr(self, '_debounce_resize_timer'):
            self.top.after_cancel(self._debounce_resize_timer)

        if self._image_references:
             self._debounce_resize_timer = self.top.after(300, lambda: self._display_images(self._current_image_paths_for_redisplay))


    def _on_mousewheel(self, event):
        widget_parent = str(event.widget.winfo_parent())
        canvas_parent = str(self.canvas.winfo_parent())
        if event.widget == self.canvas or widget_parent == canvas_parent :
            if event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            else:
                self.canvas.yview_scroll(1, "units")
            return "break"

    def _on_mousewheel_linux_up(self, event):
        widget_parent = str(event.widget.winfo_parent())
        canvas_parent = str(self.canvas.winfo_parent())
        if event.widget == self.canvas or widget_parent == canvas_parent:
            self.canvas.yview_scroll(-1, "units")
            return "break"

    def _on_mousewheel_linux_down(self, event):
        widget_parent = str(event.widget.winfo_parent())
        canvas_parent = str(self.canvas.winfo_parent())
        if event.widget == self.canvas or widget_parent == canvas_parent:
            self.canvas.yview_scroll(1, "units")
            return "break"

    def _browse_directory(self):
        dir_path = filedialog.askdirectory(parent=self.top, initialdir=self.dir_var.get())
        if dir_path:
            self.dir_var.set(dir_path)

    def _start_search(self, event=None):
        base_dir = self.dir_var.get()
        search_terms_str = self.search_terms_var.get()

        if not base_dir or not os.path.isdir(base_dir):
            messagebox.showerror("Error", "Base directory is invalid or not specified.", parent=self.top)
            return

        self.canvas.delete("all")
        self._image_references.clear()
        self.canvas.yview_moveto(0)

        found_image_paths = self._execute_image_search(base_dir, search_terms_str)
        self._current_image_paths_for_redisplay = found_image_paths

        if found_image_paths:
            self.image_area_frame.config(text=f"Results ({len(found_image_paths)} images found)")
            self._display_images(found_image_paths)
            self.export_pdf_button.config(state=tk.NORMAL)
        else:
            self.image_area_frame.config(text="Results (No images found)")
            self.export_pdf_button.config(state=tk.DISABLED)
            messagebox.showinfo("Search Complete", "No matching images found.", parent=self.top)
            self.canvas.update_idletasks()
            self.canvas.create_text(self.canvas.winfo_width()/2, 20, text="No images found.", anchor=tk.CENTER)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def _execute_image_search(self, base_dir, search_terms_str):
        matching_files = []
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}

        raw_terms = [term.strip().lower() for term in search_terms_str.split(',') if term.strip()]
        if not raw_terms and search_terms_str.strip():
            raw_terms = [search_terms_str.strip().lower()]

        for root, _, files in os.walk(base_dir):
            for filename in files:
                name_lower = filename.lower()
                _, ext = os.path.splitext(name_lower)

                if ext in image_extensions:
                    all_terms_match = True
                    if raw_terms:
                        for term in raw_terms:
                            if term not in name_lower:
                                all_terms_match = False
                                break

                    if all_terms_match:
                        matching_files.append(os.path.join(root, filename))

        return sorted(matching_files)


    def _display_images(self, image_paths):
        self.canvas.delete("all")
        self._image_references.clear()
        self.canvas.yview_moveto(0)

        num_images = len(image_paths)
        if num_images > 0:
            self.image_area_frame.config(text=f"Results ({num_images} images found)")
            self.export_pdf_button.config(state=tk.NORMAL)
        else:
            self.image_area_frame.config(text="Results (No images found)")
            self.export_pdf_button.config(state=tk.DISABLED)

        if not image_paths:
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            return

        self.top.update_idletasks()
        canvas_width = self.canvas.winfo_width() - 10
        if canvas_width <= 0: canvas_width = 300

        y_offset = 10
        padding = 10

        for img_path in image_paths:
            try:
                pil_image = Image.open(img_path)
                resized_image = self._resize_image_to_fit_canvas(pil_image, canvas_width)

                tk_image = ImageTk.PhotoImage(resized_image)
                self._image_references.append(tk_image)

                self.canvas.create_image(canvas_width / 2, y_offset, anchor=tk.N, image=tk_image)
                y_offset += resized_image.height + padding
            except FileNotFoundError:
                print(f"Error: Image file not found at {img_path}")
                self.canvas.create_text(canvas_width / 2, y_offset, text=f"Error: Not found\n{os.path.basename(img_path)}", fill="red", anchor=tk.N)
                y_offset += 40 + padding
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")
                self.canvas.create_text(canvas_width / 2, y_offset, text=f"Error loading\n{os.path.basename(img_path)}", fill="red", anchor=tk.N)
                y_offset += 40 + padding

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def _resize_image_to_fit_canvas(self, image, canvas_width):
        original_width, original_height = image.size
        if original_width == 0 or original_height == 0:
            return image

        if original_width > canvas_width:
            aspect_ratio = original_height / original_width
            new_width = canvas_width
            new_height = int(new_width * aspect_ratio)
            try:
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return resized_image
            except Exception as e:
                print(f"Error resizing image: {e}")
                return image
        return image

    def _export_images_to_pdf(self):
        if not self._current_image_paths_for_redisplay:
            messagebox.showinfo("No Images", "No images to export. Please perform a search first.", parent=self.top)
            return

        pdf_filepath = filedialog.asksaveasfilename(
            parent=self.top,
            title="Save Images as PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        )

        if not pdf_filepath:
            return

        orientation = self.pdf_orientation_var.get()
        fit_to_page = self.pdf_fit_to_page_var.get()
        add_page_numbers = self.pdf_page_numbers_var.get()

        A4_PORTRAIT_PX = (595, 842)
        A4_LANDSCAPE_PX = (842, 595)
        PAGE_MARGIN = 36

        page_size_px = A4_LANDSCAPE_PX if orientation == "Landscape" else A4_PORTRAIT_PX
        drawable_width = page_size_px[0] - (2 * PAGE_MARGIN)
        drawable_height = page_size_px[1] - (2 * PAGE_MARGIN)

        processed_page_images = []
        total_pages = len(self._current_image_paths_for_redisplay)

        try:
            font = ImageFont.load_default()
        except IOError:
            print("Default font not found. Page numbers might not be rendered correctly or at all.")
            font = None

        for i, img_path in enumerate(self._current_image_paths_for_redisplay):
            try:
                original_pil_image = Image.open(img_path)

                page_image = Image.new('RGB', page_size_px, (255, 255, 255))
                draw = ImageDraw.Draw(page_image)

                img_to_draw = original_pil_image.copy()
                if fit_to_page:
                    img_to_draw.thumbnail((drawable_width, drawable_height), Image.Resampling.LANCZOS)

                img_w, img_h = img_to_draw.size
                pos_x = PAGE_MARGIN + (drawable_width - img_w) // 2
                pos_y = PAGE_MARGIN + (drawable_height - img_h) // 2

                if img_to_draw.mode == 'RGBA':
                    page_image.paste(img_to_draw, (pos_x, pos_y), img_to_draw)
                else:
                    page_image.paste(img_to_draw, (pos_x, pos_y))


                if add_page_numbers and font:
                    page_num_text = f"Page {i + 1} of {total_pages}"
                    try:
                        if hasattr(draw, 'textbbox'): # More modern Pillow
                             bbox = draw.textbbox((0,0), page_num_text, font=font)
                             text_width = bbox[2] - bbox[0]
                        else: # Older Pillow
                             text_width = draw.textlength(page_num_text, font=font)

                        text_x = page_size_px[0] - text_width - PAGE_MARGIN
                        text_y = page_size_px[1] - PAGE_MARGIN - (font.getbbox("A")[3] if hasattr(font, "getbbox") else 20) # Approx height
                        draw.text((text_x, text_y), page_num_text, fill="black", font=font)
                    except Exception as font_e:
                        print(f"Error drawing page number for {img_path}: {font_e}")

                processed_page_images.append(page_image)

            except Exception as e:
                print(f"Skipping image {img_path} for PDF export due to error: {e}")

        if not processed_page_images:
            messagebox.showerror("Export Error", "No images could be successfully processed for PDF export.", parent=self.top)
            return

        try:
            cover_page = processed_page_images[0]
            if len(processed_page_images) > 1:
                cover_page.save(
                    pdf_filepath,
                    save_all=True,
                    append_images=processed_page_images[1:],
                    resolution=100.0
                )
            else:
                 cover_page.save(
                    pdf_filepath,
                    resolution=100.0
                )
            messagebox.showinfo("Export Successful", f"Images successfully exported to:\n{pdf_filepath}", parent=self.top)
        except Exception as e:
            messagebox.showerror("PDF Export Error", f"Could not save PDF: {e}", parent=self.top)
