from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QTextEdit,
    QLineEdit, QPushButton, QHBoxLayout, QTreeView, QLabel, QStackedWidget
)
import os
from PyQt5.QtCore import Qt, QThread, QTimer
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
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter your search query...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_files)
        self.search_input.textChanged.connect(self.start_search_timer)
        self.search_bar_layout.addWidget(self.search_input)
        self.search_bar_layout.addWidget(self.search_button)
        self.layout.addLayout(self.search_bar_layout)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_files)

        # Create the main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.main_splitter)

        # Left panel (navigation/filter)
        self.nav_panel = QTextEdit("Navigation/Filter Panel")
        self.main_splitter.addWidget(self.nav_panel)

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
        query = self.search_input.text()
        if not query:
            self.results_model.clear()
            self.results_model.setHorizontalHeaderLabels(['Name', 'Path', 'Size', 'Date Modified'])
            return

        self.results = self.indexer.search_files(query)
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
        query = self.search_input.text()

        if data['type'] in self.indexer.TEXT_EXTENSIONS or data['type'] in ['.docx', '.pdf', '.csv', '.xlsx']:
            self.text_preview.setPlainText(data['content'])
            self.highlighter = Highlighter(self.text_preview.document(), query.split())
            self.preview_stack.setCurrentWidget(self.text_preview)
        elif data['type'] in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            pixmap = QPixmap(data['path'])
            self.image_preview.setPixmap(pixmap.scaled(self.image_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.preview_stack.setCurrentWidget(self.image_preview)
