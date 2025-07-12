import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import uuid
from datetime import datetime, timezone
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

class TodoManagerDialog(tk.Toplevel):
    """
    A dialog that provides a Kanban-style board to manage tasks.
    Tasks are organized into columns and their state is persisted in a JSON file.
    """
    TODO_DIR = "todo"
    BOARD_FILE = os.path.join(TODO_DIR, "kanban_board.json")
    DEFAULT_COLUMNS = ["Todo", "In Progress", "Done"]

    def __init__(self, master):
        """
        Initializes the TodoManagerDialog.
        """
        super().__init__(master.root)
        self.title("Todo List / Kanban Board")
        self.geometry("900x600")
        self.master_app = master

        self.priority_colors = {
            "High": "#FF9999",
            "Medium": "#FFE4B5",
            "Low": "#ADD8E6",
            "None": "#F0F0F0"
        }
        self.board_data = None
        self._ensure_data_file_exists()
        self._load_board_data()

        self._setup_ui()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_ui(self):
        """Sets up the main UI components of the dialog."""
        toolbar_frame = ttk.Frame(self, padding=(5, 5, 5, 0))
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        self.add_task_button = ttk.Button(toolbar_frame, text="Add Task", command=self._add_task_ui)
        self.add_task_button.pack(side=tk.LEFT, padx=(0,5))

        self.board_frame = ttk.Frame(self, padding=(5,0,5,5))
        self.board_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.column_frames = {}
        self._draw_board()

    def _draw_board(self):
        """
        Clears and redraws the entire Kanban board UI from self.board_data.
        This method builds the columns and populates them with scrollable task lists.
        """
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        self.column_frames.clear()

        if not self.board_data or not self.board_data.get("columns"):
            ttk.Label(self.board_frame, text="No columns defined.").pack(padx=20, pady=20)
            return

        columns_by_id = {col['id']: col for col in self.board_data['columns']}

        for col_id in self.board_data.get("column_order", []):
            column_data = columns_by_id.get(col_id)
            if not column_data: continue

            column_frame = ttk.LabelFrame(self.board_frame, text=column_data.get("name", "Unnamed"), padding=5)
            column_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            canvas = tk.Canvas(column_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(column_frame, orient="vertical", command=canvas.yview)
            task_list_frame = tk.Frame(canvas)
            canvas.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            canvas_window = canvas.create_window((0, 0), window=task_list_frame, anchor="nw")

            def on_frame_configure(event, canvas=canvas):
                canvas.configure(scrollregion=canvas.bbox("all"))

            def on_canvas_configure(event, canvas=canvas, canvas_window=canvas_window):
                canvas.itemconfig(canvas_window, width=event.width)

            task_list_frame.bind("<Configure>", on_frame_configure)
            canvas.bind('<Configure>', on_canvas_configure)

            self.column_frames[col_id] = {
                "frame": column_frame,
                "canvas": canvas,
                "task_list_frame": task_list_frame,
                "tasks": []
            }

            self._populate_tasks_for_column(col_id, task_list_frame, column_data.get("tasks", []))

    def _populate_tasks_for_column(self, column_id, parent_frame, tasks_data):
        """
        Creates and displays task 'cards' for a given column.
        The tasks are first grouped by due date and sorted by priority, then
        rendered with group headers, separators, and priority-based background colors.
        """
        if not tasks_data:
            ttk.Label(parent_frame, text="(empty)").pack(pady=5)
            return

        grouped_tasks = self._group_and_sort_tasks(tasks_data)

        first_group = True
        for group_name, tasks_in_group in grouped_tasks:
            if not first_group:
                ttk.Separator(parent_frame, orient='horizontal').pack(fill='x', pady=5, padx=5)

            group_label = ttk.Label(parent_frame, text=f"— {group_name} —", font=("Arial", 9, "italic"))
            group_label.pack(pady=(5,2))
            first_group = False

            for task_data in tasks_in_group:
                task_id = task_data.get("id")
                priority = task_data.get("priority", "None")
                bg_color = self.priority_colors.get(priority, self.priority_colors["None"])

                card_frame = tk.Frame(parent_frame, relief=tk.RAISED, borderwidth=1, bg=bg_color)
                card_frame.pack(fill=tk.X, pady=3, padx=2)
                card_frame.columnconfigure(0, weight=1)

                content_frame = tk.Frame(card_frame, bg=bg_color, padx=10, pady=10)
                content_frame.grid(row=0, column=0, sticky=tk.EW)
                content_frame.columnconfigure(0, weight=1)

                title_frame = tk.Frame(content_frame, bg=bg_color)
                title_frame.grid(row=0, column=0, sticky=tk.EW)
                title_frame.columnconfigure(0, weight=1)

                title_label = ttk.Label(title_frame, text=task_data.get("title", "No Title"), font=("Arial", 10, "bold"), background=bg_color)
                title_label.grid(row=0, column=0, sticky=tk.W)

                delete_button = ttk.Button(title_frame, text="X", width=2,
                                           command=lambda c_id=column_id, t_id=task_id: self._delete_task(c_id, t_id))
                delete_button.grid(row=0, column=1, sticky=tk.E)

                details_frame = tk.Frame(content_frame, bg=bg_color)
                details_frame.grid(row=1, column=0, sticky=tk.EW, pady=(3,0))

                if priority and priority != "None":
                    priority_label = ttk.Label(details_frame, text=f"P: {priority}", font=("Arial", 8), background=bg_color)
                    priority_label.pack(side=tk.LEFT, padx=(0,10))

                due_date = task_data.get("due_date")
                if due_date:
                    due_date_label = ttk.Label(details_frame, text=f"Due: {due_date}", font=("Arial", 8), background=bg_color)
                    due_date_label.pack(side=tk.LEFT)

                move_buttons_frame = tk.Frame(content_frame, bg=bg_color)
                move_buttons_frame.grid(row=2, column=0, sticky=tk.EW, pady=(3,0))
                move_buttons_frame.columnconfigure(1, weight=1)

                current_col_index = -1
                try:
                    current_col_index = self.board_data["column_order"].index(column_id)
                except ValueError: pass

                if current_col_index > 0:
                    move_left_button = ttk.Button(move_buttons_frame, text="<", width=3,
                                                  command=lambda c_id=column_id, t_id=task_id: self._move_task(c_id, t_id, -1))
                    move_left_button.grid(row=0, column=0, sticky=tk.W)

                if current_col_index < len(self.board_data["column_order"]) - 1:
                     move_right_button = ttk.Button(move_buttons_frame, text=">", width=3,
                                                   command=lambda c_id=column_id, t_id=task_id: self._move_task(c_id, t_id, 1))
                     move_right_button.grid(row=0, column=2, sticky=tk.E)

                for widget in [card_frame, content_frame, title_frame, title_label, details_frame]:
                    widget.bind("<Button-1>", lambda e, c_id=column_id, t_id=task_id: self._edit_task_ui(c_id, t_id))
                for child in details_frame.winfo_children():
                    child.bind("<Button-1>", lambda e, c_id=column_id, t_id=task_id: self._edit_task_ui(c_id, t_id))

    def _ensure_data_file_exists(self):
        """Ensures the todo directory and the default board JSON file exist."""
        if not os.path.exists(self.TODO_DIR):
            try:
                os.makedirs(self.TODO_DIR)
            except OSError as e:
                messagebox.showerror("Error", f"Could not create directory: {self.TODO_DIR}\n{e}", parent=self)
                self.destroy()
                return

        if not os.path.exists(self.BOARD_FILE):
            default_board = {"columns": [], "column_order": []}
            for col_name in self.DEFAULT_COLUMNS:
                col_id = f"col_{uuid.uuid4()}"
                default_board["columns"].append({ "id": col_id, "name": col_name, "tasks": [] })
                default_board["column_order"].append(col_id)
            try:
                with open(self.BOARD_FILE, 'w', encoding='utf-8') as f:
                    json.dump(default_board, f, indent=2)
                self.board_data = default_board
            except IOError as e:
                messagebox.showerror("Error", f"Could not create board file: {self.BOARD_FILE}\n{e}", parent=self)
                self.destroy()

    def _load_board_data(self):
        """Loads the board data from the JSON file."""
        if not os.path.exists(self.BOARD_FILE):
            messagebox.showerror("Error", f"Board file not found: {self.BOARD_FILE}", parent=self)
            self.board_data = {"columns": [], "column_order": []}
            return
        try:
            with open(self.BOARD_FILE, 'r', encoding='utf-8') as f:
                self.board_data = json.load(f)
            if "columns" not in self.board_data or "column_order" not in self.board_data:
                 messagebox.showwarning("Data Error", "Board data is malformed. Resetting to default.", parent=self)
                 os.remove(self.BOARD_FILE)
                 self._ensure_data_file_exists()
        except json.JSONDecodeError as e:
            messagebox.showerror("Error Loading Data", f"Could not parse board data from {self.BOARD_FILE}:\n{e}", parent=self)
            self.board_data = {"columns": [], "column_order": []}
        except IOError as e:
            messagebox.showerror("Error Loading Data", f"Could not read board file: {self.BOARD_FILE}\n{e}", parent=self)
            self.board_data = {"columns": [], "column_order": []}

    def _save_board_data(self):
        """Saves the current board data to the JSON file."""
        if self.board_data is None: return
        try:
            with open(self.BOARD_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.board_data, f, indent=2)
        except IOError as e:
            messagebox.showerror("Error Saving Data", f"Could not save board data to {self.BOARD_FILE}\n{e}", parent=self)
        except TypeError as e:
            messagebox.showerror("Error Saving Data", f"Data is not serializable: {e}", parent=self)

    def _generate_timestamp(self):
        """Generates an ISO 8601 timestamp in UTC."""
        return datetime.now(timezone.utc).isoformat()

    def _group_and_sort_tasks(self, tasks_list):
        """Categorizes tasks by due date and then sorts by priority within each category."""
        from datetime import datetime, date, timedelta
        today = date.today()
        end_of_week = today + timedelta(days=6 - today.weekday())

        categories = { "Overdue": [], "Today": [], "This Week": [], "Later": [], "No Date": [] }
        category_order = ["Overdue", "Today", "This Week", "Later", "No Date"]
        priority_map = {"High": 0, "Medium": 1, "Low": 2, "None": 3}

        for task in tasks_list:
            due_date_str = task.get("due_date")
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    if due_date < today: categories["Overdue"].append(task)
                    elif due_date == today: categories["Today"].append(task)
                    elif today < due_date <= end_of_week: categories["This Week"].append(task)
                    else: categories["Later"].append(task)
                except ValueError:
                    categories["No Date"].append(task)
            else:
                categories["No Date"].append(task)

        for task_list in categories.values():
            task_list.sort(key=lambda t: priority_map.get(t.get("priority", "None"), 99))

        return [(name, tasks) for name, tasks in categories.items() if tasks]

    def _find_task_and_column(self, task_id):
        """Helper to find a task and its column by task_id."""
        for col in self.board_data.get("columns", []):
            for i, task in enumerate(col.get("tasks", [])):
                if task.get("id") == task_id:
                    return col, task, i
        return None, None, -1

    def _edit_task_ui(self, column_id, task_id):
        """Opens a dialog to edit an existing task."""
        col, task, task_index = self._find_task_and_column(task_id)
        if not task: return

        dialog = _TaskDetailDialog(self, title="Edit Task", task_data=task)
        if dialog.result:
            task.update(dialog.result)
            task['updated_at'] = self._generate_timestamp()
            col['tasks'][task_index] = task
            self._save_board_data()
            self._draw_board()

    def _delete_task(self, column_id, task_id):
        """Deletes a task after confirmation."""
        col, task, task_index = self._find_task_and_column(task_id)
        if not task: return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this task?\n\n{task.get('title')}", parent=self):
            del col['tasks'][task_index]
            self._save_board_data()
            self._draw_board()

    def _add_task_ui(self):
        """Handles the UI interaction for adding a new task."""
        dialog = _TaskDetailDialog(self, title="Add New Task")
        if dialog.result:
            new_task_data = dialog.result
            new_task_data['id'] = str(uuid.uuid4())
            ts = self._generate_timestamp()
            new_task_data['created_at'] = ts
            new_task_data['updated_at'] = ts

            if self.board_data and self.board_data.get("columns"):
                self.board_data["columns"][0].setdefault("tasks", []).append(new_task_data)
                self._save_board_data()
                self._draw_board()
            else:
                messagebox.showerror("Error", "No columns available to add a task.", parent=self)

    def _move_task(self, current_column_id, task_id, direction):
        """Moves a task to an adjacent column."""
        current_col, task, task_index = self._find_task_and_column(task_id)
        if not task or not current_col: return

        try:
            current_col_order_index = self.board_data["column_order"].index(current_column_id)
        except ValueError: return

        target_col_order_index = current_col_order_index + direction

        if 0 <= target_col_order_index < len(self.board_data["column_order"]):
            target_column_id = self.board_data["column_order"][target_col_order_index]

            target_col_object = next((c for c in self.board_data["columns"] if c["id"] == target_column_id), None)

            if target_col_object:
                task_to_move = current_col["tasks"].pop(task_index)
                task_to_move['updated_at'] = self._generate_timestamp()
                target_col_object.setdefault("tasks", []).append(task_to_move)
                self._save_board_data()
                self._draw_board()

    def on_close(self):
        self.destroy()

class _TaskDetailDialog(simpledialog.Dialog):
    """
    A modal dialog for entering or editing the details of a single task.
    Uses tkcalendar.DateEntry for date selection if the library is available.
    """
    def __init__(self, parent, title="Task Details", task_data=None):
        """
        Initializes the Task Detail dialog.
        Args:
            parent: The parent widget.
            title (str): The title for the dialog window.
            task_data (dict, optional): Existing task data to pre-fill the form.
        """
        self.task_data = task_data if task_data else {}
        super().__init__(parent, title)

    def body(self, master):
        """
        Creates the dialog body with entry fields for task details.
        Uses tkcalendar.DateEntry for due date if available, otherwise
        falls back to a standard ttk.Entry.
        """
        ttk.Label(master, text="Title:").grid(row=0, sticky=tk.W)
        self.title_entry = ttk.Entry(master, width=50)
        self.title_entry.grid(row=1, sticky=tk.EW)
        self.title_entry.insert(0, self.task_data.get("title", ""))

        ttk.Label(master, text="Description:").grid(row=2, sticky=tk.W, pady=(5,0))
        self.desc_text = tk.Text(master, width=50, height=5, wrap=tk.WORD)
        self.desc_text.grid(row=3, sticky=tk.EW)
        self.desc_text.insert("1.0", self.task_data.get("description", ""))

        details_frame = ttk.Frame(master)
        details_frame.grid(row=4, sticky=tk.EW, pady=5)

        ttk.Label(details_frame, text="Priority:").pack(side=tk.LEFT, padx=(0,5))
        default_priority = self.task_data.get("priority", "Low")
        self.priority_var = tk.StringVar(value=default_priority)
        self.priority_combo = ttk.Combobox(details_frame, textvariable=self.priority_var,
                                           values=["None", "Low", "Medium", "High"], state="readonly", width=10)
        self.priority_combo.pack(side=tk.LEFT, padx=(0,15))

        ttk.Label(details_frame, text="Due Date:").pack(side=tk.LEFT, padx=(0,5))

        if DateEntry:
            self.due_date_var = tk.StringVar(value=self.task_data.get("due_date") or "")
            self.due_date_entry = DateEntry(details_frame, width=12, background='darkblue',
                                            foreground='white', borderwidth=2, date_pattern='y-mm-dd',
                                            textvariable=self.due_date_var)
            self.due_date_entry.pack(side=tk.LEFT)
            clear_date_button = ttk.Button(details_frame, text="X", width=2,
                                           command=lambda: self.due_date_var.set(""))
            clear_date_button.pack(side=tk.LEFT, padx=(2,0))
        else:
            ttk.Label(details_frame, text="(YYYY-MM-DD)").pack(side=tk.LEFT, padx=(0,5))
            self.due_date_entry = ttk.Entry(details_frame, width=12)
            self.due_date_entry.pack(side=tk.LEFT)
            self.due_date_entry.insert(0, self.task_data.get("due_date") or "")

        return self.title_entry

    def apply(self):
        """
        Processes the data from the dialog when the OK button is pressed.
        Validates the title and stores the collected data in `self.result`.
        If validation fails, `self.result` is set to None.
        """
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Input Error", "Title is required.", parent=self)
            self.title_entry.focus_set()
            self.result = None
            return

        due_date_val = ""
        if DateEntry and isinstance(self.due_date_entry, DateEntry):
            due_date_val = self.due_date_var.get().strip()
        else:
            due_date_val = self.due_date_entry.get().strip()

        self.result = {
            "title": title,
            "description": self.desc_text.get("1.0", tk.END).strip(),
            "priority": self.priority_var.get(),
            "due_date": due_date_val or None
        }

if __name__ == '__main__':
    root = tk.Tk()
    class MockEditor:
        def __init__(self, root_window):
            self.root = root_window
    mock_master = MockEditor(root)

    def open_todo_dialog():
        dialog = TodoManagerDialog(mock_master)

    ttk.Button(root, text="Open Todo Manager", command=open_todo_dialog).pack(pady=20)
    root.mainloop()
