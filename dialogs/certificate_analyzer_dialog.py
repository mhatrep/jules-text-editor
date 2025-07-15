import tkinter as tk
from tkinter import filedialog, messagebox, ttk
# Need to ensure utils.certificate_analyzer is available
# This assumes utils package is in the parent directory or PYTHONPATH is set up.
# For direct execution within a package structure, relative imports might be needed if utils is a sibling.
# However, given the project structure, direct `import utils. ...` is often used.
import utils.certificate_analyzer as cert_analyzer

class CertificateAnalyzerDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Certificate Analyzer")
        self.geometry("700x550")
        self.parent = parent

        self.file_path = tk.StringVar()
        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(file_frame, text="Certificate File:").pack(side=tk.LEFT, padx=(0, 5))

        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=60)
        self.file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        browse_button = ttk.Button(file_frame, text="Browse...", command=self._browse_file)
        browse_button.pack(side=tk.LEFT)

        analyze_button = ttk.Button(main_frame, text="Analyze Certificate", command=self._analyze_certificate_from_file_entry)
        analyze_button.pack(pady=(0,10))

        results_frame = ttk.LabelFrame(main_frame, text="Certificate Details")
        results_frame.pack(expand=True, fill=tk.BOTH)

        self.results_text = tk.Text(results_frame, wrap=tk.WORD, height=20, width=80, font=("Courier New", 10)) # Monospaced font
        self.results_text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)

        self.results_text.insert(tk.END, "Select a certificate file (.pem, .crt, .cer, .der) and click 'Analyze Certificate'.")
        self.results_text.config(state=tk.DISABLED)

    def _browse_file(self):
        filetypes = (
            ("Certificate Files", "*.pem *.crt *.cer *.der"),
            ("PEM files", "*.pem"),
            ("CRT files", "*.crt"),
            ("CER files", "*.cer"),
            ("DER files", "*.der"),
            ("All files", "*.*")
        )
        filepath = filedialog.askopenfilename(
            title="Select Certificate File",
            filetypes=filetypes,
            parent=self
        )
        if filepath:
            self.file_path.set(filepath)
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Selected file: {filepath}\nClick 'Analyze Certificate' to see details.")
            self.results_text.config(state=tk.DISABLED)

    def _analyze_certificate_from_file_entry(self):
        filepath = self.file_path.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a certificate file first.", parent=self)
            return

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Analyzing {filepath}...\n\n")
        self.update_idletasks()

        try:
            # This uses the file-based analysis from utils.certificate_analyzer
            details = cert_analyzer.analyze_certificate(filepath)
            formatted_details = cert_analyzer.format_certificate_details(details)
            self.results_text.delete(1.0, tk.END) # Clear "Analyzing..." message
            self.results_text.insert(tk.END, formatted_details)
        except ImportError: # Should not happen if utils.certificate_analyzer is present
            self.results_text.insert(tk.END, "Error: Certificate analysis module not found.")
            messagebox.showerror("Internal Error", "Certificate analysis module (utils.certificate_analyzer) is missing.", parent=self)
        except Exception as e:
            self.results_text.insert(tk.END, f"An unexpected error occurred during analysis:\n{str(e)}")
            messagebox.showerror("Analysis Error", f"An unexpected error occurred: {e}", parent=self)

        self.results_text.config(state=tk.DISABLED)

# Main block for standalone testing (optional)
if __name__ == '__main__':
    # This setup is for testing the dialog independently.
    # It requires `utils/certificate_analyzer.py` to be in a place Python can find it (e.g., PYTHONPATH or sibling folder)
    # And an __init__.py in utils/
    import os
    # Create dummy utils and certificate_analyzer module for testing if not present
    if not os.path.exists("../utils"): # Assuming utils is a sibling to dialogs parent
        try: os.makedirs("../utils")
        except: pass # May fail if running from a different structure

    if not os.path.exists("../utils/__init__.py"):
        try:
            with open("../utils/__init__.py", "w") as f: pass
        except: pass

    if not os.path.exists("../utils/certificate_analyzer.py"):
        try:
            with open("../utils/certificate_analyzer.py", "w") as f:
                f.write('''
def analyze_certificate(file_path):
    if "error" in file_path: return {"error": "Dummy error in file path"}
    return {"Subject": "CN=Dummy Test Cert", "Issuer": "CN=Dummy Test CA", "Serial Number": "00ff"}
def format_certificate_details(details):
    if "error" in details: return f"Error: {details['error']}"
    return "\\n".join([f"{k}: {v}" for k,v in details.items()])
    ''')
            # Attempt to reload if it was just created (might not always work reliably in scripts)
            import importlib
            if 'utils.certificate_analyzer' in globals() or 'utils.certificate_analyzer' in locals():
                 importlib.reload(utils.certificate_analyzer)
            else:
                 import utils.certificate_analyzer as cert_analyzer

        except Exception as e:
            print(f"Could not create dummy utils/certificate_analyzer.py: {e}")


    root = tk.Tk()
    root.title("Main App Window (Test Host)")

    def open_dialog():
        # Ensure cert_analyzer is available, potentially re-importing if dummy was created
        global cert_analyzer
        try:
            import utils.certificate_analyzer as ca_mod
            cert_analyzer = ca_mod
        except ImportError:
            print("Failed to import utils.certificate_analyzer for test dialog.")
            return

        dialog = CertificateAnalyzerDialog(root)
        dialog.grab_set()

    button = ttk.Button(root, text="Open Certificate Analyzer Dialog", command=open_dialog)
    button.pack(padx=20, pady=20)
    root.mainloop()
