import sys
import numpy as np
from math import sin, radians, cos

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtWidgets import QPushButton, QSizePolicy

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedSize(640, 400)

        self.plot_canvas = PlotCanvas(self, width=5, height=4)

        button = QPushButton('Увеличить', self)
        button.move(500, 0)
        button.resize(140, 100)
        button.clicked.connect(lambda x: self.plot_canvas.scale(1 / 2))

        button = QPushButton('Уменьшить', self)
        button.move(500, 100)
        button.resize(140, 100)
        button.clicked.connect(lambda x: self.plot_canvas.scale(2))

        self.show()


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, linewidth=10)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        def xf(t):
            return x0 + v0 * cos(a) * t
        
        def yf(t):
            return y0 + (v0 * sin(a) * t) - ((g * (t ** 2)) / 2)

        def init():
            line.set_data([], [])
            return line,

        def animate(i):
            line.set_data(x[:int(pfg / frames * (i + 1))], y[:int(pfg / frames * (i + 1))])
            return line,
        
        g = 9.8
        x0 = 0
        y0 = 150
        v0 = 15
        a = radians(60)

        h = y0 + ((v0 * sin(a)) ** 2) / (2 * g)
        s = x0 + v0 ** 2 * sin(a * 2) / g
        t_up = v0 * sin(a) / g
        t_down = (2 * h / g) ** 0.5
        t = t_up + t_down
        print(h, s, t, t_up, t_down)

        pfg = 1000
        x = xf(np.linspace(0, t, pfg))
        y = yf(np.linspace(0, t, pfg))

        self.figure.clear()
        self.ax = ax = self.figure.add_subplot(1, 1, 1)

        ax.set_xlim(-2, max(xf(t), h + 10))
        ax.set_ylim(0, max(xf(t), h + 10))

        ax.set_xlabel('Расстояние (м)')
        ax.set_ylabel('Высота (м)')

        ax.set_title('График')

        line, = ax.plot([], [])
        frames = 100
        anim = FuncAnimation(self.fig, animate, init_func=init, frames=frames, interval=10,
                             blit=True, repeat=False)
        self.draw()

    def scale(self, base_scale):
        x_lim = self.ax.get_xlim()
        y_lim = self.ax.get_ylim()

        new_x_lim = [lim * base_scale for lim in x_lim]
        new_y_lim = [lim * base_scale for lim in y_lim]

        print(new_x_lim, new_y_lim)
        self.ax.set_xlim(new_x_lim)
        self.ax.set_ylim(new_y_lim)

        self.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
