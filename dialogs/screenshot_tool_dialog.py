import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw, UnidentifiedImageError, ImageFilter, ImageFont
import os
import time
import math

# Assuming screenshot_utils.py is in the same directory or accessible
# from .screenshot_utils import capture_screen_region, capture_full_screen, RegionSelector
# For now, this dialog will receive an image, so direct import of capture utils not immediately needed here.

class ScreenshotToolDialog(tk.Toplevel):
    def __init__(self, parent_editor_or_root, captured_image: Image.Image):
        # Determine the actual root Tk instance for the Toplevel window
        if hasattr(parent_editor_or_root, 'root'): # If TextEditor instance is passed
            actual_root = parent_editor_or_root.root
        else: # If a tk.Tk() or tk.Toplevel() instance is passed (e.g. for testing)
            actual_root = parent_editor_or_root

        super().__init__(actual_root)

        self.parent_editor = parent_editor_or_root # Could be TextEditor or a mock for testing
        self.original_image = captured_image
        _image_copy = captured_image.copy() # Work on a copy for annotations
        if _image_copy.mode != "RGBA":
            _image_copy = _image_copy.convert("RGBA")
        self.current_image_pil = _image_copy
        self.current_image_tk = None # Will hold ImageTk.PhotoImage

        # Annotation state variables
        self.current_tool = None # e.g., "rectangle", "line", "text"
        self.current_draw_color = "red"
        self.current_line_thickness = 2
        self.temp_drawing_item_id = None # For previewing shapes during drag
        self.draw_start_x = None
        self.draw_start_y = None
        self.active_tool_button = None


        self.title("Screenshot Annotation Tool")
        self.transient(actual_root)
        # self.grab_set() # Make modal if desired, consider user flow
        # Adjust geometry based on image size + sidebar width + some padding
        sidebar_width_estimate = 220
        padding_estimate = 50
        dialog_width = max(800, self.current_image_pil.width + sidebar_width_estimate + padding_estimate)
        dialog_height = max(600, self.current_image_pil.height + padding_estimate + 50) # Extra 50 for buttons below canvas if any

        # Ensure it doesn't exceed screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        dialog_width = min(dialog_width, screen_width - 50)
        dialog_height = min(dialog_height, screen_height - 50)

        self.geometry(f"{dialog_width}x{dialog_height}")
        self.resizable(True, True)
        self.minsize(600, 400)

        # --- Main layout ---
        main_frame = ttk.Frame(self, padding=5)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1) # Canvas column
        main_frame.rowconfigure(0, weight=1)    # Canvas row

        # --- Sidebar for Tools & Actions ---
        self.sidebar_frame = ttk.Frame(main_frame, width=220, relief=tk.FLAT)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 5))
        self.sidebar_frame.pack_propagate(False)

        # --- Canvas for Image Display and Annotation ---
        canvas_container_frame = ttk.Frame(main_frame) # Container to manage canvas and scrollbars
        canvas_container_frame.grid(row=0, column=1, sticky="nsew")
        canvas_container_frame.rowconfigure(0, weight=1)
        canvas_container_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_container_frame, bg="lightgrey", highlightthickness=0)
        # Scrollbars for canvas (if image is larger than view)
        hbar = ttk.Scrollbar(canvas_container_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = ttk.Scrollbar(canvas_container_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        hbar.grid(row=1, column=0, sticky="ew")
        vbar.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self._display_image_on_canvas()
        # Canvas scrollregion is set in _display_image_on_canvas

        # --- Populate Sidebar ---
        self._setup_annotation_tools_ui()
        self._setup_output_actions_ui()

        # Bindings for drawing/annotation
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self):
        shortcuts = {
            'r': "rectangle", 'R': "rectangle",
            'l': "line",      'L': "line",
            'e': "ellipse",   'E': "ellipse",
            'a': "arrow",     'A': "arrow",
            'c': "crop",      'C': "crop",
            'p': "pixelate",  'P': "pixelate",
            'h': "highlight", 'H': "highlight",
            't': "text",      'T': "text",
            'b': "blur",      'B': "blur",
        }
        for key, tool_name in shortcuts.items():
            self.bind(f"<KeyPress-{key}>", lambda event, tn=tool_name: self._handle_shortcut(tn))

    def _handle_shortcut(self, tool_name):
        # Ensure focus is not on an input field if we had one (e.g. text input for text tool itself)
        # For now, this is simple. If there were text entry widgets in the dialog,
        # we might want to check `self.focus_get()` before switching tools.
        self._set_tool(tool_name)


    def _set_tool(self, tool_name):
        # print(f"Setting tool to: {tool_name}") # Debugging
        # print(f"Previous active button: {self.active_tool_button}") # Debugging
        previous_active_button_obj = self.active_tool_button

        self.current_tool = tool_name

        new_active_button_obj = None
        if tool_name == "rectangle" and hasattr(self, 'rect_button'):
            new_active_button_obj = self.rect_button
        elif tool_name == "line" and hasattr(self, 'line_button'):
            new_active_button_obj = self.line_button
        elif tool_name == "ellipse" and hasattr(self, 'ellipse_button'):
            new_active_button_obj = self.ellipse_button
        elif tool_name == "arrow" and hasattr(self, 'arrow_button'):
            new_active_button_obj = self.arrow_button
        elif tool_name == "crop" and hasattr(self, 'crop_button'):
            new_active_button_obj = self.crop_button
        elif tool_name == "pixelate" and hasattr(self, 'pixelate_button'):
            new_active_button_obj = self.pixelate_button
        elif tool_name == "highlight" and hasattr(self, 'highlight_button'):
            new_active_button_obj = self.highlight_button
        elif tool_name == "text" and hasattr(self, 'text_button'):
            new_active_button_obj = self.text_button
        elif tool_name == "blur" and hasattr(self, 'blur_button'):
            new_active_button_obj = self.blur_button
        # Add other tools here...

        # First, deactivate the previous button IF it's different from the new one
        if previous_active_button_obj and previous_active_button_obj != new_active_button_obj:
            previous_active_button_obj.state(['!pressed'])
            # print(f"Deactivated button: {previous_active_button_obj}") # Debugging

        # Now, activate the new button if it exists
        if new_active_button_obj:
            new_active_button_obj.state(['pressed'])
            self.active_tool_button = new_active_button_obj # Update the instance variable
            # print(f"Activated button: {self.active_tool_button}") # Debugging
        else:
            # If no new button is found (e.g. NYI tool or error),
            # ensure any previously active button (if not already handled by the above) is deselected.
            if previous_active_button_obj: # Redundant if previous_active_button_obj != new_active_button_obj was true
                 previous_active_button_obj.state(['!pressed'])
            self.active_tool_button = None # No tool button is active
            # print(f"Warning: No button found for tool {tool_name} or tool is None. Active button set to None.")


    def _display_image_on_canvas(self):
        self.canvas.delete("all") # Clear previous content
        if self.current_image_pil:
            self.current_image_tk = ImageTk.PhotoImage(self.current_image_pil)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image_tk, tags="background_image")
            self.canvas.config(scrollregion=(0, 0, self.current_image_pil.width, self.current_image_pil.height))

            # Dynamic window resizing based on image content (optional, can be complex)
            # For simplicity, initial geometry is set in __init__
            # If enabling dynamic resize, ensure it doesn't conflict with user resizing.
            # new_width = max(self.winfo_width(), min(self.current_image_pil.width + self.sidebar_frame.winfo_width() + 40, self.winfo_screenwidth() - 100))
            # new_height = max(self.winfo_height(), min(self.current_image_pil.height + 80, self.winfo_screenheight() - 100))
            # self.geometry(f"{new_width}x{new_height}")


    def _setup_annotation_tools_ui(self):
        tools_group = ttk.LabelFrame(self.sidebar_frame, text="Annotation Tools", padding=10)
        tools_group.pack(fill=tk.X, pady=5, padx=5)

        self.rect_button = ttk.Button(tools_group, text="Rect (R)", command=lambda: self._set_tool("rectangle"))
        self.rect_button.pack(fill=tk.X, pady=2)

        self.line_button = ttk.Button(tools_group, text="Line (L)", command=lambda: self._set_tool("line"))
        self.line_button.pack(fill=tk.X, pady=2)

        self.ellipse_button = ttk.Button(tools_group, text="Ellipse (E)", command=lambda: self._set_tool("ellipse"))
        self.ellipse_button.pack(fill=tk.X, pady=2)

        self.arrow_button = ttk.Button(tools_group, text="Arrow (A)", command=lambda: self._set_tool("arrow"))
        self.arrow_button.pack(fill=tk.X, pady=2)

        self.crop_button = ttk.Button(tools_group, text="Crop (C)", command=lambda: self._set_tool("crop"))
        self.crop_button.pack(fill=tk.X, pady=2)

        self.pixelate_button = ttk.Button(tools_group, text="Pixelate (P)", command=lambda: self._set_tool("pixelate"))
        self.pixelate_button.pack(fill=tk.X, pady=2)

        self.highlight_button = ttk.Button(tools_group, text="Highlight (H)", command=lambda: self._set_tool("highlight"))
        self.highlight_button.pack(fill=tk.X, pady=2)

        self.text_button = ttk.Button(tools_group, text="Text (T)", command=lambda: self._set_tool("text"))
        self.text_button.pack(fill=tk.X, pady=2)

        self.blur_button = ttk.Button(tools_group, text="Blur (B)", command=lambda: self._set_tool("blur")) # New Blur button
        self.blur_button.pack(fill=tk.X, pady=2)

        ttk.Separator(tools_group, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Color Picker
        color_frame = ttk.Frame(tools_group)
        color_frame.pack(fill=tk.X, pady=3)
        ttk.Label(color_frame, text="Color:").pack(side=tk.LEFT, padx=(0,3))
        self.current_color_preview = tk.Frame(color_frame, width=20, height=20, bg=self.current_draw_color, relief=tk.SUNKEN, borderwidth=1)
        self.current_color_preview.pack(side=tk.LEFT, padx=(0,5))
        self.current_color_preview.bind("<Button-1>", self._pick_draw_color)

        # Line Thickness
        thickness_frame = ttk.Frame(tools_group)
        thickness_frame.pack(fill=tk.X, pady=3)
        ttk.Label(thickness_frame, text="Thickness:").pack(side=tk.LEFT, padx=(0,3))
        self.thickness_var = tk.IntVar(value=self.current_line_thickness)
        thickness_scale = ttk.Scale(thickness_frame, from_=1, to=20, orient=tk.HORIZONTAL, variable=self.thickness_var, command=self._update_thickness_from_scale)
        thickness_scale.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.thickness_label = ttk.Label(thickness_frame, text=str(self.current_line_thickness), width=2)
        self.thickness_label.pack(side=tk.LEFT)

    def _pick_draw_color(self, event=None):
        color_code = colorchooser.askcolor(title="Choose drawing color", initialcolor=self.current_draw_color, parent=self)
        if color_code and color_code[1]: # color_code[1] is the hex string
            self.current_draw_color = color_code[1]
            self.current_color_preview.config(bg=self.current_draw_color)

    def _update_thickness_from_scale(self, value):
        self.current_line_thickness = int(float(value))
        self.thickness_label.config(text=str(self.current_line_thickness))


    def _on_canvas_press(self, event):
        if self.current_tool == "rectangle":
            self.draw_start_x = self.canvas.canvasx(event.x) # Convert window coord to canvas coord
            self.draw_start_y = self.canvas.canvasy(event.y)
            # Create a temporary rectangle for visual feedback during drag
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_rectangle(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                outline=self.current_draw_color,
                width=self.current_line_thickness,
                dash=(4,2), # Dashed line for preview
                tags="temp_shape"
            )
        elif self.current_tool == "blur": # Blur selection is like drawing a rectangle
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_rectangle(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                outline=self.current_draw_color,
                width=self.current_line_thickness, # Can use standard thickness for temp rect
                dash=(4,2),
                tags="temp_shape"
            )
        elif self.current_tool == "blur": # Blur selection is like drawing a rectangle
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_rectangle(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                outline=self.current_draw_color,
                width=self.current_line_thickness,
                dash=(4,2),
                tags="temp_shape"
            )
        elif self.current_tool == "blur": # Blur selection is like drawing a rectangle
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_rectangle(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                outline=self.current_draw_color, # Or a distinct color
                width=self.current_line_thickness,
                dash=(4,2),
                tags="temp_shape"
            )
        elif self.current_tool == "line":
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_line(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y, # Start and end at same point initially
                fill=self.current_draw_color,
                width=self.current_line_thickness,
                dash=(4,2),
                tags="temp_shape"
            )
        elif self.current_tool == "arrow": # Same as line for press
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_line(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                fill=self.current_draw_color,
                width=self.current_line_thickness,
                dash=(4,2),
                tags="temp_shape"
            )
        elif self.current_tool == "crop": # Crop selection is like drawing a rectangle
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_rectangle(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                outline=self.current_draw_color, # Or a distinct color for crop selection
                width=self.current_line_thickness,
                dash=(4,2),
                tags="temp_shape"
            )
        elif self.current_tool == "pixelate": # Pixelate selection is like drawing a rectangle
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_rectangle(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                outline=self.current_draw_color, # Or a distinct color
                width=self.current_line_thickness,
                dash=(4,2),
                tags="temp_shape"
            )
        elif self.current_tool == "highlight": # Highlight selection is like drawing a rectangle
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            self.temp_drawing_item_id = self.canvas.create_rectangle(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                outline=self.current_draw_color, # Temporary outline
                width=1, # Thin temporary outline
                dash=(4,2),
                tags="temp_shape"
            )
        elif self.current_tool == "text":
            # For text, the press location is where the text will be anchored.
            # No drag, no temporary shape.
            text_x = self.canvas.canvasx(event.x)
            text_y = self.canvas.canvasy(event.y)

            user_text = simpledialog.askstring("Input Text", "Enter text to add:", parent=self)

            if user_text: # If user entered text and didn't cancel
                try:
                    draw = ImageDraw.Draw(self.current_image_pil)
                    # Font handling: Use default PIL font or try to load a system font.
                    try:
                        # Attempt to load a common system font with a reasonable size.
                        # This path might need adjustment for different OS or a bundled font.
                        # For more robust font handling, consider bundling a font or using a fontconfig library.
                        font_size = self.current_line_thickness * 6 # Scale font size with line thickness setting
                        font_size = max(10, font_size) # Minimum font size
                        # Common font names, PIL will search some default paths.
                        # Fallback if specific fonts aren't found.
                        font_names = ["arial.ttf", " DejaVuSans.ttf", " LiberationSans-Regular.ttf", "Geneva.ttf", "Helvetica.ttf"]
                        pil_font = None
                        for name in font_names:
                            try:
                                pil_font = ImageFont.truetype(name, font_size)
                                break
                            except IOError:
                                continue
                        if not pil_font: # Fallback to default bitmap font if no truetype found
                            pil_font = ImageFont.load_default()
                            messagebox.showwarning("Font Warning", "Default system font not found. Using basic font.", parent=self)

                    except Exception as font_e:
                        print(f"Font loading error: {font_e}")
                        pil_font = ImageFont.load_default() # Fallback
                        messagebox.showerror("Font Error", f"Could not load preferred font: {font_e}. Using basic font.", parent=self)

                    draw.text(
                        (text_x, text_y),
                        user_text,
                        fill=self.current_draw_color,
                        font=pil_font
                    )
                    self._display_image_on_canvas()
                except Exception as e:
                    messagebox.showerror("Text Error", f"Could not draw text: {e}", parent=self)
            # Reset tool state variables as no drag/release cycle for text
            self.draw_start_x, self.draw_start_y = None, None
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

        elif self.current_tool == "ellipse":
            self.draw_start_x = self.canvas.canvasx(event.x)
            self.draw_start_y = self.canvas.canvasy(event.y)
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
            # Use create_oval for ellipse preview on canvas
            self.temp_drawing_item_id = self.canvas.create_oval(
                self.draw_start_x, self.draw_start_y,
                self.draw_start_x, self.draw_start_y,
                outline=self.current_draw_color,
                width=self.current_line_thickness,
                dash=(4,2),
                tags="temp_shape"
            )
        # Add other tool press logic here

    def _on_canvas_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)

        if self.draw_start_x is None: # Should not happen if drag started after press
            return

        if self.current_tool in ["rectangle", "ellipse", "crop", "pixelate", "highlight", "blur"]:
            self.canvas.coords(self.temp_drawing_item_id, self.draw_start_x, self.draw_start_y, cur_x, cur_y)
        elif self.current_tool == "line" or self.current_tool == "arrow": # Arrow drag is same as line
            self.canvas.coords(self.temp_drawing_item_id, self.draw_start_x, self.draw_start_y, cur_x, cur_y)
        # Add other tool drag logic here

    def _on_canvas_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        if self.draw_start_x is None: # Should not happen if release is part of a draw action
            return

        if self.current_tool == "rectangle" and self.draw_start_x is not None: # Redundant check of draw_start_x
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)

            # Ensure x1 < x2 and y1 < y2 for drawing on PIL image
            x1, y1 = min(self.draw_start_x, end_x), min(self.draw_start_y, end_y)
            x2, y2 = max(self.draw_start_x, end_x), max(self.draw_start_y, end_y)

            if x1 == x2 or y1 == y2: # Not a valid rectangle (just a line or point)
                self.draw_start_x, self.draw_start_y = None, None
                return

            try:
                draw = ImageDraw.Draw(self.current_image_pil)
                draw.rectangle(
                    [x1, y1, x2, y2],
                    outline=self.current_draw_color,
                    width=self.current_line_thickness
                )
                self._display_image_on_canvas() # Refresh canvas with new drawing
            except Exception as e:
                messagebox.showerror("Annotation Error", f"Could not draw rectangle: {e}", parent=self)

            self.draw_start_x, self.draw_start_y = None, None # Reset for next shape

        elif self.current_tool == "line" and self.draw_start_x is not None:
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

            # For a line, we don't need to normalize x1,y1 with x2,y2
            # A line from (x1,y1) to (x2,y2) is fine.
            x1, y1 = self.draw_start_x, self.draw_start_y
            # end_x, end_y are already defined at the start of the function

            if x1 == end_x and y1 == end_y: # Not a valid line (just a point)
                self.draw_start_x, self.draw_start_y = None, None
                return

            try:
                draw = ImageDraw.Draw(self.current_image_pil)
                draw.line(
                    [(x1, y1), (end_x, end_y)],
                    fill=self.current_draw_color, # Note: PIL uses 'fill' for line color
                    width=self.current_line_thickness
                )
                self._display_image_on_canvas() # Refresh canvas
            except Exception as e:
                messagebox.showerror("Annotation Error", f"Could not draw line: {e}", parent=self)

            self.draw_start_x, self.draw_start_y = None, None # Reset

        elif self.current_tool == "ellipse": # No need to check self.draw_start_x here, already checked above
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

            # Ensure x1 < x2 and y1 < y2 for PIL ellipse drawing
            x1, y1 = min(self.draw_start_x, end_x), min(self.draw_start_y, end_y)
            x2, y2 = max(self.draw_start_x, end_x), max(self.draw_start_y, end_y)

            if x1 == x2 or y1 == y2: # Not a valid bounding box (results in line or point)
                self.draw_start_x, self.draw_start_y = None, None
                return

            try:
                draw = ImageDraw.Draw(self.current_image_pil)
                draw.ellipse( # PIL draws ellipse within the given bounding box
                    [x1, y1, x2, y2],
                    outline=self.current_draw_color,
                    width=self.current_line_thickness
                )
                self._display_image_on_canvas() # Refresh canvas
            except Exception as e:
                messagebox.showerror("Annotation Error", f"Could not draw ellipse: {e}", parent=self)

            self.draw_start_x, self.draw_start_y = None, None # Reset

        elif self.current_tool == "arrow":
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

            x1, y1 = self.draw_start_x, self.draw_start_y
            # end_x, end_y are already defined

            if x1 == end_x and y1 == end_y: # Not a valid line for an arrow
                self.draw_start_x, self.draw_start_y = None, None
                return

            try:
                draw = ImageDraw.Draw(self.current_image_pil)
                # Draw the main line (shaft)
                draw.line(
                    [(x1, y1), (end_x, end_y)],
                    fill=self.current_draw_color,
                    width=self.current_line_thickness
                )

                # Calculate and draw arrowhead
                # Arrowhead properties
                arrow_length = self.current_line_thickness * 5  # Length of the arrowhead lines
                arrow_angle = math.pi / 6  # Angle of arrowhead lines relative to the main line (30 degrees)

                # Angle of the main line
                line_angle = math.atan2(y1 - end_y, x1 - end_x) # Note: y1-end_y, x1-end_x to point from end towards start for arrowhead at end_x, end_y

                # Calculate points for the two lines of the arrowhead
                # Tip of the arrowhead is at (end_x, end_y)
                # Point 1
                p1_x = end_x + arrow_length * math.cos(line_angle + arrow_angle)
                p1_y = end_y + arrow_length * math.sin(line_angle + arrow_angle)
                # Point 2
                p2_x = end_x + arrow_length * math.cos(line_angle - arrow_angle)
                p2_y = end_y + arrow_length * math.sin(line_angle - arrow_angle)

                draw.line([(end_x, end_y), (p1_x, p1_y)], fill=self.current_draw_color, width=self.current_line_thickness)
                draw.line([(end_x, end_y), (p2_x, p2_y)], fill=self.current_draw_color, width=self.current_line_thickness)

                self._display_image_on_canvas() # Refresh canvas
            except Exception as e:
                messagebox.showerror("Annotation Error", f"Could not draw arrow: {e}", parent=self)

            self.draw_start_x, self.draw_start_y = None, None # Reset

        elif self.current_tool == "crop":
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

            # Ensure x1 < x2 and y1 < y2 for the crop box
            x1, y1 = min(self.draw_start_x, end_x), min(self.draw_start_y, end_y)
            x2, y2 = max(self.draw_start_x, end_x), max(self.draw_start_y, end_y)

            # Ensure the crop box has a valid area and is within image bounds (implicitly handled by PIL's crop)
            # However, coordinates must be integers for PIL crop.
            x1, y1, x2, y2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))

            # Prevent zero-area crops or crops outside image (though PIL handles latter by returning empty)
            if x1 >= x2 or y1 >= y2:
                messagebox.showwarning("Crop Error", "Invalid crop area (zero width or height).", parent=self)
                self.draw_start_x, self.draw_start_y = None, None
                return

            # Ensure crop coordinates are within the current image dimensions before cropping
            # This prevents errors if the selection is somehow outside the current image
            img_width, img_height = self.current_image_pil.size
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(img_width, x2)
            y2 = min(img_height, y2)

            if x1 >= x2 or y1 >= y2: # Check again after clamping
                messagebox.showwarning("Crop Error", "Crop area is outside the image or invalid.", parent=self)
                self.draw_start_x, self.draw_start_y = None, None
                return

            crop_box = (x1, y1, x2, y2)

            try:
                cropped_image = self.current_image_pil.crop(crop_box)
                self.current_image_pil = cropped_image
                self._display_image_on_canvas() # This will update canvas scrollregion

                # Optionally, reset the tool so the user doesn't accidentally crop again
                # self._set_tool(None) # Or set to a default selection tool if one exists
                # For now, leave tool active for potential sequential crops if desired.

            except Exception as e:
                messagebox.showerror("Crop Error", f"Could not crop image: {e}", parent=self)

            self.draw_start_x, self.draw_start_y = None, None # Reset

        elif self.current_tool == "pixelate":
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

            x1, y1 = min(self.draw_start_x, end_x), min(self.draw_start_y, end_y)
            x2, y2 = max(self.draw_start_x, end_x), max(self.draw_start_y, end_y)

            x1, y1, x2, y2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))

            if x1 >= x2 or y1 >= y2: # Zero area
                self.draw_start_x, self.draw_start_y = None, None
                return

            # Ensure coordinates are within image bounds
            img_width, img_height = self.current_image_pil.size
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(img_width, x2)
            y2 = min(img_height, y2)

            if x1 >= x2 or y1 >= y2: # Check again after clamping
                self.draw_start_x, self.draw_start_y = None, None
                return

            pixelate_box = (x1, y1, x2, y2)

            try:
                region_to_pixelate = self.current_image_pil.crop(pixelate_box)

                # Pixelation effect:
                # Determine pixelation factor (e.g., 16x16 blocks)
                # Lower factor = more pixelation
                pixel_size = 16 # Size of one 'pixel' block

                # Original size of the region
                orig_w, orig_h = region_to_pixelate.size

                if orig_w == 0 or orig_h == 0: # Should be caught by earlier checks
                    self.draw_start_x, self.draw_start_y = None, None
                    return

                # Size down, ensuring at least 1x1 pixel
                small_w = max(1, orig_w // pixel_size)
                small_h = max(1, orig_h // pixel_size)

                # Resize down to small size (pixelated)
                small_img = region_to_pixelate.resize((small_w, small_h), Image.Resampling.NEAREST)

                # Resize back up to original region size
                pixelated_region = small_img.resize((orig_w, orig_h), Image.Resampling.NEAREST)

                # Paste the pixelated region back into the main image
                self.current_image_pil.paste(pixelated_region, pixelate_box)

                self._display_image_on_canvas()
            except Exception as e:
                messagebox.showerror("Pixelate Error", f"Could not pixelate region: {e}", parent=self)

            self.draw_start_x, self.draw_start_y = None, None # Reset

        elif self.current_tool == "highlight":
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

            x1_orig, y1_orig = min(self.draw_start_x, end_x), min(self.draw_start_y, end_y)
            x2_orig, y2_orig = max(self.draw_start_x, end_x), max(self.draw_start_y, end_y)

            # Using float for precision before int conversion for the box, though not strictly necessary for highlight.
            x1f, y1f, x2f, y2f = float(x1_orig), float(y1_orig), float(x2_orig), float(y2_orig)


            if x1f >= x2f or y1f >= y2f: # Zero area
                self.draw_start_x, self.draw_start_y = None, None
                return

            # Clamp coordinates to image bounds
            img_width, img_height = self.current_image_pil.size
            x1_clamped = max(0, x1f)
            y1_clamped = max(0, y1f)
            x2_clamped = min(img_width, x2f)
            y2_clamped = min(img_height, y2f)

            if x1_clamped >= x2_clamped or y1_clamped >= y2_clamped: # Check again after clamping
                self.draw_start_x, self.draw_start_y = None, None
                return

            highlight_box = (int(round(x1_clamped)), int(round(y1_clamped)), int(round(x2_clamped)), int(round(y2_clamped)))

            highlight_color_rgba = (255, 255, 0, 100) # Yellow, ~40% opacity (alpha 0-255)

            try:
                # Ensure current image is RGBA (done in __init__)
                # Create a temporary overlay for the highlight
                overlay = Image.new("RGBA", self.current_image_pil.size, (0,0,0,0)) # Fully transparent
                draw_on_overlay = ImageDraw.Draw(overlay)

                # Draw the semi-transparent rectangle on this overlay
                draw_on_overlay.rectangle(highlight_box, fill=highlight_color_rgba, outline=None)

                # Alpha composite the overlay (with the highlight) onto the current image
                self.current_image_pil = Image.alpha_composite(self.current_image_pil, overlay)

                self._display_image_on_canvas()
            except Exception as e:
                messagebox.showerror("Highlight Error", f"Could not apply highlight: {e}", parent=self)

            self.draw_start_x, self.draw_start_y = None, None # Reset

        elif self.current_tool == "blur":
            if self.temp_drawing_item_id:
                self.canvas.delete(self.temp_drawing_item_id)
                self.temp_drawing_item_id = None

            x1, y1 = min(self.draw_start_x, end_x), min(self.draw_start_y, end_y)
            x2, y2 = max(self.draw_start_x, end_x), max(self.draw_start_y, end_y)

            x1, y1, x2, y2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))

            if x1 >= x2 or y1 >= y2: # Zero area
                self.draw_start_x, self.draw_start_y = None, None
                return

            img_width, img_height = self.current_image_pil.size
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(img_width, x2)
            y2 = min(img_height, y2)

            if x1 >= x2 or y1 >= y2: # Check again after clamping
                self.draw_start_x, self.draw_start_y = None, None
                return

            blur_box = (x1, y1, x2, y2)

            try:
                region_to_blur = self.current_image_pil.crop(blur_box)

                # Blur effect
                blur_radius = 5 # Adjust for more or less blur; can be dynamic
                # Example: blur_radius = self.current_line_thickness
                # (ensure it's an appropriate value, e.g. thickness / 2, min 1)

                blurred_region = region_to_blur.filter(ImageFilter.GaussianBlur(radius=blur_radius))

                self.current_image_pil.paste(blurred_region, blur_box)
                self._display_image_on_canvas()
            except Exception as e:
                messagebox.showerror("Blur Error", f"Could not blur region: {e}", parent=self)

            self.draw_start_x, self.draw_start_y = None, None # Reset


        # Add other tool release logic here


    def _setup_output_actions_ui(self):
        actions_group = ttk.LabelFrame(self.sidebar_frame, text="Output", padding=10)
        actions_group.pack(fill=tk.X, pady=5, padx=5, side=tk.BOTTOM) # Place at bottom of sidebar

        ttk.Button(actions_group, text="Save as PNG...", command=self._save_as_png).pack(fill=tk.X, pady=2)
        ttk.Button(actions_group, text="Copy to Clipboard", command=self._copy_to_clipboard).pack(fill=tk.X, pady=2)
        if hasattr(self.parent_editor, 'get_current_tab'): # Only show if part of TextEditor
             ttk.Button(actions_group, text="Insert into Editor", command=self._insert_into_editor).pack(fill=tk.X, pady=2)
        ttk.Button(actions_group, text="Done / Close", command=self.destroy).pack(fill=tk.X, pady=2)

    def _save_as_png(self):
        if not self.current_image_pil:
            messagebox.showwarning("No Image", "There is no image to save.", parent=self)
            return

        filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Save Screenshot As...",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )

        if filepath:
            try:
                self.current_image_pil.save(filepath, "PNG")
                messagebox.showinfo("Saved", f"Image saved successfully to:\n{filepath}", parent=self)
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save image: {e}", parent=self)

    def _copy_to_clipboard(self):
        # This is a known difficult problem for cross-platform純 Python + Tkinter + PIL.
        # Tkinter's clipboard capabilities for images are limited, especially without specific OS tools.
        # For a robust solution, a library like 'pyperclip' (for text) or more complex OS-specific
        # calls or a dedicated clipboard library that handles images (e.g., PyQt's QClipboard) would be needed.
        #
        # Simplest attempt: Try to put image path or a message.
        # A common workaround is to save to a temp file and copy the *file* (not image data)
        # or use platform specific tools.
        #
        # Given the constraints, this will be a placeholder or a very basic attempt.
        # Let's try using the clipboard_append method of Tkinter, but it's mainly for text.
        # For images, it's non-trivial.

        # For now, show a message indicating limitation.
        # A more advanced approach might involve:
        # 1. Saving the image to a temporary file.
        # 2. Using an external clipboard utility (like xclip on Linux, clip on Windows)
        #    to copy the image file or its content. This is hard to make cross-platform easily.
        # 3. For Windows, win32clipboard can be used. For macOS, pbcopy/pbpaste.

        # Simplistic approach for now:
        # Try to set image data to clipboard if possible (usually not directly for PIL Images with Tkinter)
        # Or, offer to save it and tell user to copy manually.
        # self.clipboard_clear() # Clear clipboard
        # self.clipboard_append(self.current_image_pil.tobytes()) # This is unlikely to work as expected.

        # Fallback: Inform user.
        messagebox.showinfo(
            "Copy to Clipboard",
            "Directly copying images to the clipboard is complex and not fully implemented.\n"
            "Please use 'Save as PNG...' and then copy the file manually.",
            parent=self
        )
        # TODO: Research a more robust cross-platform image clipboard solution if required.
        # One potential library: `Pillow` itself has `ImageGrab.grabclipboard()` but not a setter.
        # `pyperclip` is for text.
        # For a real app, might need to bundle `clip.exe` or use `xclip`/`wl-copy`.

    def _insert_into_editor(self):
        # This function's implementation depends heavily on the parent_editor's capabilities.
        # Assuming parent_editor has a method like `insert_image_path(path)` or `insert_image_object(image_obj)`
        if not self.current_image_pil:
            messagebox.showwarning("No Image", "There is no image to insert.", parent=self)
            return

        if hasattr(self.parent_editor, "insert_image_dialog"): # hypothetical method
            # Best case: parent editor has a method to handle a PIL image object or a path
            # For example, it might save to a temp file itself and manage it.
            try:
                # Option 1: Pass the PIL image object directly if the editor supports it
                # self.parent_editor.insert_image_dialog(self.current_image_pil)

                # Option 2: Save to a temporary file and pass the path
                import time
                temp_dir = os.path.join(os.path.expanduser("~"), ".temp_screenshots")
                os.makedirs(temp_dir, exist_ok=True)
                # Use timestamp for a more unique filename
                temp_file_path = os.path.join(temp_dir, f"screenshot_{int(time.time() * 1000)}.png")

                self.current_image_pil.save(temp_file_path, "PNG")

                # Call a method on the parent editor to insert using the path
                # This method name "insert_image_dialog" is a placeholder for whatever actual method
                # the parent TextEditor class might provide for inserting images.
                # It might be `insert_image_from_path` or similar.
                if hasattr(self.parent_editor, 'insert_image_from_path'):
                    self.parent_editor.insert_image_from_path(temp_file_path)
                    # Optionally, inform the user, though the editor itself might do that.
                    # messagebox.showinfo("Inserted", "Image passed to editor.", parent=self)
                elif hasattr(self.parent_editor, 'receive_image_path_for_insertion'): # another hypothetical
                     self.parent_editor.receive_image_path_for_insertion(temp_file_path)
                else:
                    messagebox.showwarning("Not Implemented",
                                           "The parent editor does not have a recognized method to insert this image by path.",
                                           parent=self)
                # Clean up the temp file if the editor couldn't handle it
                try:
                    os.remove(temp_file_path)
                    print(f"Cleaned up temporary file: {temp_file_path}")
                except OSError as e_remove:
                    print(f"Error removing temporary file {temp_file_path}: {e_remove}")
                return # Stop further processing for this path

            # If the editor is expected to copy the file, the temp file might be removable.
            # If the editor uses the path directly, it should not be removed here.
            # Current assumption: editor copies or manages it, so we don't delete it here.
            # Consider adding a flag or specific editor method to indicate if temp file can be deleted.

            except AttributeError:
                 messagebox.showerror("Error", "Parent editor is missing an expected attribute or method for image insertion.", parent=self)
            except Exception as e:
                messagebox.showerror("Insert Error", f"Could not insert image into editor: {e}", parent=self)
        else:
            messagebox.showwarning("Not Available",
                                   "Image insertion into the editor is not available or not configured for this parent.",
                                   parent=self)


# If running this file directly, adjust import for local testing:
if __name__ == '__main__':
    from screenshot_utils import RegionSelector, capture_screen_region, get_available_monitors, ask_monitor_selection_dialog, capture_full_screen
else: # Otherwise, use relative import when used as part of a package
    from .screenshot_utils import RegionSelector, capture_screen_region, get_available_monitors, ask_monitor_selection_dialog, capture_full_screen


# Basic test for the dialog (run this file directly)
if __name__ == '__main__':
    root = tk.Tk()
    # Keep root hidden initially, RegionSelector will manage showing/hiding it.
    # root.withdraw() # RegionSelector now handles this.

    captured_image = None
    bbox = None

    # Determine mode (for testing different paths)
    # To test region selection: mode = "region"
    # To test full screen monitor selection: mode = "fullscreen_monitor_select"
    mode = "fullscreen_monitor_select" # Default test mode for this iteration

    if mode == "region":
        # Step 1: Use RegionSelector to get a bounding box
        try:
            print("Starting region selection...")
            selector = RegionSelector(root) # Pass the main root window
            bbox = selector.select_region()
        except tk.TclError as e:
            if "display name" in str(e):
                print(f"Error: Cannot run Tkinter GUI for RegionSelector in headless environment: {e}")
            else: raise
            bbox = None
        except Exception as e:
            print(f"An error occurred during region selection: {e}")
            bbox = None

    if mode == "region" and bbox: # If region selection was done and successful
        print(f"Selected BBox: {bbox}")
        # Add a small delay for screen to stabilize after overlay removal, if needed.
        # root.after(100, lambda: continue_with_capture(bbox_val=bbox)) # Does not work well with capture

        # Need to ensure root is deiconified if RegionSelector didn't (e.g. error path)
        # However, RegionSelector is designed to deiconify. If it's not, that's a bug there.
        # If root is still withdrawn, subsequent dialogs might not behave as expected.
        if root.state() == 'withdrawn':
             print("Root window is still withdrawn after region selection. Deiconifying.")
             root.deiconify()
        root.update_idletasks() # Process any pending Tkinter events

        # Introduce a delay before capturing to allow the screen to update
        # and other windows to come to the front if the app was focused.
        # This helps prevent capturing the app's own window.
        # Tkinter's root.after is preferred over time.sleep in a Tkinter app.
        # We need a mechanism to pass the bbox to the capture function after the delay.

        # For this test script, we'll define a nested function to be called by root.after.
        # Note: This structure means subsequent code (dialog display) must also be
        # within or triggered by this delayed function if it depends on `captured_image`.

        def proceed_with_capture_and_dialog(selected_bbox):
            # nonlocal captured_image # Removed: captured_image is in the same scope, not a non-global outer scope.
            print(f"Delay complete. Capturing the selected region: {selected_bbox}")

            try:
                captured_image = capture_screen_region(selected_bbox)
            except Exception as e:
                print(f"Failed to capture screen region with bbox {selected_bbox}: {e}")
                captured_image = None

            if not captured_image:
                 messagebox.showerror("Capture Error", f"Could not capture screen region for bbox: {selected_bbox}.", parent=root if root.state() == 'normal' else None)
                 # If capture fails, ensure root is usable or destroyed cleanly
                 if root.winfo_exists():
                    if root.state() == 'withdrawn': root.deiconify() # Ensure visible for error or next action
                    # Consider if we should destroy root here or let the script end naturally.
                    # For this test, let's allow it to proceed to the end where it might be destroyed.

            # --- This part was originally after the bbox check ---
            if captured_image:
                print(f"Image captured successfully (size: {captured_image.size}). Opening annotation dialog.")
                if root.state() == 'withdrawn': # Ensure root is visible for the dialog
                    print("Deiconifying root window before showing annotation dialog.")
                    root.deiconify()

                class MockEditor: # Definition moved inside for clarity of scope
                    def __init__(self, root_window):
                        self.root = root_window
                    def insert_image_from_path(self, image_path):
                        messagebox.showinfo("Mock Editor", f"Image would be inserted from:\n{image_path}", parent=self.root)
                        print(f"MockEditor: Received image path for insertion: {image_path}")

                mock_app = MockEditor(root)
                dialog = ScreenshotToolDialog(mock_app, captured_image)
                root.wait_window(dialog)
                print("ScreenshotToolDialog closed.")
            elif selected_bbox is not None: # Bbox selected but capture failed
                print("Image capture failed after region selection.")

            # Final cleanup for the root window after everything is done
            if root.winfo_exists():
                print("Destroying main Tk root in delayed function.")
                root.destroy()
            print("Delayed part of test script finished.")
            # --- End of moved part ---

        # Schedule the capture and dialog display after a delay
        capture_delay_ms = 500 # 0.5 second delay, adjust as needed
        print(f"Region selected. Scheduling capture in {capture_delay_ms}ms...")
        root.after(capture_delay_ms, lambda b=bbox: proceed_with_capture_and_dialog(b))

        # The rest of the script (mainloop) will run, and the above function will execute later.
        # We need to ensure the mainloop runs until the delayed action and its consequences are done.
        # The root.destroy() call inside proceed_with_capture_and_dialog will terminate the mainloop.

    # --- Test Path for Full Screen Monitor Selection ---
    elif mode == "fullscreen_monitor_select": # A hypothetical mode to trigger this test path
        print("\n--- Testing Full Screen Monitor Selection and Capture ---")
        # Ensure root is visible to parent the monitor selection dialog
        if root.state() == 'withdrawn': root.deiconify()
        root.update_idletasks()


        available_monitors = get_available_monitors()
        if not available_monitors:
            # In a headless environment, messagebox will fail. Print instead for testing.
            print("ERROR: Monitor Error - Could not detect any monitors using MSS.")
            # messagebox.showerror("Monitor Error", "Could not detect any monitors using MSS.", parent=root)
            if root.winfo_exists():
                print("Destroying root window as no monitors were found.")
                root.destroy()
            # Allow script to exit naturally after this point if mode was "fullscreen_monitor_select"
        else:
            chosen_monitor_idx = ask_monitor_selection_dialog(root, available_monitors)

        if chosen_monitor_idx is not None:
            print(f"User selected monitor index for MSS: {chosen_monitor_idx}")

            # Hide root window before capture
            if root.winfo_exists(): root.withdraw()
            root.update_idletasks()
            # Add a delay before capture to allow window to hide (especially on some OS/WM)
            capture_delay_ms = 300

            def do_full_capture():
                # nonlocal captured_image # REMOVED: captured_image is in the same outer scope
                print(f"Delay complete. Capturing full screen for monitor MSS index: {chosen_monitor_idx}")
                captured_image = capture_full_screen(monitor_number=chosen_monitor_idx)

                # After capture, de-iconify root to show dialog or messages
                if root.winfo_exists(): root.deiconify()
                root.update_idletasks()

                if captured_image:
                    print(f"Full screen image captured (monitor {chosen_monitor_idx}), size: {captured_image.size}. Opening dialog.")
                    # Proceed to show ScreenshotToolDialog (copied from above)
                    class MockEditor:
                        def __init__(self, root_window): self.root = root_window
                        def insert_image_from_path(self, image_path):
                            messagebox.showinfo("Mock Editor", f"Image inserted from: {image_path}", parent=self.root)
                            print(f"MockEditor: Received image path: {image_path}")
                    mock_app = MockEditor(root)
                    dialog = ScreenshotToolDialog(mock_app, captured_image)
                    root.wait_window(dialog)
                    print("ScreenshotToolDialog (full screen) closed.")
                else:
                    messagebox.showerror("Capture Error", f"Failed to capture full screen for monitor {chosen_monitor_idx}.", parent=root)

                if root.winfo_exists(): root.destroy() # Clean up
                print("Full screen capture test finished.")

            root.after(capture_delay_ms, do_full_capture)
            if root.winfo_exists(): root.mainloop() # Start mainloop if we scheduled something

        else: # User cancelled monitor selection
            print("Monitor selection cancelled.")
            if root.winfo_exists(): root.destroy()
            print("Full screen capture test aborted by user.")
    # --- End of Test Path for Full Screen Monitor Selection ---

    else: # bbox is None (selection cancelled or failed) - This is for the region selection path
        print("Region selection was cancelled or failed.")
        if root.winfo_exists():
            if root.state() == 'withdrawn':
                print("Deiconifying root window after selection cancellation/failure.")
                root.deiconify()

            # Decide whether to show a message or just quit
            if 'selector' in locals() and selector.overlay is None: # If selection was explicitly cancelled by Esc or finishing without valid rect
                messagebox.showinfo("Cancelled", "Screenshot region selection was cancelled or no valid region was selected.", parent=root)

            # If no bbox and the delayed capture isn't going to run, we might need to destroy root here.
            # However, the proceed_with_capture_and_dialog now handles root.destroy() if it doesn't get a captured_image.
            # If bbox is None, the proceed_with_capture_and_dialog won't be scheduled by root.after.
            # So, we need to handle root destruction here for the no-bbox path.
            print("Destroying main Tk root as no bbox was selected.")
            root.destroy()
        print("Test script finished as no bbox was selected.")

    # The mainloop should be started if proceed_with_capture_and_dialog was scheduled.
    # If bbox was None, root is destroyed above, and mainloop won't/shouldn't run.
    if bbox and root.winfo_exists():
         root.mainloop()

    # This final part of the script (from the original structure) is now largely handled
    # within proceed_with_capture_and_dialog or the else block above.
    # The root.destroy() is now called within those paths.

    # if captured_image:
    #     ... this logic is now inside proceed_with_capture_and_dialog ...
    # elif bbox is not None: # Bbox selected but capture failed
    #     print("Image capture failed after region selection.")
    # if root.winfo_exists():
    #     print("Destroying main Tk root.") # This is now handled inside the conditional flows
    #     root.destroy()
    # print("Test script finished.")
