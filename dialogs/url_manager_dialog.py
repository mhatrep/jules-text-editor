import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont # For bolding group names
import os
import re
import configparser # For INI file handling
import webbrowser # For opening URLs

class UrlManagerDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("URL Manager")
        self.top.transient(self.root)
        # self.top.grab_set() # Not strictly modal, user might want to interact with editor
        self.top.geometry("700x500") # Initial size
        self.top.resizable(True, True)
        self.top.minsize(500, 350)

        self.bookmarks_data = {}  # Stores data for the currently loaded INI file's selected set
        self.all_bookmark_sets_data = {} # Stores data for ALL found INI files, keyed by filename for global search
        self.current_ini_file = None # Path to the currently loaded .ini file for the displayed set

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.grid_columnconfigure(0, weight=1) # Make treeview column expandable
        main_frame.grid_rowconfigure(1, weight=1)    # Make treeview row expandable

        # Top Controls (Combobox for sets, Load other, Search)
        top_controls_frame = ttk.Frame(main_frame)
        top_controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        top_controls_frame.grid_columnconfigure(3, weight=1) # Allow loaded file label to expand

        self.bookmark_files_map = {} # Maps display name (filename) to full path
        self.selected_bookmark_file_var = tk.StringVar()
        self.bookmarks_combobox_label = ttk.Label(top_controls_frame, text="Set:")
        self.bookmarks_combobox_label.grid(row=0, column=0, padx=(0,2), pady=(0,5), sticky=tk.W)
        self.bookmarks_combobox = ttk.Combobox(top_controls_frame, textvariable=self.selected_bookmark_file_var, state="readonly", width=20)
        self.bookmarks_combobox.grid(row=0, column=1, padx=(0,10), pady=(0,5), sticky=tk.W)
        self.bookmarks_combobox.bind("<<ComboboxSelected>>", self._on_bookmark_set_selected)

        self.load_button = ttk.Button(top_controls_frame, text="Load Other INI...", command=lambda: self._load_ini_file(filepath_arg=None))
        self.load_button.grid(row=0, column=2, padx=(0,10), pady=(0,5), sticky=tk.W)

        self.loaded_file_label_var = tk.StringVar(value="No file loaded.")
        loaded_file_label = ttk.Label(top_controls_frame, textvariable=self.loaded_file_label_var, anchor=tk.W)
        loaded_file_label.grid(row=0, column=3, padx=(0,10), pady=(0,5), sticky=tk.EW)

        search_label = ttk.Label(top_controls_frame, text="Search:")
        search_label.grid(row=0, column=4, padx=(5,0), pady=(0,5), sticky=tk.E)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_controls_frame, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=5, padx=(0,0), pady=(0,5), sticky=tk.E)
        self.search_var.trace_add("write", self._filter_display)

        self.global_search_var = tk.BooleanVar(value=False)
        global_search_checkbox = ttk.Checkbutton(top_controls_frame, text="Global", variable=self.global_search_var)
        global_search_checkbox.grid(row=0, column=6, padx=(5,0), pady=(0,5), sticky=tk.E)
        self.global_search_var.trace_add("write", self._filter_display)


        # Treeview for displaying bookmarks
        columns = ("description", "url")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="tree headings", height=15) # show="tree headings" to hide first "#0" column header but show tree lines
        self.tree.heading("#0", text="Group") # This is the tree column
        self.tree.column("#0", width=150, stretch=tk.NO, anchor=tk.W)
        self.tree.heading("description", text="Description / Name")
        self.tree.column("description", width=250 + 20, anchor=tk.W) # Added some padding
        self.tree.heading("url", text="URL")
        self.tree.column("url", width=300 + 20, anchor=tk.W) # Added some padding

        tree_scrollbar_y = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        tree_scrollbar_y.grid(row=1, column=1, sticky="ns")

        # Bottom Controls (Open URL Button)
        bottom_controls_frame = ttk.Frame(main_frame, padding=(0,10,0,0))
        bottom_controls_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.open_url_button = ttk.Button(bottom_controls_frame, text="Open Selected URL", command=self._open_selected_url, state=tk.DISABLED)
        self.open_url_button.pack(side=tk.LEFT) # pady=(5,0)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._open_selected_url) # Double click to open

        self.top.update_idletasks() # Calculate initial size
        x_pos = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y_pos = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'{self.top.winfo_width()}x{self.top.winfo_height()}+{x_pos}+{y_pos}')

        self._populate_bookmarks_dropdown() # Populate combobox with found INI files
        self._load_all_bookmark_sets_data() # Load all for global search
        self._try_load_default_ini()       # Try to load default.ini or first found

    def _load_all_bookmark_sets_data(self):
        self.all_bookmark_sets_data.clear()
        if not self.bookmark_files_map:
            return

        import configparser
        for filename, filepath in self.bookmark_files_map.items():
            parser = configparser.ConfigParser()
            try:
                parsed_files = parser.read(filepath, encoding='utf-8')
                if parsed_files: # Successfully read and parsed
                    current_file_data = {}
                    for section in parser.sections():
                        current_file_data[section] = {}
                        for description_key, url_value in parser.items(section):
                            current_file_data[section][description_key] = url_value
                    self.all_bookmark_sets_data[filename] = current_file_data
                else:
                    print(f"Warning: Could not read or parse '{filename}' for global search cache.")
            except configparser.Error as e:
                print(f"Warning: Error parsing INI file '{filename}' for global search cache: {e}")
            except Exception as e: # Catch any other unexpected errors
                print(f"Warning: Unexpected error loading '{filename}' for global search cache: {e}")


    def _find_bookmark_files(self):
        """Finds .ini files in a 'bookmarks' subdirectory relative to script or cwd."""
        filenames_paths = []
        seen_filenames = set() # To avoid duplicates if 'bookmarks' dir is in multiple search paths
        bookmarks_dirname = "bookmarks"

        # Define potential base paths: script's directory and current working directory
        possible_base_paths = [os.getcwd()]
        try: # Path of the current file (url_manager_dialog.py or editor.py if run directly)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if script_dir not in possible_base_paths:
                possible_base_paths.append(script_dir)
        except NameError: # __file__ is not defined (e.g. interactive session)
            pass

        unique_base_paths = []
        for p in possible_base_paths:
            if p not in unique_base_paths:
                unique_base_paths.append(p)

        for base_path in unique_base_paths:
            bookmarks_path = os.path.join(base_path, bookmarks_dirname)
            if os.path.isdir(bookmarks_path):
                try:
                    for entry in os.listdir(bookmarks_path):
                        if entry.lower().endswith(".ini") and entry not in seen_filenames:
                            full_path = os.path.join(bookmarks_path, entry)
                            if os.path.isfile(full_path):
                                filenames_paths.append((entry, full_path)) # (display_name, full_path)
                                seen_filenames.add(entry)
                except OSError as e:
                    print(f"Error accessing bookmarks directory {bookmarks_path}: {e}")

        filenames_paths.sort(key=lambda x: x[0].lower()) # Sort by filename, case-insensitive
        return filenames_paths

    def _populate_bookmarks_dropdown(self):
        found_files_with_paths = self._find_bookmark_files()
        self.bookmark_files_map.clear() # Clear previous map
        display_names = []

        if not found_files_with_paths:
            self.bookmarks_combobox_label.config(text="Set (None found):")
            self.bookmarks_combobox.set("")
            self.bookmarks_combobox.config(values=[], state=tk.DISABLED)
            return

        self.bookmarks_combobox_label.config(text="Set:")
        for display_name, full_path in found_files_with_paths:
            self.bookmark_files_map[display_name] = full_path
            display_names.append(display_name)

        self.bookmarks_combobox.config(values=display_names, state="readonly")
        # combobox selection will trigger _on_bookmark_set_selected if a default is set later

    def _on_bookmark_set_selected(self, event=None):
        selected_display_name = self.selected_bookmark_file_var.get()
        if selected_display_name and selected_display_name in self.bookmark_files_map:
            filepath_to_load = self.bookmark_files_map[selected_display_name]
            self._load_ini_file(filepath_arg=filepath_to_load)

    def _try_load_default_ini(self):
        """Tries to load 'default.ini' or the first file found if 'default.ini' is not present."""
        available_files = self.bookmarks_combobox.cget("values") # Get list of display names
        if not available_files:
            self.loaded_file_label_var.set("No bookmark sets found in 'bookmarks/' directory.")
            return

        file_to_load_display_name = None
        default_ini_name = "default.ini"

        if default_ini_name in available_files:
            file_to_load_display_name = default_ini_name
        elif available_files: # If default.ini not found, load the first one in the sorted list
            file_to_load_display_name = available_files[0]

        if file_to_load_display_name:
            self.selected_bookmark_file_var.set(file_to_load_display_name) # This will trigger _on_bookmark_set_selected
            filepath_to_load = self.bookmark_files_map.get(file_to_load_display_name)
            if filepath_to_load:
                 self._load_ini_file(filepath_arg=filepath_to_load) # Explicitly call to load
            else:
                print(f"Error: Display name '{file_to_load_display_name}' not found in bookmark_files_map.")
                self.loaded_file_label_var.set(f"Error finding path for {file_to_load_display_name}.")
        else:
            self.loaded_file_label_var.set("Select a bookmark set.")


    def _load_ini_file(self, filepath_arg=None):
        actual_filepath_to_load = None
        is_default_load_attempt = False # Was this load triggered by _try_load_default_ini?

        if filepath_arg and os.path.isfile(filepath_arg):
            actual_filepath_to_load = filepath_arg
            is_default_load_attempt = True # This was a programmatic load (default or combobox selection)
        else: # User clicked "Load Other INI..."
            selected_via_dialog = filedialog.askopenfilename(
                title="Open INI File",
                filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
                parent=self.top
            )
            if not selected_via_dialog: return # User cancelled dialog
            actual_filepath_to_load = selected_via_dialog
            is_default_load_attempt = False

        import configparser
        parser = configparser.ConfigParser()
        try:
            parsed_files = parser.read(actual_filepath_to_load, encoding='utf-8')
            if not parsed_files: # File was empty or not found by parser.read
                # If it was a default load attempt and a file was already loaded, don't show error, just keep old one.
                if is_default_load_attempt and self.current_ini_file and self.current_ini_file != actual_filepath_to_load:
                    print(f"Debug: Default INI file '{os.path.basename(actual_filepath_to_load)}' not found or failed to parse. Keeping '{os.path.basename(self.current_ini_file) if self.current_ini_file else 'None'}'.")
                else: # Explicit load or no prior file loaded
                    messagebox.showerror("Error", f"Could not read or parse INI file: {os.path.basename(actual_filepath_to_load)}", parent=self.top)
                    self._handle_load_error() # Clear current state
                return

            self.bookmarks_data.clear() # Clear previous set's data
            for section in parser.sections():
                self.bookmarks_data[section] = {}
                for description_key, url_value in parser.items(section):
                    self.bookmarks_data[section][description_key] = url_value

            self.current_ini_file = actual_filepath_to_load
            self.loaded_file_label_var.set(f"Loaded: {os.path.basename(actual_filepath_to_load)}")
            self._populate_treeview() # Display the newly loaded data
            self.open_url_button.config(state=tk.DISABLED) # Reset button state

        except configparser.Error as e:
            if is_default_load_attempt and self.current_ini_file and self.current_ini_file != actual_filepath_to_load:
                 print(f"Debug: Error parsing default INI file '{os.path.basename(actual_filepath_to_load)}': {e}. Keeping previously loaded file.")
            else:
                messagebox.showerror("INI Parsing Error", f"Error parsing INI file '{os.path.basename(actual_filepath_to_load)}':\n{e}", parent=self.top)
                self._handle_load_error()
        except Exception as e: # Catch-all for other unexpected errors
            if is_default_load_attempt and self.current_ini_file and self.current_ini_file != actual_filepath_to_load:
                print(f"Debug: Unexpected error loading default INI file '{os.path.basename(actual_filepath_to_load)}': {e}. Keeping previously loaded file.")
            else:
                messagebox.showerror("Error", f"An unexpected error occurred while loading '{os.path.basename(actual_filepath_to_load)}':\n{e}", parent=self.top)
                self._handle_load_error()

    def _handle_load_error(self):
        """Resets state when a file load fails explicitly."""
        self.bookmarks_data.clear()
        self.current_ini_file = None
        self.loaded_file_label_var.set("Error loading file or no file loaded.")
        self._clear_treeview()
        # self.selected_bookmark_file_var.set("") # Optionally clear combobox selection

    def _clear_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _populate_treeview(self):
        self._clear_treeview()
        if not self.bookmarks_data: return

        padding_spaces = "   " # For indenting items under groups visually

        for group_name, items in sorted(self.bookmarks_data.items()): # Sort groups alphabetically
            # Insert group as a top-level item (parent="")
            group_node_id = self.tree.insert("", tk.END, text=group_name, open=True, tags=('group',))

            sorted_items = sorted(items.items()) # Sort items within the group by description
            for description, url in sorted_items:
                # Insert item as a child of the group_node_id
                # Values correspond to the columns defined in self.tree columns=("description", "url")
                # The tree column itself is handled by the `text` parameter of the parent.
                padded_description = padding_spaces + description
                padded_url = padding_spaces + url
                self.tree.insert(group_node_id, tk.END, values=(padded_description, padded_url), tags=('item',))

        self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
        self.tree.tag_configure('item') # Default item style (can be customized if needed)


    def _filter_display(self, *args): # Called on search_var write or global_search_var change
        search_term = self.search_var.get().lower()
        self._clear_treeview()
        padding_spaces = "   "
        is_global = self.global_search_var.get()

        if not search_term and not is_global: # No search, not global -> show current loaded set
            self._populate_treeview()
            return

        if not search_term and is_global: # Global view, no filter -> show all sets
            for ini_filename, file_data in sorted(self.all_bookmark_sets_data.items()):
                file_node_id = self.tree.insert("", tk.END, text=ini_filename, open=True, tags=('file_header',))
                for group_name, items in sorted(file_data.items()):
                    group_node_id = self.tree.insert(file_node_id, tk.END, text=group_name, open=True, tags=('group',))
                    for description, url in sorted(items.items()):
                        padded_description = padding_spaces + description
                        padded_url = padding_spaces + url
                        self.tree.insert(group_node_id, tk.END, values=(padded_description, padded_url), tags=('item',))
            self.tree.tag_configure('file_header', font=tkfont.Font(weight='bold', slant='italic'))
            self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
            self.tree.tag_configure('item')
            return

        # If there is a search term:
        if is_global:
            for ini_filename, file_data in sorted(self.all_bookmark_sets_data.items()):
                file_node_id_for_this_file = None # Create file node only if matches are found within it
                for group_name, items in sorted(file_data.items()):
                    group_node_id_for_this_group = None # Create group node only if matches are found
                    for description, url in sorted(items.items()):
                        if search_term in description.lower() or search_term in url.lower():
                            if file_node_id_for_this_file is None: # First match in this file
                                file_node_id_for_this_file = self.tree.insert("", tk.END, text=ini_filename, open=True, tags=('file_header',))
                            if group_node_id_for_this_group is None: # First match in this group for this file
                                group_node_id_for_this_group = self.tree.insert(file_node_id_for_this_file, tk.END, text=group_name, open=True, tags=('group',))

                            padded_description = padding_spaces + description
                            padded_url = padding_spaces + url
                            self.tree.insert(group_node_id_for_this_group, tk.END, values=(padded_description, padded_url), tags=('item',))
            self.tree.tag_configure('file_header', font=tkfont.Font(weight='bold', slant='italic'))
            self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
            self.tree.tag_configure('item')
        else: # Search within the currently loaded self.bookmarks_data
            if not self.bookmarks_data: return
            for group_name, items in sorted(self.bookmarks_data.items()):
                group_node_id_for_this_group = None # Create group node only if matches are found
                for description, url in sorted(items.items()):
                    if search_term in description.lower() or search_term in url.lower():
                        if group_node_id_for_this_group is None: # First match in this group
                            group_node_id_for_this_group = self.tree.insert("", tk.END, text=group_name, open=True, tags=('group',))

                        padded_description = padding_spaces + description
                        padded_url = padding_spaces + url
                        self.tree.insert(group_node_id_for_this_group, tk.END, values=(padded_description, padded_url), tags=('item',))
            self.tree.tag_configure('group', font=tkfont.Font(weight='bold'))
            self.tree.tag_configure('item')


    def _open_selected_url(self, event=None): # event is passed by double-click
        selected_item_id = self.tree.focus() # Get the ID of the currently focused item
        if not selected_item_id: return

        item_tags = self.tree.item(selected_item_id, "tags")

        # If it's a group or file header, toggle open/close on single click (if desired, or handle double-click)
        if 'item' not in item_tags: # It's a group or file_header
            # Toggle open state on single click for groups/headers if it's a mouse click event
            if event and hasattr(event, 'type') and str(event.type) == "ButtonPress" and event.num == 1: # Check for left click
                 if 'group' in item_tags or 'file_header' in item_tags:
                     try:
                         self.tree.item(selected_item_id, open=not self.tree.item(selected_item_id, "open"))
                     except tk.TclError: pass # Ignore error if item somehow doesn't exist
            return


        try:
            item_values = self.tree.item(selected_item_id, "values")
            if item_values and len(item_values) >= 2: # Ensure URL is present
                padded_url = item_values[1] # URL is the second value
                url_to_open = padded_url.lstrip() # Remove leading padding
                if url_to_open:
                    import webbrowser
                    try:
                        webbrowser.open_new_tab(url_to_open)
                    except Exception as e:
                        messagebox.showerror("Error Opening URL", f"Could not open URL: {url_to_open}\nError: {e}", parent=self.top)
                else:
                    messagebox.showwarning("No URL", "Selected item does not have a valid URL after stripping padding.", parent=self.top)
            else:
                 messagebox.showwarning("No URL Data", "Could not retrieve URL for the selected item.", parent=self.top)
        except Exception as e: # Catch-all for safety
            messagebox.showerror("Error", f"An error occurred while trying to open URL: {e}", parent=self.top)


    def _on_tree_select(self, event=None):
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            self.open_url_button.config(state=tk.DISABLED)
            return

        item_tags = self.tree.item(selected_item_id, "tags")
        if 'item' in item_tags: # Enable button only if an actual bookmark item is selected
            self.open_url_button.config(state=tk.NORMAL)
        else: # It's a group or file header
            self.open_url_button.config(state=tk.DISABLED)
