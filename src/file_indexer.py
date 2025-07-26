import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class FileIndexer(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []

    def index_files(self, path):
        count = 0
        for root, dirs, files in os.walk(path):
            for name in files:
                self.files.append(os.path.join(root, name))
                count += 1
                if count % 100 == 0:
                    self.progress.emit(count)
        self.finished.emit()

    def search_files(self, query):
        results = []
        for file in self.files:
            if query.lower() in os.path.basename(file).lower():
                results.append(file)
        return results
