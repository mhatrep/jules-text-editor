def _show_list_comparison_results(self, common_lines, list1_unique, list2_unique, case_sensitive_used):
    dialog = tk.Toplevel(self.root)
    dialog.title("List Comparison Results")
    dialog.transient(self.root)
    dialog.grab_set() # Make modal
    dialog.geometry("600x400") # Initial size, can be adjusted

    main_frame = ttk.Frame(dialog, padding=10)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # Status/Info Label
    case_info = "Case Sensitive" if case_sensitive_used else "Case Insensitive"
    info_label_text = f"Comparison Mode: {case_info}"
    ttk.Label(main_frame, text=info_label_text).pack(pady=(0, 5), anchor=tk.W)

    notebook = ttk.Notebook(main_frame)
    notebook.pack(expand=True, fill=tk.BOTH, pady=5)

    def create_results_tab(tab_parent, title, lines_list):
        frame = ttk.Frame(tab_parent, padding=5)
        tab_parent.add(frame, text=f"{title} ({len(lines_list)})")

        text_area = tk.Text(frame, wrap=tk.WORD, height=10, width=50, undo=False) # No undo needed for display
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        if lines_list:
            text_area.insert(tk.END, "\n".join(lines_list))
        else:
            text_area.insert(tk.END, "-- No lines --")
        text_area.config(state=tk.DISABLED) # Read-only
        return text_area # Return for potential use by copy function

    tab1_text = create_results_tab(notebook, "Common Lines", common_lines)
    tab2_text = create_results_tab(notebook, "Only in List 1", list1_unique)
    tab3_text = create_results_tab(notebook, "Only in List 2", list2_unique)

    # Action Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(10,0))

    def on_copy_all():
        results_summary = []
        results_summary.append(f"Comparison Mode: {case_info}\n")

        results_summary.append(f"--- Common Lines ({len(common_lines)}) ---")
        results_summary.extend(common_lines if common_lines else ["-- No lines --"])
        results_summary.append("\n") # Add a blank line for separation

        results_summary.append(f"--- Only in List 1 ({len(list1_unique)}) ---")
        results_summary.extend(list1_unique if list1_unique else ["-- No lines --"])
        results_summary.append("\n")

        results_summary.append(f"--- Only in List 2 ({len(list2_unique)}) ---")
        results_summary.extend(list2_unique if list2_unique else ["-- No lines --"])

        full_results_str = "\n".join(results_summary)

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(full_results_str)
            messagebox.showinfo("Results Copied", "All comparison results copied to clipboard.", parent=dialog)
        except tk.TclError:
            messagebox.showerror("Error", "Could not copy results to clipboard.", parent=dialog)

    copy_button = ttk.Button(button_frame, text="Copy All Results", command=on_copy_all)
    copy_button.pack(side=tk.LEFT, padx=(0,5))

    close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
    close_button.pack(side=tk.RIGHT) # Align to right

    dialog.update_idletasks()
    # Center dialog relative to root, or the input dialog if it were still accessible
    x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f'+{x}+{y}')

    # Ensure the results dialog stays on top until closed.
    dialog.wait_window()
