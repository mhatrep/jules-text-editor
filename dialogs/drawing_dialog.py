import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from PIL import ImageGrab # For saving canvas

class DrawingDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root # TextEditor's root
        self.top = tk.Toplevel(self.root)
        self.top.title("Drawing Tool")
        self.top.transient(self.root) # Keep on top of parent
        # self.top.grab_set() # Modal, if desired
        self.top.resizable(True, True)

        self.current_brush_size = 5
        self.current_color = "black"
        self.drawing_mode = "pen"  # Modes: "pen", "eraser", "line", "rectangle", "circle", "triangle", "text", "highlighter"
        self.line_style = "plain" # For line tool: "plain", "uni_arrow", "bi_arrow"
        self.last_x, self.last_y = None, None
        self.line_start_x, self.line_start_y = None, None # For line/shape drawing
        self.temp_line_id = None # For previewing lines
        self.shape_start_x, self.shape_start_y = None, None
        self.temp_shape_id = None # For previewing shapes

        self.highlighter_stipple = "gray25" # Stipple for highlighter
        self.stipple_patterns = ["Solid Fill", "gray75", "gray50", "gray25", "gray12", "hourglass", "info", "questhead", "error", "warning"]
        self.current_fill_pattern_var = tk.StringVar(value=self.stipple_patterns[0])
        self.grid_rows_var = tk.IntVar(value=3)
        self.grid_cols_var = tk.IntVar(value=3)

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
        self.apply_grid_button = None # Added
        self.active_color_button = None # To track the selected color button

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

        self.basic_colors = { # Name: Hex
            "Black": "#000000", "LightRed": "#FF9999", "LightBlue": "#ADD8E6",
            "LightGreen": "#90EE90", "Yellow": "#FFFFE0" # Common highlighter yellow
        }
        self.color_palette_list = list(self.basic_colors.values()) # Order matters for display

        if self.current_color not in self.color_palette_list:
            self.current_color = self.color_palette_list[0] if self.color_palette_list else "#000000"


        num_color_cols = 5
        for i, color_code in enumerate(self.color_palette_list):
            color_btn_widget = tk.Frame(self.color_palette_frame, width=22, height=22, bg=color_code, relief=tk.RAISED, borderwidth=1)
            color_btn_widget.grid(row=i // num_color_cols, column=i % num_color_cols, padx=1, pady=1)
            color_btn_widget.bind("<Button-1>", lambda e, c=color_code, btn=color_btn_widget: self.select_color_button(c, btn))
            if color_code == self.current_color: # Highlight initially selected color
                 self.select_color_button(color_code, color_btn_widget)

        if not self.active_color_button and self.color_palette_list: # Ensure one is active
            first_color_code = self.color_palette_list[0]
            if self.color_palette_frame.winfo_children(): # Check if buttons were actually created
                 self.select_color_button(first_color_code, self.color_palette_frame.winfo_children()[0])


        # Fill Pattern (for shapes)
        fill_pattern_frame = ttk.Frame(props_group)
        fill_pattern_frame.pack(fill=tk.X, pady=(5,2))
        ttk.Label(fill_pattern_frame, text="Fill:").pack(side=tk.LEFT, padx=(0,2))
        self.fill_pattern_combo = ttk.Combobox(fill_pattern_frame, textvariable=self.current_fill_pattern_var,
                                               values=self.stipple_patterns, state="readonly", width=10)
        self.fill_pattern_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)


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
        # Pen button can be implicit or added if needed
        # self.pen_button = ttk.Button(basic_tools_subframe, text="Pen", command=self.activate_pen_mode, width=btn_width)
        # self.pen_button.grid(row=1, column=1, padx=1, pady=1, sticky="ew")


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

        self.apply_grid_button = ttk.Button(grid_controls_frame, text="Apply Grid", command=self.draw_grid_on_canvas)
        self.apply_grid_button.pack(fill=tk.X, pady=(3,0))


        # Clear and Save
        clear_save_frame = ttk.Frame(actions_group)
        clear_save_frame.pack(fill=tk.X, pady=(5,0))
        clear_button = ttk.Button(clear_save_frame, text="Clear Canvas", command=self.clear_canvas)
        clear_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,1))
        save_png_button = ttk.Button(clear_save_frame, text="Save as PNG", command=self.save_canvas_as_png)
        save_png_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(1,0))


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
            self.canvas.create_oval(x1, y1, x2, y2, fill=self.current_color, outline=self.current_color, width=0) # No outline for smooth dot
        elif self.drawing_mode == "text":
            user_text = simpledialog.askstring("Input Text", "Enter text to place on canvas:", parent=self.top)
            if user_text:
                font_size = max(20, int(self.current_brush_size * 3)) # Scale font with brush size
                text_font = ("Arial", font_size, "bold") # Example font
                self.canvas.create_text(event.x, event.y, text=user_text, fill=self.current_color, font=text_font, anchor=tk.NW)
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
            self.canvas.create_oval(x1, y1, x2, y2, fill=self.current_color, outline=self.current_color, width=0, stipple=self.highlighter_stipple)


    def draw(self, event):
        if self.drawing_mode == "pen":
            if self.last_x and self.last_y:
                self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                        width=self.current_brush_size, fill=self.current_color,
                                        capstyle=tk.ROUND, smooth=tk.TRUE, splinesteps=128) # Smoother lines
                # Also draw small ovals at points for smoother appearance if brush is large
                x1_pen, y1_pen = (event.x - self.current_brush_size / 2), (event.y - self.current_brush_size / 2)
                x2_pen, y2_pen = (event.x + self.current_brush_size / 2), (event.y + self.current_brush_size / 2)
                self.canvas.create_oval(x1_pen, y1_pen, x2_pen, y2_pen, fill=self.current_color, outline=self.current_color)
                self.last_x, self.last_y = event.x, event.y
        elif self.drawing_mode == "highlighter":
            if self.last_x and self.last_y:
                highlighter_brush_size = max(10, self.current_brush_size * 2)
                self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                        width=highlighter_brush_size, fill=self.current_color,
                                        capstyle=tk.ROUND, smooth=tk.FALSE, # Highlighter is usually not smoothed
                                        stipple=self.highlighter_stipple)
                self.last_x, self.last_y = event.x, event.y

        elif self.drawing_mode == "line":
            if self.line_start_x is not None and self.line_start_y is not None:
                if self.temp_line_id:
                    self.canvas.delete(self.temp_line_id)
                self.temp_line_id = self.canvas.create_line(self.line_start_x, self.line_start_y, event.x, event.y,
                                                            width=self.current_brush_size, fill=self.current_color,
                                                            capstyle=tk.ROUND) # Preview line
        elif self.drawing_mode in ["rectangle", "circle", "triangle"]:
            if self.shape_start_x is not None and self.shape_start_y is not None:
                if self.temp_shape_id:
                    self.canvas.delete(self.temp_shape_id)
                x1, y1 = self.shape_start_x, self.shape_start_y
                x2, y2 = event.x, event.y
                # Ensure x1 < x2 and y1 < y2 for rectangle/oval
                draw_x1, draw_y1 = min(x1,x2), min(y1,y2)
                draw_x2, draw_y2 = max(x1,x2), max(y1,y2)

                if self.drawing_mode == "rectangle":
                    self.temp_shape_id = self.canvas.create_rectangle(draw_x1, draw_y1, draw_x2, draw_y2,
                                                                    outline=self.current_color, width=self.current_brush_size,
                                                                    fill="", stipple="") # Preview outline
                elif self.drawing_mode == "circle":
                    self.temp_shape_id = self.canvas.create_oval(draw_x1, draw_y1, draw_x2, draw_y2,
                                                                 outline=self.current_color, width=self.current_brush_size,
                                                                 fill="", stipple="") # Preview outline
                elif self.drawing_mode == "triangle":
                    # For triangle, points are (mid-top, bottom-left, bottom-right)
                    p1 = ((x1 + x2) / 2, y1)
                    p2 = (x1, y2)
                    p3 = (x2, y2)
                    self.temp_shape_id = self.canvas.create_polygon(p1, p2, p3,
                                                                    outline=self.current_color, width=self.current_brush_size,
                                                                    fill="", stipple="") # Preview outline

    def stop_draw(self, event):
        if self.drawing_mode == "pen":
            self.last_x, self.last_y = None, None
        elif self.drawing_mode == "highlighter":
            self.last_x, self.last_y = None, None
        elif self.drawing_mode == "line":
            if self.temp_line_id: # Delete preview
                self.canvas.delete(self.temp_line_id)
                self.temp_line_id = None
            if self.line_start_x is not None and self.line_start_y is not None:
                x1, y1 = self.line_start_x, self.line_start_y
                x2, y2 = event.x, event.y
                arrow_option = tk.NONE
                if self.line_style == "uni_arrow": arrow_option = tk.LAST
                elif self.line_style == "bi_arrow": arrow_option = tk.BOTH
                arrow_shape_spec = (10, 12, 5) # Adjust arrow shape (base, length, width)
                self.canvas.create_line(x1, y1, x2, y2, width=self.current_brush_size, fill=self.current_color,
                                        arrow=arrow_option, arrowshape=arrow_shape_spec, capstyle=tk.ROUND)
            self.line_start_x, self.line_start_y = None, None
        elif self.drawing_mode in ["rectangle", "circle", "triangle"]:
            if self.temp_shape_id: # Delete preview
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

                if self.drawing_mode == "rectangle":
                    self.canvas.create_rectangle(draw_x1, draw_y1, draw_x2, draw_y2,
                                                 fill=self.current_color, outline=self.current_color, # Fill with current color
                                                 width=0, stipple=stipple_option) # No border, use fill
                elif self.drawing_mode == "circle":
                    self.canvas.create_oval(draw_x1, draw_y1, draw_x2, draw_y2,
                                            fill=self.current_color, outline=self.current_color,
                                            width=0, stipple=stipple_option)
                elif self.drawing_mode == "triangle":
                    p1_x, p1_y = (x1 + x2) / 2, y1 # Mid-top
                    p2_x, p2_y = x1, y2          # Bottom-left
                    p3_x, p3_y = x2, y2          # Bottom-right
                    self.canvas.create_polygon(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y,
                                               fill=self.current_color, outline=self.current_color,
                                               width=0, stipple=stipple_option)
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

    def activate_eraser(self):
        self.set_color("white") # Eraser uses white color
        self.drawing_mode = "pen" # Eraser is like a pen drawing white
        self._deactivate_all_tools_visual()
        if self.eraser_button and hasattr(self.eraser_button, 'state'): # Check if button exists
            self.eraser_button.state(['pressed'])
        self.eraser_button_active = True # Track active state

    def activate_text_tool(self):
        self.drawing_mode = "text"
        self._deactivate_all_tools_visual()
        if self.text_tool_button and hasattr(self.text_tool_button, 'state'):
            self.text_tool_button.state(['pressed'])

    def _deactivate_all_tools_visual(self):
        tool_buttons = [
            self.eraser_button, self.text_tool_button, self.highlighter_button,
            self.plain_line_button, self.uni_arrow_button, self.bi_arrow_button,
            self.rectangle_button, self.circle_button, self.triangle_button
            # Add self.pen_button here if you implement it
        ]
        for btn in tool_buttons:
            if btn and hasattr(btn, 'state'): # Check if button exists and supports state
                btn.state(['!pressed']) # Remove 'pressed' state using ttk states
        self.eraser_button_active = False # Reset eraser active tracker


    def activate_plain_line_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "plain"
        if hasattr(self.plain_line_button, 'state'): self.plain_line_button.state(['pressed'])

    def activate_uni_arrow_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "uni_arrow"
        if hasattr(self.uni_arrow_button, 'state'): self.uni_arrow_button.state(['pressed'])

    def activate_bi_arrow_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "line"
        self.line_style = "bi_arrow"
        if hasattr(self.bi_arrow_button, 'state'): self.bi_arrow_button.state(['pressed'])

    def activate_rectangle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "rectangle"
        if hasattr(self.rectangle_button, 'state'): self.rectangle_button.state(['pressed'])

    def activate_circle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "circle"
        if hasattr(self.circle_button, 'state'): self.circle_button.state(['pressed'])

    def activate_triangle_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "triangle"
        if hasattr(self.triangle_button, 'state'): self.triangle_button.state(['pressed'])

    def activate_highlighter_mode(self):
        self._deactivate_all_tools_visual()
        self.drawing_mode = "highlighter"
        if hasattr(self.highlighter_button, 'state'): self.highlighter_button.state(['pressed'])

    def activate_pen_mode(self): # Default drawing mode
        self._deactivate_all_tools_visual()
        self.drawing_mode = "pen"
        # No specific button for "pen" is visually activated unless you add one
        # Ensure a color is selected (e.g., the current self.active_color_button)
        if self.active_color_button:
            self.active_color_button.config(relief=tk.SUNKEN, borderwidth=1)
        else: # If no color button was active, select the first one
            if self.color_palette_list:
                first_color_code = self.color_palette_list[0]
                if self.color_palette_frame.winfo_children():
                     self.select_color_button(first_color_code, self.color_palette_frame.winfo_children()[0])


    def clear_canvas(self):
        if messagebox.askyesno("Clear Canvas", "Are you sure you want to clear the entire canvas?\nThis action cannot be undone (yet!).", parent=self.top):
            self.canvas.delete("all")

    def draw_grid_on_canvas(self):
        self.canvas.delete("grid_line") # Remove old grid lines
        try:
            rows = self.grid_rows_var.get()
            cols = self.grid_cols_var.get()
        except tk.TclError: # Handle cases where spinbox might have non-integer temp values
            messagebox.showerror("Input Error", "Please enter valid integer values for rows and columns.", parent=self.top)
            return

        if rows < 1 or cols < 1: return # No grid if rows/cols are less than 1

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1: # Canvas not ready
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
