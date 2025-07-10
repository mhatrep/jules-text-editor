from PIL import ImageGrab, Image, UnidentifiedImageError

def capture_screen_region(bbox=None):
    """
    Captures a specific region of the screen.
    bbox: A 4-tuple (left, top, right, bottom) defining the region.
          If None, captures the primary screen.
    Returns a Pillow Image object or None if capture fails.
    """
    try:
        image = ImageGrab.grab(bbox=bbox, all_screens=False) # all_screens=False for specific bbox
        return image
    except Exception as e:
        print(f"Error capturing screen region: {e}")
        # Could be due to various reasons, e.g., on Linux if a backend like scrot is not installed.
        # Or if bbox is invalid in some OS contexts.
        return None

def capture_full_screen(all_screens_if_possible=True):
    """
    Captures the full screen.
    all_screens_if_possible: If True, attempts to capture all screens as a composite image.
                             If False, captures only the primary screen.
    Returns a Pillow Image object or None if capture fails.
    """
    try:
        # Pillow's all_screens=True can be unreliable or behave differently across OSes
        # for true multi-monitor stitched capture. Defaulting to all_screens=False
        # to capture only the primary monitor for more predictable behavior.
        # A more advanced solution would require OS-specific APIs or different libraries
        # to get individual screen geometries and capture them.
        image = ImageGrab.grab(all_screens=False) # Changed to False for predictability
        return image
    except Exception as e:
        print(f"Error capturing full screen (primary monitor): {e}")
        return None

if __name__ == '__main__':
    # Basic test (will require manual verification of saved files)
    print("Testing screenshot utilities...")

    # Test 1: Full primary screen
    # print("Capturing full primary screen (in 3 seconds)...")
    # import time
    # time.sleep(3)
    # full_screen_img = capture_full_screen(all_screens_if_possible=False)
    # if full_screen_img:
    #     full_screen_img.save("test_fullscreen_primary.png")
    #     print("Saved test_fullscreen_primary.png")
    #     # full_screen_img.show() # Opens in default image viewer
    # else:
    #     print("Failed to capture full primary screen.")

    # Test 2: Specific region (example coordinates, adjust for your screen)
    # These coordinates are arbitrary and likely need adjustment for a meaningful test.
    # print("Capturing region (100, 100, 500, 500) (in 3 seconds)...")
    # time.sleep(3)
    # region_bbox = (100, 100, 500, 500) # x1, y1, x2, y2
    # region_img = capture_screen_region(bbox=region_bbox)
    # if region_img:
    #     region_img.save("test_region.png")
    #     print(f"Saved test_region.png (size: {region_img.size})")
    #     # region_img.show()
    # else:
    #     print(f"Failed to capture region {region_bbox}.")

    # print("Testing complete. Manually verify saved images if any.")
    pass # Keep __main__ minimal for library code


import tkinter as tk

class RegionSelector:
    def __init__(self, master_root):
        self.master_root = master_root # The main Tkinter root of the application
        self.overlay = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.selected_bbox = None

    def _on_mouse_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                    outline='red', width=2, dash=(4, 2))

    def _on_mouse_drag(self, event):
        if self.start_x is None or self.start_y is None:
            return
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def _on_mouse_release(self, event):
        if self.start_x is None or self.start_y is None: # Should not happen if drag started
            if self.overlay:
                self.overlay.destroy()
            return

        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        # Ensure x1 < x2 and y1 < y2 for the bbox
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        # Check if the selection has a valid area
        if x2 - x1 > 0 and y2 - y1 > 0:
            # Adjust coordinates relative to the screen, not just the overlay window
            # The overlay is full-screen, so its top-left (0,0) is screen's top-left
            # However, Tkinter window geometry might have offsets or be on a specific screen.
            # For ImageGrab.grab(bbox=...), coordinates are usually expected to be screen coordinates.
            # If the overlay truly covers all screens and its (0,0) matches the virtual screen (0,0),
            # then these canvas coordinates might be directly usable.
            # This needs careful testing, especially with multi-monitor setups and different OS.
            # For now, assume direct mapping from canvas (overlay) coords to screen coords.
            # The overlay's (0,0) is self.overlay.winfo_x/y() on screen. But since it's fullscreen borderless,
            # these should be 0 or close to it for the primary.
            # For multi-monitor, ImageGrab behaviour with bbox can vary.
            # Let's assume for now the overlay covers the primary screen and coordinates are relative to it.
            # A more robust solution might involve querying screen geometry for all monitors.

            # Get overlay window's top-left screen coordinates
            # This is important if the overlay itself isn't at screen (0,0)
            # (though it should be if set up as borderless fullscreen)
            overlay_x_offset = self.overlay.winfo_rootx()
            overlay_y_offset = self.overlay.winfo_rooty()

            self.selected_bbox = (
                x1 + overlay_x_offset,
                y1 + overlay_y_offset,
                x2 + overlay_x_offset,
                y2 + overlay_y_offset
            )
        else:
            self.selected_bbox = None # No valid region selected

        if self.overlay:
            self.overlay.destroy() # Close the overlay window
        self.master_root.deiconify() # Show the main window again if it was hidden


    def select_region(self):
        """
        Shows a full-screen overlay for region selection.
        Returns the selected bounding box (x1, y1, x2, y2) in screen coordinates,
        or None if selection was cancelled or invalid.
        """
        self.master_root.withdraw() # Hide the main window temporarily

        self.overlay = tk.Toplevel(self.master_root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-alpha", 0.3)  # Semi-transparent
        self.overlay.attributes("-topmost", True) # Ensure it's on top

        # On some systems, a very slight delay might be needed for the window to actually hide
        # before grabbing focus with the new overlay.
        # self.overlay.after(50, self._setup_overlay_canvas) # Slight delay
        self._setup_overlay_canvas() # Try without delay first

        # This makes the RegionSelector modal in a way, by waiting for it to close.
        # The master_root.wait_window(self.overlay) call ensures that select_region()
        # doesn't return until the overlay is destroyed.
        self.master_root.wait_window(self.overlay)

        return self.selected_bbox

    def _setup_overlay_canvas(self):
        self.canvas = tk.Canvas(self.overlay, cursor="crosshair", bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)

        # Allow Esc to cancel
        self.overlay.bind("<Escape>", lambda e: self._cancel_selection())
        self.overlay.focus_force() # Grab focus

    def _cancel_selection(self):
        self.selected_bbox = None
        if self.overlay:
            self.overlay.destroy()
        self.master_root.deiconify()


# Example Usage (for testing RegionSelector directly):
# if __name__ == '__main__':
#     root = tk.Tk()
#     # root.withdraw() # Hide main window initially for this test

#     def perform_selection():
#         root.withdraw() # Hide before selection
#         selector = RegionSelector(root)
#         bbox = selector.select_region() # This will block until selection is done or overlay closed

#         # Root window is deiconified by selector on completion/cancel
#         # root.deiconify() # No longer needed here if selector handles it

#         if bbox:
#             print(f"Selected BBox: {bbox}")
#             # Try to capture with these coordinates
#             # Note: This capture happens *after* the overlay is gone.
#             # A slight delay might be needed for the screen to refresh if main window was hidden.
#             root.after(100, lambda: _capture_and_show_selected_region(bbox))
#         else:
#             print("Region selection cancelled or invalid.")
#             root.deiconify() # Ensure main window is shown if cancelled early

#     def _capture_and_show_selected_region(bbox):
#         captured_image = capture_screen_region(bbox)
#         if captured_image:
#             try:
#                 captured_image.save("test_region_selected.png")
#                 print(f"Saved test_region_selected.png (size: {captured_image.size})")
#                 captured_image.show()
#             except Exception as e:
#                 print(f"Error saving or showing image: {e}")
#         else:
#             print("Failed to capture selected region.")
#         root.quit() # Exit Tkinter mainloop after test

#     # Button to start selection
#     select_button = tk.Button(root, text="Select Region", command=perform_selection)
#     select_button.pack(pady=20)
#     root.mainloop()
