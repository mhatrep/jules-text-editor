import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from PIL import ImageGrab, Image, ImageTk, ImageFilter, ImageOps, ImageEnhance
import cv2
import numpy as np


class DrawingDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root # TextEditor's root
        self.top = tk.Toplevel(self.root)
        self.top.title("Drawing Tool")
        self.top.transient(self.root) # Keep on top of parent
        # self.top.grab_set() # Modal, if desired
        self.top.resizable(True, True)

        self.is_maximized = False
        self.top.bind("<F11>", self.toggle_maximize)
        self.top.bind("<Escape>", self.unmaximize)

        maximize_button = ttk.Button(self.top, text="□", command=self.toggle_maximize)
        maximize_button.place(relx=1.0, rely=0, anchor='ne')

        self.original_image = None
        self.displayed_image_tk = None
        self.current_canvas_image_id = None

        self.current_brush_size = 5
        self.current_color = "black"
        self.drawing_mode = "pen"  # Modes: "pen", "eraser", "line", "rectangle", "circle", "triangle", "text", "highlighter"
        self.line_style = "plain" # For line tool: "plain", "uni_arrow", "bi_arrow"
        self.last_x, self.last_y = None, None
        self.line_start_x, self.line_start_y = None, None # For line/shape drawing
        self.temp_line_id = None # For previewing lines
        self.shape_start_x, self.shape_start_y = None, None
        self.temp_shape_id = None # For previewing shapes
        # self.last_drawn_item_ids = [] # Replaced by tagging and last_drawn_group_tag
        self.last_drawn_group_tag = None # Store the tag of the last drawn logical item/group

        self.highlighter_stipple = "gray25" # Stipple for highlighter
        self.stipple_patterns = ["Solid Fill", "gray75", "gray50", "gray25", "gray12", "hourglass", "info", "questhead", "error", "warning"]
        self.current_fill_pattern_var = tk.StringVar(value=self.stipple_patterns[0])
        self.grid_rows_var = tk.IntVar(value=3)
        self.grid_cols_var = tk.IntVar(value=3)
        self.grid_visible = False # State variable for grid visibility
        self.line_dash_options = ["Solid", "Dashed", "Dotted", "Dash-Dot"] # Line style options
        self.current_line_dash_style = tk.StringVar(value=self.line_dash_options[0]) # Current selected line style

        # To keep track of active tool button for visual feedback
        self.eraser_button = None
        self.text_tool_button = None
        self.highlighter_button = None
        self.plain_line_button = None
        self.uni_arrow_button = None
        self.bi_arrow_button = None
        self.rectangle_button = None
        self.circle_button = None
        self.triangle_button = None
        self.counter_tool_button = None
        self.select_tool_button = None # New Select tool button
        self.apply_grid_button = None
        self.active_color_button = None
        self.current_counter_value = 1 # For the new 'counter' drawing mode
        self.selection_rect_id = None # For drawing selection rectangle
        self.selected_item_ids = set() # Store IDs of selected items
        self.item_counter = 0 # To generate unique tags for item groups
        self.selected_tag = "selected_drawing_item" # Tag for visually highlighting selected items

        main_dialog_frame = ttk.Frame(self.top, padding=5)
        main_dialog_frame.pack(expand=True, fill=tk.BOTH)

        # Sidebar Frame
        self.sidebar_frame = ttk.Frame(main_dialog_frame, width=220, relief=tk.FLAT, borderwidth=0)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5), pady=0)
        self.sidebar_frame.pack_propagate(False) # Prevent sidebar from shrinking

        # Canvas Frame
        canvas_frame = ttk.Frame(main_dialog_frame)
        canvas_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # --- Properties Group ---
        props_group = ttk.LabelFrame(self.sidebar_frame, text="Properties", padding=5)
        props_group.pack(fill=tk.X, pady=5, padx=5)

        # Brush Size
        brush_frame = ttk.Frame(props_group)
        brush_frame.pack(fill=tk.X, pady=2)
        ttk.Label(brush_frame, text="Size:").pack(side=tk.LEFT, padx=(0,2))
        self.brush_size_label_var = tk.StringVar(value=str(self.current_brush_size))
        self.brush_size_scale = ttk.Scale(brush_frame, from_=1, to=50, orient=tk.HORIZONTAL, command=self.set_brush_size_from_scale)
        self.brush_size_scale.set(self.current_brush_size)
        self.brush_size_scale.pack(side=tk.LEFT, padx=(0,2), fill=tk.X, expand=True)
        ttk.Label(brush_frame, textvariable=self.brush_size_label_var, width=3).pack(side=tk.LEFT)

        # Color Palette
        color_frame = ttk.Frame(props_group)
        color_frame.pack(fill=tk.X, pady=(5,2))
        ttk.Label(color_frame, text="Color:").pack(side=tk.LEFT, anchor=tk.NW, padx=(0,3))
        self.color_palette_frame = ttk.Frame(color_frame)
        self.color_palette_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Expanded basic colors
        self.basic_colors = { # Name: Hex
            "Black": "#000000", "White": "#FFFFFF", "Red": "#FF0000", "Green": "#008000", "Blue": "#0000FF",
            "Yellow": "#FFFF00", "Orange": "#FFA500", "Purple": "#800080", "Cyan": "#00FFFF", "Magenta": "#FF00FF",
            "Brown": "#A52A2A", "Gray": "#808080", "LightGray": "#D3D3D3",
            "LightRed": "#FF9999", "LightBlue": "#ADD8E6", "LightGreen": "#90EE90",
            "LightYellow": "#FFFFE0", # Common highlighter yellow
            "DarkRed": "#8B0000", "DarkGreen": "#006400", "DarkBlue": "#00008B"
        }
        self.color_palette_list = list(self.basic_colors.values())

        if self.current_color not in self.color_palette_list:
            self.current_color = self.basic_colors.get("Black", "#000000")

        num_color_cols = 5
        for i, color_code in enumerate(self.color_palette_list):
            color_btn_widget = tk.Frame(self.color_palette_frame, width=22, height=22, bg=color_code, relief=tk.RAISED, borderwidth=1)
            color_btn_widget.grid(row=i // num_color_cols, column=i % num_color_cols, padx=1, pady=1)
            color_btn_widget.bind("<Button-1>", lambda e, c=color_code, btn=color_btn_widget: self.select_color_button(c, btn))
            if color_code == self.current_color:
                 self.select_color_button(color_code, color_btn_widget)

        if not self.active_color_button and self.color_palette_list:
            first_color_code = self.color_palette_list[0]
            if self.color_palette_frame.winfo_children():
                 self.select_color_button(first_color_code, self.color_palette_frame.winfo_children()[0])

        # Fill Pattern (for shapes)
        fill_pattern_frame = ttk.Frame(props_group)
        fill_pattern_frame.pack(fill=tk.X, pady=(5,2))
        ttk.Label(fill_pattern_frame, text="Fill:").pack(side=tk.LEFT, padx=(0,2))
        self.fill_pattern_combo = ttk.Combobox(fill_pattern_frame, textvariable=self.current_fill_pattern_var,
                                               values=self.stipple_patterns, state="readonly", width=10)
        self.fill_pattern_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Line Dash Style
        line_style_frame = ttk.Frame(props_group)
        line_style_frame.pack(fill=tk.X, pady=(5,2))
        ttk.Label(line_style_frame, text="Line Style:").pack(side=tk.LEFT, padx=(0,2))
        self.line_dash_options = ["Solid", "Dashed", "Dotted", "Dash-Dot"]
        self.current_line_dash_style = tk.StringVar(value=self.line_dash_options[0])
        self.line_dash_style_combo = ttk.Combobox(line_style_frame, textvariable=self.current_line_dash_style,
                                                  values=self.line_dash_options, state="readonly", width=10)
        self.line_dash_style_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Call to setup text tool options (which will create self.text_options_frame)
        self._setup_text_options_ui(props_group)


        # --- Tools Group ---
        tools_group = ttk.LabelFrame(self.sidebar_frame, text="Tools", padding=5)
        tools_group.pack(fill=tk.X, pady=5, padx=5)

        basic_tools_subframe = ttk.Frame(tools_group)
        basic_tools_subframe.pack(fill=tk.X)
        btn_width = 9 # Adjusted for better fit

        self.eraser_button = ttk.Button(basic_tools_subframe, text="Eraser", command=self.activate_eraser, width=btn_width)
        self.eraser_button.grid(row=0, column=0, padx=1, pady=1, sticky="ew")
        self.text_tool_button = ttk.Button(basic_tools_subframe, text="Text", command=self.activate_text_tool, width=btn_width)
        self.text_tool_button.grid(row=0, column=1, padx=1, pady=1, sticky="ew")

        self.highlighter_button = ttk.Button(basic_tools_subframe, text="Highlight", command=self.activate_highlighter_mode, width=btn_width)
        self.highlighter_button.grid(row=1, column=0, padx=1, pady=1, sticky="ew")

        self.select_tool_button = ttk.Button(basic_tools_subframe, text="Select", command=self.activate_select_tool, width=btn_width)
        self.select_tool_button.grid(row=1, column=1, padx=1, pady=1, sticky="ew") # Added Select button

        shape_tools_subframe = ttk.Frame(tools_group)
        shape_tools_subframe.pack(fill=tk.X, pady=(5,0))
        self.rectangle_button = ttk.Button(shape_tools_subframe, text="□", command=self.activate_rectangle_mode, width=5)
        self.rectangle_button.pack(side=tk.LEFT, padx=1)
        self.circle_button = ttk.Button(shape_tools_subframe, text="○", command=self.activate_circle_mode, width=5)
        self.circle_button.pack(side=tk.LEFT, padx=1)
        self.triangle_button = ttk.Button(shape_tools_subframe, text="△", command=self.activate_triangle_mode, width=5)
        self.triangle_button.pack(side=tk.LEFT, padx=1)
        self.counter_tool_button = ttk.Button(shape_tools_subframe, text="123", command=self.activate_counter_tool, width=5)
        self.counter_tool_button.pack(side=tk.LEFT, padx=1)

        line_tools_subframe = ttk.Frame(tools_group)
        line_tools_subframe.pack(fill=tk.X, pady=(5,0))
        self.plain_line_button = ttk.Button(line_tools_subframe, text="--", command=self.activate_plain_line_mode, width=5)
        self.plain_line_button.pack(side=tk.LEFT, padx=1)
        self.uni_arrow_button = ttk.Button(line_tools_subframe, text="→", command=self.activate_uni_arrow_mode, width=5)
        self.uni_arrow_button.pack(side=tk.LEFT, padx=1)
        self.bi_arrow_button = ttk.Button(line_tools_subframe, text="↔", command=self.activate_bi_arrow_mode, width=5)
        self.bi_arrow_button.pack(side=tk.LEFT, padx=1)

        shape_tools_subframe = ttk.Frame(tools_group)
        shape_tools_subframe.pack(fill=tk.X, pady=(5,0))
        self.rectangle_button = ttk.Button(shape_tools_subframe, text="□", command=self.activate_rectangle_mode, width=5)
        self.rectangle_button.pack(side=tk.LEFT, padx=1)
        self.circle_button = ttk.Button(shape_tools_subframe, text="○", command=self.activate_circle_mode, width=5)
        self.circle_button.pack(side=tk.LEFT, padx=1)
        self.triangle_button = ttk.Button(shape_tools_subframe, text="△", command=self.activate_triangle_mode, width=5)
        self.triangle_button.pack(side=tk.LEFT, padx=1)
        self.counter_tool_button = ttk.Button(shape_tools_subframe, text="123", command=self.activate_counter_tool, width=5)
        self.counter_tool_button.pack(side=tk.LEFT, padx=1)


        # --- Image Filters Group ---
        filters_group = ttk.LabelFrame(self.sidebar_frame, text="Image Filters", padding=5)
        filters_group.pack(fill=tk.X, pady=5, padx=5)

        load_image_button = ttk.Button(filters_group, text="Load Image", command=self._load_image)
        load_image_button.pack(fill=tk.X, pady=(0, 5))

        self.filter_options = [
            "Original", "Sketch", "Cartoonify", "Oil Painting", "Posterize",
            "Edge Enhance", "Emboss", "Solarize", "Blur", "Mosaic", "Sepia",
            "Black and White"
        ]
        self.current_filter_var = tk.StringVar(value=self.filter_options[0])
        self.filter_menu = ttk.Combobox(filters_group, textvariable=self.current_filter_var,
                                        values=self.filter_options, state="readonly")
        self.filter_menu.pack(fill=tk.X)
        self.filter_menu.bind("<<ComboboxSelected>>", self.apply_selected_filter)

        # --- Image Adjustments Group ---
        adjustments_group = ttk.LabelFrame(self.sidebar_frame, text="Image Adjustments", padding=5)
        adjustments_group.pack(fill=tk.X, pady=5, padx=5)

        # Brightness
        brightness_frame = ttk.Frame(adjustments_group)
        brightness_frame.pack(fill=tk.X, pady=2)
        ttk.Label(brightness_frame, text="Brightness:").pack(side=tk.LEFT)
        self.brightness_scale = ttk.Scale(brightness_frame, from_=0, to=2, orient=tk.HORIZONTAL, command=self.apply_image_adjustments)
        self.brightness_scale.set(1)
        self.brightness_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Contrast
        contrast_frame = ttk.Frame(adjustments_group)
        contrast_frame.pack(fill=tk.X, pady=2)
        ttk.Label(contrast_frame, text="Contrast:").pack(side=tk.LEFT)
        self.contrast_scale = ttk.Scale(contrast_frame, from_=0, to=2, orient=tk.HORIZONTAL, command=self.apply_image_adjustments)
        self.contrast_scale.set(1)
        self.contrast_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Transparency
        transparency_frame = ttk.Frame(adjustments_group)
        transparency_frame.pack(fill=tk.X, pady=2)
        ttk.Label(transparency_frame, text="Transparency:").pack(side=tk.LEFT)
        self.transparency_scale = ttk.Scale(transparency_frame, from_=0, to=1, orient=tk.HORIZONTAL, command=self.apply_image_adjustments)
        self.transparency_scale.set(1)
        self.transparency_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Canvas Actions Group (moved to bottom of sidebar) ---
        actions_group = ttk.LabelFrame(self.sidebar_frame, text="Canvas Actions", padding=5)
        actions_group.pack(fill=tk.X, pady=5, padx=5, side=tk.BOTTOM) # Pack at bottom

        # Grid Controls
        grid_controls_frame = ttk.Frame(actions_group)
        grid_controls_frame.pack(fill=tk.X, pady=(0,5))

        row_col_frame = ttk.Frame(grid_controls_frame) # Frame for row/col entries
        row_col_frame.pack(fill=tk.X)
        ttk.Label(row_col_frame, text="Rows:").pack(side=tk.LEFT, padx=(0,1))
        self.grid_rows_spinbox = ttk.Spinbox(row_col_frame, from_=1, to=20, width=3, textvariable=self.grid_rows_var)
        self.grid_rows_spinbox.pack(side=tk.LEFT, padx=(0,3))
        ttk.Label(row_col_frame, text="Cols:").pack(side=tk.LEFT, padx=(0,1))
        self.grid_cols_spinbox = ttk.Spinbox(row_col_frame, from_=1, to=20, width=3, textvariable=self.grid_cols_var)
        self.grid_cols_spinbox.pack(side=tk.LEFT, padx=(0,3))

        self.apply_grid_button = ttk.Button(grid_controls_frame, text="Show Grid", command=self.toggle_grid) # Text updated in Step 3
        self.apply_grid_button.pack(fill=tk.X, pady=(3,0))


        # Clear and Save
        clear_save_frame = ttk.Frame(actions_group)
        clear_save_frame.pack(fill=tk.X, pady=(5,0))
        clear_button = ttk.Button(clear_save_frame, text="Clear Canvas", command=self.clear_canvas)
        clear_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,1))
        save_png_button = ttk.Button(clear_save_frame, text="Save as PNG", command=self.save_canvas_as_png)
        save_png_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(1,0))

        # Delete Last Drawn button
        delete_last_button = ttk.Button(actions_group, text="Delete Last Drawn", command=self._delete_last_drawn)
        delete_last_button.pack(fill=tk.X, pady=(5,0))


        # Canvas
        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=1, highlightbackground="grey")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        # Keyboard shortcuts for tools
        self.top.bind('l', lambda event: self.activate_plain_line_mode())
        self.top.bind('L', lambda event: self.activate_plain_line_mode()) # Shift+L
        self.top.bind('a', lambda event: self.activate_uni_arrow_mode())
        self.top.bind('A', lambda event: self.activate_uni_arrow_mode())
        self.top.bind('b', lambda event: self.activate_bi_arrow_mode())
        self.top.bind('B', lambda event: self.activate_bi_arrow_mode())
        self.top.bind('r', lambda event: self.activate_rectangle_mode())
        self.top.bind('R', lambda event: self.activate_rectangle_mode())
        self.top.bind('c', lambda event: self.activate_circle_mode())
        self.top.bind('C', lambda event: self.activate_circle_mode())
        self.top.bind('t', lambda event: self.activate_triangle_mode())
        self.top.bind('T', lambda event: self.activate_triangle_mode())
        self.top.bind('e', lambda event: self.activate_eraser())
        self.top.bind('E', lambda event: self.activate_eraser())
        self.top.bind('x', lambda event: self.activate_text_tool()) # 'x' for text
        self.top.bind('X', lambda event: self.activate_text_tool())
        self.top.bind('p', lambda event: self.activate_pen_mode()) # 'p' for pen
        self.top.bind('P', lambda event: self.activate_pen_mode())
        self.top.bind('h', lambda event: self.activate_highlighter_mode())
        self.top.bind('H', lambda event: self.activate_highlighter_mode())


        self.top.update_idletasks()
        initial_width = max(700, self.sidebar_frame.winfo_reqwidth() + 500) # Ensure sidebar fits
        initial_height = 550
        x_pos = self.root.winfo_x() + (self.root.winfo_width() // 2) - (initial_width // 2)
        y_pos = self.root.winfo_y() + (self.root.winfo_height() // 2) - (initial_height // 2)
        self.top.geometry(f'{initial_width}x{initial_height}+{x_pos}+{y_pos}')
        self.top.minsize(self.sidebar_frame.winfo_reqwidth() + 200, 400) # Min size based on sidebar

    def start_draw(self, event):
        if self.drawing_mode == "pen":
            self.last_x, self.last_y = event.x, event.y
            # Draw a small dot for click-only drawing
            x1 = event.x - self.current_brush_size / 2
            y1 = event.y - self.current_brush_size / 2
            x2 = event.x + self.current_brush_size / 2
            y2 = event.y + self.current_brush_size / 2
            dot_id = self.canvas.create_oval(x1, y1, x2, y2, fill=self.current_color, outline=self.current_color, width=0)
            group_tag = f"item_group_{self.item_counter}"
            self.canvas.addtag_withtag(group_tag, dot_id)
            self.last_drawn_group_tag = group_tag # Update last drawn group
            self.item_counter += 1
        elif self.drawing_mode == "text":
            user_text = simpledialog.askstring("Input Text", "Enter text to place on canvas:", parent=self.top)
            if user_text:
                # Define font (consider making this more configurable later)
                # For now, use a fixed font style and scale size with brush_size for consistency.
                font_size = max(10, int(self.current_brush_size * 2.5)) # Ensure a minimum font size
                if font_size > 40: font_size = 40 # Cap max font size for sanity
                text_font_family = "Arial"
                text_font_weight = "normal"
                # If current color is very light, consider making text black or dark grey, or vice-versa
                # For now, text color is self.current_color

                temp_font = tk.font.Font(family=text_font_family, size=font_size, weight=text_font_weight)
                text_width = temp_font.measure(user_text)
                text_height = temp_font.metrics("linespace") # Ascent + descent

                if self.add_bg_shape_var.get():
                    padding = 10 # Pixels around the text
                    shape_type = self.text_bg_shape_type_var.get()
                    # Shape fill color will be self.current_color (main selected color)
                    # Text color will also be self.current_color. If they need to differ,
                    # user must change current_color or we need separate color pickers.
                    # For contrast, let's make text color black if background is not black, else white.
                    text_draw_color = "black"
                    if self.current_color.lower() == "#000000" or self.current_color.lower() == "black":
                        text_draw_color = "white"


                    shape_x1 = event.x - text_width / 2 - padding
                    shape_y1 = event.y - text_height / 2 - padding
                    shape_x2 = event.x + text_width / 2 + padding
                    shape_y2 = event.y + text_height / 2 + padding

                    # Center of the shape is event.x, event.y
                    text_x_center = event.x
                    text_y_center = event.y
                    shape_id = None
                    stipple_option = ""
                    selected_pattern = self.current_fill_pattern_var.get()
                    if selected_pattern != "Solid Fill":
                        stipple_option = selected_pattern

                    shape_fill_color = self.text_bg_fill_color_var.get()
                    shape_outline_color = self.text_bg_outline_color_var.get()

                    if shape_type == "Rectangle":
                        shape_id = self.canvas.create_rectangle(shape_x1, shape_y1, shape_x2, shape_y2,
                                                                fill=shape_fill_color, outline=shape_outline_color, width=1,
                                                                stipple=stipple_option)
                    elif shape_type == "Ellipse":
                        shape_id = self.canvas.create_oval(shape_x1, shape_y1, shape_x2, shape_y2,
                                                           fill=shape_fill_color, outline=shape_outline_color, width=1,
                                                           stipple=stipple_option)

                    # Text color contrast should be against the shape_fill_color now
                    text_draw_color = "black" # Default
                    try:
                        # Basic check: if shape_fill_color is dark, use white text.
                        # This is a rough heuristic. A proper luminance check would be better.
                        r, g, b = self.canvas.winfo_rgb(shape_fill_color) # Returns 0-65535 range
                        # Normalize to 0-1 and calculate approximate luminance
                        luminance = (0.299 * (r/65535.0)) + (0.587 * (g/65535.0)) + (0.114 * (b/65535.0))
                        if luminance < 0.5: # If background is dark
                            text_draw_color = "white"
                    except tk.TclError: # If color string is invalid (e.g., empty)
                        pass # Keep default text_draw_color


                    text_id = self.canvas.create_text(text_x_center, text_y_center, text=user_text,
                                                      fill=text_draw_color, font=temp_font, anchor=tk.CENTER)
                    group_tag = f"item_group_{self.item_counter}"
                    self.item_counter += 1
                    if shape_id:
                        self.canvas.addtag_withtag(group_tag, shape_id)
                    self.canvas.addtag_withtag(group_tag, text_id)
                    self.last_drawn_group_tag = group_tag # Update last drawn group
                else: # No background shape
                    text_id = self.canvas.create_text(event.x, event.y, text=user_text,
                                                      fill=self.current_color, font=temp_font, anchor=tk.NW)
                    group_tag = f"item_group_{self.item_counter}"
                    self.canvas.addtag_withtag(group_tag, text_id)
                    self.last_drawn_group_tag = group_tag # Update last drawn group
                    self.item_counter += 1
        elif self.drawing_mode == "line":
            self.line_start_x, self.line_start_y = event.x, event.y
        elif self.drawing_mode in ["rectangle", "circle", "triangle"]:
            self.shape_start_x, self.shape_start_y = event.x, event.y
        elif self.drawing_mode == "highlighter":
            self.last_x, self.last_y = event.x, event.y
            highlighter_brush_size = max(10, self.current_brush_size * 2) # Highlighter is thicker
            x1 = event.x - highlighter_brush_size / 2
            y1 = event.y - highlighter_brush_size / 2
            x2 = event.x + highlighter_brush_size / 2
            y2 = event.y + highlighter_brush_size / 2
            # For highlighter, last_drawn_item_ids will be populated by continuous draw in self.draw
            # self.canvas.create_oval(x1, y1, x2, y2, fill=self.current_color, outline=self.current_color, width=0, stipple=self.highlighter_stipple)
        elif self.drawing_mode == "select":
            if self.selected_item_ids: # If items are already selected, this click is to move them
                # Calculate the bounding box of the entire selection
                if not self.selected_item_ids: return # Should not happen if logic is right

                all_coords = []
                for item_id in self.selected_item_ids:
                    try:
                        coords = self.canvas.coords(item_id) # Gets [x1,y1,x2,y2] for rect/oval, or [x1,y1,x2,y2,...] for line/poly
                        # For text, coords are just [x,y]. Bbox is better for text.
                        if self.canvas.type(item_id) == "text":
                             bbox = self.canvas.bbox(item_id) # x1,y1,x2,y2
                             if bbox: all_coords.extend([bbox[0], bbox[1], bbox[2], bbox[3]])
                        elif coords: # For other shapes that have coords
                             # For items like lines (x1,y1,x2,y2,x3,y3...), find min/max of all x and y
                            if len(coords) >=2:
                                item_xs = coords[0::2]
                                item_ys = coords[1::2]
                                all_coords.extend([min(item_xs), min(item_ys), max(item_xs), max(item_ys)])
                    except tk.TclError: continue # Item might have been deleted or has no coords

                if not all_coords: # No valid coordinates found for selected items
                    # This might happen if only empty groups are somehow selected
                    self.selected_item_ids.clear() # Clear selection as it's invalid for move
                    # Proceed to marquee selection below
                    self.shape_start_x, self.shape_start_y = event.x, event.y
                    return

                # Determine overall bounding box of the selection
                sel_x1 = min(all_coords[0::2])
                sel_y1 = min(all_coords[1::2])
                sel_x2 = max(all_coords[0::2])
                sel_y2 = max(all_coords[1::2])

                current_center_x = (sel_x1 + sel_x2) / 2
                current_center_y = (sel_y1 + sel_y2) / 2

                dx = event.x - current_center_x
                dy = event.y - current_center_y

                for item_id in self.selected_item_ids:
                    try:
                        self.canvas.move(item_id, dx, dy)
                        self.canvas.dtag(item_id, self.selected_tag) # De-highlight after move
                    except tk.TclError: pass
                self.selected_item_ids.clear()
                # self.last_drawn_group_tag = None # Moving isn't "drawing" a new last item for undo
                # Or, if move should be undoable, we'd need a more complex undo stack.

            else: # No items currently selected, so this click starts a marquee selection
                self.shape_start_x, self.shape_start_y = event.x, event.y
                if self.selection_rect_id: # Delete old selection rectangle
                    self.canvas.delete(self.selection_rect_id)
                    self.selection_rect_id = None
        elif self.drawing_mode == "counter":
            # --- Counter Tool Logic ---
            radius = 30 # Doubled radius
            text_color = "white"
            fill_color = "teal"
            outline_color = "darkslategrey"
            font_size = 20 # Adjusted font size for larger circle, not strictly double to ensure fit
            counter_font = ("Arial", font_size, "bold")

            # Circle coordinates (event.x, event.y is the center)
            c_x1 = event.x - radius
            c_y1 = event.y - radius
            c_x2 = event.x + radius
            c_y2 = event.y + radius

            shape_id = self.canvas.create_oval(c_x1, c_y1, c_x2, c_y2,
                                               fill=fill_color, outline=outline_color, width=1)
            text_id = self.canvas.create_text(event.x, event.y, text=str(self.current_counter_value),
                                              fill=text_color, font=counter_font, anchor=tk.CENTER)

            group_tag = f"item_group_{self.item_counter}"
            self.canvas.addtag_withtag(group_tag, shape_id)
            self.canvas.addtag_withtag(group_tag, text_id)
            self.last_drawn_group_tag = group_tag # Update last drawn group
            self.item_counter += 1

            self.current_counter_value += 1
            if self.current_counter_value > 99: # Changed from 8 to 99
                self.current_counter_value = 1 # Reset after 99


    def draw(self, event):
        if self.drawing_mode == "pen":
            if self.last_x and self.last_y:
                self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                        width=self.current_brush_size, fill=self.current_color,
                                        capstyle=tk.ROUND, smooth=tk.TRUE, splinesteps=128)
                x1_pen, y1_pen = (event.x - self.current_brush_size / 2), (event.y - self.current_brush_size / 2)
                x2_pen, y2_pen = (event.x + self.current_brush_size / 2), (event.y + self.current_brush_size / 2)
                self.canvas.create_oval(x1_pen, y1_pen, x2_pen, y2_pen, fill=self.current_color, outline=self.current_color)
                self.last_x, self.last_y = event.x, event.y
        elif self.drawing_mode == "highlighter":
            if self.last_x and self.last_y:
                highlighter_brush_size = max(10, self.current_brush_size * 2)
                self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                        width=highlighter_brush_size, fill=self.current_color,
                                        capstyle=tk.ROUND, smooth=tk.FALSE,
                                        stipple=self.highlighter_stipple)
                self.last_x, self.last_y = event.x, event.y
        elif self.drawing_mode == "line":
            if self.line_start_x is not None and self.line_start_y is not None:
                if self.temp_line_id:
                    self.canvas.delete(self.temp_line_id)
                dash_style = self.get_dash_pattern()
                self.temp_line_id = self.canvas.create_line(
                    self.line_start_x, self.line_start_y, event.x, event.y,
                    width=self.current_brush_size, fill=self.current_color,
                    capstyle=tk.ROUND, dash=dash_style
                )
        elif self.drawing_mode == "select": # Moved select logic to be its own primary elif
            if self.shape_start_x is not None and self.shape_start_y is not None:
                if self.selection_rect_id:
                    self.canvas.delete(self.selection_rect_id)
                self.selection_rect_id = self.canvas.create_rectangle(
                    self.shape_start_x, self.shape_start_y, event.x, event.y,
                    outline="blue", dash=(4, 4)
                )
        elif self.drawing_mode in ["rectangle", "circle", "triangle"]:
            if self.shape_start_x is not None and self.shape_start_y is not None:
                if self.temp_shape_id:
                    self.canvas.delete(self.temp_shape_id)
                # These x1,y1,x2,y2 are for the current preview shape, not related to select tool's shape_start_x
                preview_x1, preview_y1 = self.shape_start_x, self.shape_start_y
                preview_x2, preview_y2 = event.x, event.y

                draw_x1, draw_y1 = min(preview_x1, preview_x2), min(preview_y1, preview_y2)
                draw_x2, draw_y2 = max(preview_x1, preview_x2), max(preview_y1, preview_y2)

                if self.drawing_mode == "rectangle":
                    self.temp_shape_id = self.canvas.create_rectangle(
                        draw_x1, draw_y1, draw_x2, draw_y2,
                        outline=self.current_color, width=self.current_brush_size,
                        fill="", stipple=""
                    )
                elif self.drawing_mode == "circle":
                    self.temp_shape_id = self.canvas.create_oval(
                        draw_x1, draw_y1, draw_x2, draw_y2,
                        outline=self.current_color, width=self.current_brush_size,
                        fill="", stipple=""
                    )
                elif self.drawing_mode == "triangle":
                    p1 = ((preview_x1 + preview_x2) / 2, preview_y1)
                    p2 = (preview_x1, preview_y2)
                    p3 = (preview_x2, preview_y2)
                    self.temp_shape_id = self.canvas.create_polygon(
                        p1, p2, p3,
                        outline=self.current_color, width=self.current_brush_size,
                        fill="", stipple=""
                    )

    def stop_draw(self, event):
        if self.drawing_mode == "pen":
            self.last_x, self.last_y = None, None
        elif self.drawing_mode == "highlighter":
            self.last_x, self.last_y = None, None
        elif self.drawing_mode == "line":
            if self.temp_line_id:
                self.canvas.delete(self.temp_line_id)
                self.temp_line_id = None
            if self.line_start_x is not None and self.line_start_y is not None:
                x1, y1 = self.line_start_x, self.line_start_y
                x2, y2 = event.x, event.y
                arrow_option = tk.NONE
                if self.line_style == "uni_arrow": arrow_option = tk.LAST
                elif self.line_style == "bi_arrow": arrow_option = tk.BOTH
                arrow_shape_spec = (16, 20, 8)
                dash_style = self.get_dash_pattern()
                line_id = self.canvas.create_line(x1, y1, x2, y2, width=self.current_brush_size, fill=self.current_color,
                                                  arrow=arrow_option, arrowshape=arrow_shape_spec, capstyle=tk.ROUND,
                                                  dash=dash_style)
                group_tag = f"item_group_{self.item_counter}"
                self.canvas.addtag_withtag(group_tag, line_id)
                self.last_drawn_group_tag = group_tag # Update last drawn group
                self.item_counter += 1
            self.line_start_x, self.line_start_y = None, None
        elif self.drawing_mode == "select":
            if self.selection_rect_id:
                self.canvas.delete(self.selection_rect_id)
                self.selection_rect_id = None

            # Final selection coordinates
            # Ensure shape_start_x/y are not None before using them
            if self.shape_start_x is None or self.shape_start_y is None: return

            x1, y1 = min(self.shape_start_x, event.x), min(self.shape_start_y, event.y)
            x2, y2 = max(self.shape_start_x, event.x), max(self.shape_start_y, event.y)

            if abs(x1 - x2) < 2 and abs(y1 - y2) < 2:
                click_radius = 5
                items_under_click = self.canvas.find_overlapping(
                    event.x - click_radius, event.y - click_radius,
                    event.x + click_radius, event.y + click_radius
                )
                if items_under_click:
                    self.selected_item_ids = {items_under_click[-1]}
                else:
                    self.selected_item_ids.clear()
            else:
                self.selected_item_ids = set(self.canvas.find_overlapping(x1, y1, x2, y2))

            # Process group tags for all initially found items
            final_selection = set()
            for item_id in self.selected_item_ids:
                tags = self.canvas.gettags(item_id)
                found_group_tag = None
                for tag in tags:
                    if tag.startswith("item_group_"):
                        found_group_tag = tag
                        break
                if found_group_tag:
                    # Add all items with this group tag to the final selection
                    final_selection.update(self.canvas.find_withtag(found_group_tag))
                else:
                    # If no group tag, it's a standalone item (e.g. old drawing or pen stroke part)
                    final_selection.add(item_id)
            self.selected_item_ids = final_selection

            # Apply visual highlighting to the final selection
            if self.selected_item_ids:
                # print(f"Final selected IDs (with groups): {self.selected_item_ids}") # Debug
                self.canvas.itemconfig(self.selected_tag, outline="blue", dash=(4,2), width=2) # Configure the tag's appearance
                for item_id in self.selected_item_ids:
                    self.canvas.addtag_withtag(self.selected_tag, item_id)

            self.shape_start_x, self.shape_start_y = None, None

        elif self.drawing_mode in ["rectangle", "circle", "triangle"]:
            if self.temp_shape_id:
                self.canvas.delete(self.temp_shape_id)
                self.temp_shape_id = None
            if self.shape_start_x is not None and self.shape_start_y is not None:
                x1, y1 = self.shape_start_x, self.shape_start_y
                x2, y2 = event.x, event.y
                draw_x1, draw_y1 = min(x1,x2), min(y1,y2)
                draw_x2, draw_y2 = max(x1,x2), max(y1,y2)
                selected_pattern = self.current_fill_pattern_var.get()
                stipple_option = ""
                if selected_pattern != "Solid Fill":
                    stipple_option = selected_pattern

                shape_id = None
                if self.drawing_mode == "rectangle":
                    shape_id = self.canvas.create_rectangle(draw_x1, draw_y1, draw_x2, draw_y2,
                                                            fill=self.current_color, outline=self.current_color,
                                                            width=0, stipple=stipple_option)
                elif self.drawing_mode == "circle":
                    shape_id = self.canvas.create_oval(draw_x1, draw_y1, draw_x2, draw_y2,
                                                       fill=self.current_color, outline=self.current_color,
                                                       width=0, stipple=stipple_option)
                elif self.drawing_mode == "triangle":
                    p1_x, p1_y = (x1 + x2) / 2, y1
                    p2_x, p2_y = x1, y2
                    p3_x, p3_y = x2, y2
                    shape_id = self.canvas.create_polygon(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y,
                                                          fill=self.current_color, outline=self.current_color,
                                                          width=0, stipple=stipple_option)
                if shape_id:
                    group_tag = f"item_group_{self.item_counter}"
                    self.canvas.addtag_withtag(group_tag, shape_id)
                    self.last_drawn_group_tag = group_tag # Update last drawn group
                    self.item_counter += 1
            self.shape_start_x, self.shape_start_y = None, None


    def set_brush_size_from_scale(self, value):
        self.current_brush_size = int(float(value))
        self.brush_size_label_var.set(str(self.current_brush_size))

    def select_color_button(self, color_code, button_widget):
        self.current_color = color_code
        # Reset previously active button's relief
        if self.active_color_button and self.active_color_button != button_widget:
            self.active_color_button.config(relief=tk.RAISED, borderwidth=1)
        # Set new active button's relief
        button_widget.config(relief=tk.SUNKEN, borderwidth=1)
        self.active_color_button = button_widget
        # If eraser was active and a new color is chosen (not white), deactivate eraser
        if self.eraser_button and hasattr(self.eraser_button, 'state') and 'pressed' in self.eraser_button.state():
            if color_code != "white": # Assuming white is eraser color
                 self.eraser_button.state(['!pressed']) # Remove pressed state
                 self.eraser_button_active = False # Explicitly track state

    def set_color(self, color): # Called by activate_eraser
        self.current_color = color
        # Find the button corresponding to this color and select it
        # This is a bit more complex if colors are not unique or if 'white' isn't in palette
        # For simplicity, this is handled by select_color_button when a palette button is clicked.
        # If eraser is selected, the 'white' color is set, but no palette button might be 'sunken'.

    def _toggle_text_bg_options(self):
        """Shows or hides the shape type and color options for text background."""
        if self.add_bg_shape_var.get():
            # Ensure it's packed into text_options_frame, typically after the checkbutton
            if not self.text_bg_details_frame.winfo_ismapped():
                 self.text_bg_details_frame.pack(in_=self.text_options_frame, fill=tk.X, pady=(0,5), padx=2)
        else:
            self.text_bg_details_frame.pack_forget()

    def _pick_text_bg_color(self, color_type):
        """
        Opens a color chooser dialog to select a color for either the fill or
        the outline of the text's background shape. Updates the corresponding
        StringVar and preview swatch.

        Args:
            color_type (str): Either 'fill' or 'outline' to specify which color
                              is being picked.
        """
        from tkinter import colorchooser # Local import

        initial_color = None
        if color_type == 'fill':
            initial_color = self.text_bg_fill_color_var.get()
        elif color_type == 'outline':
            initial_color = self.text_bg_outline_color_var.get()

        color_code = colorchooser.askcolor(title=f"Choose Text Background {color_type.capitalize()} Color",
                                          initialcolor=initial_color, parent=self.top)
        if color_code and color_code[1]: # Check if a color was chosen (color_code[1] is the hex string)
            if color_type == 'fill':
                self.text_bg_fill_color_var.set(color_code[1])
                self.text_bg_fill_preview.config(bg=color_code[1])
            elif color_type == 'outline':
                self.text_bg_outline_color_var.set(color_code[1])
                self.text_bg_outline_preview.config(bg=color_code[1])

    def activate_eraser(self):
        self.set_color("white") # Eraser uses white color
        self.drawing_mode = "pen" # Eraser is like a pen drawing white
        self._deactivate_all_tools_visual()
        if self.eraser_button and hasattr(self.eraser_button, 'state'): # Check if button exists
            self.eraser_button.state(['pressed'])
        self.eraser_button_active = True # Track active state
        self.text_options_frame.pack_forget() # Hide text options

    def activate_text_tool(self):
        self.drawing_mode = "text"
        self._deactivate_all_tools_visual()
        if self.text_tool_button and hasattr(self.text_tool_button, 'state'):
            self.text_tool_button.state(['pressed'])

        # Show text options frame - ensure it's packed within props_group correctly
        # It should be packed relative to other elements in props_group.
        # Assuming props_group's children are fill_pattern_frame, then tools_group etc.
        # Let's find fill_pattern_frame and pack text_options_frame after it, if it exists.
        # Or, more simply, just pack it. If props_group uses .pack, order matters.
        # For now, simple pack:
        # self.text_options_frame.pack(fill=tk.X, pady=5, padx=0) # Simple pack in props_group
        # More controlled packing:
        # Iterate props_group children to find an anchor or pack at end
        # For now, let's assume it's okay to pack it at the end of props_group's current children
        # or try to place it more specifically if props_group structure is simple.
        # If props_group contains [brush_frame, color_frame, fill_pattern_frame], then text_options_frame.

        # Check if props_group exists (it should)
        if hasattr(self, 'props_group') and self.props_group.winfo_exists():
             # Pack text_options_frame into props_group if not already there or visible
            if not self.text_options_frame.winfo_ismapped():
                self.text_options_frame.pack(in_=self.props_group, fill=tk.X, pady=5, padx=0)
        self._toggle_text_bg_options() # Set initial state of sub-options


    def _deactivate_all_tools_visual(self):
        tool_buttons = [
            self.eraser_button, self.text_tool_button, self.highlighter_button,
            self.plain_line_button, self.uni_arrow_button, self.bi_arrow_button,
            self.rectangle_button, self.circle_button, self.triangle_button,
            self.counter_tool_button, self.select_tool_button # Added select button
            # Add self.pen_button here if you implement it
        ]
        for btn in tool_buttons:
            if btn and hasattr(btn, 'state'): # Check if button exists and supports state
                btn.state(['!pressed']) # Remove 'pressed' state using ttk states
        self.eraser_button_active = False # Reset eraser active tracker

    def activate_select_tool(self):
        """Activates the selection tool mode."""
        self._deactivate_all_tools_visual()
        self.drawing_mode = "select"
        if hasattr(self.select_tool_button, 'state'): self.select_tool_button.state(['pressed'])
        self.text_options_frame.pack_forget() # Hide text options
        # Potentially clear any active drawing previews like temp_line or temp_shape
        if self.temp_line_id: self.canvas.delete(self.temp_line_id); self.temp_line_id = None
        if self.temp_shape_id: self.canvas.delete(self.temp_shape_id); self.temp_shape_id = None


    def activate_plain_line_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "plain"
        if hasattr(self.plain_line_button, 'state'): self.plain_line_button.state(['pressed'])
        self.text_options_frame.pack_forget()

    def activate_uni_arrow_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "uni_arrow"
        if hasattr(self.uni_arrow_button, 'state'): self.uni_arrow_button.state(['pressed'])
        self.text_options_frame.pack_forget()

    def activate_bi_arrow_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "bi_arrow"
        if hasattr(self.bi_arrow_button, 'state'): self.bi_arrow_button.state(['pressed'])
        self.text_options_frame.pack_forget()

    def activate_rectangle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "rectangle"
        if hasattr(self.rectangle_button, 'state'): self.rectangle_button.state(['pressed'])
        self.text_options_frame.pack_forget()

    def activate_circle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "circle"
        if hasattr(self.circle_button, 'state'): self.circle_button.state(['pressed'])
        self.text_options_frame.pack_forget()

    def activate_triangle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "triangle"
        if hasattr(self.triangle_button, 'state'): self.triangle_button.state(['pressed'])
        self.text_options_frame.pack_forget()

    def activate_highlighter_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "highlighter"
        if hasattr(self.highlighter_button, 'state'): self.highlighter_button.state(['pressed'])
        self.text_options_frame.pack_forget() # Hide text options

    def activate_counter_tool(self):
        """
        Activates the 'Counter' drawing mode.
        This mode allows placing numbered circles (1-8) on the canvas.
        Resets the counter to 1 each time the tool is selected.
        """
        self._deactivate_all_tools_visual()
        self.drawing_mode = "counter"
        self.current_counter_value = 1 # Reset counter when tool is selected
        if hasattr(self.counter_tool_button, 'state'): self.counter_tool_button.state(['pressed'])
        self.text_options_frame.pack_forget() # Hide text options

    def get_dash_pattern(self):
        """Returns the tkinter dash pattern tuple based on the selected line style."""
        style = self.current_line_dash_style.get()
        if style == "Dashed":
            return (6, 4) # 6px on, 4px off
        elif style == "Dotted":
            return (2, 4) # 2px on, 4px off (long space makes it look dotted)
        elif style == "Dash-Dot":
            return (6, 4, 2, 4) # Dash, space, dot, space
        return () # Solid

    def _setup_text_options_ui(self, parent_props_group):
        """
        Sets up the UI elements specific to the Text tool's background options,
        including enabling background, shape type, and dedicated fill/outline colors.
        This frame is shown/hidden based on whether the Text tool is active.
        Called during __init__.
        """
        # Text tool specific options - Variables
        self.add_bg_shape_var = tk.BooleanVar(value=False)
        self.text_bg_shape_type_var = tk.StringVar(value="Rectangle")
        self.text_bg_fill_color_var = tk.StringVar(value="lightgrey") # Default fill for text bg
        self.text_bg_outline_color_var = tk.StringVar(value="black")   # Default outline for text bg

        self.text_options_frame = ttk.LabelFrame(parent_props_group, text="Text Background", padding=5)
        # This frame is packed/unpacked by tool activation methods.

        self.add_bg_shape_check = ttk.Checkbutton(self.text_options_frame,
                                                  text="Add background shape",
                                                  variable=self.add_bg_shape_var,
                                                  command=self._toggle_text_bg_options)
        self.add_bg_shape_check.pack(fill=tk.X, pady=2, anchor=tk.W)

        self.text_bg_details_frame = ttk.Frame(self.text_options_frame)
        # This sub-frame is packed/unpacked by _toggle_text_bg_options

        # Shape Type
        ttk.Label(self.text_bg_details_frame, text="Shape:").grid(row=0, column=0, sticky=tk.W, padx=(0,2))
        self.text_bg_shape_combo = ttk.Combobox(self.text_bg_details_frame,
                                               textvariable=self.text_bg_shape_type_var,
                                               values=["Rectangle", "Ellipse"],
                                               state="readonly", width=12)
        self.text_bg_shape_combo.grid(row=0, column=1, columnspan=2, padx=(0,5), sticky=tk.EW) # Span to align with color pickers

        # Shape Fill Color
        ttk.Label(self.text_bg_details_frame, text="Fill:").grid(row=1, column=0, sticky=tk.W, pady=(5,0))
        self.text_bg_fill_preview = tk.Frame(self.text_bg_details_frame, width=20, height=20, relief=tk.SUNKEN, borderwidth=1)
        self.text_bg_fill_preview.grid(row=1, column=1, sticky=tk.W, padx=(0,5), pady=(5,0))
        self.text_bg_fill_preview.config(bg=self.text_bg_fill_color_var.get())
        text_bg_fill_button = ttk.Button(self.text_bg_details_frame, text="Choose...",
                                         command=lambda: self._pick_text_bg_color('fill'), width=8)
        text_bg_fill_button.grid(row=1, column=2, sticky=tk.E, pady=(5,0))

        # Shape Outline Color
        ttk.Label(self.text_bg_details_frame, text="Outline:").grid(row=2, column=0, sticky=tk.W, pady=(5,0))
        self.text_bg_outline_preview = tk.Frame(self.text_bg_details_frame, width=20, height=20, relief=tk.SUNKEN, borderwidth=1)
        self.text_bg_outline_preview.grid(row=2, column=1, sticky=tk.W, padx=(0,5), pady=(5,0))
        self.text_bg_outline_preview.config(bg=self.text_bg_outline_color_var.get())
        text_bg_outline_button = ttk.Button(self.text_bg_details_frame, text="Choose...",
                                            command=lambda: self._pick_text_bg_color('outline'), width=8)
        text_bg_outline_button.grid(row=2, column=2, sticky=tk.E, pady=(5,0))

        self.text_bg_details_frame.columnconfigure(1, minsize=30) # Ensure space for preview
        self.text_bg_details_frame.columnconfigure(2, weight=1) # Allow choose button to align E


    def activate_pen_mode(self): # Default drawing mode
        self._deactivate_all_tools_visual()
        self.drawing_mode = "pen"
        self.text_options_frame.pack_forget() # Hide text options
        # No specific button for "pen" is visually activated unless you add one
        # Ensure a color is selected (e.g., the current self.active_color_button)
        if self.active_color_button:
            self.active_color_button.config(relief=tk.SUNKEN, borderwidth=1)
        else: # If no color button was active, select the first one
            if self.color_palette_list:
                first_color_code = self.color_palette_list[0]
                if self.color_palette_frame.winfo_children():
                     self.select_color_button(first_color_code, self.color_palette_frame.winfo_children()[0])

    def _delete_last_drawn(self):
        """Deletes the last drawn logical item/group from the canvas."""
        if self.last_drawn_group_tag:
            self.canvas.delete(self.last_drawn_group_tag)
            self.last_drawn_group_tag = None # Clear the tag
        else:
            messagebox.showinfo("Info", "Nothing to delete (no last drawn item recorded).", parent=self.top)


    def clear_canvas(self):
        if messagebox.askyesno("Clear Canvas", "Are you sure you want to clear the entire canvas?\nThis action cannot be undone (yet!).", parent=self.top):
            self.canvas.delete("all")
            # self.last_drawn_item_ids = [] # No longer used
            self.last_drawn_group_tag = None # Clear last drawn group tag
            self.item_counter = 0 # Reset item counter for tags
            if self.grid_visible: # If grid was visible, reset its state
                self.grid_visible = False
                if hasattr(self, 'apply_grid_button'): # Ensure button exists
                    self.apply_grid_button.config(text="Show Grid")
            self.selected_item_ids.clear() # Clear any active selection
            if self.selection_rect_id: # Remove selection rectangle if present
                # This case should ideally not happen if selection_rect_id is temporary,
                # but good to be defensive.
                # self.canvas.delete(self.selection_rect_id) # Not strictly needed if it's only in draw()
                self.selection_rect_id = None


    def toggle_grid(self):
        """Toggles the visibility of the grid on the canvas."""
        if self.grid_visible:
            self.canvas.delete("grid_line")
            self.grid_visible = False
            self.apply_grid_button.config(text="Show Grid")
        else:
            # Ensure previous grid lines are cleared before drawing new ones,
            # in case dimensions or row/col counts changed.
            self.canvas.delete("grid_line")
            try:
                rows = self.grid_rows_var.get()
                cols = self.grid_cols_var.get()
            except tk.TclError:
                messagebox.showerror("Input Error", "Please enter valid integer values for rows and columns.", parent=self.top)
                return

            if rows < 1 or cols < 1:
                messagebox.showinfo("Info", "Grid requires at least 1 row and 1 column.", parent=self.top)
                return

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                messagebox.showwarning("Canvas Size Error", "Canvas is not ready or too small to draw a grid.", parent=self.top)
                return

            cell_width = canvas_width / cols
            cell_height = canvas_height / rows

            for i in range(1, cols): # Vertical lines
                x = i * cell_width
                self.canvas.create_line(x, 0, x, canvas_height, fill="lightgrey", dash=(2, 2), tags="grid_line")
            for i in range(1, rows): # Horizontal lines
                y = i * cell_height
                self.canvas.create_line(0, y, canvas_width, y, fill="lightgrey", dash=(2, 2), tags="grid_line")

            self.grid_visible = True
            self.apply_grid_button.config(text="Hide Grid")


    def save_canvas_as_png(self):
        try:
            from PIL import ImageGrab # Ensure Pillow is available
        except ImportError:
            messagebox.showerror("Dependency Missing","The 'Pillow' library is not installed. Please install it (e.g., pip install Pillow) to save images.",parent=self.top)
            return

        filepath = filedialog.asksaveasfilename(
            parent=self.top,
            title="Save Canvas As PNG",
            defaultextension=".png",
            initialfile="drawing.png",
            filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")]
        )
        if not filepath: return # User cancelled

        try:
            # Get canvas coordinates relative to the screen
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()

            if width <= 0 or height <= 0: # Check for valid dimensions
                messagebox.showerror("Save Error", "Canvas has no dimensions to capture.", parent=self.top)
                return

            # Ensure UI updates are processed before grabbing
            self.top.update_idletasks()
            # Short delay to ensure canvas is fully rendered, especially if there were recent changes.
            # This can be OS/environment dependent.
            self.canvas.after(200, lambda: self._capture_and_save_png(filepath, x, y, width, height))

        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save canvas as PNG: {e}", parent=self.top)

    def _capture_and_save_png(self, filepath, x, y, width, height):
        try:
            from PIL import ImageGrab
            bbox = (x, y, x + width, y + height)
            image = ImageGrab.grab(bbox=bbox, all_screens=True) # all_screens=True for multi-monitor setups

            if image is None: # Check if grab failed
                messagebox.showerror("Capture Error", "Failed to grab canvas image. Image is None.", parent=self.top)
                return
            if image.width == 0 or image.height == 0:
                messagebox.showerror("Capture Error", "Grabbed image has zero dimensions.", parent=self.top)
                return

            image.save(filepath, "PNG")
            messagebox.showinfo("Save Successful", f"Canvas saved successfully as {filepath}", parent=self.top)
        except Exception as e:
            error_detail = str(e)
            if "grab" in error_detail.lower() and "X server" in error_detail: # Linux specific hint
                error_detail += "\n\nThis might be an issue with screen grabbing on your Linux environment. Ensure necessary tools (e.g., scrot, maim, or X server configuration) are set up if Pillow relies on them."
            elif "Permission denied" in error_detail:
                 error_detail += f"\n\nEnsure you have write permissions for the directory: {os.path.dirname(filepath)}"
            messagebox.showerror("Save Error", f"Could not save canvas as PNG: {error_detail}", parent=self.top)

    def _load_image(self):
        filepath = filedialog.askopenfilename(
            parent=self.top,
            title="Load Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            self.original_image = Image.open(filepath).convert("RGBA")
            self._display_image(self.original_image)
            self.current_filter_var.set("Original")
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load image: {e}", parent=self.top)

    def _display_image(self, pil_image):
        if self.current_canvas_image_id:
            self.canvas.delete(self.current_canvas_image_id)

        self.canvas.config(width=pil_image.width, height=pil_image.height)
        self.displayed_image_tk = ImageTk.PhotoImage(pil_image)
        self.current_canvas_image_id = self.canvas.create_image(
            0, 0,
            anchor=tk.NW, image=self.displayed_image_tk
        )
        self.canvas.tag_lower(self.current_canvas_image_id)

    def apply_selected_filter(self, event=None):
        if not self.original_image:
            messagebox.showinfo("No Image", "Please load an image first.", parent=self.top)
            self.current_filter_var.set("Original")
            return

        filter_name = self.current_filter_var.get()
        filtered_image = None

        if filter_name == "Original":
            filtered_image = self.original_image
        elif filter_name == "Sketch":
            filtered_image = self._apply_sketch_filter()
        elif filter_name == "Cartoonify":
            filtered_image = self._apply_cartoonify_filter()
        elif filter_name == "Oil Painting":
            filtered_image = self._apply_oil_painting_filter()
        elif filter_name == "Posterize":
            filtered_image = self._apply_posterize_filter()
        elif filter_name == "Edge Enhance":
            filtered_image = self._apply_edge_enhance_filter()
        elif filter_name == "Emboss":
            filtered_image = self._apply_emboss_filter()
        elif filter_name == "Solarize":
            filtered_image = self._apply_solarize_filter()
        elif filter_name == "Blur":
            filtered_image = self._apply_blur_filter()
        elif filter_name == "Mosaic":
            filtered_image = self._apply_mosaic_filter()
        elif filter_name == "Sepia":
            filtered_image = self._apply_sepia_filter()
        elif filter_name == "Black and White":
            filtered_image = self._apply_bw_filter()

        if filtered_image:
            self._display_image(filtered_image)

    def _pil_to_cv2(self, pil_image):
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)

    def _cv2_to_pil(self, cv2_image):
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGRA2RGBA))

    def _apply_sketch_filter(self):
        img_cv = self._pil_to_cv2(self.original_image)
        grey_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        invert = cv2.bitwise_not(grey_img)
        blur = cv2.GaussianBlur(invert, (21, 21), 0)
        inverted_blur = cv2.bitwise_not(blur)
        sketch = cv2.divide(grey_img, inverted_blur, scale=256.0)
        return self._cv2_to_pil(cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR))

    def _apply_cartoonify_filter(self):
        img_cv = self._pil_to_cv2(self.original_image)
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2RGB)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img_rgb, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        return self._cv2_to_pil(cartoon)

    def _apply_oil_painting_filter(self):
        img_cv = self._pil_to_cv2(self.original_image)
        oil_painting = cv2.xphoto.oilPainting(img_cv, 7, 1)
        return self._cv2_to_pil(oil_painting)

    def _apply_posterize_filter(self):
        return ImageOps.posterize(self.original_image.convert("RGB"), 3)

    def _apply_edge_enhance_filter(self):
        return self.original_image.filter(ImageFilter.EDGE_ENHANCE_MORE)

    def _apply_emboss_filter(self):
        return self.original_image.filter(ImageFilter.EMBOSS)

    def _apply_solarize_filter(self):
        return ImageOps.solarize(self.original_image.convert("RGB"), threshold=128)

    def _apply_blur_filter(self):
        return self.original_image.filter(ImageFilter.GaussianBlur(5))

    def _apply_mosaic_filter(self):
        img = self.original_image.copy()
        size = 16
        img = img.resize((img.width // size, img.height // size), Image.NEAREST)
        img = img.resize((img.width * size, img.height * size), Image.NEAREST)
        return img

    def _apply_sepia_filter(self):
        img = self.original_image.convert("RGB")
        width, height = img.size
        pixels = img.load()

        for py in range(height):
            for px in range(width):
                r, g, b = img.getpixel((px, py))
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                if tr > 255: tr = 255
                if tg > 255: tg = 255
                if tb > 255: tb = 255
                pixels[px, py] = (tr, tg, tb)
        return img

    def _apply_bw_filter(self):
        return self.original_image.convert("L")

    def toggle_maximize(self, event=None):
        if self.is_maximized:
            self.unmaximize()
        else:
            self.top.attributes("-fullscreen", True)
            self.is_maximized = True

    def unmaximize(self, event=None):
        self.top.attributes("-fullscreen", False)
        self.is_maximized = False

    def apply_image_adjustments(self, event=None):
        if not self.original_image:
            return

        brightness = self.brightness_scale.get()
        contrast = self.contrast_scale.get()
        transparency = self.transparency_scale.get()

        # Start with the original image
        adjusted_image = self.original_image.copy()

        # Apply brightness
        enhancer = ImageEnhance.Brightness(adjusted_image)
        adjusted_image = enhancer.enhance(brightness)

        # Apply contrast
        enhancer = ImageEnhance.Contrast(adjusted_image)
        adjusted_image = enhancer.enhance(contrast)

        # Apply transparency
        if adjusted_image.mode != 'RGBA':
            adjusted_image = adjusted_image.convert('RGBA')
        alpha = adjusted_image.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(transparency)
        adjusted_image.putalpha(alpha)

        self._display_image(adjusted_image)
