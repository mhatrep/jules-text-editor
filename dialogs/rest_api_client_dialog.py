import tkinter as tk
from tkinter import ttk, messagebox
import json # For pretty printing JSON response

try:
    import requests
except ImportError:
    requests = None # Will be checked in _send_request

class RestApiClientDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.root = parent_editor.root
        self.top = tk.Toplevel(self.root)
        self.top.title("REST API Client")
        self.top.transient(self.root)
        self.top.grab_set() # Modal
        self.top.resizable(True, True)

        self.url_var = tk.StringVar(value="https://jsonplaceholder.typicode.com/todos/1")
        self.method_var = tk.StringVar(value="GET")
        self.http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        self.body_type_var = tk.StringVar(value="JSON") # Default body type
        self.body_types = ["JSON", "XML", "Plain Text", "None"] # Supported body types

        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Request Setup (URL, Method)
        request_setup_frame = ttk.Frame(main_frame)
        request_setup_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Label(request_setup_frame, text="URL:").pack(side=tk.LEFT, padx=(0,5))
        url_entry = ttk.Entry(request_setup_frame, textvariable=self.url_var, width=70)
        url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,10))
        url_entry.focus_set()
        ttk.Label(request_setup_frame, text="Method:").pack(side=tk.LEFT, padx=(0,5))
        method_combobox = ttk.Combobox(request_setup_frame, textvariable=self.method_var, values=self.http_methods, state="readonly", width=10)
        method_combobox.pack(side=tk.LEFT)
        method_combobox.bind("<<ComboboxSelected>>", self._on_method_change)


        # Request Details Notebook (Headers, Body)
        request_notebook = ttk.Notebook(main_frame)
        request_notebook.pack(expand=True, fill=tk.BOTH, pady=(0,10))

        # Request Headers Tab
        req_headers_frame = ttk.Frame(request_notebook, padding=5)
        request_notebook.add(req_headers_frame, text="Headers")
        ttk.Label(req_headers_frame, text="Enter headers (HeaderName: HeaderValue), one per line:").pack(anchor=tk.W, pady=(0,2))
        self.req_headers_text = tk.Text(req_headers_frame, height=5, width=80, wrap=tk.WORD, undo=True)
        self.req_headers_text.pack(expand=True, fill=tk.BOTH)
        self.req_headers_text.insert("1.0", "User-Agent: JulesTextEditor/1.0\nAccept: */*")


        # Request Body Tab
        self.req_body_frame = ttk.Frame(request_notebook, padding=5) # Store as instance var to enable/disable
        request_notebook.add(self.req_body_frame, text="Body")

        body_options_frame = ttk.Frame(self.req_body_frame)
        body_options_frame.pack(fill=tk.X, pady=(0,5))
        ttk.Label(body_options_frame, text="Body Type:").pack(side=tk.LEFT, padx=(0,5))
        self.body_type_combo = ttk.Combobox(body_options_frame, textvariable=self.body_type_var, values=self.body_types, state="readonly", width=15)
        self.body_type_combo.pack(side=tk.LEFT)
        self.body_type_combo.bind("<<ComboboxSelected>>", self._on_body_type_change)

        self.req_body_text = tk.Text(self.req_body_frame, height=8, width=80, wrap=tk.WORD, undo=True)
        self.req_body_text.pack(expand=True, fill=tk.BOTH)
        self.req_body_text.insert("1.0", "{\n  \"key\": \"value\",\n  \"example\": true\n}") # Example JSON

        # Send Button and Status Label
        send_button = ttk.Button(main_frame, text="Send Request", command=self._send_request)
        send_button.pack(pady=5)
        self.status_label_var = tk.StringVar(value="Status: -")
        status_display_label = ttk.Label(main_frame, textvariable=self.status_label_var, font=("TkDefaultFont", 10, "bold"))
        status_display_label.pack(anchor=tk.W, pady=(5,2))


        # Response Details Notebook (Body, Headers)
        response_notebook = ttk.Notebook(main_frame)
        response_notebook.pack(expand=True, fill=tk.BOTH, pady=(0,10))

        # Response Body Tab
        resp_body_frame = ttk.Frame(response_notebook, padding=5)
        response_notebook.add(resp_body_frame, text="Response Body")
        self.resp_body_text = tk.Text(resp_body_frame, height=10, width=80, wrap=tk.WORD, undo=False)
        self.resp_body_text.pack(expand=True, fill=tk.BOTH)
        self.resp_body_text.config(state=tk.DISABLED) # Read-only

        # Response Headers Tab
        resp_headers_frame = ttk.Frame(response_notebook, padding=5)
        response_notebook.add(resp_headers_frame, text="Response Headers")
        self.resp_headers_text = tk.Text(resp_headers_frame, height=8, width=80, wrap=tk.WORD, undo=False)
        self.resp_headers_text.pack(expand=True, fill=tk.BOTH)
        self.resp_headers_text.config(state=tk.DISABLED) # Read-only

        # Copy Button
        copy_button_frame = ttk.Frame(main_frame)
        copy_button_frame.pack(fill=tk.X, pady=(5,0))
        self.copy_resp_body_button = ttk.Button(copy_button_frame, text="Copy Response Body", command=self._copy_response_body, state=tk.DISABLED)
        self.copy_resp_body_button.pack(side=tk.LEFT)


        self._on_method_change() # Initialize body text area state based on default method
        self.top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f"{self.top.winfo_width()}x{self.top.winfo_height()}+{x}+{y}")
        self.top.minsize(500, 600) # Ensure dialog is reasonably sized
        self.top.bind("<Escape>", lambda e: self.top.destroy()) # Close on Escape

    def _on_method_change(self, event=None):
        method = self.method_var.get()
        no_body_methods = ["GET", "HEAD", "DELETE", "OPTIONS"] # Methods that typically don't have a body
        if method in no_body_methods:
            self.req_body_text.config(state=tk.DISABLED)
            self.body_type_combo.config(state=tk.DISABLED)
        else:
            self.req_body_text.config(state=tk.NORMAL)
            self.body_type_combo.config(state=tk.NORMAL)

    def _on_body_type_change(self, event=None):
        # Could potentially auto-update Content-Type header here, but might be too intrusive.
        # For now, this is a manual process for the user.
        pass

    def _parse_headers_text(self, headers_str):
        headers = {}
        for line in headers_str.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        return headers

    def _update_headers_text(self, key_to_update, new_value):
        """Updates or adds a header in the request headers text area."""
        current_headers_content = self.req_headers_text.get("1.0", tk.END + "-1c")
        lines = current_headers_content.splitlines()
        found = False
        new_lines = []
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                if key.strip().lower() == key_to_update.lower():
                    new_lines.append(f"{key_to_update}: {new_value}")
                    found = True
                else:
                    new_lines.append(line)
            else: # Keep empty or malformed lines as they are
                new_lines.append(line)

        if not found: # Add new header
            new_lines.append(f"{key_to_update}: {new_value}")
            # Ensure there's a newline if adding to existing non-empty content
            if not current_headers_content.strip(): # If text area was empty
                 self.req_headers_text.delete("1.0", tk.END)
                 self.req_headers_text.insert("1.0", "\n".join(new_lines).strip()) # Avoid leading/trailing newlines if only one header
            elif not current_headers_content.endswith('\n'):
                 self.req_headers_text.insert(tk.END, f"\n{key_to_update}: {new_value}")
            else:
                 self.req_headers_text.insert(tk.END, f"{key_to_update}: {new_value}\n")
        else: # If header was updated, replace entire content
            self.req_headers_text.delete("1.0", tk.END)
            self.req_headers_text.insert("1.0", "\n".join(new_lines))

        # Ensure last line has a newline if content exists (for cleaner multi-line editing)
        final_content = self.req_headers_text.get("1.0", tk.END + "-1c")
        if final_content.strip() and not final_content.endswith('\n'):
            self.req_headers_text.insert(tk.END, "\n")


    def _send_request(self):
        if requests is None:
            messagebox.showerror("Dependency Missing", "The 'requests' library is not installed. Please install it (e.g., pip install requests).", parent=self.top)
            self.status_label_var.set("Status: Error - 'requests' library missing")
            return

        url = self.url_var.get()
        method = self.method_var.get()
        headers_str = self.req_headers_text.get("1.0", tk.END + "-1c")
        body_str = self.req_body_text.get("1.0", tk.END + "-1c") if self.req_body_text.cget("state") == tk.NORMAL else None

        if not url:
            messagebox.showerror("Input Error", "URL cannot be empty.", parent=self.top)
            return

        headers = self._parse_headers_text(headers_str)

        # Automatically set Content-Type based on body_type_var if body exists and Content-Type not manually set
        if body_str and 'content-type' not in (k.lower() for k in headers):
            body_type = self.body_type_var.get()
            if body_type == "JSON":
                headers['Content-Type'] = 'application/json'
            elif body_type == "XML":
                headers['Content-Type'] = 'application/xml'
            elif body_type == "Plain Text":
                headers['Content-Type'] = 'text/plain'
            # If Content-Type was added, reflect it in the UI (optional, but good for user feedback)
            if 'Content-Type' in headers and not any(h.lower().startswith("content-type:") for h in headers_str.splitlines()):
                 self._update_headers_text("Content-Type", headers['Content-Type'])


        self.status_label_var.set(f"Status: Sending {method} request to {url}...")
        self.top.update_idletasks() # Ensure status label updates immediately

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body_str.encode('utf-8') if body_str else None, # Encode body if present
                timeout=10 # 10-second timeout
            )
            self.status_label_var.set(f"Status: {response.status_code} {response.reason}")

            # Display Response Headers
            self.resp_headers_text.config(state=tk.NORMAL)
            self.resp_headers_text.delete("1.0", tk.END)
            for key, value in response.headers.items():
                self.resp_headers_text.insert(tk.END, f"{key}: {value}\n")
            self.resp_headers_text.config(state=tk.DISABLED)

            # Display Response Body
            self.resp_body_text.config(state=tk.NORMAL)
            self.resp_body_text.delete("1.0", tk.END)
            response_content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in response_content_type:
                try:
                    json_body = response.json()
                    pretty_json = json.dumps(json_body, indent=2, sort_keys=True)
                    self.resp_body_text.insert(tk.END, pretty_json)
                except json.JSONDecodeError: # If it says JSON but isn't valid
                    self.resp_body_text.insert(tk.END, response.text)
            else: # For non-JSON, display raw text
                self.resp_body_text.insert(tk.END, response.text)
            self.resp_body_text.config(state=tk.DISABLED)
            self.copy_resp_body_button.config(state=tk.NORMAL if response.text else tk.DISABLED)

        except requests.exceptions.Timeout:
            messagebox.showerror("Request Error", "Request timed out.", parent=self.top)
            self.status_label_var.set("Status: Error - Timeout")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Request Error", "Could not connect to the server. Check the URL and network connection.", parent=self.top)
            self.status_label_var.set("Status: Error - Connection Failed")
        except requests.exceptions.RequestException as e: # Catch other requests-related errors
            messagebox.showerror("Request Error", f"An error occurred: {e}", parent=self.top)
            self.status_label_var.set(f"Status: Error - {type(e).__name__}")
            # Clear response areas on error
            self.resp_headers_text.config(state=tk.NORMAL); self.resp_headers_text.delete("1.0", tk.END); self.resp_headers_text.config(state=tk.DISABLED)
            self.resp_body_text.config(state=tk.NORMAL); self.resp_body_text.delete("1.0", tk.END); self.resp_body_text.config(state=tk.DISABLED)
            self.copy_resp_body_button.config(state=tk.DISABLED)


    def _copy_response_body(self):
        response_body_content = self.resp_body_text.get("1.0", tk.END + "-1c")
        if response_body_content: # Check if there's content
            try:
                self.top.clipboard_clear()
                self.top.clipboard_append(response_body_content)
                messagebox.showinfo("Copied", "Response body copied to clipboard.", parent=self.top)
            except tk.TclError:
                 messagebox.showerror("Error", "Could not copy to clipboard. TclError occurred.", parent=self.top)
        else:
            messagebox.showwarning("Empty Response", "There is no response body to copy.", parent=self.top)
