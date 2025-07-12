import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import sys # Added for sys.argv in _load_predefined_scripts
import configparser # For INI file parsing

class ScriptRunnerDialog(tk.Toplevel):
    """
    A dialog for running various types of scripts (Python, Shell, Batch, EXE)
    and viewing their output. Supports loading predefined scripts from INI files
    within a dedicated 'scripts' directory.
    """
    SCRIPTS_DIR = "scripts" # Directory where INI script files are located

    def __init__(self, master):
        """
        Initializes the ScriptRunnerDialog.

        Args:
            master: The parent widget (typically the main TextEditor instance).
        """
        super().__init__(master.root)
        self.title("Run Script")
        self.geometry("700x650") # Adjusted for predefined scripts list
        self.master_app = master

        self.process = None
        self.output_updater_thread = None
        self.stop_event = threading.Event()
        self.predefined_scripts = {}  # Stores {name: {path, type, params}}
        self.all_script_names_sorted = [] # For quick filtering and full list display
        self._populating_from_listbox = False # Flag to manage listbox selection clearing

        # --- UI Setup ---
        # Important: UI elements must be created before _load_predefined_scripts is called,
        # as _load_predefined_scripts configures some of these elements (e.g., ini_file_combo).
        main_config_execution_frame = ttk.Frame(self, padding="5")
        main_config_execution_frame.pack(fill=tk.X, side=tk.TOP)

        self._setup_predefined_scripts_ui(main_config_execution_frame) # Creates self.ini_file_combo
        self._setup_manual_config_ui(main_config_execution_frame)
        self._setup_execution_controls_ui() # Controls like Run, Stop, Status
        self._setup_output_display_ui()     # Output text area

        self._load_predefined_scripts() # Now safe to call, as UI elements it might use are created

        self._center_dialog()
        self.transient(self.master_app.root)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)

        # Initial focus on filter entry if predefined scripts exist and INI files were found,
        # else on script file entry.
        if self.predefined_scripts and self.found_ini_files: # Check if INIs were actually found
            self.filter_entry.focus_set()
        else:
            self.script_file_entry.focus_set()

    def _setup_predefined_scripts_ui(self, parent_frame):
        """
        Sets up the UI elements for displaying and filtering predefined scripts.
        This includes the filter entry, listbox, and scrollbar.
        Called during __init__.
        """
        predefined_scripts_frame = ttk.LabelFrame(parent_frame, text="Predefined Scripts", padding="5")
        predefined_scripts_frame.pack(fill=tk.X, pady=(0, 5), expand=True)
        predefined_scripts_frame.columnconfigure(0, weight=1) # Column for controls within this frame

        # INI File Selection Combobox
        ttk.Label(predefined_scripts_frame, text="Script Collection:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=(2,0))
        self.ini_file_var = tk.StringVar()
        self.ini_file_combo = ttk.Combobox(predefined_scripts_frame, textvariable=self.ini_file_var, state="readonly", width=38)
        self.ini_file_combo.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=(0,5))
        self.ini_file_combo.bind("<<ComboboxSelected>>", self._on_ini_file_selected)
        self.found_ini_files = [] # Stores full file paths of discovered INI files.
                                  # The corresponding combobox values are just the filenames.

        # Filter Entry
        ttk.Label(predefined_scripts_frame, text="Filter Scripts:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=(5,0))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self._filter_scripts_list)
        self.filter_entry = ttk.Entry(predefined_scripts_frame, textvariable=self.filter_var, width=40)
        self.filter_entry.grid(row=3, column=0, sticky=tk.EW, padx=5, pady=(0, 5))

        # Listbox for scripts
        listbox_frame = ttk.Frame(predefined_scripts_frame)
        listbox_frame.grid(row=4, column=0, sticky=tk.NSEW, padx=5) # Changed row from 1 to 4
        listbox_frame.rowconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)

        self.scripts_listbox = tk.Listbox(listbox_frame, height=6, exportselection=False)
        self.scripts_listbox.grid(row=0, column=0, sticky=tk.NSEW)
        self.scripts_listbox.bind("<<ListboxSelect>>", self._on_script_selected_from_list)

        scripts_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.scripts_listbox.yview)
        scripts_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.scripts_listbox.config(yscrollcommand=scripts_scrollbar.set)

        predefined_scripts_frame.rowconfigure(1, weight=1)
        self._populate_scripts_listbox()

    def _setup_manual_config_ui(self, parent_frame):
        """
        Sets up the UI elements for manually configuring a script to run.
        This includes script type dropdown, file path entry (with open location button),
        browse button, and parameters entry.
        Called during __init__.
        """
        manual_config_frame = ttk.LabelFrame(parent_frame, text="Manual Configuration", padding="10")
        manual_config_frame.pack(fill=tk.X, side=tk.TOP, pady=5)
        manual_config_frame.columnconfigure(1, weight=1) # Make entry fields expand

        # Script Type
        ttk.Label(manual_config_frame, text="Script Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.script_type_var = tk.StringVar()
        self.script_type_combo = ttk.Combobox(manual_config_frame, textvariable=self.script_type_var,
                                              values=["Python", "Shell", "Batch", "EXE"], state="readonly")
        self.script_type_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.script_type_combo.current(0)
        self.script_type_combo.bind("<<ComboboxSelected>>", self.on_script_type_change)

        # Script File
        ttk.Label(manual_config_frame, text="Script File:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.script_file_var = tk.StringVar()
        script_file_frame = ttk.Frame(manual_config_frame)
        script_file_frame.grid(row=1, column=1, sticky=tk.EW)
        script_file_frame.columnconfigure(0, weight=1)

        self.script_file_entry = ttk.Entry(script_file_frame, textvariable=self.script_file_var, width=52) # Adjusted width
        self.script_file_entry.grid(row=0, column=0, padx=(0, 2), pady=5, sticky=tk.EW)

        self.open_file_button = ttk.Button(script_file_frame, text="📄", width=3, command=self._open_script_file) # New button
        self.open_file_button.grid(row=0, column=1, padx=(2,2), pady=5)
        self.open_file_button.config(state=tk.DISABLED)

        self.open_location_button = ttk.Button(script_file_frame, text="📂", width=3, command=self._open_script_location)
        self.open_location_button.grid(row=0, column=2, padx=(0,0), pady=5) # Adjusted column
        self.open_location_button.config(state=tk.DISABLED)

        # Single trace to update both buttons related to script path
        self.script_file_var.trace_add("write", self._update_script_path_buttons_state)
        self.script_file_var.trace_add("write", self._clear_listbox_selection_on_manual_edit)

        self.browse_button = ttk.Button(manual_config_frame, text="Browse...", command=self._browse_file_and_clear_list_selection)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        # Input Parameters
        ttk.Label(manual_config_frame, text="Parameters:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.params_entry = ttk.Entry(manual_config_frame, width=60)
        self.params_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.params_entry.bind("<Return>", lambda event: self.run_script())

    def _setup_execution_controls_ui(self):
        """
        Sets up the UI elements for script execution control.
        This includes the 'Run Script' and 'Stop Execution' buttons, and the status label.
        Called during __init__.
        """
        controls_frame = ttk.Frame(self, padding="10")
        controls_frame.pack(fill=tk.X, side=tk.TOP)

        self.run_button = ttk.Button(controls_frame, text="Run Script", command=self.run_script)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(controls_frame, text="Stop Execution", command=self.stop_script, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.status_label_var = tk.StringVar(value="Status: Idle")
        self.status_label = ttk.Label(controls_frame, textvariable=self.status_label_var)
        self.status_label.pack(side=tk.LEFT, padx=10)

    def _setup_output_display_ui(self):
        """
        Sets up the UI elements for displaying script output.
        This includes the main text area and its scrollbar.
        Called during __init__.
        """
        output_frame = ttk.LabelFrame(self, text="Output", padding="10")
        # Make this frame expand and fill the remaining space
        output_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP, padx=10, pady=(0, 10))
        output_frame.rowconfigure(0, weight=1)    # Allow text widget to expand vertically
        output_frame.columnconfigure(0, weight=1) # Allow text widget to expand horizontally


        self.output_text = tk.Text(output_frame, wrap=tk.WORD, height=10) # Initial height, will expand
        self.output_text.grid(row=0, column=0, sticky=tk.NSEW) # Use grid for better expansion control
        # self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # Old pack
        self.output_text.config(state=tk.DISABLED)

        output_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        output_scrollbar.grid(row=0, column=1, sticky=tk.NS) # Use grid for scrollbar
        # output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y) # Old pack
        self.output_text.config(yscrollcommand=output_scrollbar.set)

        # Frame for output action buttons
        output_actions_frame = ttk.Frame(output_frame)
        output_actions_frame.grid(row=1, column=0, columnspan=2, sticky=tk.E, pady=(5,0))

        self.copy_output_button = ttk.Button(output_actions_frame, text="Copy Output", command=self._copy_output_to_clipboard, state=tk.DISABLED)
        self.copy_output_button.pack(side=tk.LEFT, padx=(0,5))

        self.save_output_button = ttk.Button(output_actions_frame, text="Save Output As...", command=self._save_output_to_file, state=tk.DISABLED)
        self.save_output_button.pack(side=tk.LEFT)

        # Trace changes in output_text to enable/disable copy/save buttons
        self.output_text.bind("<<Modified>>", self._on_output_text_changed)


    def _on_output_text_changed(self, event=None):
        """Callback when the output_text content changes."""
        # The Text widget's "modified" flag needs to be reset manually after checking.
        if self.output_text.edit_modified():
            content = self.output_text.get("1.0", tk.END + "-1c") # -1c to exclude trailing newline
            if content and content.strip():
                self.copy_output_button.config(state=tk.NORMAL)
                self.save_output_button.config(state=tk.NORMAL)
            else:
                self.copy_output_button.config(state=tk.DISABLED)
                self.save_output_button.config(state=tk.DISABLED)
            self.output_text.edit_modified(False) # Reset modified flag

    def _copy_output_to_clipboard(self):
        """Copies the content of the output text area to the clipboard."""
        content = self.output_text.get("1.0", tk.END + "-1c") # -1c to exclude trailing newline
        if content.strip(): # Only copy if there's actual content (not just whitespace)
            try:
                self.clipboard_clear()
                self.clipboard_append(content)
                original_status = self.status_label_var.get()
                self.status_label_var.set("Output copied to clipboard!")
                # Revert status after 2 seconds, but only if it hasn't changed due to another operation
                self.after(2000, lambda current_status=self.status_label_var.get(), revert_to=original_status: \
                           self.status_label_var.set(revert_to) if self.status_label_var.get() == "Output copied to clipboard!" else None)
            except tk.TclError:
                messagebox.showerror("Error", "Could not access clipboard.", parent=self)
        else:
            # messagebox.showinfo("Info", "Nothing to copy from output.", parent=self) # Optional: inform if nothing to copy
            pass

    def _save_output_to_file(self):
        """Saves the content of the output text area to a user-selected file."""
        content = self.output_text.get("1.0", tk.END + "-1c")
        if not content.strip():
            messagebox.showinfo("Info", "Output is empty, nothing to save.", parent=self)
            return

        filepath = filedialog.asksaveasfilename(
            title="Save Script Output As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Log Files", "*.log"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                original_status = self.status_label_var.get()
                self.status_label_var.set(f"Output saved to {os.path.basename(filepath)}")
                self.after(3000, lambda current_status=self.status_label_var.get(), revert_to=original_status: \
                           self.status_label_var.set(revert_to) if self.status_label_var.get().startswith("Output saved to") else None)
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save output to file:\n{e}", parent=self)

    def _load_predefined_scripts(self):
        """
        Scans the SCRIPTS_DIR for `*.ini` files, populates the 'Script Collection'
        combobox with their names, and by default, loads scripts from the first
        INI file found. This method is called during dialog initialization.
        """
        # Determine the path to the 'scripts' directory
        # Simplification: Assumes editor.py's dir or CWD is the base for finding 'scripts/'
        base_app_path = os.path.dirname(os.path.realpath(sys.argv[0] if hasattr(sys, 'argv') and sys.argv[0] else __file__))
        scripts_dir_path = os.path.join(base_app_path, self.SCRIPTS_DIR)

        if not os.path.isdir(scripts_dir_path):
            scripts_dir_path_cwd = os.path.join(os.getcwd(), self.SCRIPTS_DIR)
            if os.path.isdir(scripts_dir_path_cwd):
                scripts_dir_path = scripts_dir_path_cwd
            else:
                self.ini_file_combo.config(values=[])
                self.ini_file_var.set("")
                # print(f"DEBUG: Scripts directory '{self.SCRIPTS_DIR}' not found relative to app or CWD.")
                self._clear_and_update_script_list() # Ensure script list is cleared
                return

        # Scan for INI files
        self.found_ini_files = [] # Store full paths
        ini_filenames_for_combo = [] # Store just filenames for display

        try:
            for item in os.listdir(scripts_dir_path):
                if item.lower().endswith(".ini"):
                    full_path = os.path.join(scripts_dir_path, item)
                    if os.path.isfile(full_path):
                        self.found_ini_files.append(full_path)
                        ini_filenames_for_combo.append(item)

            # Sort both lists consistently (e.g., alphabetically by filename)
            # Create pairs, sort by filename, then extract sorted full_paths and filenames
            if ini_filenames_for_combo:
                sorted_pairs = sorted(zip(ini_filenames_for_combo, self.found_ini_files))
                ini_filenames_for_combo = [pair[0] for pair in sorted_pairs]
                self.found_ini_files = [pair[1] for pair in sorted_pairs]

        except OSError as e:
            messagebox.showerror("Error Scanning Scripts", f"Could not scan scripts directory '{scripts_dir_path}': {e}", parent=self)
            self.ini_file_combo.config(values=[])
            self.ini_file_var.set("")
            self._clear_and_update_script_list()
            return

        self.ini_file_combo.config(values=ini_filenames_for_combo)
        if ini_filenames_for_combo:
            self.ini_file_var.set(ini_filenames_for_combo[0])
            self.ini_file_combo.config(state="readonly") # Enable if there are options
            self._load_scripts_from_specific_ini(self.found_ini_files[0])
        else:
            self.ini_file_var.set("")
            self.ini_file_combo.config(state="disabled") # Disable if no options
            self._clear_and_update_script_list()

    def _load_scripts_from_specific_ini(self, ini_filepath):
        """
        Loads script configurations from a single specified INI file path.
        This method is called initially for the default INI and when a new INI
        is selected from the combobox. It updates `self.predefined_scripts`
        and `self.all_script_names_sorted`, then refreshes the script listbox.

        Args:
            ini_filepath (str): The full path to the INI file to load.
        """
        config = configparser.ConfigParser()
        self._clear_and_update_script_list(clear_only=True) # Clear current script data

        if not ini_filepath or not os.path.exists(ini_filepath):
            messagebox.showerror("Error", f"INI file not found: {ini_filepath}", parent=self)
            self._populate_scripts_listbox() # Update listbox (will be empty)
            return

        try:
            config.read(ini_filepath)
            current_file_scripts = {}
            for section in config.sections():
                try:
                    path = config.get(section, 'path')
                    script_type = config.get(section, 'type', fallback='Python')
                    params = config.get(section, 'params', fallback='')

                    if not path:
                        print(f"Warning: Script '{section}' in {os.path.basename(ini_filepath)} is missing 'path'. Skipping.")
                        continue
                    valid_types = ["Python", "Shell", "Batch", "EXE"]
                    if script_type not in valid_types:
                        print(f"Warning: Script '{section}' in {os.path.basename(ini_filepath)} has invalid type '{script_type}'. Skipping.")
                        continue
                    current_file_scripts[section] = {'path': path, 'type': script_type, 'params': params}
                except configparser.NoOptionError as e:
                    print(f"Warning: Missing option in script '{section}' in {os.path.basename(ini_filepath)}: {e}. Skipping.")

            self.predefined_scripts = current_file_scripts
            self.all_script_names_sorted = sorted(self.predefined_scripts.keys(), key=lambda k: k.lower())

        except configparser.Error as e:
            messagebox.showerror("INI Load Error", f"Error reading {os.path.basename(ini_filepath)}: {e}", parent=self)
        except Exception as e: # Catch other potential errors
            messagebox.showerror("Error", f"An unexpected error occurred while loading {os.path.basename(ini_filepath)}: {e}", parent=self)

        self._populate_scripts_listbox() # Refresh the listbox with newly loaded scripts

    def _on_ini_file_selected(self, event=None):
        """
        Callback for when a new INI file is selected from the 'Script Collection' combobox.
        Loads scripts from the newly selected INI file.
        """
        selected_ini_filename = self.ini_file_var.get()
        if not selected_ini_filename:
            self._clear_and_update_script_list() # Should not happen if combobox is managed well
            return

        # Find the full path for the selected filename from self.found_ini_files
        # This relies on the combobox values being the basenames from self.found_ini_files
        # and that self.found_ini_files was sorted in the same way as the combo values.
        selected_full_path = None
        try:
            # Assuming self.ini_file_combo['values'] are sorted filenames
            # and self.found_ini_files contains corresponding sorted full paths.
            combo_values = list(self.ini_file_combo.cget('values'))
            if selected_ini_filename in combo_values:
                idx = combo_values.index(selected_ini_filename)
                if 0 <= idx < len(self.found_ini_files):
                    selected_full_path = self.found_ini_files[idx]
        except ValueError: # Should ideally not happen
             pass


        if selected_full_path:
            self._load_scripts_from_specific_ini(selected_full_path)
        else:
            print(f"Error: Could not determine full path for INI file '{selected_ini_filename}'.")
            self._clear_and_update_script_list()

    def _clear_and_update_script_list(self, clear_only=False):
        """Clears script data and optionally updates the listbox."""
        self.predefined_scripts.clear()
        self.all_script_names_sorted.clear()
        if not clear_only:
            self._populate_scripts_listbox()

    def _populate_scripts_listbox(self, scripts_to_show=None):
        """
        Populates the listbox with script names.
        If scripts_to_show is None, shows all scripts from the currently loaded INI file.
        """
        self.scripts_listbox.delete(0, tk.END)

        names_to_display = scripts_to_show
        if names_to_display is None: # If None, means show all sorted script names
            names_to_display = self.all_script_names_sorted

        for name in names_to_display:
            self.scripts_listbox.insert(tk.END, name)

    def _filter_scripts_list(self, *args):
        """Filters the scripts listbox based on the text in the filter_entry."""
        filter_text = self.filter_var.get().lower()
        if not filter_text:
            self._populate_scripts_listbox() # Show all if filter is empty
            return

        filtered_names = [
            name for name in self.all_script_names_sorted
            if filter_text in name.lower()
        ]
        self._populate_scripts_listbox(filtered_names)

    def _on_script_selected_from_list(self, event=None):
        """Handles selection of a script from the predefined listbox."""
        selected_indices = self.scripts_listbox.curselection()
        if not selected_indices:
            return

        selected_name = self.scripts_listbox.get(selected_indices[0])
        script_config = self.predefined_scripts.get(selected_name)

        if script_config:
            self._populating_from_listbox = True # Set flag before programmatic change
            try:
                self.script_file_var.set(script_config['path'])
                self.params_entry.delete(0, tk.END)
                self.params_entry.insert(0, script_config['params'])

                # Set script type in combobox
                script_type = script_config['type']
                available_types = self.script_type_combo.cget('values') # Corrected: cget
                if script_type in available_types:
                    self.script_type_combo.set(script_type)
                else:
                    self.script_type_combo.set("Python")
                    messagebox.showwarning("Script Load Warning",
                                           f"Script '{selected_name}' has an unrecognized type '{script_type}'. Defaulting to Python.",
                                           parent=self)
            finally:
                self._populating_from_listbox = False # Unset flag

            # Optionally, disable manual file browsing if a predefined script is chosen,
            # or clear selection if user starts browsing manually.

            # Set script type in combobox
            script_type = script_config['type']
            available_types = self.script_type_combocget('values')
            if script_type in available_types:
                self.script_type_combo.set(script_type)
            else:
                # This case should ideally be caught during INI parsing
                self.script_type_combo.set("Python") # Fallback or error
                messagebox.showwarning("Script Load Warning",
                                       f"Script '{selected_name}' has an unrecognized type '{script_type}'. Defaulting to Python.",
                                       parent=self)

            # Optionally, disable manual file browsing if a predefined script is chosen,
            # or clear selection if user starts browsing manually.
            # For now, just populates the fields. User can still override by browsing.
        self._update_script_path_buttons_state() # Renamed and now updates both buttons
        # No explicit call to _clear_listbox_selection_on_manual_edit here,
        # because selecting from listbox *should* keep it selected. Manual edits will clear it.

    def _clear_listbox_selection_on_manual_edit(self, *args):
        """
        If the script_file_var is changed by user typing (not by listbox selection),
        it clears the listbox selection.
        This needs a way to distinguish programmatic changes (from listbox) vs direct user edits.
        A simple flag can achieve this.
        """
        if hasattr(self, '_populating_from_listbox') and self._populating_from_listbox:
            return # Change was due to listbox selection, so don't clear selection

        # If the current script path no longer matches any predefined script's path,
        # then clear the selection. This is a more robust way.
        current_path = self.script_file_var.get()
        selected_name_in_list = self._get_selected_listbox_name()

        if selected_name_in_list:
            predefined_path = self.predefined_scripts.get(selected_name_in_list, {}).get('path')
            if current_path != predefined_path:
                self.scripts_listbox.selection_clear(0, tk.END)
        # Also, if script_file_var is empty (e.g. user deleted path), clear selection.
        elif not current_path and selected_name_in_list:
             self.scripts_listbox.selection_clear(0, tk.END)


    def _get_selected_listbox_name(self):
        """Returns the name of the currently selected item in the listbox, or None."""
        selected_indices = self.scripts_listbox.curselection()
        if not selected_indices:
            return None
        return self.scripts_listbox.get(selected_indices[0])

    def _update_script_path_buttons_state(self, *args):
        """
        Enables or disables the 'Open File Location' (folder icon 📂) and
        'Open Script File' (document icon 📄) buttons.
        These buttons are enabled if `script_file_var` contains a path to an existing file.
        Called when `script_file_var` changes or a predefined script is selected.
        """
        script_path = self.script_file_var.get()
        is_valid_file = script_path and os.path.isfile(script_path)

        if is_valid_file:
            self.open_location_button.config(state=tk.NORMAL)
            self.open_file_button.config(state=tk.NORMAL)
        else:
            self.open_location_button.config(state=tk.DISABLED)
            self.open_file_button.config(state=tk.DISABLED)

    def _open_script_file(self):
        """
        Opens the script file (specified in the 'Script File' entry) using the
        system's default application for that file type.
        """
        script_path = self.script_file_var.get()
        if not script_path or not os.path.isfile(script_path):
            messagebox.showerror("Error", "Invalid or non-existent script file path.", parent=self)
            return

        try:
            if os.name == 'nt': # Windows
                os.startfile(os.path.normpath(script_path))
            elif os.name == 'posix': # macOS, Linux
                if sys.platform == "darwin": # macOS
                    subprocess.run(['open', script_path], check=True)
                else: # Linux and other POSIX
                    subprocess.run(['xdg-open', script_path], check=True)
            else:
                messagebox.showinfo("Unsupported OS", "Opening files this way is not supported on this OS.", parent=self)
        except FileNotFoundError: # For xdg-open or open if not found
             messagebox.showerror("Error", "Could not find necessary command (xdg-open or open).", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open script file: {e}", parent=self)

    def _open_script_location(self):
        """Opens the directory of the script specified in the script_file_entry."""
        script_path = self.script_file_var.get()
        if not script_path:
            messagebox.showinfo("Info", "No script file specified.", parent=self)
            return

        if not os.path.exists(script_path): # Check if path exists at all
            messagebox.showerror("Error", f"Script path does not exist: {script_path}", parent=self)
            return

        directory = os.path.dirname(script_path)
        if not os.path.isdir(directory): # Check if directory is valid after dirname
             directory = os.getcwd() # Fallback to current working directory if dirname is odd

        try:
            if os.name == 'nt': # Windows
                # os.startfile(directory) # This opens the directory itself, not explorer AT the directory usually
                subprocess.run(['explorer', os.path.normpath(directory)], check=False)
            elif os.name == 'posix': # macOS, Linux
                if sys.platform == "darwin": # macOS
                    subprocess.run(['open', directory], check=True)
                else: # Linux and other POSIX
                    subprocess.run(['xdg-open', directory], check=True)
            else:
                messagebox.showinfo("Unsupported OS", "Opening file location is not supported on this OS.", parent=self)
        except FileNotFoundError:
             messagebox.showerror("Error", "Could not find file explorer. Ensure xdg-open (Linux) or open (macOS) is available.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file location: {e}", parent=self)


    def _center_dialog(self):
        """Centers the dialog on the master application window."""
        self.master_app.root.update_idletasks() # Ensure master window dimensions are up-to-date
        master_x = self.master_app.root.winfo_x()
        master_y = self.master_app.root.winfo_y()
        master_width = self.master_app.root.winfo_width()
        master_height = self.master_app.root.winfo_height()

        self.update_idletasks() # Ensure dialog dimensions are up-to-date
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        x_offset = (master_width - dialog_width) // 2
        y_offset = (master_height - dialog_height) // 2

        # Handle cases where master_app might not be the root Tk() instance directly
        # but a frame or similar. Fallback to screen centering if geometry is odd.
        final_x = master_x + x_offset
        final_y = master_y + y_offset

        # Basic sanity check for position, ensure it's not off-screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        if final_x < 0 or final_y < 0 or final_x + dialog_width > screen_width or final_y + dialog_height > screen_height:
            # Fallback to centering on screen if calculated position is problematic
            final_x = (screen_width - dialog_width) // 2
            final_y = (screen_height - dialog_height) // 2

        self.geometry(f"+{final_x}+{final_y}")
        self.transient(self.master_app.root) # Set as transient to master (modal-like behavior)

    def on_script_type_change(self, event=None):
        """
        Callback when the script type selection changes.
        Clears the script file entry.
        """
        self.script_file_var.set("") # Clear file path when script type changes
        self._clear_listbox_selection_on_manual_edit()

    def _browse_file_and_clear_list_selection(self):
        """Handles file browsing and ensures listbox selection is cleared."""
        self.browse_file() # Call original browse_file logic
        # No need to explicitly call _clear_listbox_selection here if browse_file sets script_file_var,
        # as the trace on script_file_var will call _clear_listbox_selection_on_manual_edit.
        # However, if browse_file might NOT change script_file_var (e.g. user cancels dialog),
        # an explicit clear might be desired if any interaction with "Browse" should deselect.
        # For now, relying on script_file_var trace is okay. If script_file_var is set by browse,
        # its trace will fire. If not set (cancel), selection remains, which is acceptable.

    def browse_file(self):
        """Opens a file dialog to select a script file based on the selected script type."""
        # This method is now effectively the core logic called by _browse_file_and_clear_list_selection
        script_type = self.script_type_var.get()
        filetypes = [("All files", "*.*")] # Default
        if script_type == "Python":
            filetypes = [("Python files", "*.py"), ("All files", "*.*")]
        elif script_type == "Shell":
            filetypes = [("Shell scripts", "*.sh"), ("All files", "*.*")]
        elif script_type == "Batch":
            filetypes = [("Batch files", "*.bat"), ("All files", "*.*")]
        elif script_type == "EXE":
            filetypes = [("Executable files", "*.exe"), ("All files", "*.*")]

        filepath = filedialog.askopenfilename(
            title=f"Select {script_type} File",
            filetypes=filetypes,
            defaultextension=filetypes[0][1] if filetypes else None
        )
        if filepath:
            self.script_file_var.set(filepath)

    def _update_output_continuously(self):
        """
        Reads output from the running script's stdout and stderr pipes
        and updates the output Text widget. This method is run in a separate thread.
        Handles process completion and updates UI accordingly.
        """
        try:
            # Read from stdout
            for line_bytes in iter(self.process.stdout.readline, b''):
                if self.stop_event.is_set(): break
                line = line_bytes.decode(errors='replace') # Decode, replacing errors
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)
                self.master_app.root.update_idletasks() # Ensure UI remains responsive

            # Read from stderr (after stdout is exhausted or if interleaved reading is too complex)
            # A more robust solution might use select.select or separate threads for stdout/stderr
            # if truly interleaved real-time output from both streams is critical.
            for line_bytes in iter(self.process.stderr.readline, b''):
                if self.stop_event.is_set(): break # Check if stop was requested
                line = line_bytes.decode(errors='replace') # Decode, replacing errors
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, f"[STDERR] {line}") # Differentiate stderr
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)
                self.master_app.root.update_idletasks()
        except Exception as e:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, f"\nError reading script output: {e}\n")
            self.output_text.config(state=tk.DISABLED)
        finally:
            self.process.stdout.close()
            self.process.stderr.close()
            self.process.wait() # Ensure process is fully cleaned up
            if not self.stop_event.is_set(): # If not stopped manually
                exit_code = self.process.returncode
                self.status_label_var.set(f"Status: {'Completed' if exit_code == 0 else f'Failed (Code: {exit_code})'}")
            else:
                self.status_label_var.set("Status: Stopped by user")

            self.run_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.browse_button.config(state=tk.NORMAL)
            self.script_type_combo.config(state="readonly")
            self.script_file_entry.config(state=tk.NORMAL)
            self.params_entry.config(state=tk.NORMAL)
            self.process = None
            self.stop_event.clear() # Reset stop event for next run


    def run_script(self):
        """
        Validates inputs and initiates the script execution process.
        Constructs the command, starts a subprocess, and launches a thread
        to monitor the script's output.
        """
        script_path = self.script_file_var.get()
        script_type = self.script_type_var.get()
        params_str = self.params_entry.get()

        # --- Input Validations ---
        if not script_path:
            messagebox.showerror("Error", "Please select a script file.", parent=self)
            return
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Script file not found: {script_path}", parent=self)
            return

        # Check for execute permissions (primarily for Shell and EXE)
        if not os.access(script_path, os.X_OK) and script_type in ["Shell", "EXE"]:
            # Python and Batch scripts are run by interpreters, so X_OK might not be set/needed.
            if not (script_type == "Python" or script_type == "Batch"):
                 messagebox.showwarning("Warning", f"Script may not be executable: {script_path}", parent=self)

        # --- Command Construction ---
        command = []
        if script_type == "Python":
            command.append("python") # Consider using sys.executable for portability
            command.append(script_path)
        elif script_type == "Shell":
            # For .sh files, they usually have a shebang. If not, might need 'bash' or 'sh' explicitly.
            # Making it executable (chmod +x) is typically done by the user.
            command.append(script_path) # direct execution
        elif script_type == "Batch":
            command.append("cmd")
            command.append("/c")
            command.append(script_path)
        elif script_type == "EXE":
            command.append(script_path)
        else:
            messagebox.showerror("Error", f"Unsupported script type: {script_type}", parent=self)
            return

        if params_str:
            # Basic splitting by space. For more complex arguments, shlex.split might be considered.
            command.extend(params_str.split())

        # --- UI Updates for Running State ---
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END) # Clear previous output
        self.output_text.insert(tk.END, f"Running: {' '.join(command)}\n--------------------\n")
        self.output_text.config(state=tk.DISABLED)

        self.status_label_var.set("Status: Running...")
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.DISABLED)
        self.script_type_combo.config(state=tk.DISABLED)
        self.script_file_entry.config(state=tk.DISABLED)
        self.params_entry.config(state=tk.DISABLED)
        self.stop_event.clear() # Ensure stop event is clear before starting

        # --- Subprocess Execution ---
        try:
            # Determine if shell=True is needed (generally avoided for security unless necessary)
            # For .bat on Windows, cmd /c is used, so shell=False is fine.
            # For .sh on Linux/macOS, direct execution (shell=False) is fine if executable and has shebang.
            # For .sh on Windows, behavior is complex (WSL, Git Bash, etc.); direct execution might fail.
            # Keeping shell=False as the default for better security and predictability.
            use_shell = False
            # Example: if script_type == "Shell" and os.name == 'nt':
            #    use_shell = True # This might be needed for some .sh interpreters on Windows if not using WSL directly

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE, # Capture standard output
                stderr=subprocess.PIPE, # Capture standard error
                shell=use_shell,
                cwd=os.path.dirname(script_path) or os.getcwd() # Execute in script's directory if possible
            )

            # Start a new thread to read the script's output without blocking the UI
            self.output_updater_thread = threading.Thread(target=self._update_output_continuously, daemon=True)
            self.output_updater_thread.start()

        except FileNotFoundError:
            messagebox.showerror("Error", f"Execution failed: Command or script not found. Ensure the interpreter (e.g., python) is in PATH or the script is correctly specified.", parent=self)
            self.status_label_var.set("Status: Failed (File Not Found)")
            self._reset_controls_to_idle()
        except PermissionError:
            messagebox.showerror("Error", f"Execution failed: Permission denied for script or interpreter.", parent=self)
            self.status_label_var.set("Status: Failed (Permission Denied)")
            self._reset_controls_to_idle()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start script: {e}", parent=self)
            self.status_label_var.set(f"Status: Failed ({type(e).__name__})")
            self._reset_controls_to_idle()
            if self.process: # Ensure cleanup if Popen succeeded but something else failed
                if self.process.stdout: self.process.stdout.close()
                if self.process.stderr: self.process.stderr.close()
                try: self.process.terminate()
                except OSError: pass
                self.process.wait()
            self.process = None


    def stop_script(self):
        """
        Stops the currently running script.
        It first tries to terminate gracefully, then kills if necessary.
        """
        if self.process and self.process.poll() is None:  # Check if process is actually running
            self.status_label_var.set("Status: Stopping...")
            self.stop_event.set()  # Signal the output reader thread to stop processing output

            try:
                self.process.terminate()  # SIGTERM
                try:
                    # Wait for a short period for the process to terminate
                    self.process.wait(timeout=2)
                    self.status_label_var.set("Status: Terminated by user")
                except subprocess.TimeoutExpired:
                    # If terminate didn't work, force kill
                    self.process.kill()  # SIGKILL
                    self.status_label_var.set("Status: Force killed by user")
            except OSError as e:
                messagebox.showerror("Error", f"Error stopping script: {e}", parent=self)
                self.status_label_var.set(f"Status: Error stopping ({e.errno})")
            # The _update_output_continuously thread's finally block will handle resetting UI controls
        else:
            # If process is not running or already stopped, ensure controls are reset
            self._reset_controls_to_idle()

    def _reset_controls_to_idle(self):
        """Resets UI controls to their idle state (e.g., after script finishes or is stopped)."""
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.NORMAL)
        self.script_type_combo.config(state="readonly")
        self.script_file_entry.config(state=tk.NORMAL)
        self.params_entry.config(state=tk.NORMAL)

        # Only set to Idle if not already in a failed state
        current_status = self.status_label_var.get()
        if not current_status.startswith("Status: Failed") and not current_status.startswith("Status: Error"):
             self.status_label_var.set("Status: Idle")

        self.process = None
        self.stop_event.clear() # Important to clear for the next run

    def on_close(self, event=None):
        """
        Handles the dialog window close event.
        Prompts the user if a script is running. Stops the script and joins
        the output thread before destroying the window.
        """
        if self.process and self.process.poll() is None: # If a script is currently running
            if messagebox.askyesno("Running Script",
                                   "A script is currently running. Do you want to stop it and close the dialog?",
                                   parent=self):
                self.stop_script() # Attempt to stop the script
                # Wait for the output updater thread to finish, as it might be writing to UI
                if self.output_updater_thread and self.output_updater_thread.is_alive():
                    self.output_updater_thread.join(timeout=1.5) # Increased timeout slightly
                self.destroy()
            else:
                return  # User chose not to close
        else:
            # If no script is running, or if it has finished/been stopped
            if self.output_updater_thread and self.output_updater_thread.is_alive():
                self.stop_event.set()  # Signal the thread to stop (if it's somehow stuck)
                self.output_updater_thread.join(timeout=1.0)
            self.destroy()

if __name__ == '__main__':
    # This block allows testing the ScriptRunnerDialog independently.
    # To run: python script_runner_dialog.py
    root = tk.Tk()
    root.title("Main Test Window for ScriptRunnerDialog")

    def _copy_output_to_clipboard(self):
        """Copies the content of the output text area to the clipboard."""
        content = self.output_text.get("1.0", tk.END + "-1c") # -1c to exclude trailing newline
        if content.strip(): # Only copy if there's actual content (not just whitespace)
            try:
                self.clipboard_clear()
                self.clipboard_append(content)
                # Optionally, provide feedback e.g., briefly change button text or status bar
                original_status = self.status_label_var.get()
                self.status_label_var.set("Output copied to clipboard!")
                self.after(2000, lambda: self.status_label_var.set(original_status)) # Revert status after 2s
            except tk.TclError:
                messagebox.showerror("Error", "Could not access clipboard.", parent=self)
        else:
            # Optionally, inform user if there's nothing to copy
            # messagebox.showinfo("Info", "Nothing to copy from output.", parent=self)
            pass # Or do nothing silently

    def _save_output_to_file(self):
        """Saves the content of the output text area to a user-selected file."""
        # Placeholder for now
        content = self.output_text.get("1.0", tk.END + "-1c")
        if not content.strip():
            messagebox.showinfo("Info", "Output is empty, nothing to save.", parent=self)
            return

        filepath = filedialog.asksaveasfilename(
            title="Save Script Output As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Log Files", "*.log"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.status_label_var.set(f"Output saved to {os.path.basename(filepath)}")
                self.after(3000, lambda: self.status_label_var.set("Status: Idle")) # Or previous status
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save output to file:\n{e}", parent=self)

    # Create a mock master_app that the dialog expects
    # In a real scenario, 'master_app' would be the TextEditor instance.
    mock_master_app = type('MockMasterApp', (), {'root': root})()

    def open_script_runner_dialog():
        dialog = ScriptRunnerDialog(mock_master_app)
        # dialog.grab_set() # Optional: make it modal during testing

    ttk.Button(root, text="Open Script Runner Dialog", command=open_script_runner_dialog).pack(padx=50, pady=50)
    root.mainloop()
