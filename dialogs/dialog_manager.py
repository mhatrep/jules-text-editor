import tkinter as tk
from tkinter import simpledialog, messagebox
from dialogs.file_search_dialog import FileSearchDialog
from dialogs.image_search_dialog import ImageSearchDialog
from dialogs.flow_diagram_dialog import FlowDiagramDialog
from dialogs.quick_text_dialog import QuickTextDialog
from dialogs.list_comparison_results_dialog import ListComparisonResultsDialog
from dialogs.find_replace_dialog import FindReplaceDialog
from dialogs.pdf_tool_dialog import PdfToolDialog
from dialogs.screenshot_tool_dialog import ScreenshotToolDialog
from dialogs.screenshot_utils import RegionSelector, capture_full_screen, capture_screen_region
from data_to_table_converter import DataParsingError
from dialogs.rest_api_client_dialog import RestApiClientDialog
from dialogs.sql_parser_dialog import SqlParserDialog
from dialogs.excel_to_html_dialog import ExcelToHtmlDialog
from dialogs.excel_to_csv_stats_dialog import ExcelToCsvStatsDialog
from dialogs.excel_to_csv_dialog import ExcelToCsvDialog
from dialogs.fake_data_generator_dialog import FakeDataGeneratorDialog
from dialogs.url_manager_dialog import UrlManagerDialog
from dialogs.drawing_dialog import DrawingDialog
from dialogs.security_tool_dialog import SecurityToolDialog
from dialogs.script_runner_dialog import ScriptRunnerDialog
from dialogs.document_converter_dialog import DocumentConverterDialog
from dialogs.todo_manager_dialog import TodoManagerDialog
from dialogs.calendar_dialog import CalendarDialog
from dialogs.clipboard_manager_dialog import ClipboardManagerDialog
from dialogs.pptx_to_image_dialog import PptxToImageDialog
from dialogs.flashcard_dialog import FlashcardDialog

class DialogManager:
    def __init__(self, editor):
        self.editor = editor

    def open_find_replace_dialog(self, event=None):
        if not hasattr(self.editor, 'find_replace_dialog_instance') or \
           not self.editor.find_replace_dialog_instance or \
           not self.editor.find_replace_dialog_instance.winfo_exists():
            self.editor.find_replace_dialog_instance = FindReplaceDialog(self.editor)
        self.editor.find_replace_dialog_instance.show()
        return "break"

    def open_quick_text_dialog(self, event=None):
        dialog = QuickTextDialog(self.editor)
        return "break"

    def open_flow_diagram_dialog(self, event=None):
        dialog = FlowDiagramDialog(self.editor)
        return "break"

    def open_file_search_dialog(self, event=None):
        dialog = FileSearchDialog(self.editor)
        return "break"

    def open_image_search_dialog(self, event=None):
        dialog = ImageSearchDialog(self.editor)
        return "break"

    def open_pdf_tool_dialog(self, event=None):
        dialog = PdfToolDialog(self.editor)
        return "break"

    def open_screenshot_tool_action(self, mode):
        captured_image = None
        if mode == "region":
            try:
                selector = RegionSelector(self.editor.root)
                bbox = selector.select_region()
                if bbox:
                    self.editor.root.after(300, lambda: self.editor._proceed_with_capture(bbox, mode))
                else:
                    if not self.editor.root.winfo_viewable():
                        self.editor.root.deiconify()
            except Exception as e:
                messagebox.showerror("Region Selection Error", f"Could not select region: {e}", parent=self.editor.root)
                if not self.editor.root.winfo_viewable(): self.editor.root.deiconify()
            return "break"
        elif mode == "fullscreen":
            was_visible = self.editor.root.winfo_viewable()
            if was_visible:
                self.editor.root.withdraw()
                self.editor.root.after(500, lambda: self.editor._proceed_with_capture(None, mode, was_visible))
            else:
                self.editor.root.after(50, lambda: self.editor._proceed_with_capture(None, mode, was_visible))
            return "break"
        return "break"

    def open_rest_api_client_dialog(self, event=None):
        dialog = RestApiClientDialog(self.editor)
        return "break"

    def open_sql_parser_dialog(self, event=None):
        dialog = SqlParserDialog(self.editor)
        return "break"

    def open_excel_to_html_dialog(self, event=None):
        dialog = ExcelToHtmlDialog(self.editor)
        return "break"

    def open_excel_to_csv_stats_dialog(self, event=None):
        dialog = ExcelToCsvStatsDialog(self.editor)
        return "break"

    def open_excel_to_csv_dialog(self, event=None):
        dialog = ExcelToCsvDialog(self.editor)
        return "break"

    def open_fake_data_generator_dialog(self, event=None):
        dialog = FakeDataGeneratorDialog(self.editor)
        return "break"

    def open_url_manager_dialog(self, event=None):
        dialog = UrlManagerDialog(self.editor)
        return "break"

    def open_drawing_tool_action(self, event=None):
        dialog = DrawingDialog(self.editor)
        return "break"

    def open_security_tool_dialog(self, event=None):
        dialog = SecurityToolDialog(self.editor.root)
        return "break"

    def open_script_runner_dialog(self, event=None):
        dialog = ScriptRunnerDialog(self.editor)
        return "break"

    def open_doc_converter_dialog(self, event=None):
        dialog = DocumentConverterDialog(self.editor)
        return "break"

    def open_calendar_dialog(self, event=None):
        dialog = CalendarDialog(self.editor)
        return "break"

    def open_clipboard_manager_dialog(self, event=None):
        dialog = ClipboardManagerDialog(self.editor)
        return "break"

    def open_flashcard_dialog(self, event=None):
        dialog = FlashcardDialog(self.editor)
        return "break"

    def open_pptx_to_image_dialog(self, event=None):
        dialog = PptxToImageDialog(self.editor)
        return "break"

    def open_todo_manager_dialog(self, event=None):
        dialog = TodoManagerDialog(self.editor)
        return "break"

    def prompt_go_to_line(self, event=None):
        current_tab = self.editor.get_current_tab()
        if not current_tab: return "break"
        text_area = current_tab.text_area
        try:
            total_lines = int(text_area.index(f"{tk.END}-1c").split('.')[0])
        except (ValueError, tk.TclError):
            total_lines = 1
        line_num = simpledialog.askinteger("Go to Line", f"Enter line number (1-{total_lines}):", parent=self.editor.root, minvalue=1, maxvalue=total_lines)
        if line_num is not None:
            if 1 <= line_num <= total_lines:
                text_area.mark_set(tk.INSERT, f"{line_num}.0")
                text_area.see(f"{line_num}.0")
                text_area.focus_set()
            else:
                messagebox.showwarning("Go to Line", f"Line number {line_num} is out of range (1-{total_lines}).", parent=self.editor.root)
        return "break"
