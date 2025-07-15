import tkinter as tk
from tkinter import ttk, filedialog
import pyperclip

class ClipboardManagerDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master.root)
        self.title("Clipboard Manager")
        self.geometry("400x500")
        self.master_app = master
        self.clipboard_history = []

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.history_listbox = tk.Listbox(main_frame)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_listbox.bind("<Double-Button-1>", self.copy_selected_to_clipboard)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=5)

        self.copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=self.copy_selected_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear History", command=self.clear_history)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.copy_all_button = ttk.Button(button_frame, text="Copy All", command=self._copy_all_to_clipboard)
        self.copy_all_button.pack(side=tk.RIGHT, padx=(0, 5))

        self.save_all_button = ttk.Button(button_frame, text="Save All", command=self._save_all_to_file)
        self.save_all_button.pack(side=tk.RIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)

        self.check_clipboard()

    def check_clipboard(self):
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard and (not self.clipboard_history or current_clipboard != self.clipboard_history[-1]):
                self.clipboard_history.append(current_clipboard)
                self.update_history_listbox()
        except pyperclip.PyperclipException:
            # This can happen if the clipboard is empty or contains non-string data
            pass
        self.after(1000, self.check_clipboard)

    def update_history_listbox(self):
        self.history_listbox.delete(0, tk.END)
        for item in reversed(self.clipboard_history):
            self.history_listbox.insert(tk.END, item.strip().split('\n')[0])

    def copy_selected_to_clipboard(self, event=None):
        selected_indices = self.history_listbox.curselection()
        if selected_indices:
            selected_index = len(self.clipboard_history) - 1 - selected_indices[0]
            pyperclip.copy(self.clipboard_history[selected_index])

    def delete_selected(self):
        selected_indices = self.history_listbox.curselection()
        if selected_indices:
            selected_index = len(self.clipboard_history) - 1 - selected_indices[0]
            del self.clipboard_history[selected_index]
            self.update_history_listbox()

    def clear_history(self):
        self.clipboard_history.clear()
        self.update_history_listbox()

    def _copy_all_to_clipboard(self):
        pyperclip.copy("\n\n".join(self.clipboard_history))

    def _save_all_to_file(self):
        filepath = filedialog.asksaveasfilename(
            initialfile="clipboard_history.txt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n\n".join(self.clipboard_history))

    def on_close(self, event=None):
        self.destroy()
