import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import tkinter.font as tkfont
from PIL import ImageGrab, Image, ImageTk, ImageDraw, ImageFont
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import string
import re
import collections
import random
import quick_transformer
import utils.text_processing as text_processing
import subprocess
import csv
import configparser
import webbrowser
import world_clock
import base64
import io

try:
    import graphviz
except ImportError:
    graphviz = None

try:
    import data_to_table_converter
    from data_to_table_converter import DataParsingError
except ImportError:
    data_to_table_converter = None
    DataParsingError = Exception

import fnmatch
from dialogs.dialog_manager import DialogManager

ICON_DATA = {
    "new-file": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAALElEQVR4nGNgGP7gPxTgkmei1IJhYAAjMgdfYKFoYmSE66PYBQTB4I/GYQAANzAUAE4vZ6sAAAAASUVORK5CYII=",
    "open-file": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAATUlEQVR4nGNgGGjAyMDA8J+APF7AwsDAwPD/OhadmsS5gIWAPD7XQSzCpwiby1A0a0JcwMjAwPCfkGJcgIk8baMGUNUAWFIlmGAGLwAAMSoK76Jc2uIAAAAASUVORK5CYII=",
    "save": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAR0lEQVR4nGNgGGjACGP8////P8maGRkZWVAFEGyYcTAxXHwmUm1FBwNvAAsuCeTwwMbHaQAxcYFs2MCHwXAzgNjcQHquwQMAnwQQIMt8N1YAAAAASUVORK5CYII=",
    "cut": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAZklEQVR4nN2QQRYAIQhCsfvf2dm0UAOz7bDzQV8S+J8c8Bd/MVNBmJ8ABpjaFOeYSwAFUY/3zMW+UR8fgLrpNieAAw4PS42UK74BdtxgUjuqBYSaEtLeoIaZvzpTNap5uqHTNDfSB8XmLgcK6yY3AAAAAElFTkSuQmCC",
    "copy": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAUklEQVR4nM2TMQ4AIAgDD+P/v4yr0ZSADtoJAhSoAq9hk+3FfAD67LhrDrOtFoCW6BrimqCrgBh53dEkAeQ0+UwD9VRZgrU687E+0CBa+ug2yhj/xwop/X5ZvQAAAABJRU5ErkJggg==",
    "paste": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAXklEQVR4nGNgGGjAiMT+T6J6BgYGBgYWZM7aG89w6gzWkMIqzoJVFLcGdFcy4jSAgYGB4f9/3L5iZGTE7wJkRfgATgPQwwPqJfyBiEUDOhgNA1qEAal5AcMcMvSgAgDpuBj2wE5HTAAAAABJRU5ErkJggg==",
    "undo": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAQUlEQVR4nGNgGGjAiFvq/38kZTjVMRHWTLILiLMZhwuItxmLAaRrxuKCkW4A4SgjwgWkG4JDA3qUkpyUyfMOWQAAM1YMGG2M/iMAAAAASUVORK5CYII=",
    "redo": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAARUlEQVR4nGNgGGjASFjJ//9IyjHUM5FmH7JhRLsAv0tIdAGmYWQagDCEAgModsEwMAASlWQagEgHJCZlVM1kuAAzL1AMAPs4DBgARkQKAAAAAElFTkSuQmCC",
    "format-code": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAMklEQVR4nGNgGAWMyJz/////x6qIkZERmzgDAwMDE7VdRH9AVBhg1QgNl5ESBsM8HQAAxrsMChLkGikAAAAASUVORK5CYII=",
    "calendar": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAQ0lEQVR4nGNgGGjAiMT+T45+JmTe////Gf7//080m4GBgQHFAHIAxQZQHAYsyDxkvxHUyQixe+DDYNQAKqQDSh3AAAAd5x4CxlAVJAAAAABJRU5ErkJggg==",
}

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class EditorTab:
    def __init__(self, notebook_widget, app_instance, file_path=None, default_title="Untitled"):
        self.app = app_instance
        self.notebook = notebook_widget
        self.frame = ttk.Frame(self.notebook, padding=2)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.line_numbers_font = tkfont.Font(family=app_instance.editor_font.cget("family"), size=app_instance.editor_font.cget("size"))
        self.line_numbers_canvas = tk.Canvas(self.frame, width=65, bg='lightgrey', highlightthickness=0)
        self.line_numbers_visible = self.app.show_line_numbers
        if self.line_numbers_visible: self.line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y)
        self.text_area = tk.Text(self.frame, wrap=tk.WORD, undo=True, yscrollcommand=self.sync_scroll_text, font=app_instance.editor_font)
        self.text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.current_file = file_path
        self.text_changed = False
        self.text_area.bind("<<Modified>>", self.on_text_changed_tab_and_update_lines)
        self.text_area.bind("<Configure>", self.on_text_changed_tab_and_update_lines)
        self.text_area.bind("<MouseWheel>", self.on_scroll_wheel)
        self.text_area.bind("<Button-4>", self.on_scroll_wheel)
        self.text_area.bind("<Button-5>", self.on_scroll_wheel)
        self.text_area.bind("<KeyRelease>", self.on_key_or_mouse_release)
        self.text_area.bind("<ButtonRelease-1>", self.on_key_or_mouse_release)
        self.text_area.bind("<KeyRelease>", self.update_current_line_highlight, add="+")
        self.text_area.bind("<ButtonRelease-1>", self.update_current_line_highlight, add="+")
        self.text_area.bind("<FocusIn>", self.update_current_line_highlight, add="+")
        self.text_area.tag_configure("search_highlight", background="yellow", foreground="black")
        self.text_area.tag_configure("current_search_highlight", background="orange", foreground="black")
        self._keyword_highlight_after_id = None
        self._syntax_highlight_after_id = None
        self.current_language_name = None
        self.tab_original_text_for_filter: str | None = None
        self.is_tab_filtered_view: bool = False
        self.tab_filter_str: str = ""
        self.tab_filter_case_sensitive: bool = False
        self.tab_filter_invert: bool = False
        self.find_replace_mod_seq = 0
        self.text_area.tag_configure("hl_keyword", foreground="#0000FF")
        self.text_area.tag_configure("hl_comment", foreground="#008000")
        self.text_area.tag_configure("hl_string", foreground="#A52A2A")
        self.text_area.tag_configure("hl_number", foreground="#FF00FF")
        self.text_area.tag_configure("hl_operator", foreground="#FF8C00")
        self.text_area.tag_configure("hl_builtin", foreground="#20B2AA")
        self.text_area.tag_configure("current_line_highlight", background="#FFFFE0")
        self.tab_notes_style_active = self.app.notes_style_active
        self._notes_style_highlight_after_id = None
        notes_bold_font = tkfont.Font(family=self.app.editor_font.cget("family"), size=self.app.editor_font.cget("size"), weight="bold")
        self.text_area.tag_configure("notes_number", foreground="red")
        self.text_area.tag_configure("notes_header", foreground="navy", font=notes_bold_font)
        self.text_area.tag_configure("notes_comment", foreground="dark green", font=notes_bold_font)
        self.text_area.tag_configure("notes_separator", foreground="orange")
        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=self.sync_scroll_text)
        self.redraw_line_numbers()

        self.default_title = default_title
        if file_path:
            self.load_file_content(file_path)
        else:
            self.update_tab_title()

        self.apply_keyword_highlights(self.app.keyword_highlight_settings)
        self._detect_and_set_language(self.current_file)
        self.text_area.bind("<KeyPress>", self.on_text_area_keypress_filtered, add="+")
        self.update_current_line_highlight()

    def update_current_line_highlight(self, event=None):
        self.text_area.tag_remove("current_line_highlight", "1.0", tk.END)
        try:
            if not self.text_area.winfo_exists(): return
            cursor_pos = self.text_area.index(tk.INSERT)
            line_num = cursor_pos.split('.')[0]
            self.text_area.tag_add("current_line_highlight", f"{line_num}.0", f"{line_num}.end")
        except tk.TclError: pass
        except Exception as e: print(f"Error updating current line highlight: {e}")

    def on_text_area_keypress_filtered(self, event):
        if self.is_tab_filtered_view:
            if event.state & 0x0004:
                keysym_lower = event.keysym.lower()
                if keysym_lower == 'x': return "break"
                if keysym_lower in ['c', 'a']: return
                return
            modifying_keysyms = ["BackSpace", "Delete", "Return", "Tab", "KP_Enter"]
            if event.keysym in modifying_keysyms: return "break"
            if event.char and event.char.isprintable() and not (event.state & 0x0004): return "break"
            return
        return

    def load_file_content(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f: content = f.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
            self.current_file = filepath
            self.text_changed = False
            self.text_area.edit_modified(False)
            self.update_tab_title()
            self._detect_and_set_language(self.current_file)
            self.apply_keyword_highlights(self.app.keyword_highlight_settings)
        except Exception as e:
            messagebox.showerror("Error Opening File", str(e))
            self.close_tab(check_save=False)

    def update_tab_title(self):
        tab_text = os.path.basename(self.current_file) if self.current_file else self.default_title
        if self.text_changed: tab_text = "*" + tab_text
        try:
            current_tabs = self.notebook.tabs()
            if self.frame_id() in current_tabs: self.notebook.tab(self.frame_id(), text=tab_text)
        except tk.TclError: pass

    def on_text_changed_tab_and_update_lines(self, event=None):
        if event and str(event.type) == "Modified":
            if not self.is_tab_filtered_view:
                if self.text_area.edit_modified():
                    if not self.text_changed:
                        self.text_changed = True
                        self.update_tab_title()
                    self.find_replace_mod_seq += 1
            self.text_area.edit_modified(False)
        self.text_area.after(1, self.redraw_line_numbers)
        if event and (str(event.type) == "Modified" or str(event.type) == "Configure"):
            self.app.update_status_bar()
            if str(event.type) == "Modified":
                self.clear_search_highlight_tags()
                if self.app.keyword_highlight_settings.get("active", False):
                    if self._keyword_highlight_after_id: self.text_area.after_cancel(self._keyword_highlight_after_id)
                    self._keyword_highlight_after_id = self.text_area.after(500, lambda: self.apply_keyword_highlights(self.app.keyword_highlight_settings))
                if self.current_language_name:
                    if self._syntax_highlight_after_id: self.text_area.after_cancel(self._syntax_highlight_after_id)
                    self._syntax_highlight_after_id = self.text_area.after(500, self.apply_syntax_highlighting)
                if self.tab_notes_style_active:
                    if self._notes_style_highlight_after_id: self.text_area.after_cancel(self._notes_style_highlight_after_id)
                    self._notes_style_highlight_after_id = self.text_area.after(500, self.apply_notes_style_highlighting)

    def clear_search_highlight_tags(self):
        self.text_area.tag_remove("search_highlight", "1.0", tk.END)
        self.text_area.tag_remove("current_search_highlight", "1.0", tk.END)

    def apply_text_filter(self):
        if not self.tab_filter_str:
            if self.is_tab_filtered_view and self.tab_original_text_for_filter is not None:
                current_insert = self.text_area.index(tk.INSERT)
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", self.tab_original_text_for_filter)
                self.tab_original_text_for_filter = None
                try:
                    self.text_area.mark_set(tk.INSERT, current_insert)
                    self.text_area.see(current_insert)
                except tk.TclError: self.text_area.mark_set(tk.INSERT, "1.0")
            self.is_tab_filtered_view = False
        else:
            if not self.is_tab_filtered_view:
                self.tab_original_text_for_filter = self.text_area.get("1.0", tk.END + "-1c")
            self.is_tab_filtered_view = True
            source_text_for_filtering = self.tab_original_text_for_filter if self.tab_original_text_for_filter is not None else self.text_area.get("1.0", tk.END + "-1c")
            lines = source_text_for_filtering.splitlines(keepends=True)
            matching_lines = []
            str_to_find = self.tab_filter_str if self.tab_filter_case_sensitive else self.tab_filter_str.lower()
            for line_content_with_ending in lines:
                line_to_check_in = line_content_with_ending if self.tab_filter_case_sensitive else line_content_with_ending.lower()
                match_found = (str_to_find in line_to_check_in)
                if self.tab_filter_invert:
                    if not match_found: matching_lines.append(line_content_with_ending)
                else:
                    if match_found: matching_lines.append(line_content_with_ending)
            self.text_area.delete("1.0", tk.END)
            if matching_lines: self.text_area.insert("1.0", "".join(matching_lines))

        self.redraw_line_numbers()
        if self.current_language_name: self.apply_syntax_highlighting()
        if self.app.keyword_highlight_settings.get("active", False): self.apply_keyword_highlights(self.app.keyword_highlight_settings)
        self.app.update_status_bar()

    def _detect_and_set_language(self, filepath):
        self.current_language_name = None
        if not filepath:
            self.apply_syntax_highlighting()
            return
        _, extension = os.path.splitext(filepath)
        extension = extension.lower()
        if self.app and hasattr(self.app, 'language_definitions'):
            for lang_name, lang_def in self.app.language_definitions.items():
                if extension in lang_def.get("extensions", []):
                    self.current_language_name = lang_name
                    break
        self.apply_syntax_highlighting()

    def _clear_syntax_highlight_tags(self):
        syntax_tags_to_clear = ["hl_keyword", "hl_comment", "hl_string", "hl_number", "hl_operator", "hl_builtin"]
        for tag in syntax_tags_to_clear:
            try: self.text_area.tag_remove(tag, "1.0", tk.END)
            except tk.TclError: pass

    def apply_syntax_highlighting(self):
        if not self.current_language_name or not self.app.language_definitions: return
        lang_def = self.app.language_definitions.get(self.current_language_name)
        if not lang_def or not lang_def.get("rules"): return
        self._clear_syntax_highlight_tags()
        all_text = self.text_area.get("1.0", tk.END)
        if not all_text.strip(): return
        import re
        for rule in lang_def["rules"]:
            token_type = rule["token_type"]
            pattern_str = rule["pattern"]
            try:
                for match in re.finditer(pattern_str, all_text):
                    start_offset, end_offset = match.span()
                    start_idx = self.text_area.index(f"1.0 + {start_offset} chars")
                    end_idx = self.text_area.index(f"1.0 + {end_offset} chars")
                    self.text_area.tag_add(token_type, start_idx, end_idx)
            except re.error as e: print(f"Regex error for language {self.current_language_name}, pattern {pattern_str}: {e}")
            except tk.TclError as e:
                print(f"TclError during syntax highlighting: {e}. Text might have changed.")
                return

    def apply_keyword_highlights(self, highlight_settings):
        for i in range(len(self.app.pastel_colors) + 5):
            try: self.text_area.tag_remove(f"user_keyword_{i}", "1.0", tk.END)
            except tk.TclError: pass
        if not highlight_settings or not highlight_settings.get("active", False) or not highlight_settings.get("parsed_keywords"): return
        keywords = highlight_settings["parsed_keywords"]
        case_sensitive = highlight_settings["case_sensitive"]
        whole_word = highlight_settings["whole_word"]
        kw_to_color = highlight_settings["keyword_to_color_map"]
        kw_to_tag = highlight_settings["keyword_to_tag_name_map"]
        for keyword_text in keywords:
            tag_name = kw_to_tag.get(keyword_text)
            color = kw_to_color.get(keyword_text)
            if not tag_name or not color: continue
            self.text_area.tag_configure(tag_name, background=color, foreground="black")
            start_index = "1.0"
            while True:
                nocase_local = not case_sensitive
                search_pattern = keyword_text
                use_regexp_for_this_keyword = False
                if whole_word: pass
                length_var = tk.IntVar()
                pos = self.text_area.search(search_pattern, start_index, tk.END, nocase=nocase_local, regexp=use_regexp_for_this_keyword, exact=whole_word, count=length_var)
                if pos:
                    match_len = length_var.get()
                    if match_len == 0 and len(search_pattern) > 0 : match_len = len(search_pattern)
                    if match_len > 0:
                        end_pos = self.text_area.index(f"{pos} + {match_len} chars")
                        self.text_area.tag_add(tag_name, pos, end_pos)
                        start_index = end_pos
                    else: break
                else: break

    def on_key_or_mouse_release(self, event=None): self.app.update_status_bar()

    def on_scroll_wheel(self, event):
        if event.num == 4: self.text_area.yview_scroll(-1, "units")
        elif event.num == 5: self.text_area.yview_scroll(1, "units")
        elif event.delta: self.text_area.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def sync_scroll_text(self, *args):
        self.scrollbar.set(*args)
        self.redraw_line_numbers()

    def redraw_line_numbers(self):
        if not self.line_numbers_visible or not self.line_numbers_canvas.winfo_ismapped(): return
        self.line_numbers_canvas.delete("all")
        self.text_area.update_idletasks()
        first_visible_char_index = self.text_area.index("@0,0")
        if not first_visible_char_index: return
        try: first_line_num = int(first_visible_char_index.split('.')[0])
        except ValueError: return
        first_visible_line_bbox = self.text_area.dlineinfo(f"{first_line_num}.0")
        if not first_visible_line_bbox:
            if self.text_area.index("end-1c") == "1.0":
                 self.line_numbers_canvas.create_text(self.line_numbers_canvas.winfo_width() - 2, 0, anchor=tk.NW, text="1", font=self.line_numbers_font)
            return
        y_offset_of_content_top_from_visible_area_top = first_visible_line_bbox[1]
        current_line_to_draw_num = first_line_num
        while True:
            dline_info = self.text_area.dlineinfo(f"{current_line_to_draw_num}.0")
            if dline_info is None: break
            line_y_in_text_content = dline_info[1]
            line_height_in_text_content = dline_info[3]
            canvas_y_for_line_top = line_y_in_text_content - y_offset_of_content_top_from_visible_area_top
            if canvas_y_for_line_top > self.line_numbers_canvas.winfo_height(): break
            if (canvas_y_for_line_top + line_height_in_text_content) >= 0 and canvas_y_for_line_top <= self.line_numbers_canvas.winfo_height():
                canvas_x_for_number = self.line_numbers_canvas.winfo_width() - 2
                self.line_numbers_canvas.create_text(canvas_x_for_number, canvas_y_for_line_top, anchor=tk.NE, text=str(current_line_to_draw_num), font=self.line_numbers_font)
            current_line_to_draw_num += 1
            if current_line_to_draw_num > first_line_num + 5000:
                 print(f"DEBUG: redraw_line_numbers breaking early after drawing {5000} lines.")
                 break
            total_lines_str = self.text_area.index(f"{tk.END}-1c").split('.')[0]
            if total_lines_str.isdigit() and current_line_to_draw_num > int(total_lines_str) + 1: break

    def get_content(self): return self.text_area.get("1.0", tk.END + "-1c")
    def frame_id(self): return self.frame

    def close_tab(self, check_save=True):
        if check_save and not self.check_unsaved_changes_tab(): return False
        try:
            selected_tab_before_close = self.app.notebook.index(tk.CURRENT)
            self.notebook.forget(self.frame_id())
            if self in self.app.tabs: self.app.tabs.remove(self)
            else: print(f"Warning: EditorTab instance {self} was not found in self.app.tabs during close_tab.")
            if not self.app.tabs:
                if self.app.quitting_app: pass
                else: self.app.new_file_action()
            else:
                if not self.app.quitting_app and len(self.app.notebook.tabs()) > 0:
                    if selected_tab_before_close >= len(self.app.notebook.tabs()):
                        self.app.notebook.select(len(self.app.notebook.tabs()) - 1)
            if not self.app.quitting_app:
                try:
                    self.app.update_app_title()
                    self.app.update_status_bar()
                except tk.TclError: pass
            return True
        except tk.TclError as e:
            print(f"Error closing tab (TclError): {e}")
            return False
        except Exception as e:
            print(f"Unexpected error closing tab: {e}")
            return False

    def apply_notes_style_highlighting(self, event=None):
        if not self.tab_notes_style_active:
            self.clear_notes_style_highlighting()
            if self.current_language_name and hasattr(self, 'apply_syntax_highlighting'): self.apply_syntax_highlighting()
            if self.app.keyword_highlight_settings.get("active", False) and hasattr(self, 'apply_keyword_highlights'): self.apply_keyword_highlights(self.app.keyword_highlight_settings)
            return
        if hasattr(self, '_clear_syntax_highlight_tags'): self._clear_syntax_highlight_tags()
        if hasattr(self.app, 'pastel_colors'):
            for i in range(len(self.app.pastel_colors) + 5):
                try: self.text_area.tag_remove(f"user_keyword_{i}", "1.0", tk.END)
                except tk.TclError: pass
        self.clear_notes_style_highlighting()
        all_text = self.text_area.get("1.0", tk.END)
        if not all_text.strip(): return
        number_pattern = r'(?<![a-zA-Z_])(?<!\.)-?\b(?:\d+\.?\d*|\.\d+)\b(?!\.)(?![a-zA-Z_])'
        header_pattern = r'^([^:]+):'
        comment_pattern = r'#.*'
        separator_pattern = r'^(?:-{2,}|={2,})$'
        for match in re.finditer(separator_pattern, all_text, re.MULTILINE):
            start_idx = self.text_area.index(f"1.0 + {match.start()} chars")
            end_idx = self.text_area.index(f"1.0 + {match.end()} chars")
            self.text_area.tag_add("notes_separator", start_idx, end_idx)
        for match in re.finditer(header_pattern, all_text, re.MULTILINE):
            start_idx = self.text_area.index(f"1.0 + {match.start(0)} chars")
            end_colon_offset = match.group(0).find(':')
            if end_colon_offset != -1:
                actual_end_offset = match.start(0) + end_colon_offset + 1
                end_idx = self.text_area.index(f"1.0 + {actual_end_offset} chars")
            else: end_idx = self.text_area.index(f"1.0 + {match.end(0)} chars")
            line_text_for_header_check = all_text[match.start() : match.end()]
            if not (line_text_for_header_check.strip().startswith("---") or line_text_for_header_check.strip().startswith("===")):
                self.text_area.tag_add("notes_header", start_idx, end_idx)
        for match in re.finditer(comment_pattern, all_text):
            start_idx = self.text_area.index(f"1.0 + {match.start()} chars")
            end_idx = self.text_area.index(f"1.0 + {match.end()} chars")
            self.text_area.tag_add("notes_comment", start_idx, end_idx)
        for match in re.finditer(number_pattern, all_text):
            match_start_idx = self.text_area.index(f"1.0 + {match.start()} chars")
            match_end_idx = self.text_area.index(f"1.0 + {match.end()} chars")
            tags_at_start = self.text_area.tag_names(match_start_idx)
            is_already_styled_exclusively = False
            for tag_name in tags_at_start:
                if tag_name in ["notes_comment", "notes_separator", "notes_header"]:
                    is_already_styled_exclusively = True
                    break
            if not is_already_styled_exclusively: self.text_area.tag_add("notes_number", match_start_idx, match_end_idx)

    def clear_notes_style_highlighting(self):
        self.text_area.tag_remove("notes_number", "1.0", tk.END)
        self.text_area.tag_remove("notes_header", "1.0", tk.END)
        self.text_area.tag_remove("notes_comment", "1.0", tk.END)
        self.text_area.tag_remove("notes_separator", "1.0", tk.END)

    def check_unsaved_changes_tab(self):
        if self.text_changed:
            self.notebook.select(self.frame_id())
            file_display_name = os.path.basename(self.current_file) if self.current_file else "Untitled"
            response = messagebox.askyesnocancel("Unsaved Changes", f"Do you want to save the changes to {file_display_name}?")
            if response is True: return self.app.save_file_action(save_as_if_needed=False)
            elif response is False: return True
            else: return False
        return True

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        self.quitting_app = False
        self.tabs = []
        self.untitled_counter = 1
        self.show_line_numbers = True
        self.notes_style_active = False
        self._is_updating_filter_bar_from_tab = False
        self.known_fixed_fonts = sorted([
            "TkFixedFont", "Courier New", "Courier", "Consolas", "DejaVu Sans Mono",
            "Liberation Mono", "Menlo", "Monaco", "Source Code Pro", "Fira Code",
            "Inconsolata", "Fixedsys", "Terminal", "Monospace"
        ])
        system_fonts = set(tkfont.families())
        preferred_defaults = ["Courier New", "Consolas", "TkFixedFont"]
        default_family_to_set = None
        for preferred_font in preferred_defaults:
            if preferred_font in system_fonts:
                default_family_to_set = preferred_font
                break
        if not default_family_to_set:
            for ff in self.known_fixed_fonts:
                if ff in system_fonts:
                    default_family_to_set = ff
                    break
        if not default_family_to_set: default_family_to_set = "TkFixedFont"
        self.current_font_family = default_family_to_set
        self.current_font_size = 14
        self.current_font_weight = "normal"
        self.current_font_slant = "roman"
        self.editor_font = tkfont.Font(family=self.current_font_family, size=self.current_font_size, weight=self.current_font_weight, slant=self.current_font_slant)
        self.keyword_highlight_settings = {
            "keywords_input_string": "", "parsed_keywords": [],
            "keyword_to_color_map": {}, "keyword_to_tag_name_map": {},
            "case_sensitive": False, "whole_word": True, "active": False
        }
        self.pastel_colors = ["#FFDFD3", "#FFFACD", "#D7E9F7", "#E0FFFF", "#F0FFF0", "#FFE4E1", "#FAFAD2", "#ADD8E6", "#E6E6FA", "#FFF0F5"]
        self.language_definitions = {
            "python": {
                "extensions": [".py", ".pyw"],
                "rules": [
                    {"token_type": "hl_comment", "pattern": r"#.*"},
                    {"token_type": "hl_string", "pattern": r"(\"\"\"(?:[^\"]|\\\"|\n)*?\"\"\"|\'\'\'(?:[^\']|\\\'|\n)*?\'\'\'|\"[^\"\\\n]*(?:\\.[^\"\\\n]*)*\"|\'[^\'\\\n]*(?:\\.[^\'\\\n]*)*\')"},
                    {"token_type": "hl_keyword", "pattern": r'\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b'},
                    {"token_type": "hl_builtin", "pattern": r'\b(abs|all|any|ascii|bin|bool|bytearray|bytes|callable|chr|classmethod|compile|complex|delattr|dict|dir|divmod|enumerate|eval|exec|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|print|property|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|vars|zip|__import__)\b'},
                    {"token_type": "hl_number", "pattern": r'\b(?:0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+|[0-9]+\.?[0-9]*(?:[eE][+-]?[0-9]+)?|[0-9]+)\b'},
                    {"token_type": "hl_operator", "pattern": r"(\+|\-|\*|/|%|=|==|!=|>|<|>=|<=|&|\||\^|~|<<|>>|\*\*|//|@)"}
                ]
            }
        }
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.toolbar_frame = ttk.Frame(self.root, relief=tk.FLAT, padding=2)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        # World Clock Frame
        self.world_clock_frame = ttk.Frame(self.root, relief=tk.FLAT, padding=(5,2))
        self.world_clock_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,2))
        self.timezones_to_display = [
            {"label": "New York (ET):", "tz": "America/New_York"},
            {"label": "Chicago (CT):",  "tz": "America/Chicago"},
            {"label": "Los Angeles (PT):", "tz": "America/Los_Angeles"},
            {"label": "UK:",             "tz": "Europe/London"},
            {"label": "India (IST):",     "tz": "Asia/Kolkata"},
            {"label": "Japan (JST):",     "tz": "Asia/Tokyo"},
            {"label": "UTC:",            "tz": "Etc/UTC"},
        ]
        self.world_clock_labels = []
        self._initialize_world_clocks()

        self.filter_bar_frame = ttk.Frame(self.root, padding=(5,2))
        self.filter_text_var = tk.StringVar()
        ttk.Label(self.filter_bar_frame, text="Filter:").pack(side=tk.LEFT, padx=(0,5))
        self.filter_entry = ttk.Entry(self.filter_bar_frame, textvariable=self.filter_text_var, width=40)
        self.filter_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.filter_case_var = tk.BooleanVar(value=False)
        self.filter_case_checkbox = ttk.Checkbutton(self.filter_bar_frame, text="Case Sensitive", variable=self.filter_case_var)
        self.filter_case_checkbox.pack(side=tk.LEFT, padx=5)
        self.filter_invert_var = tk.BooleanVar(value=False)
        self.filter_invert_checkbox = ttk.Checkbutton(self.filter_bar_frame, text="Invert", variable=self.filter_invert_var)
        self.filter_invert_checkbox.pack(side=tk.LEFT, padx=5)
        self.filter_close_btn = ttk.Button(self.filter_bar_frame, text="✕", command=self.toggle_filter_bar, width=3)
        self.filter_close_btn.pack(side=tk.LEFT, padx=5)
        self.filter_text_var.trace_add("write", self.on_filter_settings_changed)
        self.filter_case_var.trace_add("write", self.on_filter_settings_changed)
        self.filter_invert_var.trace_add("write", self.on_filter_settings_changed)

        self.dialog_manager = DialogManager(self)

        btn_padx = 3
        btn_pady = 2
        self.new_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["new-file"]))
        self.open_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["open-file"]))
        self.save_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["save"]))
        self.cut_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["cut"]))
        self.copy_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["copy"]))
        self.paste_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["paste"]))
        self.undo_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["undo"]))
        self.redo_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["redo"]))
        self.format_code_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["format-code"]))
        self.calendar_icon = ImageTk.PhotoImage(data=base64.b64decode(ICON_DATA["calendar"]))

        self.new_btn = ttk.Button(self.toolbar_frame, image=self.new_icon, command=self.new_file_action_handler)
        self.new_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.new_btn, "New File")
        self.open_btn = ttk.Button(self.toolbar_frame, image=self.open_icon, command=self.open_file_action_handler)
        self.open_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.open_btn, "Open File")
        self.save_btn = ttk.Button(self.toolbar_frame, image=self.save_icon, command=lambda: self.save_action_handler(save_as_if_needed=False))
        self.save_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.save_btn, "Save File")
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=btn_pady)
        self.cut_btn = ttk.Button(self.toolbar_frame, image=self.cut_icon, command=self.cut_action)
        self.cut_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.cut_btn, "Cut")
        self.copy_btn = ttk.Button(self.toolbar_frame, image=self.copy_icon, command=self.copy_action)
        self.copy_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.copy_btn, "Copy")
        self.paste_btn = ttk.Button(self.toolbar_frame, image=self.paste_icon, command=self.paste_action)
        self.paste_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.paste_btn, "Paste")
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=btn_pady)
        self.undo_btn = ttk.Button(self.toolbar_frame, image=self.undo_icon, command=self.undo_action)
        self.undo_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.undo_btn, "Undo")
        self.redo_btn = ttk.Button(self.toolbar_frame, image=self.redo_icon, command=self.redo_action)
        self.redo_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.redo_btn, "Redo")
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=btn_pady)
        self.format_code_btn = ttk.Button(self.toolbar_frame, image=self.format_code_icon, command=self.format_code)
        self.format_code_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.format_code_btn, "Format Code")
        self.calendar_btn = ttk.Button(self.toolbar_frame, image=self.calendar_icon, command=self.dialog_manager.open_calendar_dialog)
        self.calendar_btn.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        ToolTip(self.calendar_btn, "Calendar")
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=btn_pady)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.new_file_action_handler, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open...", command=self.open_file_action_handler, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save", command=lambda: self.save_action_handler(save_as_if_needed=False), accelerator="Ctrl+S")
        self.file_menu.add_command(label="Save As...", command=self.save_as_action_handler, accelerator="Ctrl+Shift+S")
        self.file_menu.add_command(label="Close Tab", command=self.close_current_tab_action_handler, accelerator="Ctrl+W")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_editor_action)
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Undo", command=self.undo_action, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Redo", command=self.redo_action, accelerator="Ctrl+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut_action, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Copy", command=self.copy_action, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Paste", command=self.paste_action, accelerator="Ctrl+V")
        self.edit_menu.add_command(label="Strip Clipboard Formatting", command=self.strip_clipboard_formatting_action)
        self.edit_menu.add_command(label="Copy File Path", command=self.copy_file_path_action)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", command=self.select_all_action, accelerator="Ctrl+A")
        self.format_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Format", menu=self.format_menu)
        self.trim_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Trim", menu=self.trim_menu)
        self.trim_menu.add_command(label="Leading Whitespace", command=lambda: self.trim_whitespace("leading"))
        self.trim_menu.add_command(label="Trailing Whitespace", command=lambda: self.trim_whitespace("trailing"))
        self.trim_menu.add_command(label="Both Ends Whitespace", command=lambda: self.trim_whitespace("both"))
        self.case_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Change Case", menu=self.case_menu)
        self.case_menu.add_command(label="To UPPERCASE", command=lambda: self.change_case("upper"))
        self.case_menu.add_command(label="To lowercase", command=lambda: self.change_case("lower"))
        self.case_menu.add_command(label="To Title Case", command=lambda: self.change_case("title"))
        self.format_menu.add_command(label="Sort Lines...", command=self.sort_lines_dialog)
        self.format_menu.add_command(label="Pad Lines...", command=self.pad_lines_dialog)
        self.format_menu.add_command(label="Add Prefix/Suffix to Lines...", command=self.add_prefix_suffix_dialog)
        self.format_menu.add_separator()
        self.line_spacing_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Line Spacing", menu=self.line_spacing_menu)
        self.line_spacing_menu.add_command(label="Condense Internal Whitespace", command=self.condense_internal_whitespace)
        self.line_spacing_menu.add_command(label="Double Space Lines", command=self.double_space_lines)
        self.line_spacing_menu.add_command(label="Reduce Multiple Blank Lines to One", command=self.reduce_blank_lines)
        self.line_alteration_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Line Alteration", menu=self.line_alteration_menu)
        self.line_alteration_menu.add_command(label="Delete Duplicate Consecutive Lines", command=self.delete_duplicate_consecutive_lines)
        self.line_alteration_menu.add_command(label="Reverse Lines", command=self.reverse_lines_action)
        self.join_split_lines_menu = tk.Menu(self.format_menu, tearoff=0)
        self.format_menu.add_cascade(label="Join/Split Lines", menu=self.join_split_lines_menu)
        self.join_split_lines_menu.add_command(label="Join Lines (with space)", command=self.join_lines_with_space)
        self.join_split_lines_menu.add_command(label="Join Lines (with ', ')", command=self.join_lines_with_comma_space)
        self.format_menu.add_separator()
        self.format_menu.add_command(label="Remove Punctuation", command=self.remove_punctuation_action)
        self.format_menu.add_command(label="Shuffle Lines", command=self.shuffle_lines_action)
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)

        self.text_data_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Text & Data", menu=self.text_data_menu)

        self.analysis_menu = tk.Menu(self.text_data_menu, tearoff=0)
        self.text_data_menu.add_cascade(label="Analysis", menu=self.analysis_menu)
        self.analysis_menu.add_command(label="Text Statistics...", command=self.text_statistics_action)
        self.analysis_menu.add_command(label="Count Word Frequency...", command=self.count_word_frequency_action)
        self.analysis_menu.add_command(label="Extract Unique Words...", command=self.extract_unique_words_dialog)
        self.analysis_menu.add_command(label="Extract UPPERCASE Words...", command=self.extract_uppercase_words_action)

        self.transformation_menu = tk.Menu(self.text_data_menu, tearoff=0)
        self.text_data_menu.add_cascade(label="Transformation", menu=self.transformation_menu)
        self.transformation_menu.add_command(label="QuickText Transformer...", command=self.dialog_manager.open_quick_text_dialog)
        self.transformation_menu.add_command(label="Add Prefix/Suffix to Lines...", command=self.add_prefix_suffix_dialog)
        self.transformation_menu.add_command(label="Pad Lines...", command=self.pad_lines_dialog)
        self.transformation_menu.add_command(label="Sort Lines...", command=self.sort_lines_dialog)

        self.filtering_menu = tk.Menu(self.text_data_menu, tearoff=0)
        self.text_data_menu.add_cascade(label="Filtering", menu=self.filtering_menu)
        self.filtering_menu.add_command(label="Extract Lines by Length...", command=self.extract_lines_by_length_dialog)
        self.filtering_menu.add_command(label="Remove Blank Lines", command=self.remove_all_blank_lines)
        self.filtering_menu.add_command(label="Keep Lines Matching Regex...", command=lambda: self.filter_lines_by_regex_dialog(action_mode="keep"))
        self.filtering_menu.add_command(label="Remove Lines Matching Regex...", command=lambda: self.filter_lines_by_regex_dialog(action_mode="remove"))

        self.conversion_menu = tk.Menu(self.text_data_menu, tearoff=0)
        self.text_data_menu.add_cascade(label="Conversion", menu=self.conversion_menu)
        self.conversion_menu.add_command(label="View Data as Table (JSON/YAML)...", command=self.view_data_as_table_action)
        self.conversion_menu.add_command(label="Convert CSV to Text Table", command=self.csv_to_text_table_action)
        self.conversion_menu.add_command(label="Document to Text Converter...", command=self.dialog_manager.open_doc_converter_dialog)
        self.conversion_menu.add_command(label="Excel to HTML Site...", command=self.dialog_manager.open_excel_to_html_dialog)
        self.conversion_menu.add_command(label="Excel to CSVs & Stats...", command=self.dialog_manager.open_excel_to_csv_stats_dialog)
        self.conversion_menu.add_command(label="Excel to Multiple CSVs...", command=self.dialog_manager.open_excel_to_csv_dialog)

        self.dev_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Development", menu=self.dev_menu)
        self.dev_menu.add_command(label="REST API Client...", command=self.dialog_manager.open_rest_api_client_dialog)
        self.dev_menu.add_command(label="SQL Parser...", command=self.dialog_manager.open_sql_parser_dialog)
        self.dev_menu.add_command(label="Run Script...", command=self.dialog_manager.open_script_runner_dialog)
        self.dev_menu.add_command(label="Fake Data Generator...", command=self.dialog_manager.open_fake_data_generator_dialog)
        self.regex_utilities_menu = tk.Menu(self.dev_menu, tearoff=0)
        self.dev_menu.add_cascade(label="Regex Utilities", menu=self.regex_utilities_menu)
        self.regex_utilities_menu.add_command(label="Extract by Pattern (Regex)...", command=self.extract_pattern_dialog)

        self.utilities_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Utilities", menu=self.utilities_menu)
        self.utilities_menu.add_command(label="URL Manager...", command=self.dialog_manager.open_url_manager_dialog)
        self.utilities_menu.add_command(label="Compare Two Lists...", command=self.open_compare_lists_dialog)
        self.utilities_menu.add_command(label="Todo List / Kanban...", command=self.dialog_manager.open_todo_manager_dialog)
        self.utilities_menu.add_command(label="Clipboard Manager...", command=self.dialog_manager.open_clipboard_manager_dialog)
        self.utilities_menu.add_command(label="Flashcards...", command=self.dialog_manager.open_flashcard_dialog)
        self.utilities_menu.add_command(label="Security Tool...", command=self.dialog_manager.open_security_tool_dialog)

        self.media_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="Media", menu=self.media_menu)
        self.media_menu.add_command(label="Image Search by Name...", command=self.dialog_manager.open_image_search_dialog)
        self.media_menu.add_command(label="Drawing Tool...", command=self.dialog_manager.open_drawing_tool_action)
        self.media_menu.add_command(label="Create Flow Diagram...", command=self.dialog_manager.open_flow_diagram_dialog)
        self.media_menu.add_command(label="PowerPoint to Images...", command=self.dialog_manager.open_pptx_to_image_dialog)
        self.media_menu.add_command(label="PDF Tools...", command=self.dialog_manager.open_pdf_tool_dialog)
        self.screenshot_menu = tk.Menu(self.media_menu, tearoff=0)
        self.media_menu.add_cascade(label="Screenshot Tool", menu=self.screenshot_menu)
        self.screenshot_menu.add_command(label="Capture Region...", command=lambda: self.dialog_manager.open_screenshot_tool_action(mode="region"))
        self.screenshot_menu.add_command(label="Capture Full Screen...", command=lambda: self.dialog_manager.open_screenshot_tool_action(mode="fullscreen"))

        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Search", menu=self.search_menu)
        self.search_menu.add_command(label="Find/Replace in Current File...", command=self.dialog_manager.open_find_replace_dialog, accelerator="Ctrl+F")
        self.search_menu.add_command(label="Search in Files...", command=self.dialog_manager.open_file_search_dialog, accelerator="Ctrl+Shift+F")
        self.search_menu.add_separator()
        self.search_menu.add_command(label="Go to Line...", command=self.dialog_manager.prompt_go_to_line, accelerator="Ctrl+G")
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Change Font...", command=self.open_font_dialog)
        self.view_menu.add_command(label="Keyword Highlighting...", command=self.open_keyword_highlight_dialog)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Toggle Line Numbers", command=self.toggle_line_numbers_action)
        self.view_menu.add_command(label="Toggle Notes Style", command=self.toggle_notes_style_action)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Toggle Filter Bar", command=self.toggle_filter_bar, accelerator="Ctrl+Shift+F")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.status_bar_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=2)
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label_line_col = ttk.Label(self.status_bar_frame, text="Ln 1, Col 1", width=20)
        self.status_label_line_col.pack(side=tk.LEFT, padx=5)
        self.status_label_total_lines = ttk.Label(self.status_bar_frame, text="Lines: 1", width=15)
        self.status_label_total_lines.pack(side=tk.LEFT, padx=5)
        self.status_label_file_path = ttk.Label(self.status_bar_frame, text="File: Untitled", anchor=tk.W)
        self.status_label_file_path.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.dialog_manager = DialogManager(self)
        self.new_file_action()
        self.update_app_title()
        self.root.bind_all("<Control-n>", self.new_file_action_handler)
        self.root.bind_all("<Control-o>", self.open_file_action_handler)
        self.root.bind_all("<Control-s>", lambda event: self.save_action_handler(save_as_if_needed=False))
        self.root.bind_all("<Control-S>", self.save_as_action_handler)
        self.root.bind_all("<Control-w>", self.close_current_tab_action_handler)
        self.root.bind_all("<Control-f>", self.dialog_manager.open_find_replace_dialog)
        self.root.bind_all("<Control-g>", self.dialog_manager.prompt_go_to_line)
        self.root.bind_all("<Control-F>", lambda event: self.toggle_filter_bar())
        self.root.bind_all("<Control-z>", lambda event: self.undo_action())
        self.root.bind_all("<Control-y>", lambda event: self.redo_action())
        self.root.bind_all("<Control-x>", lambda event: self.cut_action())
        self.root.bind_all("<Control-c>", lambda event: self.copy_action())
        self.root.bind_all("<Control-v>", lambda event: self.paste_action())
        self.root.bind_all("<Control-a>", lambda event: self.select_all_action())
        self.root.protocol("WM_DELETE_WINDOW", self.exit_editor_action)

    def _initialize_world_clocks(self):
        self.world_clock_frames = {}
        for widget in self.world_clock_frame.winfo_children():
            widget.destroy()

        self._update_world_clocks()

    def _update_world_clocks(self):
        time_data = {}
        for tz_info in self.timezones_to_display:
            day_of_week, date_str, formatted_time = world_clock.get_formatted_datetime(tz_info["tz"])
            group_key = f"{day_of_week},{date_str}"
            if group_key not in time_data:
                time_data[group_key] = []
            time_data[group_key].append(f"{tz_info['label']} {formatted_time}")

        for day in list(self.world_clock_frames.keys()):
            if day not in time_data:
                self.world_clock_frames[day].destroy()
                del self.world_clock_frames[day]

        for day, times in time_data.items():
            if day not in self.world_clock_frames:
                day_frame = ttk.LabelFrame(self.world_clock_frame, text=day)
                day_frame.pack(side=tk.LEFT, padx=10, pady=2, fill=tk.Y)
                self.world_clock_frames[day] = day_frame

            day_frame = self.world_clock_frames[day]
            for widget in day_frame.winfo_children():
                widget.destroy()

            am_times = [t for t in times if "AM" in t]
            pm_times = [t for t in times if "PM" in t]

            if am_times:
                ttk.Label(day_frame, text="AM: " + " | ".join(am_times)).pack(anchor="w")

            if pm_times:
                ttk.Label(day_frame, text="PM: " + " | ".join(pm_times)).pack(anchor="w")

        self.root.after(5000, self._update_world_clocks)


    def get_current_tab(self):
        try:
            selected_tab_frame_id = self.notebook.select()
            if not selected_tab_frame_id:
                 if self.tabs: return self.tabs[0]
                 return None
            for tab_obj in self.tabs:
                if str(tab_obj.frame_id()) == str(selected_tab_frame_id): return tab_obj
            return None
        except tk.TclError: return None

    def on_tab_changed(self, event=None):
        self.update_app_title()
        self.update_status_bar()
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.tab_notes_style_active = self.notes_style_active
            if self.notes_style_active: current_tab.apply_notes_style_highlighting()
            else:
                current_tab.clear_notes_style_highlighting()
                if self.keyword_highlight_settings.get("active", False): current_tab.apply_keyword_highlights(self.keyword_highlight_settings)
                if current_tab.current_language_name: current_tab.apply_syntax_highlighting()
                else: current_tab._clear_syntax_highlight_tags()
            if self.filter_bar_frame.winfo_ismapped():
                self._is_updating_filter_bar_from_tab = True
                try:
                    self.filter_text_var.set(current_tab.tab_filter_str)
                    self.filter_case_var.set(current_tab.tab_filter_case_sensitive)
                    self.filter_invert_var.set(current_tab.tab_filter_invert)
                finally: self._is_updating_filter_bar_from_tab = False
                current_tab.apply_text_filter()
            else:
                if current_tab.is_tab_filtered_view or current_tab.tab_filter_str: current_tab.apply_text_filter()
            if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists(): self.update_find_replace_button_states()
            current_tab.update_current_line_highlight()

    def on_filter_settings_changed(self, *args):
        if self._is_updating_filter_bar_from_tab: return
        current_tab = self.get_current_tab()
        if not current_tab: return
        current_tab.tab_filter_str = self.filter_text_var.get()
        current_tab.tab_filter_case_sensitive = self.filter_case_var.get()
        current_tab.tab_filter_invert = self.filter_invert_var.get()
        current_tab.apply_text_filter()
        if hasattr(self, "find_replace_dialog") and self.find_replace_dialog.winfo_exists(): self.update_find_replace_button_states()

    def update_status_bar(self):
        current_tab = self.get_current_tab()
        if current_tab and current_tab.text_area:
            cursor_pos = current_tab.text_area.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            self.status_label_line_col.config(text=f"Ln {line}, Col {col + 1}")
            total_lines = int(current_tab.text_area.index(f"{tk.END}-1c").split('.')[0])
            self.status_label_total_lines.config(text=f"Lines: {total_lines}")
            file_path_display = "Untitled"
            if current_tab.current_file: file_path_display = os.path.basename(current_tab.current_file)
            self.status_label_file_path.config(text=f"File: {file_path_display}")
        else:
            self.status_label_line_col.config(text="Ln --, Col --")
            self.status_label_total_lines.config(text="Lines: --")
            self.status_label_file_path.config(text="File: --")

    def update_app_title(self):
        current_tab = self.get_current_tab()
        if current_tab:
            base_name = os.path.basename(current_tab.current_file) if current_tab.current_file else "Untitled"
            title = f"Jules Text Editor - {base_name}"
            if current_tab.text_changed: title = "*" + title
            self.root.title(title)
        else: self.root.title("Jules Text Editor")

    def new_file_action_handler(self, event=None): self.new_file_action(); return "break"
    def new_file_action(self):
        default_tab_name = f"Untitled {self.untitled_counter}"
        new_tab = EditorTab(self.notebook, self, default_title=default_tab_name)
        self.tabs.append(new_tab)
        self.notebook.add(new_tab.frame, text=default_tab_name)
        self.untitled_counter += 1
        self.notebook.select(new_tab.frame_id())
        new_tab.text_area.focus_set()
        self.update_app_title()
        self.update_status_bar()

    def open_file_action_handler(self, event=None): self.open_file_action(); return "break"
    def open_file_action(self):
        filepath = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")])
        if filepath:
            for tab in self.tabs:
                if tab.current_file == filepath:
                    self.notebook.select(tab.frame_id())
                    self.update_status_bar()
                    return
            new_tab = EditorTab(self.notebook, self, file_path=filepath)
            if new_tab.current_file:
                self.tabs.append(new_tab)
                self.notebook.add(new_tab.frame)
                new_tab.update_tab_title()
                self.notebook.select(new_tab.frame_id())
                new_tab.text_area.focus_set()
            else: new_tab.frame.destroy()
        self.update_app_title()
        self.update_status_bar()

    def save_action_handler(self, event=None, save_as_if_needed=True): self.save_file(save_as_if_needed=save_as_if_needed); return "break"
    def save_as_action_handler(self, event=None): self.save_as_file(); return "break"
    def save_file(self, save_as_if_needed=True):
        current_tab = self.get_current_tab()
        if not current_tab: return False
        if not current_tab.current_file or save_as_if_needed: return self.save_as_file()
        try:
            if current_tab.is_tab_filtered_view and current_tab.tab_original_text_for_filter is not None:
                content_to_save = current_tab.tab_original_text_for_filter
            else: content_to_save = current_tab.get_content()
            with open(current_tab.current_file, "w", encoding="utf-8") as f: f.write(content_to_save)
            current_tab.text_changed = False
            current_tab.text_area.edit_modified(False)
            current_tab.update_tab_title()
            self.update_app_title()
            self.update_status_bar()
            return True
        except Exception as e:
            messagebox.showerror("Error Saving File", str(e))
            return False

    def save_as_file(self):
        current_tab = self.get_current_tab()
        if not current_tab: return False

        if current_tab.current_file:
            initial_filename = os.path.basename(current_tab.current_file)
        else:
            initial_filename = f"{current_tab.default_title}.txt"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=initial_filename,
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if filepath:
            current_tab.current_file = filepath
            save_successful = self.save_file(save_as_if_needed=False)

            if save_successful:
                current_tab._detect_and_set_language(filepath)
                current_tab.update_tab_title()
                self.update_app_title()
                self.update_status_bar()
                return True
            else:
                current_tab.current_file = None
                current_tab.update_tab_title()
                self.update_app_title()
                self.update_status_bar()
                return False

        self.update_status_bar()
        return False

    def close_current_tab_action_handler(self, event=None): self.close_current_tab_action(); return "break"
    def close_current_tab_action(self):
        current_tab = self.get_current_tab()
        if current_tab: current_tab.close_tab()
        self.update_status_bar()

    def exit_editor_action(self):
        self.quitting_app = True
        for tab in list(self.tabs):
            if not tab.close_tab():
                self.quitting_app = False
                return
        if not self.tabs: self.root.destroy()

    def get_active_text_area(self):
        current_tab = self.get_current_tab()
        if current_tab: return current_tab.text_area
        return None

    def undo_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            try: text_area.edit_undo()
            except tk.TclError: pass
        return "break"

    def redo_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            try: text_area.edit_redo()
            except tk.TclError: pass
        return "break"

    def cut_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area and text_area.tag_ranges(tk.SEL): text_area.event_generate("<<Cut>>")
        return "break"

    def copy_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area and text_area.tag_ranges(tk.SEL): text_area.event_generate("<<Copy>>")
        return "break"

    def paste_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            try:
                plain_text = self.root.clipboard_get()
                if text_area.tag_ranges(tk.SEL):
                    sel_first = text_area.index(tk.SEL_FIRST)
                    sel_last = text_area.index(tk.SEL_LAST)
                    text_area.delete(sel_first, sel_last)
                text_area.insert(tk.INSERT, plain_text)
                text_area.see(tk.INSERT)
                text_area.event_generate("<<Modified>>")
            except tk.TclError:
                try: text_area.event_generate("<<Paste>>")
                except tk.TclError: pass
        return "break"

    def select_all_action(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            text_area.tag_add(tk.SEL, "1.0", tk.END)
            text_area.mark_set(tk.INSERT, "1.0")
            text_area.see(tk.INSERT)
        return "break"

    def copy_file_path_action(self, event=None):
        current_tab = self.get_current_tab()
        if current_tab and current_tab.current_file:
            try:
                filepath = os.path.abspath(current_tab.current_file)
                self.root.clipboard_clear()
                self.root.clipboard_append(filepath)
            except Exception as e: pass
        else: pass
        return "break"

    def strip_clipboard_formatting_action(self, event=None):
        try:
            plain_text = self.root.clipboard_get()
            if isinstance(plain_text, str):
                self.root.clipboard_clear()
                self.root.clipboard_append(plain_text)
        except tk.TclError: pass
        return "break"

    def _process_text(self, operation_func, *args, **kwargs):
        text_area = self.get_active_text_area()
        if not text_area: return
        try:
            sel_start = text_area.index(tk.SEL_FIRST)
            sel_end = text_area.index(tk.SEL_LAST)
            selected_text = text_area.get(sel_start, sel_end)
            processed_text = operation_func(selected_text, *args, **kwargs)
            if selected_text != processed_text:
                text_area.delete(sel_start, sel_end)
                text_area.insert(sel_start, processed_text)
                text_area.event_generate("<<Modified>>")
        except tk.TclError:
            full_text = text_area.get("1.0", tk.END + "-1c")
            processed_text = operation_func(full_text, *args, **kwargs)
            if full_text != processed_text:
                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", processed_text)
                text_area.event_generate("<<Modified>>")

    def trim_whitespace(self, mode="both"):
        self._process_text(text_processing.trim_whitespace, mode)

    def change_case(self, case_type):
        self._process_text(text_processing.change_case, case_type)

    def sort_lines_dialog(self):
        pass

    def filter_lines_by_regex_dialog(self, action_mode: str, event=None): pass
    def apply_filter_lines_by_regex(self, regex_str: str, case_insensitive: bool, action_mode: str): pass
    def update_sort_options_state(self): pass
    def apply_sort_lines(self, sort_type, case_sensitive, remove_duplicates):
        self._process_text(text_processing.sort_lines, sort_type, case_sensitive, remove_duplicates)

    def _search_in_text(self, text_widget, pattern, start_index, end_index, case_sensitive, whole_word, regex, backwards):
        if not pattern:
            return None, 0

        search_flags = tk.SEL_FIRST
        count_var = tk.IntVar()

        if backwards:
            pos = text_widget.search(pattern, start_index, stopindex=end_index,
                                     nocase=not case_sensitive, regexp=regex, backwards=True, count=count_var)
        else:
            pos = text_widget.search(pattern, start_index, stopindex=end_index,
                                     nocase=not case_sensitive, regexp=regex, count=count_var)

        if pos:
            match_len = count_var.get()
            if match_len == 0 and len(pattern) > 0 and not regex:
                match_len = len(pattern)
            return pos, match_len
        return None, 0

    def find_next_action_from_dialog(self, find_what, case_sensitive, whole_word, regex, search_backwards=False):
        current_tab = self.get_current_tab()
        if not current_tab or not find_what:
            if self.find_replace_dialog_instance:
                self.find_replace_dialog_instance.update_search_results([], -1, "Not found")
            return

        text_area = current_tab.text_area

        dialog = self.find_replace_dialog_instance
        is_new_search = not dialog.current_matches or \
                        dialog.last_find_what != find_what or \
                        dialog.last_case_sensitive != case_sensitive or \
                        dialog.last_whole_word != whole_word or \
                        dialog.last_regex != regex

        if is_new_search:
            dialog.current_matches = []
            dialog.current_match_index = -1
            self.clear_all_search_highlights_active_tab()

            dialog.last_find_what = find_what
            dialog.last_case_sensitive = case_sensitive
            dialog.last_whole_word = whole_word
            dialog.last_regex = regex

            current_pos = "1.0"
            while True:
                match_pos, match_len = self._search_in_text(text_area, find_what, current_pos, tk.END,
                                                            case_sensitive, whole_word, regex, False)
                if match_pos and match_len > 0:
                    end_pos = text_area.index(f"{match_pos}+{match_len}c")
                    dialog.current_matches.append((match_pos, end_pos))
                    current_pos = end_pos
                else:
                    break

            if dialog.current_matches:
                dialog.current_match_index = 0
            else:
                dialog.update_search_results([], -1, "Not found")
                return
        else:
            if not dialog.current_matches:
                dialog.update_search_results([], -1, "Not found")
                return

            if search_backwards:
                dialog.current_match_index -= 1
                if dialog.current_match_index < 0:
                    dialog.current_match_index = len(dialog.current_matches) - 1
            else:
                dialog.current_match_index += 1
                if dialog.current_match_index >= len(dialog.current_matches):
                    dialog.current_match_index = 0

        if 0 <= dialog.current_match_index < len(dialog.current_matches):
            self.navigate_to_match_from_dialog(dialog.current_match_index)
        else:
             dialog.update_search_results(dialog.current_matches, -1, "Not found")


    def replace_action_from_dialog(self, find_what, replace_with, case_sensitive, whole_word, regex):
        current_tab = self.get_current_tab()
        dialog = self.find_replace_dialog_instance
        if not current_tab or not dialog or dialog.current_match_index == -1:
            if dialog: dialog.update_search_results(dialog.current_matches, dialog.current_match_index, "No match selected")
            return

        text_area = current_tab.text_area
        try:
            start_index, end_index = dialog.current_matches[dialog.current_match_index]
            selected_text = text_area.get(start_index, end_index)
            text_area.delete(start_index, end_index)
            text_area.insert(start_index, replace_with)
            text_area.event_generate("<<Modified>>")
            dialog.current_matches.pop(dialog.current_match_index)
            self.clear_all_search_highlights_active_tab()

            if not dialog.current_matches:
                dialog.current_match_index = -1
                dialog.update_search_results([], -1, "Replaced. No more matches.")
            elif dialog.current_match_index >= len(dialog.current_matches):
                dialog.current_match_index = 0
                self.navigate_to_match_from_dialog(dialog.current_match_index)
            else:
                 self.navigate_to_match_from_dialog(dialog.current_match_index)

        except tk.TclError as e:
            if dialog: dialog.update_search_results(dialog.current_matches, dialog.current_match_index, f"Error: {e}")
        except IndexError:
            if dialog: dialog.update_search_results([], -1, "Error: Match list desynchronized.")

    def replace_all_action_from_dialog(self, find_what, replace_with, case_sensitive, whole_word, regex):
        current_tab = self.get_current_tab()
        if not current_tab or not find_what:
            if self.find_replace_dialog_instance:
                self.find_replace_dialog_instance.update_search_results([], -1, "Not found")
            return 0

        text_area = current_tab.text_area
        self.clear_all_search_highlights_active_tab()

        count = 0
        current_pos = "1.0"
        original_text_changed_flag = current_tab.text_changed

        text_area.config(undo=False)
        try:
            while True:
                match_pos, match_len = self._search_in_text(text_area, find_what, current_pos, tk.END,
                                                            case_sensitive, whole_word, regex, False)
                if match_pos and match_len > 0:
                    end_pos = text_area.index(f"{match_pos}+{match_len}c")
                    text_area.delete(match_pos, end_pos)
                    text_area.insert(match_pos, replace_with)
                    count += 1
                    current_pos = text_area.index(f"{match_pos}+{len(replace_with)}c")
                    if not current_pos: break
                else:
                    break
        finally:
            text_area.config(undo=True)

        if count > 0:
            text_area.event_generate("<<Modified>>")
            current_tab.text_changed = True
            current_tab.update_tab_title()

        if self.find_replace_dialog_instance:
            self.find_replace_dialog_instance.update_search_results([], -1, f"Replaced {count} occurrence(s).")
            self.find_replace_dialog_instance.current_matches = []
            self.find_replace_dialog_instance.current_match_index = -1

        self.update_status_bar()
        return count

    def clear_all_search_highlights_active_tab(self):
        current_tab = self.get_current_tab()
        if current_tab:
            try:
                current_tab.text_area.tag_remove("search_highlight", "1.0", tk.END)
            except tk.TclError: pass

    def clear_current_search_highlight_active_tab(self):
        current_tab = self.get_current_tab()
        if current_tab:
            try:
                current_tab.text_area.tag_remove("current_search_highlight", "1.0", tk.END)
            except tk.TclError: pass

    def navigate_to_match_from_dialog(self, match_idx_in_dialog_list):
        current_tab = self.get_current_tab()
        dialog = self.find_replace_dialog_instance
        if not current_tab or not dialog or not dialog.current_matches or \
           not (0 <= match_idx_in_dialog_list < len(dialog.current_matches)):
            if dialog: dialog.update_search_results(dialog.current_matches, dialog.current_match_index, "Invalid match index")
            return

        text_area = current_tab.text_area
        self.clear_current_search_highlight_active_tab()

        for start_idx, end_idx in dialog.current_matches:
            try: text_area.tag_add("search_highlight", start_idx, end_idx)
            except tk.TclError: pass

        current_start_idx, current_end_idx = dialog.current_matches[match_idx_in_dialog_list]
        try:
            text_area.tag_add("current_search_highlight", current_start_idx, current_end_idx)
            text_area.see(current_start_idx)
            text_area.mark_set(tk.INSERT, current_start_idx)
            dialog.current_match_index = match_idx_in_dialog_list
            dialog.update_search_results(dialog.current_matches, match_idx_in_dialog_list)
        except tk.TclError:
            if dialog:
                dialog.update_search_results(dialog.current_matches, dialog.current_match_index, "Error: Match location invalid")
            return

        self.update_status_bar()

    def open_font_dialog(self): pass
    def update_font_preview(self, preview_label, family_var, size_var, bold_var, italic_var): pass
    def apply_new_font(self, family, size, weight, slant): pass
    def open_keyword_highlight_dialog(self): pass
    def update_keyword_highlight_settings(self, input_str, case_sens, whole_word): pass
    def clear_keyword_highlight_settings(self): pass
    def apply_all_tabs_keyword_highlights(self): pass
    def double_space_lines(self): self._process_text(text_processing.double_space_lines)
    def reduce_blank_lines(self): self._process_text(text_processing.reduce_blank_lines)
    def remove_all_blank_lines(self): self._process_text(text_processing.remove_all_blank_lines)
    def delete_duplicate_consecutive_lines(self): self._process_text(text_processing.delete_duplicate_consecutive_lines)
    def reverse_lines_action(self): self._process_text(text_processing.reverse_lines)
    def extract_lines_by_length_dialog(self, event=None): pass
    def apply_extract_lines_by_length(self, length_val: int, mode: str, keep_empty: bool): pass
    def pad_lines_dialog(self, event=None): pass
    def apply_pad_lines(self, target_length: int, pad_char: str, alignment: str): self._process_text(text_processing.pad_lines, target_length, pad_char, alignment)
    def remove_punctuation_action(self, event=None): self._process_text(text_processing.remove_punctuation)
    def extract_uppercase_words_action(self, event=None): pass
    def count_word_frequency_action(self, event=None): pass
    def shuffle_lines_action(self, event=None): self._process_text(text_processing.shuffle_lines)
    def text_statistics_action(self, event=None): pass
    def extract_unique_words_dialog(self, event=None): pass
    def apply_extract_unique_words(self, case_sensitive: bool, sort_alpha: bool): pass
    def add_prefix_suffix_dialog(self, event=None): pass
    def apply_add_prefix_suffix(self, prefix_str: str, suffix_str: str, skip_empty: bool): self._process_text(text_processing.add_prefix_suffix, prefix_str, suffix_str, skip_empty)
    def extract_pattern_dialog(self, event=None): pass
    def csv_to_text_table_action(self, event=None): pass
    def apply_extract_pattern(self, regex_pattern_str: str, case_insensitive: bool, unique_only: bool): pass
    def open_compare_lists_dialog(self, event=None): pass

    def _perform_and_show_list_comparison(self, list1_str: str, list2_str: str, case_sensitive: bool):
        list1_lines = [line for line in list1_str.splitlines() if line.strip()]
        list2_lines = [line for line in list2_str.splitlines() if line.strip()]

        if not case_sensitive:
            list1_map = {line.lower(): line for line in list1_lines}
            list2_map = {line.lower(): line for line in list2_lines}
        else:
            list1_map = {line: line for line in list1_lines}
            list2_map = {line: line for line in list2_lines}

        set1_keys = set(list1_map.keys())
        set2_keys = set(list2_map.keys())

        common_keys = set1_keys.intersection(set2_keys)
        list1_unique_keys = set1_keys.difference(set2_keys)
        list2_unique_keys = set2_keys.difference(set1_keys)

        common_lines_orig_case = sorted([list1_map[k] for k in common_keys])
        list1_unique_orig_case = sorted([list1_map[k] for k in list1_unique_keys])
        list2_unique_orig_case = sorted([list2_map[k] for k in list2_unique_keys])

        ListComparisonResultsDialog(self.root, common_lines_orig_case, list1_unique_orig_case, list2_unique_orig_case, case_sensitive)

    def _process_selected_lines(self, line_operation_func, preserves_original_endings=True): pass
    def condense_internal_whitespace(self): self._process_text(text_processing.condense_internal_whitespace)
    def join_lines_with_space(self): self._process_text(text_processing.join_lines, " ")
    def join_lines_with_comma_space(self): self._process_text(text_processing.join_lines, ", ")

    def toggle_filter_bar(self, event=None):
        current_tab = self.get_current_tab()
        if self.filter_bar_frame.winfo_ismapped():
            self.filter_bar_frame.pack_forget()
            if current_tab and (current_tab.is_tab_filtered_view or current_tab.tab_filter_str):
                self._is_updating_filter_bar_from_tab = True
                try:
                    current_tab.tab_filter_str = ""
                    current_tab.tab_filter_case_sensitive = False
                    current_tab.tab_filter_invert = False
                    self.filter_text_var.set("")
                    self.filter_case_var.set(False)
                    self.filter_invert_var.set(False)
                finally:
                    self._is_updating_filter_bar_from_tab = False
                current_tab.apply_text_filter()
        else:
            self.filter_bar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,2), before=self.notebook)
            if current_tab:
                self._is_updating_filter_bar_from_tab = True
                try:
                    self.filter_text_var.set(current_tab.tab_filter_str)
                    self.filter_case_var.set(current_tab.tab_filter_case_sensitive)
                    self.filter_invert_var.set(current_tab.tab_filter_invert)
                finally:
                    self._is_updating_filter_bar_from_tab = False
                current_tab.apply_text_filter()
            self.filter_entry.focus_set()
        return "break"

    def toggle_line_numbers_action(self, event=None):
        self.show_line_numbers = not self.show_line_numbers
        for tab in self.tabs:
            tab.line_numbers_visible = self.show_line_numbers
            if tab.line_numbers_visible:
                if not tab.line_numbers_canvas.winfo_ismapped():
                    tab.line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y, before=tab.text_area)
                tab.redraw_line_numbers()
            else:
                if tab.line_numbers_canvas.winfo_ismapped():
                    tab.line_numbers_canvas.pack_forget()
        current_tab = self.get_current_tab()
        if current_tab and current_tab.line_numbers_visible:
            current_tab.redraw_line_numbers()

    def toggle_notes_style_action(self, event=None):
        self.notes_style_active = not self.notes_style_active
        for tab in self.tabs:
            tab.tab_notes_style_active = self.notes_style_active
            if tab.tab_notes_style_active:
                if hasattr(tab, '_clear_syntax_highlight_tags'): tab._clear_syntax_highlight_tags()
                if hasattr(tab, 'apply_notes_style_highlighting'): tab.apply_notes_style_highlighting()
                else: print(f"DEBUG: Tab {tab.current_file or 'Untitled'} missing apply_notes_style_highlighting")
            else:
                if hasattr(tab, 'clear_notes_style_highlighting'): tab.clear_notes_style_highlighting()
                else: print(f"DEBUG: Tab {tab.current_file or 'Untitled'} missing clear_notes_style_highlighting")
                if tab.current_language_name and hasattr(tab, 'apply_syntax_highlighting'): tab.apply_syntax_highlighting()
                if self.keyword_highlight_settings.get("active", False) and hasattr(tab, 'apply_keyword_highlights'): tab.apply_keyword_highlights(self.keyword_highlight_settings)
        current_tab = self.get_current_tab()
        if current_tab:
            if hasattr(current_tab, 'text_area') and current_tab.text_area.winfo_exists():
                current_tab.text_area.update_idletasks()

    def _proceed_with_capture(self, bbox, mode, was_visible_for_fullscreen=None):
        try:
            from dialogs.screenshot_utils import capture_full_screen, capture_screen_region
            from dialogs.screenshot_tool_dialog import ScreenshotToolDialog
            from PIL import Image
        except ImportError:
             if was_visible_for_fullscreen is not None and was_visible_for_fullscreen: self.root.deiconify()
             messagebox.showerror("Screenshot Tool Error", "Component loading failed during capture.", parent=self.root)
             return

        captured_image = None
        if mode == "region" and bbox:
            captured_image = capture_screen_region(bbox)
        elif mode == "fullscreen":
            captured_image = capture_full_screen()

        if was_visible_for_fullscreen is not None and was_visible_for_fullscreen:
            self.root.deiconify()

        if mode == "region" and not self.root.winfo_viewable():
            self.root.deiconify()

        if captured_image and isinstance(captured_image, Image.Image):
            try:
                dialog = ScreenshotToolDialog(self, captured_image)
            except Exception as e:
                 messagebox.showerror("Screenshot Tool Error", f"Could not open screenshot editor: {e}", parent=self.root)
        elif mode:
            messagebox.showerror("Capture Failed", "Could not capture screenshot. Ensure no other overlay is active or try a different capture mode.", parent=self.root)

    def _display_search_results(self, results, search_phrase, is_regex, is_case_sensitive):
        if not results: messagebox.showinfo("Search Results", "No matches found.", parent=self.root); return
        results_tab = EditorTab(self.notebook, self)
        self.tabs.append(results_tab)
        display_phrase = search_phrase[:30] + '...' if len(search_phrase) > 30 else search_phrase
        results_tab_title = f"[Search Results: \"{display_phrase}\"]"
        self.notebook.add(results_tab.frame, text=results_tab_title)
        self.notebook.select(results_tab.frame_id())
        results_text_widget = results_tab.text_area
        results_text_widget.config(state=tk.NORMAL)
        results_text_widget.delete("1.0", tk.END)
        highlight_tag_name = "search_result_highlight"
        results_text_widget.tag_configure(highlight_tag_name, background="yellow", foreground="black")
        grouped_results = collections.defaultdict(list)
        for result in results: grouped_results[result['filepath']].append(result)
        for filepath, file_matches in grouped_results.items():
            results_text_widget.insert(tk.END, f"File: {filepath}\n================================\n")
            for i, result in enumerate(file_matches):
                results_text_widget.insert(tk.END, f"  Line: {result['line_number']}\n")
                for before_line in result['context_before']: results_text_widget.insert(tk.END, f"    {before_line}\n")
                prefix_for_matched_line = "  > "
                matched_line_display_start_index = results_text_widget.index(tk.END + "-1c")
                results_text_widget.insert(tk.END, f"{prefix_for_matched_line}{result['matched_line']}\n")
                highlight_start_tk = f"{matched_line_display_start_index} + {len(prefix_for_matched_line) + result['match_start']} chars"
                highlight_end_tk = f"{matched_line_display_start_index} + {len(prefix_for_matched_line) + result['match_end']} chars"
                results_text_widget.tag_add(highlight_tag_name, highlight_start_tk, highlight_end_tk)
                for after_line in result['context_after']: results_text_widget.insert(tk.END, f"    {after_line}\n")
                if i < len(file_matches) - 1: results_text_widget.insert(tk.END, "  --------------------------------\n")
                else: results_text_widget.insert(tk.END, "\n")
        results_text_widget.config(state=tk.DISABLED)
        results_tab.text_changed = False
        results_tab.current_file = None
        results_tab.update_tab_title()
        self.update_app_title()
        self.update_status_bar()
        results_tab.text_area.focus_set()

    def view_data_as_table_action(self, event=None):
        current_tab = self.get_current_tab()
        if not current_tab: messagebox.showerror("Error", "No active tab to process."); return "break"
        if data_to_table_converter is None:
            messagebox.showerror("Dependency Missing", "The 'data_to_table_converter' module or 'PyYAML' library is missing. Please ensure PyYAML is installed.", parent=self.root)
            return "break"
        content = current_tab.get_content()
        if not content.strip(): messagebox.showinfo("No Content", "Current tab is empty.", parent=self.root); return "break"
        try:
            parsed_data, data_type = data_to_table_converter.parse_data(content)
            table_string = data_to_table_converter.format_to_text_table(parsed_data)
            table_view_tab = EditorTab(self.notebook, self)
            self.tabs.append(table_view_tab)
            original_filename = os.path.basename(current_tab.current_file) if current_tab.current_file else "Untitled"
            table_tab_title = f"[Table View] {original_filename} ({data_type})"
            self.notebook.add(table_view_tab.frame, text=table_tab_title)
            self.notebook.select(table_view_tab.frame_id())
            table_view_tab.text_area.insert(tk.END, table_string)
            table_view_tab.text_area.config(state=tk.DISABLED)
            table_view_tab.text_changed = False
            table_view_tab.current_file = None
            table_view_tab.update_tab_title()
            self.update_app_title()
            self.update_status_bar()
            table_view_tab.text_area.focus_set()
        except DataParsingError as e: messagebox.showerror("Data Parsing Error", str(e), parent=self.root)
        except Exception as e: messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.root)
        return "break"

    def format_code(self):
        current_tab = self.get_current_tab()
        if not current_tab or not current_tab.current_file:
            messagebox.showerror("Error", "Please save the file first.", parent=self.root)
            return

        file_path = current_tab.current_file
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        content = current_tab.get_content()
        formatter = None
        if extension == ".py":
            formatter = ["black", "-"]
        elif extension in [".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".scss", ".html", ".md"]:
            formatter = ["prettier", "--stdin-filepath", file_path]

        if formatter:
            try:
                process = subprocess.run(formatter, input=content, capture_output=True, text=True, check=True)
                formatted_content = process.stdout
                if content != formatted_content:
                    current_tab.text_area.delete("1.0", tk.END)
                    current_tab.text_area.insert("1.0", formatted_content)
            except FileNotFoundError:
                messagebox.showerror("Formatting Error", f"Could not find formatter. Please ensure that '{formatter[0]}' is installed and in your system's PATH.", parent=self.root)
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Formatting Error", f"Error formatting code: {e.stderr}", parent=self.root)
        else:
            messagebox.showinfo("Info", "No formatter available for this file type.", parent=self.root)

from dialogs.excel_to_csv_stats_dialog import ExcelToCsvStatsDialog
from dialogs.excel_to_csv_dialog import ExcelToCsvDialog
from dialogs.fake_data_generator_dialog import FakeDataGeneratorDialog
from dialogs.url_manager_dialog import UrlManagerDialog
from dialogs.excel_to_html_dialog import ExcelToHtmlDialog
from dialogs.sql_parser_dialog import SqlParserDialog
from dialogs.rest_api_client_dialog import RestApiClientDialog
from dialogs.security_tool_dialog import SecurityToolDialog
from dialogs.script_runner_dialog import ScriptRunnerDialog
from dialogs.document_converter_dialog import DocumentConverterDialog
from dialogs.todo_manager_dialog import TodoManagerDialog
from dialogs.calendar_dialog import CalendarDialog
from dialogs.clipboard_manager_dialog import ClipboardManagerDialog
from dialogs.pptx_to_image_dialog import PptxToImageDialog
from dialogs.flashcard_dialog import FlashcardDialog

from tkinterdnd2 import TkinterDnD
from ttkthemes import ThemedTk
from tkinterdnd2 import TkinterDnD

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = TextEditor(root)
    root.mainloop()
