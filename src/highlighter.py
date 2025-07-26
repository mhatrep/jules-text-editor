import re
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtCore import Qt

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent, keywords):
        super().__init__(parent)
        self.keywords = keywords
        self.highlighting_rules = []

        brush = QColor("yellow")
        text_format = QTextCharFormat()
        text_format.setBackground(brush)

        for word in self.keywords:
            pattern = f"\\b{word}\\b"
            rule = (pattern, text_format)
            self.highlighting_rules.append(rule)

    def highlightBlock(self, text):
        for pattern, text_format in self.highlighting_rules:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                self.setFormat(start, end - start, text_format)
