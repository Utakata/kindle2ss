from PySide6.QtWidgets import QWidget, QRubberBand
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QColor, QPalette, QPen, QPainter

class SelectionOverlay(QWidget):
    # Signal to return the selected geometry (x, y, w, h)
    selection_confirmed = Signal(int, int, int, int)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(Qt.CrossCursor)

        self.start_point = None
        self.end_point = None
        self.is_selecting = False

        # Visuals
        self.overlay_color = QColor(0, 0, 0, 100) # Semi-transparent black
        self.selection_border_color = QColor(0, 120, 215) # Windows Blue
        self.selection_fill_color = QColor(0, 120, 215, 50)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw full screen overlay
        painter.fillRect(self.rect(), self.overlay_color)

        if self.start_point and self.end_point:
            rect = QRect(self.start_point, self.end_point).normalized()

            # Clear the overlay inside the selection to make it transparent/highlighted
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Draw border
            pen = QPen(self.selection_border_color, 2)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Draw faint fill
            painter.fillRect(rect, self.selection_fill_color)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_point = event.pos()

            rect = QRect(self.start_point, self.end_point).normalized()
            if rect.width() > 10 and rect.height() > 10:
                self.selection_confirmed.emit(rect.x(), rect.y(), rect.width(), rect.height())
                self.close()
            else:
                # Reset if selection is too small (accidental click)
                self.start_point = None
                self.end_point = None
                self.update()

    def keyPressEvent(self, event):
        # Escape to cancel
        if event.key() == Qt.Key_Escape:
            self.close()
