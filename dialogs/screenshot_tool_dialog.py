import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw, UnidentifiedImageError
import os

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
        self.current_image_pil = captured_image.copy() # Work on a copy for annotations
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

    def _set_tool(self, tool_name):
        self.current_tool = tool_name
        # Optionally, update button reliefs to show active tool
        if self.active_tool_button:
            self.active_tool_button.state(['!pressed']) # ttk uses state for pressed

        if tool_name == "rectangle" and self.rect_button:
            self.active_tool_button = self.rect_button
        # Add other tools here...
        # elif tool_name == "ellipse" and self.ellipse_button:
        #     self.active_tool_button = self.ellipse_button

        if self.active_tool_button:
            self.active_tool_button.state(['pressed'])


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
        # Store other buttons similarly if you add them:
        # self.ellipse_button = ttk.Button(tools_group, text="Ellipse (E)", command=lambda: self._set_tool("ellipse"))
        # self.ellipse_button.pack(fill=tk.X, pady=2)
        ttk.Button(tools_group, text="Ellipse (E) (NYI)").pack(fill=tk.X, pady=2) # NYI = Not Yet Implemented
        ttk.Button(tools_group, text="Line (L) (NYI)").pack(fill=tk.X, pady=2)
        ttk.Button(tools_group, text="Arrow (A) (NYI)").pack(fill=tk.X, pady=2)
        ttk.Button(tools_group, text="Text (T) (NYI)").pack(fill=tk.X, pady=2)
        ttk.Button(tools_group, text="Highlight (H) (NYI)").pack(fill=tk.X, pady=2)
        ttk.Button(tools_group, text="Crop (C) (NYI)").pack(fill=tk.X, pady=2)

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
        # Add other tool press logic here

    def _on_canvas_drag(self, event):
        if self.current_tool == "rectangle" and self.draw_start_x is not None:
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.temp_drawing_item_id, self.draw_start_x, self.draw_start_y, cur_x, cur_y)
        # Add other tool drag logic here

    def _on_canvas_release(self, event):
        if self.current_tool == "rectangle" and self.draw_start_x is not None:
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
        # Add other tool release logic here


    def _setup_output_actions_ui(self):
        actions_group = ttk.LabelFrame(self.sidebar_frame, text="Output", padding=10)
        actions_group.pack(fill=tk.X, pady=5, padx=5, side=tk.BOTTOM) # Place at bottom of sidebar

        ttk.Button(actions_group, text="Save as PNG...").pack(fill=tk.X, pady=2)
        ttk.Button(actions_group, text="Copy to Clipboard").pack(fill=tk.X, pady=2)
        if hasattr(self.parent_editor, 'get_current_tab'): # Only show if part of TextEditor
             ttk.Button(actions_group, text="Insert into Editor").pack(fill=tk.X, pady=2)
        ttk.Button(actions_group, text="Done / Close", command=self.destroy).pack(fill=tk.X, pady=2)


# Basic test for the dialog (run this file directly)
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Hide the main root window

    # Create a dummy image for testing
    try:
        dummy_image = Image.new("RGB", (600, 400), "lightblue")
        draw = ImageDraw.Draw(dummy_image)
        draw.text((50, 50), "Test Screenshot", fill="black")
    except Exception as e:
        print(f"Could not create dummy image for testing: {e}")
        dummy_image = None

    if dummy_image:
        # Mock parent editor for testing
        class MockEditor:
            def __init__(self, root_window):
                self.root = root_window
                # No get_current_tab for mock, so "Insert into Editor" won't show

        mock_app = MockEditor(root)
        dialog = ScreenshotToolDialog(mock_app, dummy_image)
        dialog.mainloop()
    else:
        print("Pillow not available or dummy image creation failed. Cannot run dialog test.")
        root.destroy()
