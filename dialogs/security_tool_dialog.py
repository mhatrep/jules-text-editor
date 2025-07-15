import tkinter as tk
from tkinter import ttk, messagebox
from dialogs.certificate_analyzer_dialog import CertificateAnalyzerDialog
import utils.system_certificate_store as sys_cert_store
import utils.hashing_util as hashing_util
import utils.url_coding_util as url_coding_util # Added for URL Coding utility
import platform

class SecurityToolDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Developer Security Utilities")
        self.geometry("800x650") # Adjusted size
        self.minsize(600, 450)

        self._system_certs_cache = []

        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill=tk.BOTH, pady=(0, 10))

        self._setup_certificate_tools_tab()
        self._setup_other_utilities_tab() # Modified to include hashing

        close_button_frame = ttk.Frame(main_frame)
        close_button_frame.pack(fill=tk.X, pady=(10,0))
        close_button = ttk.Button(close_button_frame, text="Close", command=self.destroy)
        close_button.pack(side=tk.RIGHT)

    def _setup_certificate_tools_tab(self):
        cert_tools_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(cert_tools_frame, text="Certificate Utilities")

        cert_buttons_frame = ttk.Frame(cert_tools_frame)
        cert_buttons_frame.pack(fill=tk.X, pady=(0,10))

        analyze_cert_button = ttk.Button(
            cert_buttons_frame,
            text="Analyze Certificate File...",
            command=self._open_certificate_analyzer_from_file_dialog
        )
        analyze_cert_button.pack(side=tk.LEFT, pady=5, padx=5)

        self.load_store_button = ttk.Button(
            cert_buttons_frame,
            text=f"Load System Certificates ({platform.system()})",
            command=self._load_system_certificates
        )
        self.load_store_button.pack(side=tk.LEFT, pady=5, padx=5)

        self.status_label = ttk.Label(cert_buttons_frame, text="")
        self.status_label.pack(side=tk.LEFT, pady=5, padx=10)

        self.cert_store_display_frame = ttk.LabelFrame(cert_tools_frame, text="System Certificates")
        self.cert_store_display_frame.pack(expand=True, fill=tk.BOTH, pady=(5,0))

        self.cert_tree = ttk.Treeview(
            self.cert_store_display_frame,
            columns=("subject", "issuer", "serial", "valid_to", "source"),
            show="headings"
        )
        self.cert_tree.heading("subject", text="Subject CN")
        self.cert_tree.heading("issuer", text="Issuer CN")
        self.cert_tree.heading("serial", text="Serial Number")
        self.cert_tree.heading("valid_to", text="Valid To")
        self.cert_tree.heading("source", text="Source/Details")

        self.cert_tree.column("subject", width=250, anchor=tk.W, stretch=tk.YES)
        self.cert_tree.column("issuer", width=250, anchor=tk.W, stretch=tk.YES)
        self.cert_tree.column("serial", width=200, anchor=tk.W, stretch=tk.NO)
        self.cert_tree.column("valid_to", width=150, anchor=tk.W, stretch=tk.NO)
        self.cert_tree.column("source", width=300, anchor=tk.W, stretch=tk.YES)

        cert_tree_scrollbar_y = ttk.Scrollbar(self.cert_store_display_frame, orient=tk.VERTICAL, command=self.cert_tree.yview)
        cert_tree_scrollbar_x = ttk.Scrollbar(self.cert_store_display_frame, orient=tk.HORIZONTAL, command=self.cert_tree.xview)
        self.cert_tree.configure(yscrollcommand=cert_tree_scrollbar_y.set, xscrollcommand=cert_tree_scrollbar_x.set)

        self.cert_tree.grid(row=0, column=0, sticky="nsew")
        cert_tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        cert_tree_scrollbar_x.grid(row=1, column=0, sticky="ew")

        self.cert_store_display_frame.grid_rowconfigure(0, weight=1)
        self.cert_store_display_frame.grid_columnconfigure(0, weight=1)

        self.cert_tree.bind("<Double-1>", self._on_system_certificate_selected)
        self.cert_tree.bind("<Return>", self._on_system_certificate_selected)

    def _setup_other_utilities_tab(self):
        other_tools_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(other_tools_frame, text="Other Utilities")

        # --- Hashing Utility Section ---
        hashing_frame = ttk.LabelFrame(other_tools_frame, text="Hashing Tool", padding="10")
        hashing_frame.pack(fill=tk.X, pady=5, anchor="n") # Anchor to north

        # Input Text
        ttk.Label(hashing_frame, text="Input Text:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.hash_input_text = tk.Text(hashing_frame, height=4, width=60) # Set initial width
        self.hash_input_text.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        hash_input_scrollbar = ttk.Scrollbar(hashing_frame, orient=tk.VERTICAL, command=self.hash_input_text.yview)
        self.hash_input_text.config(yscrollcommand=hash_input_scrollbar.set)
        hash_input_scrollbar.grid(row=1, column=3, sticky="ns", pady=5)
        hashing_frame.grid_rowconfigure(1, weight=1)

        # Algorithm Selection (Now just a label, as we compute all)
        # ttk.Label(hashing_frame, text="Algorithm:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        # self.hash_algo_var = tk.StringVar(value="sha256")
        hash_algos = ["md5", "sha1", "sha256", "sha512"]
        # algo_menu = ttk.Combobox(hashing_frame, textvariable=self.hash_algo_var, values=hash_algos, state="readonly", width=10)
        # algo_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Compute Button
        compute_hash_button = ttk.Button(hashing_frame, text="Compute Hashes", command=self._compute_and_display_hashes) # plural
        compute_hash_button.grid(row=2, column=0, columnspan=3, padx=5, pady=(10,5), sticky="ew") # Centered or full width

        hashing_frame.grid_columnconfigure(0, weight=1) # Allow expansion for input/output fields
        hashing_frame.grid_columnconfigure(1, weight=1)
        hashing_frame.grid_columnconfigure(2, weight=1)


        # Output Hashes
        self.hash_output_vars = {} # Store StringVars for outputs
        output_row_start = 3
        for i, algo_name in enumerate(hash_algos):
            ttk.Label(hashing_frame, text=f"{algo_name.upper()}:").grid(row=output_row_start + i, column=0, padx=5, pady=2, sticky="w")
            output_var = tk.StringVar()
            # Increased width for output, ensure it expands
            output_entry = ttk.Entry(hashing_frame, textvariable=output_var, state="readonly")
            output_entry.grid(row=output_row_start + i, column=1, columnspan=2, padx=5, pady=2, sticky="ew")
            self.hash_output_vars[algo_name] = output_var

        # Ensure the hashing_frame itself can expand horizontally if other_tools_frame does
        other_tools_frame.columnconfigure(0, weight=1)

        # --- URL Encoding/Decoding Section ---
        url_coding_frame = ttk.LabelFrame(other_tools_frame, text="URL Encoder/Decoder", padding="10")
        url_coding_frame.pack(fill=tk.X, pady=10, anchor="n") # Anchor to north, add some vertical space

        ttk.Label(url_coding_frame, text="Input/Output Text:").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.url_text_area = tk.Text(url_coding_frame, height=6, width=60) # Shared Text area
        self.url_text_area.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        url_text_scrollbar = ttk.Scrollbar(url_coding_frame, orient=tk.VERTICAL, command=self.url_text_area.yview)
        self.url_text_area.config(yscrollcommand=url_text_scrollbar.set)
        url_text_scrollbar.grid(row=1, column=2, sticky="ns", pady=5) # Place scrollbar to the right
        url_coding_frame.grid_rowconfigure(1, weight=1)

        button_frame_url = ttk.Frame(url_coding_frame)
        button_frame_url.grid(row=2, column=0, columnspan=2, pady=(5,0), sticky="ew")

        url_encode_button = ttk.Button(button_frame_url, text="URL Encode", command=self._url_encode_action)
        url_encode_button.pack(side=tk.LEFT, padx=5)

        url_decode_button = ttk.Button(button_frame_url, text="URL Decode", command=self._url_decode_action)
        url_decode_button.pack(side=tk.LEFT, padx=5)

        url_coding_frame.columnconfigure(0, weight=1) # Allow text area to expand
        url_coding_frame.columnconfigure(1, weight=1) # Allow text area to expand (if columnspan=2 on text area)


    def _compute_and_display_hashes(self): # Renamed for clarity
        self.status_label.config(text="Computing hashes...")
        self.update_idletasks()
        input_text = self.hash_input_text.get("1.0", tk.END + "-1c").strip() # Strip whitespace

        if not input_text: # If input is empty after stripping, clear hashes
            for algo_name in self.hash_output_vars:
                self.hash_output_vars[algo_name].set("")
            self.status_label.config(text="Input is empty.")
            return

        for algo_name, output_var in self.hash_output_vars.items():
            computed_hash = hashing_util.compute_hash(input_text, algo_name)
            output_var.set(computed_hash if computed_hash else "Error computing hash")
        self.status_label.config(text="Hashes computed.")


    def _open_certificate_analyzer_from_file_dialog(self):
        analyzer_dialog = CertificateAnalyzerDialog(self)
        analyzer_dialog.grab_set()

    def _open_certificate_details_window(self, pem_data_string, title_suffix=None):
        try:
            from utils.certificate_analyzer import analyze_certificate_data, format_certificate_details

            details = analyze_certificate_data(pem_data_string.encode('utf-8'))
            formatted_details = format_certificate_details(details)

            details_window = tk.Toplevel(self)
            details_window.title(f"Certificate Details: {title_suffix}" if title_suffix else "Certificate Details")
            details_window.geometry("650x500")

            text_frame = ttk.Frame(details_window, padding=5)
            text_frame.pack(expand=True, fill=tk.BOTH)

            text_area = tk.Text(text_frame, wrap=tk.WORD, height=20, width=80)
            text_area.insert(tk.END, formatted_details)
            text_area.config(state=tk.DISABLED)

            text_scrollbar_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_area.yview)
            text_area.config(yscrollcommand=text_scrollbar_y.set)

            text_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

            ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)
            details_window.grab_set()
            details_window.transient(self)

        except ImportError:
             messagebox.showerror("Error", "Certificate analysis components are missing.", parent=self)
        except Exception as e:
             messagebox.showerror("Error", f"Could not display certificate details: {e}", parent=self)


    def _load_system_certificates(self):
        self.status_label.config(text="Loading system certificates...")
        self.load_store_button.config(state=tk.DISABLED)
        self.update_idletasks()

        try:
            certs = sys_cert_store.get_system_certificates()
            for item in self.cert_tree.get_children(): self.cert_tree.delete(item)
            self._system_certs_cache = []

            if not certs:
                self.status_label.config(text="No system certificates found or OS not supported.")
            elif isinstance(certs, list) and certs and "error" in certs[0]:
                self.status_label.config(text=f"Error: {certs[0]['error']}")
                messagebox.showerror("Error Loading Certificates", certs[0]['error'], parent=self)
            else:
                self._system_certs_cache = certs
                for i, cert_summary in enumerate(certs):
                    self.cert_tree.insert("", tk.END, iid=str(i), values=(
                        cert_summary.get('subject_cn', 'N/A'),
                        cert_summary.get('issuer_cn', 'N/A'),
                        cert_summary.get('serial_number', 'N/A'),
                        cert_summary.get('valid_to', 'N/A'),
                        cert_summary.get('source_detail', 'N/A')
                    ))
                self.status_label.config(text=f"Loaded {len(certs)} system certificates.")
        except Exception as e:
            self.status_label.config(text=f"Failed to load certificates.")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self)
        finally:
            self.load_store_button.config(state=tk.NORMAL)

    def _on_system_certificate_selected(self, event=None):
        selected_items = self.cert_tree.selection()
        if not selected_items: return

        selected_iid = selected_items[0]
        try:
            cert_index = int(selected_iid)
            selected_cert_info = self._system_certs_cache[cert_index]
            title_suffix = selected_cert_info.get('subject_cn', 'Selected Certificate')

            if selected_cert_info.get("pem_data"):
                self._open_certificate_details_window(selected_cert_info["pem_data"], title_suffix)
            elif selected_cert_info.get("raw_windows_info"):
                raw_ps_info = selected_cert_info["raw_windows_info"]
                details_text = "Windows Certificate Summary (Full analysis requires export/PEM):\n"
                details_text += f"  Store: {selected_cert_info.get('source_detail', 'N/A')}\n"
                details_text += f"  Subject: {raw_ps_info.get('Subject', 'N/A')}\n"
                details_text += f"  Issuer: {raw_ps_info.get('Issuer', 'N/A')}\n"
                details_text += f"  Serial: {raw_ps_info.get('SerialNumber', 'N/A')}\n"
                details_text += f"  Thumbprint (from PS): {raw_ps_info.get('Thumbprint', 'N/A')}\n"
                details_text += f"  Valid From: {selected_cert_info.get('valid_from', 'N/A')}\n"
                details_text += f"  Valid To: {selected_cert_info.get('valid_to', 'N/A')}\n"

                self._show_simple_details_dialog("Windows Cert Info", title_suffix, details_text)
            else:
                messagebox.showinfo("No Details", "No direct analysis data (PEM or Raw) available for this certificate summary.", parent=self)
        except (IndexError, ValueError) as e:
            messagebox.showerror("Error", f"Could not retrieve certificate details: {e}", parent=self)

    def _show_simple_details_dialog(self, window_title_prefix, item_title, details_text):
        details_window = tk.Toplevel(self)
        details_window.title(f"{window_title_prefix}: {item_title}")
        details_window.geometry("600x300")
        text_area = tk.Text(details_window, wrap=tk.WORD, height=10, width=70)
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        text_area.insert(tk.END, details_text)
        text_area.config(state=tk.DISABLED)
        ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=5)
        details_window.grab_set()
        details_window.transient(self)

    def _url_encode_action(self):
        input_text = self.url_text_area.get("1.0", tk.END + "-1c")
        if not input_text:
            # Optionally show a warning or just do nothing / clear output
            self.url_text_area.delete("1.0", tk.END) # Clear if input is empty
            return

        encoded_text = url_coding_util.url_encode_string(input_text)
        if encoded_text is not None:
            self.url_text_area.delete("1.0", tk.END)
            self.url_text_area.insert("1.0", encoded_text)
        else:
            messagebox.showerror("Encoding Error", "Could not URL encode the provided text.", parent=self)

    def _url_decode_action(self):
        input_text = self.url_text_area.get("1.0", tk.END + "-1c")
        if not input_text:
            self.url_text_area.delete("1.0", tk.END)
            return

        decoded_text = url_coding_util.url_decode_string(input_text)
        if decoded_text is not None:
            self.url_text_area.delete("1.0", tk.END)
            self.url_text_area.insert("1.0", decoded_text)
        else:
            messagebox.showerror("Decoding Error", "Could not URL decode the provided text. It might be malformed.", parent=self)


if __name__ == '__main__':
    import os
    if not os.path.exists("dialogs"): os.makedirs("dialogs")
    if not os.path.exists("dialogs/__init__.py"):
        with open("dialogs/__init__.py", "w") as f: pass

    if not os.path.exists("dialogs/certificate_analyzer_dialog.py"):
        with open("dialogs/certificate_analyzer_dialog.py", "w") as f:
            f.write("""import tkinter as tk; from tkinter import ttk
class CertificateAnalyzerDialog(tk.Toplevel):
    def __init__(self, parent): super().__init__(parent); self.title("Dummy Cert Analyzer")
""")

    if not os.path.exists("utils"): os.makedirs("utils")
    if not os.path.exists("utils/__init__.py"):
        with open("utils/__init__.py", "w") as f: pass
    if not os.path.exists("utils/system_certificate_store.py"):
        with open("utils/system_certificate_store.py", "w") as f:
            f.write("""
def get_system_certificates():
    return [{"subject_cn": "DummySystemCert1", "issuer_cn": "DummySystemCA", "serial_number": "sys123", "valid_to": "2027-01-01", "source_detail": "Dummy System Store", "pem_data": "-----BEGIN DUMMY-----\\ndummy\\n-----END DUMMY-----"}]
""")
    if not os.path.exists("utils/certificate_analyzer.py"):
         with open("utils/certificate_analyzer.py", "w") as f:
            f.write("""
def analyze_certificate_data(pem_bytes): return {"Subject": "Dummy Parsed Subject", "Issuer": "Dummy Parsed Issuer"}
def format_certificate_details(details): return f"Formatted: {details.get('Subject')} / {details.get('Issuer')}"
""")
    if not os.path.exists("utils/hashing_util.py"):
        with open("utils/hashing_util.py", "w") as f:
            f.write("""
def compute_hash(text, algorithm="sha256"):
    if not text: return ""
    import hashlib
    h = hashlib.new(algorithm)
    h.update(text.encode('utf-8'))
    return h.hexdigest()
""")
    if not os.path.exists("utils/url_coding_util.py"): # Dummy for url_coding_util
        with open("utils/url_coding_util.py", "w") as f:
            f.write("""
import urllib.parse
def url_encode_string(s): return urllib.parse.quote(s) if s is not None else ""
def url_decode_string(s): return urllib.parse.unquote(s) if s is not None else ""
""")

    # This dynamic import/reload section can be problematic.
    # It's best to run this test script in an environment where modules are correctly installed/available.
    # For agent execution, we assume the file system state is consistent.
    # import importlib
    # if 'utils.certificate_analyzer' in globals() or 'utils.certificate_analyzer' in locals(): importlib.reload(utils.certificate_analyzer)
    # ... and so on for other potentially reloaded modules

    root = tk.Tk()
    root.title("Main App Window (Test)")

    def open_security_tool():
        sec_dialog = SecurityToolDialog(root)

    button = ttk.Button(root, text="Open Security Tool", command=open_security_tool)
    button.pack(padx=20, pady=20)

    root.mainloop()
