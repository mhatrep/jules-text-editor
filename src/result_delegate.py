from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontMetrics, QColor

class ResultDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        if not index.isValid():
            return

        painter.save()

        # Get data from the model
        icon = index.data(Qt.DecorationRole)
        name = index.model().data(index.model().index(index.row(), 0))
        path = index.model().data(index.model().index(index.row(), 1))
        snippet = index.model().data(index.model().index(index.row(), 4)) if index.model().columnCount() > 4 else ""

        # Draw background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, QColor("white"))

        # Draw icon
        icon_rect = option.rect
        icon_rect.setWidth(32)
        icon.paint(painter, icon_rect, Qt.AlignCenter)

        # Draw text
        text_rect = option.rect
        text_rect.setLeft(icon_rect.right() + 5)

        font_metrics = QFontMetrics(painter.font())
        name_height = font_metrics.height()
        path_height = font_metrics.height()

        painter.drawText(text_rect.left(), text_rect.top() + name_height, name)
        painter.drawText(text_rect.left(), text_rect.top() + name_height + path_height, path)
        if snippet:
            painter.drawText(text_rect.left(), text_rect.top() + name_height + path_height * 2, snippet)

        painter.restore()

    def sizeHint(self, option, index):
        if not index.isValid():
            return super().sizeHint(option, index)

        font_metrics = QFontMetrics(option.font)
        name_height = font_metrics.height()
        path_height = font_metrics.height()
        snippet_height = font_metrics.height() * 2

        return QSize(200, name_height + path_height + snippet_height + 10)
