import sys

import numpy as np
from math import sin, cos, radians as rad

from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QTimer

from PyQt5 import uic

DATA_DIR = "resources"


class TrajectoryGraph(FigureCanvas):
    def __init__(self, root: QMainWindow, parent, width: int, height: int, dpi=100):
        """
        :param width: Ширина графика в дюймах
        :param height: Высота графика в дюймах
        :param dpi: Количество точек на дюйм
        """

        self.figure = Figure(figsize=(width, height), dpi=dpi, linewidth=10)
        self.parent = root
        FigureCanvas.__init__(self, self.figure)
        self.setParent(parent)

        self.plot()

    def plot(self):
        """
        Отрисовка траектории движения брошенного тела
        :return: None
        """
        def xf(tf):
            return x0 + v0 * cos(a) * tf

        def yf(tf):
            return y0 + (v0 * sin(a) * tf) - ((g * (tf ** 2)) / 2)

        def init():
            data.set_data([], [])
            return data,

        def animation(frame):
            data.set_data(x[:int(pfg / frames * (frame + 1))], y[:int(pfg / frames * (frame + 1))])
            return data,

        # Начальные значения
        g = 10
        a = rad(self.parent.angle_dsb.value())
        v0 = self.parent.v0_dsb.value()
        x0 = self.parent.x0_dsb.value()
        y0 = self.parent.y0_dsb.value()
        #

        # Основные параметры броска
        h = y0 + ((v0 * sin(a)) ** 2) / (2 * g)
        s = x0 + v0 ** 2 * sin(a * 2) / g
        t_up = v0 * sin(a) / g
        t_down = (2 * h / g) ** 0.5
        t = t_up + t_down
        #

        # Вычисление точек
        pfg = 1000
        x = xf(np.linspace(0, t, pfg))
        y = yf(np.linspace(0, t, pfg))
        #

        self.axes_limit = max(xf(t), h + 10)

        self.figure.clear()
        self.ax = self.figure.add_subplot(1, 1, 1)
        self.customize_graph(self.axes_limit)

        data, = self.ax.plot([], [])
        frames, interval = 200, 10
        self.ax.text(self.axes_limit * .65, self.axes_limit * .9, '$t_{полн} = ' + f'{t:.2f}' + 'с$')
        self.ax.text(self.axes_limit * .65, self.axes_limit * .8, '$h_{max} = ' + f'{h:.2f}' + 'м$')
        self.ax.text(self.axes_limit * .65, self.axes_limit * .7, '$s_{пол} = ' + f'{s:.2f}' + 'м$')
        self.anim = FuncAnimation(self.figure, animation, init_func=init,
                                  frames=frames, interval=interval, repeat=False, blit=True)
        self.draw()
        return frames * interval

    def customize_graph(self, limit):
        self.ax.set_xlim(-2, limit)
        self.ax.set_ylim(0, limit)

        self.ax.set_title('Траектория движения')
        self.ax.set_xlabel('Расстояние (м)')
        self.ax.set_ylabel('Высота (м)')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi(f"{DATA_DIR}/ui_files/main.ui", self)
        self.graph = TrajectoryGraph(self, self.graph_tab, 5, 4)

        self.timer = QTimer()
        self.timer.timeout.connect(self.finish_build)

        self.build_btn = QPushButton('Построить', self.graph_tab)
        self.build_btn.resize(75, 25)

        self.build_btn.clicked.connect(self.build_graph)

    def build_graph(self):
        anim_time = self.graph.plot()
        self.build_btn.setEnabled(False)

        self.timer.setInterval(anim_time)
        self.timer.start()

    def finish_build(self):
        self.timer.stop()
        self.build_btn.setEnabled(True)

    def mouseMoveEvent(self, a0) -> None:
        print(a0.pos())

    def resizeEvent(self, a0) -> None:
        self.graph.move(self.width() - self.graph.width(), 0)
        shift = self.graph.width() // 2 - self.build_btn.width() // 2
        self.build_btn.move(self.graph.x() + shift, self.graph.height() + 25)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    wnd = MainWindow()
    wnd.show()

    sys.excepthook = except_hook
    sys.exit(app.exec())
