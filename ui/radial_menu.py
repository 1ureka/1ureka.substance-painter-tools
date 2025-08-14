from PySide2 import QtCore, QtGui, QtWidgets
import math


class RadialMenu(QtWidgets.QWidget):
    def __init__(self, parent=None, options=None, callback=None):
        super().__init__(parent)
        self.options = options or ["One", "Two", "Three", "Four"]
        self.callback = callback
        self.radius = 100
        self.inner_radius = 24
        self.highlight = -1

        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    def show_at_cursor(self):
        pos = QtGui.QCursor.pos()
        size = self.radius * 2 + 4
        self.setGeometry(pos.x() - size // 2, pos.y() - size // 2, size, size)
        self.show()
        self.raise_()
        self.grabMouse()
        self.grabKeyboard()
        self.setMouseTracking(True)

    def paintEvent(self, _):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        center = QtCore.QPoint(self.width() // 2, self.height() // 2)
        n = len(self.options)
        step = 2 * math.pi / n

        # 背景
        p.setBrush(QtGui.QColor(0, 0, 0, 90))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(center, self.radius, self.radius)

        for i, text in enumerate(self.options):
            start_angle = (-math.pi / 2) + i * step
            mid_angle = start_angle + step / 2

            if i == self.highlight:
                path = QtGui.QPainterPath()
                path.moveTo(center)
                path.arcTo(self.rect().adjusted(2, 2, -2, -2), 90 - (i + 1) * 360 / n, 360 / n)
                path.closeSubpath()
                p.setBrush(QtGui.QColor(255, 255, 255, 70))
                p.setPen(QtCore.Qt.NoPen)
                p.drawPath(path)

            r = self.radius - 32
            tx = center.x() + r * math.cos(mid_angle)
            ty = center.y() + r * math.sin(mid_angle)
            rect = QtCore.QRectF(tx - 40, ty - 14, 80, 28)
            p.setPen(QtGui.QPen(QtGui.QColor(240, 240, 240)))
            p.drawText(rect, QtCore.Qt.AlignCenter, text)

        # 中心圓
        p.setBrush(QtGui.QColor(20, 20, 20, 180))
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 60)))
        p.drawEllipse(center, self.inner_radius, self.inner_radius)

    def mouseMoveEvent(self, e):
        self.highlight = self._sector_from_pos(e.pos())
        self.update()

    def mouseReleaseEvent(self, e):
        self.releaseMouse()
        self.releaseKeyboard()
        self.hide()

        if e.button() == QtCore.Qt.LeftButton:
            idx = self._sector_from_pos(e.pos())
            if idx >= 0:
                self.callback(self.options[idx])

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.releaseMouse()
            self.releaseKeyboard()
            self.hide()
        else:
            super().keyPressEvent(e)

    def _sector_from_pos(self, pos):
        center = QtCore.QPoint(self.width() // 2, self.height() // 2)
        v = QtCore.QPointF(pos - center)
        angle = math.atan2(-v.y(), v.x())
        angle = (-angle + math.pi / 2) % (2 * math.pi)

        n = len(self.options)
        step = 2 * math.pi / n
        return int(angle // step)
