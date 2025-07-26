from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QTextEdit,
    QLineEdit, QPushButton, QHBoxLayout, QTreeView, QLabel, QStackedWidget
)
import os
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap
from src.file_indexer import FileIndexer

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
        self.search_bar_layout.addWidget(self.search_input)
        self.search_bar_layout.addWidget(self.search_button)
        self.layout.addLayout(self.search_bar_layout)

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

    def search_files(self):
        query = self.search_input.text()
        if not query:
            return

        results = self.indexer.search_files(query)
        self.results_model.clear()
        self.results_model.setHorizontalHeaderLabels(['Name', 'Path', 'Size', 'Date Modified'])
        for file in results:
            name_item = QStandardItem(os.path.basename(file))
            path_item = QStandardItem(file)
            size_item = QStandardItem(str(os.path.getsize(file)))
            date_item = QStandardItem(str(os.path.getmtime(file)))
            self.results_model.appendRow([name_item, path_item, size_item, date_item])
