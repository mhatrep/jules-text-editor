from PIL import ImageGrab, Image, UnidentifiedImageError

def capture_screen_region(bbox=None):
    """
    Captures a specific region of the screen.
    bbox: A 4-tuple (left, top, right, bottom) defining the region.
          If None, captures the primary screen.
    Returns a Pillow Image object or None if capture fails.
    """
    # Note on multi-monitor for region capture:
    # If all_screens=True were used with a bbox, the bbox coordinates would need to be
    # relative to the entire virtual screen space. The current RegionSelector provides
    # coordinates relative to its overlay (typically on the primary screen).
    # Therefore, all_screens=False is used for predictable behavior with the current
    # RegionSelector, limiting capture to the screen where the region was selected (usually primary).
    # True multi-monitor region selection would require a more advanced RegionSelector
    # and potentially different capture libraries or OS-specific APIs.
    try:
        image = ImageGrab.grab(bbox=bbox, all_screens=False) # all_screens=False for specific bbox
        return image
    except Exception as e:
        print(f"Error capturing screen region (bbox={bbox}, all_screens=False): {e}")
        # Could be due to various reasons, e.g., on Linux if a backend like scrot is not installed.
        # Or if bbox is invalid in some OS contexts.
        return None

def capture_full_screen(monitor_number=None):
    """
    Captures the full screen of a specified monitor, or all screens.
    monitor_number: The mss monitor number (1 for primary, 2 for secondary, etc.).
                    If 0, captures the entire virtual screen (all monitors combined via mss).
                    If None, attempts to use Pillow's ImageGrab for primary or all (legacy behavior, less reliable for multi).
    Returns a Pillow Image object or None if capture fails.
    """
    try:
        import mss
        import mss.tools
        from PIL import Image # Ensure Image is imported for conversion

        if monitor_number is not None: # Use mss for specific monitor or all_monitors[0]
            with mss.mss() as sct:
                if monitor_number < 0: # Should not happen if UI provides valid numbers
                    raise ValueError("Monitor number must be non-negative.")

                if monitor_number == 0: # mss.monitors[0] is the full virtual screen
                    monitor_definition = sct.monitors[0]
                    print(f"Attempting to capture full virtual screen (all monitors via mss): {monitor_definition}")
                elif monitor_number > 0 and monitor_number < len(sct.monitors):
                    monitor_definition = sct.monitors[monitor_number]
                    print(f"Attempting to capture monitor {monitor_number} via mss: {monitor_definition}")
                else:
                    print(f"Invalid monitor number {monitor_number} for mss (available: {len(sct.monitors)-1} physical). Falling back.")
                    # Fallback to Pillow's all_screens attempt if monitor_number is out of mss range
                    # This part of fallback might be removed if UI strictly uses get_available_monitors
                    return capture_full_screen(monitor_number=None) # Recursive call for fallback

                sct_img = sct.grab(monitor_definition)

                # Convert the mss BGRA/BGR SShot object to a PIL Image
                img = Image.frombytes("RGB", (sct_img.width, sct_img.height), sct_img.rgb, "raw", "BGR")
                # mss typically provides BGRA, but sct_img.rgb gives BGR. If alpha is needed:
                # img = Image.frombytes('RGBA', (sct_img.width, sct_img.height), sct_img.bgra, 'raw', 'BGRA')
                print(f"Captured via mss. Resulting image size: {img.size}")
                return img
        else:
            # Legacy/Fallback behavior: Use Pillow's ImageGrab (less reliable for multi-monitor)
            # Defaulting to all_screens=True for Pillow's attempt at composite
            print("Attempting capture with Pillow ImageGrab (all_screens=True, may be primary or composite).")
            pil_image = ImageGrab.grab(all_screens=True)
            if pil_image:
                print(f"Captured via Pillow ImageGrab. Resulting image size: {pil_image.size}")
            return pil_image

    except ImportError:
        print("MSS library not found. Falling back to Pillow ImageGrab for full screen capture.")
        try:
            pil_image_fallback = ImageGrab.grab(all_screens=True) # Try all screens with Pillow
            if pil_image_fallback:
                 print(f"Captured via Pillow ImageGrab (fallback). Resulting image size: {pil_image_fallback.size}")
            return pil_image_fallback
        except Exception as e_pil:
            print(f"Error during fallback Pillow ImageGrab full screen capture: {e_pil}")
            return None
    except Exception as e:
        print(f"Error capturing full screen (monitor_number={monitor_number}): {e}")
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
        # self.master_root.deiconify() # REMOVED: Calling code will handle de-iconifying


    def select_region(self):
        """
        Shows a full-screen overlay (typically on the primary monitor) for region selection.
        Returns the selected bounding box (x1, y1, x2, y2) in screen coordinates
        (relative to the virtual screen, but selection is usually limited to the primary monitor),
        or None if selection was cancelled or invalid.
        For true cross-monitor region selection, this class would need significant enhancements.
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
        # self.master_root.deiconify() # REMOVED: Calling code will handle de-iconifying


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

def get_available_monitors():
    """
    Uses mss to get a list of available monitors.
    Returns a list of tuples: (monitor_mss_idx, description_string)
    monitor_mss_idx: The index to be used with `sct.monitors[]`.
                     Typically, 0 is the full virtual screen, 1 is the primary physical monitor, etc.
    description_string: A human-readable string describing the monitor and its geometry.
    Returns an empty list if mss is not available or fails to initialize.
    """
    try:
        import mss
        import mss.exception
    except ImportError:
        print("MSS library not found. Please install it: pip install mss")
        return [] # No mss, no monitors.

    monitors_info = []
    try:
        with mss.mss() as sct:
            # sct.monitors[0] is the "all-in-one" monitor (full virtual screen).
            # Physical monitors typically start from sct.monitors[1].
            if not sct.monitors:
                print("MSS reported no monitors.")
                return []

            # Add the "All Monitors (Composite)" option, using monitor index 0 for mss
            # This is sct.monitors[0] by mss convention (the full virtual desktop)
            all_screens_monitor = sct.monitors[0]
            monitors_info.append(
                (0, f"All Monitors (Virtual Screen): {all_screens_monitor['width']}x{all_screens_monitor['height']} at ({all_screens_monitor['left']},{all_screens_monitor['top']})")
            )

            # Add individual physical monitors
            # mss.monitors[1], mss.monitors[2], ... are physical monitors.
            for monitor_mss_index in range(1, len(sct.monitors)):
                monitor = sct.monitors[monitor_mss_index]
                # User-facing number will be monitor_mss_index (e.g., Monitor 1, Monitor 2)
                desc = f"Monitor {monitor_mss_index}: {monitor['width']}x{monitor['height']} at ({monitor['left']},{monitor['top']})"
                monitors_info.append((monitor_mss_index, desc)) # Store true mss index for later use

    except mss.exception.ScreenShotError as e:
        print(f"MSS ScreenShotError (likely no display server or other init issue): {e}")
        return [] # Return empty list if MSS cannot initialize

    return monitors_info

if __name__ == '__main__':
    # ... (existing test code for RegionSelector and headless capture) ...

    # Test get_available_monitors
    print("\nTesting monitor detection:")
    available_monitors = get_available_monitors()
    if available_monitors:
        print("Available monitors:")
        for mss_idx, desc in available_monitors: # mss_idx is the actual index for sct.monitors
            print(f"  MSS Index: {mss_idx}, Description: {desc}")
    else:
        print("No monitors detected by MSS or MSS not available/initializable.")

    print("\nTesting capture_full_screen (will attempt monitor 1, then fallback):")
    # First, try with a specific monitor_number (e.g., 1 for primary physical if mss worked)
    # In headless, mss will fail, so it should go through fallback paths.
    img_mon1 = capture_full_screen(monitor_number=1)
    if img_mon1:
        img_mon1.save("test_capture_monitor1_or_fallback.png")
        print("Saved test_capture_monitor1_or_fallback.png")
    else:
        print("Failed to capture with monitor_number=1 attempt (or its fallback).")

    print("\nTesting capture_full_screen (monitor_number=0 for 'All Virtual Screen' via mss, then fallback):")
    img_mon0 = capture_full_screen(monitor_number=0)
    if img_mon0:
        img_mon0.save("test_capture_monitor0_or_fallback.png")
        print("Saved test_capture_monitor0_or_fallback.png")
    else:
        print("Failed to capture with monitor_number=0 attempt (or its fallback).")

    print("\nTesting capture_full_screen (monitor_number=None for legacy Pillow attempt):")
    img_none = capture_full_screen(monitor_number=None)
    if img_none:
        img_none.save("test_capture_monitorNone_pillow.png")
        print("Saved test_capture_monitorNone_pillow.png")
    else:
        print("Failed to capture with monitor_number=None attempt.")


def ask_monitor_selection_dialog(parent_root, monitors):
    """
    Displays a dialog to select a monitor from the provided list.
    parent_root: The parent Tkinter window for the dialog.
    monitors: A list of (monitor_mss_idx, description_string) tuples,
              typically generated by `get_available_monitors()`.
    Returns the selected monitor_mss_idx (e.g., 0 for all, 1 for monitor 1),
              or None if the dialog is cancelled.
    """
    if not monitors:
        return None # No monitors to choose from

    if len(monitors) == 1 and monitors[0][0] == 0: # Only "All Monitors (Virtual Screen)"
        # If only the virtual screen option is there (e.g. single physical monitor setup or mss only reports that)
        # we can arguably just return that without prompting, or prompt if we want to be explicit.
        # For now, let's assume if only "All" is present, we select it.
        # However, get_available_monitors() should ideally always list physical monitors if present.
        # If get_available_monitors returns [(0, "All...")] and [(1, "Monitor 1...")], this case is fine.
        # This condition is more for if mss *only* gives the virtual screen.
        # Let's assume the list always has at least "All" (idx 0) and potentially physicals (idx 1+).
        # If only "All" and one physical, that's two options. If only "All", then it's one.
        # Let's only skip dialog if there's truly only one option, and that option is monitor 0 (All).
        # A more robust check: if there's only one *type* of choice.
        # If only one monitor is available (e.g. "All Monitors" if it's the only one, or one physical if mss lists it that way)
        # then no need to ask.
        # The current get_available_monitors always adds "All" (idx 0) first.
        # So if len(monitors) == 1, it must be "All".
        if len(monitors) == 1:
             print("Only one monitor option ('All Monitors') available, selecting by default.")
             return monitors[0][0] # Return the index (0)

    import tkinter as tk # Local import for dialog
    from tkinter import simpledialog, ttk

    # Using a Toplevel dialog for better control over layout
    dialog = tk.Toplevel(parent_root)
    dialog.title("Select Monitor")
    dialog.transient(parent_root)
    dialog.grab_set() # Make modal

    # Center dialog
    parent_root.update_idletasks()
    dialog_width = 350
    dialog_height = 150 + (len(monitors) * 20) # Adjust height based on number of monitors
    dialog_height = min(max(dialog_height, 150), 400) # Min/max height
    x = parent_root.winfo_x() + (parent_root.winfo_width() // 2) - (dialog_width // 2)
    y = parent_root.winfo_y() + (parent_root.winfo_height() // 2) - (dialog_height // 2)
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    dialog.resizable(False, False)

    ttk.Label(dialog, text="Choose a monitor to capture:").pack(pady=10, padx=10)

    selected_monitor_idx = tk.IntVar(value=monitors[0][0]) # Default to first option (usually "All")

    for mss_idx, description in monitors:
        rb = ttk.Radiobutton(dialog, text=description, variable=selected_monitor_idx, value=mss_idx)
        rb.pack(anchor=tk.W, padx=20)

    result_holder = {"value": None} # To store result from button command

    def on_ok():
        result_holder["value"] = selected_monitor_idx.get()
        dialog.destroy()

    def on_cancel():
        result_holder["value"] = None
        dialog.destroy()

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10, fill=tk.X, side=tk.BOTTOM)

    ok_button = ttk.Button(button_frame, text="OK", command=on_ok)
    # ok_button.pack(side=tk.LEFT, padx=10, pady=10) # pack to one side
    ok_button.pack(side=tk.RIGHT, padx=(0, 20)) # Place OK on right

    cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
    # cancel_button.pack(side=tk.RIGHT, padx=10, pady=10)
    cancel_button.pack(side=tk.RIGHT, padx=(0, 5)) # Place Cancel to its left

    dialog.protocol("WM_DELETE_WINDOW", on_cancel) # Handle window close button

    parent_root.wait_window(dialog) # Wait for dialog to close

    return result_holder["value"]
