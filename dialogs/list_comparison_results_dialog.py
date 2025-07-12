import tkinter as tk
from tkinter import ttk, messagebox

class ListComparisonResultsDialog(tk.Toplevel):
    def __init__(self, parent, common_lines, list1_unique, list2_unique, case_sensitive_used):
        super().__init__(parent)
        self.parent = parent
        self.common_lines = common_lines
        self.list1_unique = list1_unique
        self.list2_unique = list2_unique
        self.case_sensitive_used = case_sensitive_used

        self.title("List Comparison Results")
        self.transient(parent)
        self.grab_set() # Make modal
        self.geometry("600x400") # Initial size

        self._setup_ui()
        self._center_dialog()

        # Ensure the results dialog stays on top until closed.
        self.wait_window()

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Status/Info Label
        case_info = "Case Sensitive" if self.case_sensitive_used else "Case Insensitive"
        info_label_text = f"Comparison Mode: {case_info}"
        ttk.Label(main_frame, text=info_label_text).pack(pady=(0, 5), anchor=tk.W)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True, fill=tk.BOTH, pady=5)

        self.tab1_text_area = self._create_results_tab(notebook, "Common Lines", self.common_lines)
        self.tab2_text_area = self._create_results_tab(notebook, "Only in List 1", self.list1_unique)
        self.tab3_text_area = self._create_results_tab(notebook, "Only in List 2", self.list2_unique)

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0))

        copy_button = ttk.Button(button_frame, text="Copy All Results", command=self._on_copy_all)
        copy_button.pack(side=tk.LEFT, padx=(0,5))

        close_button = ttk.Button(button_frame, text="Close", command=self.destroy)
        close_button.pack(side=tk.RIGHT)

    def _create_results_tab(self, tab_parent, title, lines_list):
        frame = ttk.Frame(tab_parent, padding=5)
        tab_parent.add(frame, text=f"{title} ({len(lines_list)})")

        text_area = tk.Text(frame, wrap=tk.WORD, height=10, width=50, undo=False)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        if lines_list:
            text_area.insert(tk.END, "\n".join(lines_list))
        else:
            text_area.insert(tk.END, "-- No lines --")
        text_area.config(state=tk.DISABLED) # Read-only
        return text_area

    def _on_copy_all(self):
        results_summary = []
        case_info = "Case Sensitive" if self.case_sensitive_used else "Case Insensitive"
        results_summary.append(f"Comparison Mode: {case_info}\n")

        results_summary.append(f"--- Common Lines ({len(self.common_lines)}) ---")
        results_summary.extend(self.common_lines if self.common_lines else ["-- No lines --"])
        results_summary.append("\n")

        results_summary.append(f"--- Only in List 1 ({len(self.list1_unique)}) ---")
        results_summary.extend(self.list1_unique if self.list1_unique else ["-- No lines --"])
        results_summary.append("\n")

        results_summary.append(f"--- Only in List 2 ({len(self.list2_unique)}) ---")
        results_summary.extend(self.list2_unique if self.list2_unique else ["-- No lines --"])

        full_results_str = "\n".join(results_summary)

        try:
            self.clipboard_clear()
            self.clipboard_append(full_results_str)
            messagebox.showinfo("Results Copied", "All comparison results copied to clipboard.", parent=self)
        except tk.TclError:
            messagebox.showerror("Error", "Could not copy results to clipboard.", parent=self)

    def _center_dialog(self):
        self.update_idletasks()
        # Center dialog relative to parent
        if self.parent:
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            dialog_width = self.winfo_width()
            dialog_height = self.winfo_height()

            x = parent_x + (parent_width // 2) - (dialog_width // 2)
            y = parent_y + (parent_height // 2) - (dialog_height // 2)
            self.geometry(f'+{x}+{y}')
        else: # Fallback if no parent, center on screen (less ideal for transient dialogs)
            self.geometry(f'+{self.winfo_screenwidth() // 2 - self.winfo_width() // 2}+{self.winfo_screenheight() // 2 - self.winfo_height() // 2}')

if __name__ == '__main__':
    # Example Usage (for testing the dialog directly)
    root = tk.Tk()
    root.title("Main Application Window")
    root.geometry("800x600")

    def open_dialog():
        common = ["apple", "banana"]
        l1_unique = ["orange", "grape"]
        l2_unique = ["mango", "pineapple", "strawberry"]
        ListComparisonResultsDialog(root, common, l1_unique, l2_unique, True)

    ttk.Button(root, text="Open List Comparison Results", command=open_dialog).pack(pady=20)
    root.mainloop()
