from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QTextEdit,
    QLineEdit, QPushButton, QHBoxLayout, QTreeView, QLabel, QStackedWidget,
    QFormLayout, QComboBox, QSpinBox, QDateEdit, QCheckBox
)
import os
from PyQt5.QtCore import Qt, QThread, QTimer, QDate
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap
from src.file_indexer import FileIndexer
from src.highlighter import Highlighter

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
        self.recent_searches = []

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_files)

        # Create the main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.main_splitter)

        # Left panel (navigation/filter)
        self.nav_panel = QWidget()
        self.nav_layout = QFormLayout(self.nav_panel)
        self.main_splitter.addWidget(self.nav_panel)

        self.file_type_filter = QComboBox()
        self.file_type_filter.addItems(["All", ".txt", ".pdf", ".docx", ".csv", ".xlsx"])
        self.nav_layout.addRow("File type:", self.file_type_filter)

        self.min_size_filter = QSpinBox()
        self.min_size_filter.setRange(0, 1024 * 1024)
        self.min_size_filter.setSuffix(" KB")
        self.nav_layout.addRow("Min size:", self.min_size_filter)

        self.max_size_filter = QSpinBox()
        self.max_size_filter.setRange(0, 1024 * 1024)
        self.max_size_filter.setSuffix(" KB")
        self.nav_layout.addRow("Max size:", self.max_size_filter)

        self.start_date_filter = QDateEdit()
        self.start_date_filter.setDate(QDate.currentDate().addYears(-1))
        self.start_date_filter.setCalendarPopup(True)
        self.nav_layout.addRow("From date:", self.start_date_filter)

        self.end_date_filter = QDateEdit()
        self.end_date_filter.setDate(QDate.currentDate())
        self.end_date_filter.setCalendarPopup(True)
        self.nav_layout.addRow("To date:", self.end_date_filter)

        self.file_type_filter.currentIndexChanged.connect(self.search_files)
        self.min_size_filter.valueChanged.connect(self.search_files)
        self.max_size_filter.valueChanged.connect(self.search_files)
        self.start_date_filter.dateChanged.connect(self.search_files)
        self.end_date_filter.dateChanged.connect(self.search_files)

        self.fuzzy_checkbox = QCheckBox("Enable fuzzy matching")
        self.nav_layout.addRow(self.fuzzy_checkbox)
        self.fuzzy_checkbox.stateChanged.connect(self.search_files)

        # Center splitter (results and preview)
        self.center_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.center_splitter)

        # Search results view
        self.results_view = QTreeView()
        self.results_model = QStandardItemModel()
        self.results_view.setModel(self.results_model)
        self.results_model.setHorizontalHeaderLabels(['Name', 'Path', 'Size', 'Date Modified'])
        self.results_view.selectionModel().selectionChanged.connect(self.on_result_selected)
        self.center_splitter.addWidget(self.results_view)

        # File preview panel
        self.preview_stack = QStackedWidget()
        self.center_splitter.addWidget(self.preview_stack)

        self.text_preview = QTextEdit()
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)

        self.preview_stack.addWidget(self.text_preview)
        self.preview_stack.addWidget(self.image_preview)

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


        file_type = self.file_type_filter.currentText()
        min_size = self.min_size_filter.value()
        max_size = self.max_size_filter.value()
        start_date = self.start_date_filter.date().toPyDate()
        end_date = self.end_date_filter.date().toPyDate()
        fuzzy = self.fuzzy_checkbox.isChecked()

        self.results = self.indexer.search_files(query, file_type, min_size, max_size, start_date, end_date, fuzzy)
        self.results_model.clear()
        self.results_model.setHorizontalHeaderLabels(['Name', 'Path', 'Size', 'Date Modified'])
        for data in self.results:
            name_item = QStandardItem(data['name'])
            path_item = QStandardItem(data['path'])
            size_item = QStandardItem(str(data['size']))
            date_item = QStandardItem(data['modified'].strftime("%Y-%m-%d %H:%M:%S"))
            self.results_model.appendRow([name_item, path_item, size_item, date_item])

    def on_result_selected(self, selected, deselected):
        if not selected.indexes():
            return

        index = selected.indexes()[0]
        data = self.results[index.row()]
        query = self.search_input.currentText()

        if data['type'] in self.indexer.TEXT_EXTENSIONS or data['type'] in ['.docx', '.pdf', '.csv', '.xlsx']:
            self.text_preview.setPlainText(data['content'])
            self.highlighter = Highlighter(self.text_preview.document(), query.split())
            self.preview_stack.setCurrentWidget(self.text_preview)
        elif data['type'] in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            pixmap = QPixmap(data['path'])
            self.image_preview.setPixmap(pixmap.scaled(self.image_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.preview_stack.setCurrentWidget(self.image_preview)
