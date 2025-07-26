from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QTextEdit,
    QLineEdit, QPushButton, QHBoxLayout, QTreeView, QLabel, QStackedWidget,
    QFormLayout, QComboBox, QSpinBox, QDateEdit, QCheckBox, QFileIconProvider,
    QTableView, QScrollArea, QMenu, QFileSystemModel, QListWidget, QAction,
    QFileDialog
)
import os
import pandas as pd
import fitz
import subprocess
import sys
import json
from PyQt5.QtCore import Qt, QThread, QTimer, QDate, QFileInfo
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap, QImage
from src.file_indexer import FileIndexer
from src.highlighter import Highlighter
from src.result_delegate import ResultDelegate

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Search Application")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Search bar
        self.search_bar_layout = QHBoxLayout()
        self.search_input = QComboBox()
        self.search_input.setEditable(True)
        self.search_input.setPlaceholderText("Enter your search query...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_files)
        self.search_input.lineEdit().textChanged.connect(self.start_search_timer)
        self.search_bar_layout.addWidget(self.search_input)
        self.search_bar_layout.addWidget(self.search_button)
        self.layout.addLayout(self.search_bar_layout)

        # Toolbar
        self.toolbar = self.addToolBar("Main")
        self.toggle_filters_action = self.toolbar.addAction("Toggle Filters")
        self.toggle_filters_action.triggered.connect(self.toggle_filter_panel)
        self.toggle_preview_action = self.toolbar.addAction("Toggle Preview")
        self.toggle_preview_action.triggered.connect(self.toggle_preview_panel)
        self.theme_action = self.toolbar.addAction("Toggle Theme")
        self.theme_action.triggered.connect(self.toggle_theme)
        self.font_size_action = self.toolbar.addAction("Toggle Large Font")
        self.font_size_action.triggered.connect(self.toggle_font_size)
        self.recent_searches = []
        self.dark_theme = False
        self.large_font = False

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_files)

        # Filter panel
        self.filter_panel = QWidget()
        self.filter_layout = QFormLayout(self.filter_panel)
        self.layout.addWidget(self.filter_panel)
        self.filter_panel.setVisible(False)

        # Main Splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.main_splitter)

        # Left Panel
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.main_splitter.addWidget(self.left_panel)

        self.dir_explorer = QTreeView()
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath('')
        self.dir_explorer.setModel(self.fs_model)
        self.dir_explorer.setRootIndex(self.fs_model.index(''))
        self.dir_explorer.selectionModel().selectionChanged.connect(self.on_dir_selected)
        self.left_layout.addWidget(self.dir_explorer)

        self.favorites_list = QListWidget()
        self.favorites_list.itemClicked.connect(self.on_favorite_selected)
        self.left_layout.addWidget(self.favorites_list)

        self.favorites_toolbar = QHBoxLayout()
        self.add_fav_button = QPushButton("Add Fav")
        self.add_fav_button.clicked.connect(self.add_favorite)
        self.rem_fav_button = QPushButton("Rem Fav")
        self.rem_fav_button.clicked.connect(self.remove_favorite)
        self.favorites_toolbar.addWidget(self.add_fav_button)
        self.favorites_toolbar.addWidget(self.rem_fav_button)
        self.left_layout.addLayout(self.favorites_toolbar)

        self.load_favorites()

        # Center Panel
        self.center_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.center_splitter)

        self.file_type_filter_layout = QHBoxLayout()
        self.file_type_filters = {}
        for file_type in ["All", ".txt", ".pdf", ".docx", ".csv", ".xlsx"]:
            checkbox = QCheckBox(file_type)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.search_files)
            self.file_type_filter_layout.addWidget(checkbox)
            self.file_type_filters[file_type] = checkbox
        self.filter_layout.addRow("File type:", self.file_type_filter_layout)

        self.min_size_filter = QSpinBox()
        self.min_size_filter.setRange(0, 1024 * 1024)
        self.min_size_filter.setSuffix(" KB")
        self.filter_layout.addRow("Min size:", self.min_size_filter)

        self.max_size_filter = QSpinBox()
        self.max_size_filter.setRange(0, 1024 * 1024)
        self.max_size_filter.setSuffix(" KB")
        self.filter_layout.addRow("Max size:", self.max_size_filter)

        self.start_date_filter = QDateEdit()
        self.start_date_filter.setDate(QDate.currentDate().addYears(-1))
        self.start_date_filter.setCalendarPopup(True)
        self.filter_layout.addRow("From date:", self.start_date_filter)

        self.end_date_filter = QDateEdit()
        self.end_date_filter.setDate(QDate.currentDate())
        self.end_date_filter.setCalendarPopup(True)
        self.filter_layout.addRow("To date:", self.end_date_filter)

        self.time_range_filter = QComboBox()
        self.time_range_filter.addItems(["All time", "Today", "This week", "This month", "This year"])
        self.filter_layout.addRow("Time range:", self.time_range_filter)

        self.min_size_filter.valueChanged.connect(self.search_files)
        self.max_size_filter.valueChanged.connect(self.search_files)
        self.start_date_filter.dateChanged.connect(self.search_files)
        self.end_date_filter.dateChanged.connect(self.search_files)
        self.time_range_filter.currentIndexChanged.connect(self.on_time_range_changed)

        self.fuzzy_checkbox = QCheckBox("Enable fuzzy matching")
        self.filter_layout.addRow(self.fuzzy_checkbox)
        self.fuzzy_checkbox.stateChanged.connect(self.search_files)

        # Search results view
        self.results_view = QTreeView()
        self.results_model = QStandardItemModel()
        self.results_view.setModel(self.results_model)
        self.results_model.setHorizontalHeaderLabels(['Name', 'Path', 'Size', 'Date Modified', 'Snippet'])
        self.results_view.setItemDelegate(ResultDelegate(self.results_view))
        self.results_view.selectionModel().selectionChanged.connect(self.on_result_selected)
        self.results_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_view.customContextMenuRequested.connect(self.show_context_menu)
        self.center_splitter.addWidget(self.results_view)

        # File preview panel
        self.preview_stack = QStackedWidget()
        self.center_splitter.addWidget(self.preview_stack)

        self.text_preview = QTextEdit()
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.table_preview = QTableView()
        self.pdf_preview_area = QScrollArea()
        self.pdf_preview_label = QLabel()
        self.pdf_preview_area.setWidget(self.pdf_preview_label)
        self.pdf_preview_area.setWidgetResizable(True)


        self.preview_stack.addWidget(self.text_preview)
        self.preview_stack.addWidget(self.image_preview)
        self.preview_stack.addWidget(self.table_preview)
        self.preview_stack.addWidget(self.pdf_preview_area)

        # Set initial sizes
        self.main_splitter.setSizes([200, 1000])
        self.center_splitter.setSizes([600, 200])

        self.indexer = FileIndexer()
        self.thread = QThread()
        self.indexer.moveToThread(self.thread)
        self.thread.started.connect(lambda: self.indexer.index_files("."))
        self.indexer.finished.connect(self.thread.quit)
        self.thread.start()

    def start_search_timer(self):
        self.search_timer.start(500)  # Debounce time of 500ms

    def search_files(self):
        query = self.search_input.currentText()
        if query and query not in self.recent_searches:
            self.recent_searches.insert(0, query)
            self.search_input.insertItem(0, query)
            if len(self.recent_searches) > 10:
                self.recent_searches.pop()
                self.search_input.removeItem(10)


        file_types = [ft for ft, cb in self.file_type_filters.items() if cb.isChecked()]
        if "All" in file_types:
            file_types = None

        min_size = self.min_size_filter.value()
        max_size = self.max_size_filter.value()
        start_date = self.start_date_filter.date().toPyDate()
        end_date = self.end_date_filter.date().toPyDate()
        fuzzy = self.fuzzy_checkbox.isChecked()

        self.results = self.indexer.search_files(query, file_types, min_size, max_size, start_date, end_date, fuzzy)
        self.results_model.clear()
        self.results_model.setHorizontalHeaderLabels(['Name', 'Path', 'Size', 'Date Modified', 'Snippet'])
        provider = QFileIconProvider()
        for data in self.results:
            name_item = QStandardItem(data['name'])
            file_info = QFileInfo(data['path'])
            icon = provider.icon(file_info)
            name_item.setIcon(icon)
            path_item = QStandardItem(data['path'])
            size_item = QStandardItem(str(data['size']))
            date_item = QStandardItem(data['modified'].strftime("%Y-%m-%d %H:%M:%S"))
            snippet_item = QStandardItem(data.get('snippet', ''))
            self.results_model.appendRow([name_item, path_item, size_item, date_item, snippet_item])

    def on_result_selected(self, selected, deselected):
        if not selected.indexes():
            return

        index = selected.indexes()[0]
        data = self.results[index.row()]
        query = self.search_input.currentText()

        if data['type'] in ['.csv', '.xlsx']:
            if data['type'] == '.csv':
                df = pd.read_csv(data['path'])
            else:
                df = pd.read_excel(data['path'])

            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(df.columns)
            for row in df.values:
                items = [QStandardItem(str(item)) for item in row]
                model.appendRow(items)
            self.table_preview.setModel(model)
            self.preview_stack.setCurrentWidget(self.table_preview)
        elif data['type'] == '.pdf':
            doc = fitz.open(data['path'])
            pix = doc.get_page_pixmap(0)
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            self.pdf_preview_label.setPixmap(QPixmap.fromImage(image))
            self.preview_stack.setCurrentWidget(self.pdf_preview_area)
        elif data['type'] in self.indexer.TEXT_EXTENSIONS or data['type'] in ['.docx']:
            self.text_preview.setPlainText(data['content'])
            self.highlighter = Highlighter(self.text_preview.document(), query.split())
            self.preview_stack.setCurrentWidget(self.text_preview)
        elif data['type'] in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            pixmap = QPixmap(data['path'])
            self.image_preview.setPixmap(pixmap.scaled(self.image_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.preview_stack.setCurrentWidget(self.image_preview)

    def show_context_menu(self, pos):
        index = self.results_view.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)
        open_action = menu.addAction("Open")
        open_folder_action = menu.addAction("Open Containing Folder")

        action = menu.exec_(self.results_view.viewport().mapToGlobal(pos))

        if action == open_action:
            self.open_file(index)
        elif action == open_folder_action:
            self.open_folder(index)

    def open_file(self, index):
        data = self.results[index.row()]
        path = data['path']
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def add_favorite(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder to Add to Favorites")
        if path:
            self.favorites_list.addItem(path)
            self.save_favorites()

    def remove_favorite(self):
        for item in self.favorites_list.selectedItems():
            self.favorites_list.takeItem(self.favorites_list.row(item))
        self.save_favorites()

    def on_favorite_selected(self, item):
        path = item.text()
        self.indexer.index_files(path)
        self.search_files()

    def load_favorites(self):
        if os.path.exists("favorites.json"):
            with open("favorites.json", "r") as f:
                favorites = json.load(f)
                self.favorites_list.addItems(favorites)

    def save_favorites(self):
        favorites = [self.favorites_list.item(i).text() for i in range(self.favorites_list.count())]
        with open("favorites.json", "w") as f:
            json.dump(favorites, f)

    def on_time_range_changed(self, index):
        today = QDate.currentDate()
        if index == 0: # All time
            self.start_date_filter.setDate(today.addYears(-10))
            self.end_date_filter.setDate(today)
        elif index == 1: # Today
            self.start_date_filter.setDate(today)
            self.end_date_filter.setDate(today)
        elif index == 2: # This week
            self.start_date_filter.setDate(today.addDays(-today.dayOfWeek() + 1))
            self.end_date_filter.setDate(today)
        elif index == 3: # This month
            self.start_date_filter.setDate(QDate(today.year(), today.month(), 1))
            self.end_date_filter.setDate(today)
        elif index == 4: # This year
            self.start_date_filter.setDate(QDate(today.year(), 1, 1))
            self.end_date_filter.setDate(today)
        self.search_files()

    def on_dir_selected(self, selected, deselected):
        if not selected.indexes():
            return
        index = selected.indexes()[0]
        path = self.fs_model.filePath(index)
        self.indexer.index_files(path)
        self.search_files()

    def toggle_font_size(self):
        self.large_font = not self.large_font
        font = self.font()
        if self.large_font:
            font.setPointSize(16)
        else:
            font.setPointSize(10)
        self.setFont(font)

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        if self.dark_theme:
            with open("src/dark_theme.qss", "r") as f:
                self.setStyleSheet(f.read())
        else:
            with open("src/light_theme.qss", "r") as f:
                self.setStyleSheet(f.read())

    def toggle_filter_panel(self):
        self.filter_panel.setVisible(not self.filter_panel.isVisible())

    def toggle_preview_panel(self):
        self.center_splitter.widget(1).setVisible(not self.center_splitter.widget(1).isVisible())

    def open_folder(self, index):
        data = self.results[index.row()]
        path = os.path.dirname(data['path'])
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
