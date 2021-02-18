import sys
import numpy as np

from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtWidgets import QPushButton, QComboBox, QTableWidgetItem, QHeaderView

from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import QTimer, QSize, Qt

from PyQt5 import uic

from formulas import *
from constants import *

from math import sin, cos, radians as rad

variables = {v0: None, a: None, h: None, s: None, t: None, vmx: None, vmn: None, tu: None, td: None}
name_to_variable = {
    'Стартовая скорость (м/с)': v0, 'Угол наклона (degrees)': a,
    'Макс. высота (м)': h, 'Дальность полета (м)': s, 'Время полета (с)': t,
    'Время подъема (с)': tu, 'Время спуска (с)': td,
    'Макс. скорость (м/с)': vmx, 'Мин. скорость (м/с)': vmn
}
variable_to_name = {value: key for key, value in name_to_variable.items()}


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
            return _x0 + _v0 * cos(_a) * tf

        def yf(tf):
            return _y0 + (_v0 * sin(_a) * tf) - ((g_const * (tf ** 2)) / 2)

        def init():
            data.set_data([], [])
            return data,

        def animation(frame):
            data.set_data(x[:int(pfg / frames * (frame + 1))], y[:int(pfg / frames * (frame + 1))])
            return data,

        # Начальные значения
        _a = rad(self.parent.angle_dsb.value())
        _v0 = self.parent.v0_dsb.value()
        _x0 = self.parent.x0_dsb.value()
        _y0 = self.parent.y0_dsb.value()
        #

        # Основные параметры броска
        _h = _y0 + ((_v0 * sin(_a)) ** 2) / (2 * g_const)
        _s = _x0 + _v0 ** 2 * sin(_a * 2) / g_const
        _t_up = _v0 * sin(_a) / g_const
        _t_down = (2 * _h / g_const) ** 0.5
        _t = _t_up + _t_down
        print(_t, type(_t))
        #

        # Вычисление точек
        pfg = 1000
        x = xf(np.linspace(0, _t, pfg))
        y = yf(np.linspace(0, _t, pfg))
        #

        # Построение графика
        self.axes_lim = max(xf(_t), _h + 10)

        self.figure.clear()
        self.ax = self.figure.add_subplot(1, 1, 1)
        self.customize_graph(self.axes_lim)

        data, = self.ax.plot([], [])
        frames, interval = 200, 10
        self.ax.text(self.axes_lim * .65, self.axes_lim * .9, '$t_{полн} = ' + f'{_t:.2f}' + 'с$')
        self.ax.text(self.axes_lim * .65, self.axes_lim * .8, '$h_{max} = ' + f'{_h:.2f}' + 'м$')
        self.ax.text(self.axes_lim * .65, self.axes_lim * .7, '$s_{пол} = ' + f'{_s:.2f}' + 'м$')
        self.anim = FuncAnimation(self.figure, animation, init_func=init,
                                  frames=frames, interval=interval, repeat=False, blit=True)
        self.draw()
        #

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

        # Первый tab
        self.graph = TrajectoryGraph(self, self.graph_tab, 5, 4)

        self.timer = QTimer()
        self.timer.timeout.connect(self.finish_build)

        self.build_btn = QPushButton('Построить', self.graph_tab)
        self.build_btn.resize(75, 25)

        self.build_btn.clicked.connect(self.build_graph)
        #

        # Второй tab
        self.error_message = QMessageBox(self)
        self.error_message.setWindowTitle('Ошибка')

        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon('resources/images/plus.png'))
        self.add_btn.setIconSize(QSize(28, 28))
        self.add_btn.clicked.connect(self.add_row)
        self.table_cbs = []
        self.delete_buttons = []

        self.known_values_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.known_values_table.setRowCount(1)
        self.known_values_table.setCellWidget(0, 2, self.add_btn)

        self.unknown_values_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.unknown_values_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.find_btn.clicked.connect(self.find_values)
        #

    def build_graph(self):
        """ Функция запускает "строительство" графика """
        anim_time = self.graph.plot()
        self.build_btn.setEnabled(False)

        self.timer.setInterval(anim_time)
        self.timer.start()

    def finish_build(self):
        """ Слот для конца "строительства" графика """
        self.timer.stop()
        self.build_btn.setEnabled(True)

    def add_row(self):
        """ Добавляет строку в таблицу известных величин (2 tab) """

        def suitable_items(all_items):
            table_items = [table_cb.currentText() for table_cb in self.table_cbs]
            return list(filter(lambda item: item not in table_items and item != 'Все', all_items))

        rows = self.known_values_table.rowCount()
        self.known_values_table.insertRow(rows)

        cb = QComboBox()
        items = [self.find_type_cb.itemText(i) for i in range(self.find_type_cb.count())]
        cb.addItems(suitable_items(items))

        del_btn = QPushButton(delete_char)
        del_btn.clicked.connect(self.delete_row)

        self.table_cbs.append(cb)
        self.delete_buttons.append(del_btn)

        self.known_values_table.setCellWidget(rows, 0, cb)
        self.known_values_table.setItem(rows, 1, QTableWidgetItem('0'))
        self.known_values_table.setCellWidget(rows, 2, del_btn)

    def delete_row(self):
        """ Удаляет строку из таблицы известных величин (2 tab) """

        row_index = self.delete_buttons.index(self.sender())
        self.delete_buttons.remove(self.sender())
        self.table_cbs.pop(row_index)
        self.known_values_table.removeRow(row_index + 1)

    def find_values(self):
        """ Функция "ищет" необходимые величины """
        for var in variables:
            variables[var] = None

        for i in range(1, self.known_values_table.rowCount()):
            item_name = self.table_cbs[i - 1].currentText()
            value = float(self.known_values_table.item(i, 1).text())

            variables[name_to_variable[item_name]] = value

        try:
            known_values = {key: variables[key] for key in
                            filter(lambda key: variables[key] is not None, variables)}
            known_values, formulas = find(known_values)
            info = [
                (variable_to_name[key], f'{key} = {formulas[key][0]}',
                 f'{float(known_values[key]):.2f}')
                for key in formulas
            ]
            print(*info, sep='\n')
        except ValueError as ve:
            self.error_message.setText(ve.__str__())
            self.error_message.show()
            return

        if not info:
            self.error_message.setText('С имеющимися данными невозможно '
                                       'рассчитать какую-либо величину')
            self.error_message.show()

        self.unknown_values_table.setRowCount(0)
        for i in range(len(info)):
            self.unknown_values_table.setRowCount(self.unknown_values_table.rowCount() + 1)
            for j in range(len(info[0])):
                self.unknown_values_table.setItem(i, j, QTableWidgetItem(str(info[i][j])))
                self.unknown_values_table.item(i, j).setFlags(Qt.ItemIsEditable)
                self.unknown_values_table.item(i, j).setForeground(QColor('black'))

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
