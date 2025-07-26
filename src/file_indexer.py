import os
import datetime
import docx
import pandas as pd
from PyPDF2 import PdfReader
from fuzzywuzzy import fuzz
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class FileIndexer(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = {}
        self.TEXT_EXTENSIONS = ['.txt', '.md', '.json', '.xml', '.ini', '.py', '.js', '.java', '.cpp', '.html']

    def index_files(self, path):
        count = 0
        for root, dirs, files in os.walk(path):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    stat = os.stat(file_path)
                    file_type = os.path.splitext(name)[1].lower()
                    file_data = {
                        'name': name,
                        'path': file_path,
                        'size': stat.st_size,
                        'created': datetime.datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.datetime.fromtimestamp(stat.st_mtime),
                        'type': file_type,
                        'content': ''
                    }

                    if file_type in self.TEXT_EXTENSIONS:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_data['content'] = f.read()
                    elif file_type == '.docx':
                        doc = docx.Document(file_path)
                        file_data['content'] = "\n".join([p.text for p in doc.paragraphs])
                    elif file_type == '.pdf':
                        with open(file_path, 'rb') as f:
                            reader = PdfReader(f)
                            file_data['content'] = "\n".join([page.extract_text() for page in reader.pages])
                    elif file_type == '.csv':
                        df = pd.read_csv(file_path)
                        file_data['content'] = df.to_string()
                    elif file_type == '.xlsx':
                        df = pd.read_excel(file_path)
                        file_data['content'] = df.to_string()

                    self.files[file_path] = file_data
                    count += 1
                    if count % 100 == 0:
                        self.progress.emit(count)
                except Exception:
                    pass
        self.finished.emit()

    def search_files(self, query, file_types=None, min_size=None, max_size=None, start_date=None, end_date=None, fuzzy=False):
        query = query.lower()
        terms = query.split()

        results = list(self.files.values())

        # Filter by file type
        if file_types:
            results = [data for data in results if data['type'] in file_types]

        # Filter by size
        if min_size is not None:
            results = [data for data in results if data['size'] >= min_size * 1024]
        if max_size is not None and max_size > 0:
            results = [data for data in results if data['size'] <= max_size * 1024]

        # Filter by date
        if start_date is not None:
            results = [data for data in results if data['modified'].date() >= start_date]
        if end_date is not None:
            results = [data for data in results if data['modified'].date() <= end_date]

        if not terms:
            return results

        # Separate terms into AND, OR, and NOT groups
        and_terms = [term for term in terms if term not in ['and', 'or', 'not'] and not term.startswith('not:')]
        or_terms = [term for term in terms if term in ['or']] # Not implemented yet
        not_terms = [term.replace('not:', '') for term in terms if term.startswith('not:')]

        # Filter out NOT terms
        if not_terms:
            results = [data for data in results if not any(term in data['name'].lower() or term in data['content'].lower() for term in not_terms)]

        # Filter for AND terms
        if and_terms:
            if fuzzy:
                results = [data for data in results if all(fuzz.partial_ratio(term, data['name'].lower()) > 70 or fuzz.partial_ratio(term, data['content'].lower()) > 70 for term in and_terms)]
            else:
                results = [data for data in results if all(term in data['name'].lower() or term in data['content'].lower() for term in and_terms)]

        # Generate snippets
        for data in results:
            data['snippet'] = self.generate_snippet(data['content'], and_terms)

        return results

    def generate_snippet(self, content, terms):
        if not content or not terms:
            return ""

        lines = content.splitlines()
        for i, line in enumerate(lines):
            if any(term in line.lower() for term in terms):
                return " ".join(lines[i:i+3])
        return " ".join(lines[:3])
