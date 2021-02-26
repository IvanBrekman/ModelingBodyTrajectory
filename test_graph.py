import sys
import numpy as np
from math import sin, radians, cos

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QDoubleSpinBox, QMessageBox
from PyQt5.QtWidgets import QPushButton, QSizePolicy, QVBoxLayout, QLabel

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation


class AboutWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Идет сохранение...')

        self.info = QLabel(self)
        self.info.setText('Программа "Арифмометр" позволяет выполнять 3\n')
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.info)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedSize(640, 400)
        self.message = QMessageBox()
        self.message.setText('Сохраняем...')
        self.message.setWindowTitle('Сохраняем')
        self.message.setFixedSize(300, 0)
        self.about = AboutWindow()

        self.plot_canvas = PlotCanvas(self, width=5, height=4)
        print(self.findChild(PlotCanvas, 'plot_canvas'))

        button = QPushButton('Увеличить', self)
        button.move(500, 0)
        button.resize(140, 100)
        button.clicked.connect(lambda x: self.plot_canvas.scale(10 / 11))

        button = QPushButton('Уменьшить', self)
        button.move(500, 100)
        button.resize(140, 100)
        button.clicked.connect(lambda x: self.plot_canvas.scale(11 / 10))

        button = QPushButton('Сохранить', self)
        button.move(500, 200)
        button.resize(140, 100)
        button.clicked.connect(self.save)

        button = QPushButton('Сохранить анимацию', self)
        button.move(500, 300)
        button.resize(140, 100)
        button.clicked.connect(self.save_anim)

        self.show()

    def save(self):
        self.plot_canvas.fig.savefig('figure.jpg')
        self.plot_canvas.plot(True)
    
    def save_anim(self):
        self.setEnabled(False)
        self.about.show()
        self.update()
        print(0)
        self.plot_canvas.anim.save('figure.gif', writer='imagemagick')
        print(1)
        self.setEnabled(True)


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, linewidth=10)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        self.x_lim = 0
        self.y_lim = 0

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot(False)

    def plot(self, is_scale_changes):
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

        pfg = 1000
        x = xf(np.linspace(0, t, pfg))
        y = yf(np.linspace(0, t, pfg))

        self.figure.clear()
        self.ax = ax = self.figure.add_subplot(1, 1, 1)

        if not is_scale_changes:
            ax.set_xlim(-2, max(xf(t), h + 10))
            ax.set_ylim(0, max(xf(t), h + 10))
        else:
            ax.set_xlim(self.x_lim)
            ax.set_ylim(self.y_lim)

        ax.set_xlabel('Расстояние (м)')
        ax.set_ylabel('Высота (м)')

        ax.set_title('График')

        line, = ax.plot([], [])
        frames = 200 if not is_scale_changes else 1
        self.anim = FuncAnimation(self.fig, animate, init_func=init, frames=frames, interval=10,
                                  blit=True, repeat=False)
        self.draw()

    def scale(self, base_scale):
        x_lim = self.ax.get_xlim()
        y_lim = self.ax.get_ylim()

        new_x_lim = [lim * base_scale for lim in x_lim]
        new_y_lim = [lim * base_scale for lim in y_lim]

        print(new_x_lim, new_y_lim)
        self.x_lim = new_x_lim
        self.y_lim = new_y_lim

        self.plot(True)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        print(delta)
        if delta > 0:
            self.scale(10 / 11)
        else:
            self.scale(11 / 10)

    def mouseMoveEvent(self, event):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
