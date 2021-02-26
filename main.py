import os
import sys
import time

import numpy as np
import webbrowser

from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtWidgets import QPushButton, QComboBox, QDoubleSpinBox
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog

from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtCore import QTimer, QSize, Qt

from resources.ui_files import main_wnd, about_wnd, settings_wnd, about_shot_wnd, save_results

from formulas import *
from constants import *
from database_requests import *

from math import sin, cos, radians as rad


# Словари связей
variables = {variable: None for variable in all_variables}
name_to_variable = {
    'Стартовая скорость (м/с)': v0, 'Угол наклона (degrees)': a,
    'Макс. высота (м)': h, 'Дальность полета (м)': s, 'Время полета (с)': t,
    'Время подъема (с)': tu, 'Время спуска (с)': td,
    'Макс. скорость (м/с)': vmx, 'Мин. скорость (м/с)': vmn, 'Начальная высота (м)': y0
}
variable_to_name = {value: key for key, value in name_to_variable.items()}
str_variable_to_name = {str(value): key for key, value in name_to_variable.items()}
variable_to_max_value = {v0: 1_000, a: 90, h: 10_000, s: 100_000, t: 2_000,
                         tu: 1_000, td: 1_000, vmx: 1_000, vmn: 1_000, y0: 5_000}
#


class TrajectoryGraph(FigureCanvas):
    """ Класс-наследник для реализации графика на QWidget """

    def __init__(self, root: QMainWindow, parent, width: int, height: int, dpi=100):
        """
        :param root: Родительский виджет
        :param parent: Родительский виджет, на котором располагается график (может совпадать с root)
        :param width: Ширина графика в дюймах
        :param height: Высота графика в дюймах
        :param dpi: Количество точек на дюйм
        """

        self.figure = Figure(figsize=(width, height), dpi=dpi, linewidth=10)
        self.parent = root

        FigureCanvas.__init__(self, self.figure)  # Инициализация объекта Figure
        self.setParent(parent)  # Установка родительского виджета

        self.point = None  # Точка для отрисовки
        self.plot()  # Начальная отрисовка графика для его появления

    def plot(self, is_new=True) -> int:
        """
        Отрисовка траектории движения брошенного тела
        :return: Время отрисовки графика (в милисекундах)
        """

        def xf(tf):
            return _v0 * cos(_a) * tf

        def yf(tf):
            return _y0 + (_v0 * sin(_a) * tf) - ((CONSTANTS['g'] * (tf ** 2)) / 2)

        def init():
            data.set_data([], [])
            return data,

        def animation(frame):
            data.set_data(x[:int(pfg / frames * (frame + 1))], y[:int(pfg / frames * (frame + 1))])
            return data,

        # Начальные значения
        _a = rad(self.parent.angle_dsb.value())
        _v0 = self.parent.v0_dsb.value()
        _y0 = self.parent.y0_dsb.value()
        #

        # Основные параметры броска
        _h = _y0 + ((_v0 * sin(_a)) ** 2) / (2 * CONSTANTS['g'])
        _t_up = _v0 * sin(_a) / CONSTANTS['g']
        _t_down = (2 * _h / CONSTANTS['g']) ** 0.5
        _t = _t_up + _t_down
        _s = _v0 * cos(_a) * _t
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
        interval = 10
        frames = (CONSTANTS['graph_time_ms'] // 10) if is_new and CONSTANTS['is_animated'] else 1
        self.ax.text(self.axes_lim * .65, self.axes_lim * .9, '$t_{полн} = ' + f'{_t:.2f}' + 'с$')
        self.ax.text(self.axes_lim * .65, self.axes_lim * .8, '$h_{max} = ' + f'{_h:.2f}' + 'м$')
        self.ax.text(self.axes_lim * .65, self.axes_lim * .7, '$s_{пол} = ' + f'{_s:.2f}' + 'м$')

        if not is_new and self.point is not None:
            self.ax.scatter(*self.point)

        self.anim = FuncAnimation(self.figure, animation, init_func=init,
                                  frames=frames, interval=interval, repeat=False, blit=True)
        self.draw()
        #

        return frames * interval

    def scatter(self, tf) -> list:
        """
        Метод отрисовывает точку на графика в определенный момент времени
        :param tf: Мгновенный момент времени
        :return: Список координат точки
        """

        # Загрузка начальных условий
        _a = rad(self.parent.angle_dsb.value())
        _v0 = self.parent.v0_dsb.value()
        _y0 = self.parent.y0_dsb.value()
        #

        # Вычисление координат
        x = _v0 * cos(_a) * tf
        y = _y0 + (_v0 * sin(_a) * tf) - ((CONSTANTS['g'] * (tf ** 2)) / 2)
        #

        # Установка точки и отрисовка графика
        self.point = (x, y)
        self.plot(False)
        #

        return [x, y]

    def customize_graph(self, limit):
        """ Дизайн графика """

        self.ax.set_xlim(-0.05 * limit, 1.05 * limit)
        self.ax.set_ylim(0, limit)

        self.ax.set_title('Траектория движения')
        self.ax.set_xlabel('Расстояние (м)')
        self.ax.set_ylabel('Высота (м)')


class AboutWindow(QWidget, about_wnd.Ui_Form):
    """ Классно окна "О программе" """

    def __init__(self):
        super().__init__()
        self.setupUi(self)


class SettingsWindow(QWidget, settings_wnd.Ui_Form):
    """ Класс окна настроек """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setupUi(self)

        # Получение настроек из бвзы данных #
        params = {param: value for p_id, param, value in get_data_from_db(MY_DB, 'settings', '*')}

        # Загрузка настроек
        self.g_dsb.setValue(params['g'])
        self.graph_time_dsb.setValue(params['graph_time_ms'] / 1_000)
        self.is_animated_chb.setCheckState(int(params['is_animated']) * 2)
        #

        self.save_btn.clicked.connect(self.save_settings)

    def save_settings(self):
        """ Метод сохраняет введенные значения """

        # Обновление таблицы settings в базе данных
        values = {'g': self.g_dsb.value(), 'graph_time_ms': self.graph_time_dsb.value() * 1_000,
                  'is_animated': int(self.is_animated_chb.isChecked())}
        for param in ('g', 'graph_time_ms', 'is_animated'):
            update_data_in_db(MY_DB, 'settings', {'value': values[param]}, {'param': param})
        #

        update_constants()  # Обновление глобальных констант
        self.destroy()


class AboutShotWindow(QWidget, about_shot_wnd.Ui_Form):
    """ Класс окна с информацией о броске """

    def __init__(self, info: dict, moment_pos=None):
        super().__init__()

        self.info = {key: value for key, value in info.items() if key != y0}

        # Добавление мгновенных высоты и перемещения
        moment_h = moment_pos[1] if moment_pos is not None else 0.0
        moment_s = moment_pos[0] if moment_pos is not None else 0.0
        self.info['mh'] = moment_h
        self.info['ms'] = moment_s
        #

        self.initUI()

    def initUI(self):
        self.setupUi(self)

        # Загрузка информации о броске
        for variable, value in self.info.items():
            dsb = self.findChild(QDoubleSpinBox, f'dsb_{variable}')
            dsb.setValue(value)
            dsb.setStyleSheet("color: black;")
        #


class SaveShotWindow(QWidget, save_results.Ui_Form):
    """ Класс окна сохранения эксперимента """

    def __init__(self, parent, shot_info: dict, shot_graph: TrajectoryGraph):
        """
        :param parent: Родительский виджет
        :param shot_info: Словарь информации о броске
        :param shot_graph: Объект Figure в родительском виджете
        """

        super().__init__()

        self.parent = parent
        self.shot_info = shot_info
        self.shot_graph = shot_graph

        self.initUI()

    def initUI(self):
        self.setupUi(self)

        self.message = QMessageBox()
        self.save_btn.clicked.connect(self.save)

    def save(self):
        # Вывод предупреждающеге сообщения
        self.message.setWindowTitle('Идет сохранение...')
        self.message.setText(' ' * 50)
        self.message.show()
        #

        name = self.name_le.text().strip()
        path = f'{DATA_DIR}/results'
        not_allowed_symbols = ('\\', '/', ':', '*', '?', '"', '\'', '<', '>', '|')

        # Проверка на пустое или некорректное название эксперимента
        if not name or any(symbol in name for symbol in not_allowed_symbols):
            self.message.setText('Название не должно быть пустым или содержать следующие знаки:\n' +
                                 '\t' * 3 + ' '.join(not_allowed_symbols))
            self.message.show()
            return
        #

        # Проверка на повторяющееся название эксперимента
        names = [res[0] for res in get_data_from_db(MY_DB, 'results', 'name')]
        if name in names:
            self.message.setText('Эксперимент с таким названием уже сохранен')
            self.message.show()
            return
        #

        # Создание файла с информацией о броске
        file_name = f'{name}.txt'
        if os.path.exists(file_name):
            raise NameError(f'Error occurred in SaveShotWindow.save() method. '
                            f'Name {file_name} already exist')

        with open(f'{path}/info_files/{file_name}', mode='w') as info_file:
            for var, value in self.shot_info.items():
                info_file.write(f'{variable_to_name[var]}: {value}\n')
        #

        # Сохранение графика броска
        need_gif = self.graph_save_type_cb.currentText() == 'Анимацию (.gif)'
        graph_file_name = f'{name}.{"gif" if need_gif else "jpg"}'
        if os.path.exists(graph_file_name):
            raise NameError(f'Error occurred in SaveShotWindow.save() method. '
                            f'Name {graph_file_name} already exist')
        
        if need_gif:
            self.shot_graph.anim.save(f'{path}/graph_files/{graph_file_name}', writer='imagemagick')
        else:
            self.shot_graph.figure.savefig(f'{path}/graph_files/{graph_file_name}')
        #

        # Сохранение информации о броске в базу данных #
        add_data_to_db(MY_DB, 'results', ('name', 'info_file', 'graph_file'),
                       (name, file_name, graph_file_name))

        self.message.hide()  # Убрать предупреждающее сообщение
        self.shot_graph.plot(False)  # Отрисовка графика заново
        self.parent.load_exp_table()  # Обновление таблицы экспериментов
        self.destroy()


class MainWindow(QMainWindow, main_wnd.Ui_MainWindow):
    """ Класс основного окна приложения """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setupUi(self)

        # Установка триггеров для menuBar
        self.about_action.triggered.connect(self.show_about_wnd)
        self.open_web_action.triggered.connect(self.open_web_page)
        self.open_book_action.triggered.connect(self.open_book)
        self.settings_action.triggered.connect(self.show_settings_wnd)
        #

        # Первый tab
        self.graph = TrajectoryGraph(self, self.graph_tab, 5, 4)
        self.shot_data = {}
        self.moment_pos = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.finish_build)

        self.load_btn = QPushButton('Загрузить', self.graph_tab)
        self.load_btn.resize(75, 25)
        self.load_btn.clicked.connect(self.load_info)

        self.example_btn = QPushButton('Пример файла', self.graph_tab)
        self.example_btn.resize(85, 25)
        self.example_btn.clicked.connect(self.show_example_file)

        self.build_btn = QPushButton('Построить', self.graph_tab)
        self.build_btn.resize(75, 25)
        self.build_btn.clicked.connect(self.build_graph)

        self.about_shot_btn = QPushButton('О броске', self.graph_tab)
        self.about_shot_btn.resize(75, 25)
        self.about_shot_btn.setEnabled(False)
        self.about_shot_btn.clicked.connect(self.show_about_shot_wnd)

        self.shot_type_cb.currentIndexChanged.connect(self.change_shot_type)
        self.moment_time_dsb.valueChanged.connect(self.draw_moment_pos)
        self.save_shot_btn.clicked.connect(self.show_save_shot_wnd)
        #

        # Второй tab
        self.error_message = QMessageBox(self)
        self.error_message.setWindowTitle('Ошибка')

        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon('resources/images/plus.png'))
        self.add_btn.setIconSize(QSize(28, 28))
        self.add_btn.clicked.connect(self.add_row)

        self.need_to_update_items = True
        self.table_cbs = []
        self.delete_buttons = []

        self.known_values_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.known_values_table.setRowCount(1)
        for i in range(2):
            self.known_values_table.setItem(0, i, QTableWidgetItem(''))
            self.known_values_table.item(0, i).setFlags(Qt.ItemIsEditable)
        self.known_values_table.setCellWidget(0, 2, self.add_btn)

        self.unknown_values_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.unknown_values_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.unknown_values_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.find_type_cb.currentIndexChanged.connect(self.change_table)
        self.var_fame_chb.stateChanged.connect(self.change_y0_fame)
        self.find_btn.clicked.connect(self.find_values)
        #

        # Третий tab
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.load_exp_table()
        #
    
    @staticmethod
    def open_web_page():
        """ Метод открывает ссылкы на информационные ресурсы """

        webbrowser.open('https://resh.edu.ru/subject/lesson/3025/start/')
        webbrowser.open('https://resh.edu.ru/subject/lesson/3131/start/')
        webbrowser.open('https://resh.edu.ru/subject/lesson/3024/start/')

    @staticmethod
    def open_book():
        """ Метод открывает учебник в формате pdf """

        path = f'{DATA_DIR}/database/Учебник Физика 10 класс Касьянов Профильный уровень.pdf'
        os.startfile(os.path.abspath(path))

    def show_about_wnd(self):
        self.about_wnd = AboutWindow()
        self.about_wnd.show()

    def show_settings_wnd(self):
        self.settings_wnd = SettingsWindow()
        self.settings_wnd.show()

    def load_from_file(self, file_path: str) -> bool:
        """ Метод загружает информацию в 1 tab из фалйа file_path """

        if not os.path.isfile(file_path):  # Проверка на существование файла
            raise ValueError(f'Error occurred in MainWindow.load_from_file method.'
                             f'Incorrect path {file_path}')

        with open(file_path) as info_file:  # Загрузка информации в словарь
            info = dict([line.strip().split(': ') for line in info_file.readlines()])

        # Проверка на корректность файла
        try:
            self.v0_dsb.setValue(float(info[variable_to_name[v0]]))
            self.angle_dsb.setValue(float(info[variable_to_name[a]]))
            self.y0_dsb.setValue(float(info[variable_to_name[y0]]))
        except (KeyError, ValueError):
            self.error_message.setText('Выбранный файл неправильного формата')
            self.error_message.show()
            return False
        #

        return True

    # tab 1
    def change_shot_type(self):
        """ Метод настраивает интерфейс в зависимости от указанного типа броска """

        if self.shot_type_cb.currentText() == 'Произвольный':
            self.angle_dsb.setEnabled(True)
        elif self.shot_type_cb.currentText() == 'Вертикальный':
            self.angle_dsb.setValue(90)
            self.angle_dsb.setEnabled(False)
        elif self.shot_type_cb.currentText() == 'Горизонтальный':
            self.angle_dsb.setValue(0)
            self.angle_dsb.setEnabled(False)
        else:
            raise TypeError(f'Error in change_shot_type method. Chosen unknown shot type '
                            f'"{self.shot_type_cb.currentText()}"')
        self.moment_time_dsb.setEnabled(False)

    def load_info(self):
        """ Метод загружает информацию с файла """

        file_path, ok_pressed = QFileDialog.getOpenFileName(self, 'Выбрать файл', '', 'Файл (*.txt)')
        
        if ok_pressed:
            is_ok = self.load_from_file(file_path)
            if not is_ok:
                return

            self.message = QMessageBox()
            self.message.setText('Информация успешно загружена с файла')
            self.message.show()

    def build_graph(self):
        """ Функция запускает "строительство" графика """

        # Обнуление старой информации
        self.moment_time_dsb.disconnect()
        self.moment_time_dsb.setValue(0)
        self.moment_time_dsb.valueChanged.connect(self.draw_moment_pos)
        self.moment_pos = None
        anim_time = self.graph.plot()  # отрисовка графика
        #

        # Отключение зависимого интерфейса
        self.save_shot_btn.setEnabled(False)
        self.build_btn.setEnabled(False)
        self.about_shot_btn.setEnabled(False)
        self.moment_time_dsb.setEnabled(False)
        #

        # Запуск таймера на строительство графика
        self.timer.setInterval(anim_time)
        self.timer.start()
        #

    def finish_build(self):
        """ Слот для конца "строительства" графика """

        # Возобновление интерфейса
        self.timer.stop()
        self.save_shot_btn.setEnabled(True)
        self.build_btn.setEnabled(True)
        self.about_shot_btn.setEnabled(True)
        self.moment_time_dsb.setEnabled(True)
        #

        # Расчет информации о броске
        known_values = {v0: self.v0_dsb.value(), a: self.angle_dsb.value(), y0: self.y0_dsb.value()}

        change_state = False
        if self.var_fame_chb.isChecked():
            self.var_fame_chb.setCheckState(0)
            change_state = True

        find(known_values)

        if change_state:
            self.var_fame_chb.setCheckState(2)
        #

        self.moment_time_dsb.setMaximum(known_values[t])
        self.shot_data = known_values

    def draw_moment_pos(self):
        """ Функция отрисовывает положение материальной точки в определенный момент времени """

        x, y = self.graph.scatter(self.moment_time_dsb.value())
        self.moment_pos = [x, y]

    @staticmethod
    def show_example_file():
        os.startfile(os.path.abspath(f'{DATA_DIR}/database/example.txt'))

    def show_about_shot_wnd(self):
        self.about_shot_wnd = AboutShotWindow(self.shot_data, self.moment_pos)
        self.about_shot_wnd.show()

    def show_save_shot_wnd(self):
        self.save_shot_wnd = SaveShotWindow(self, self.shot_data, self.graph)
        self.save_shot_wnd.show()
    #

    # tab 2
    def add_row(self):
        """ Добавляет строку в таблицу известных величин (2 tab) """

        def suitable_items(all_items):
            """ Поиск возможных значений для типа переменной """

            table_items = [table_cb.currentText() for table_cb in self.table_cbs]
            return list(filter(lambda item: item not in table_items and item != 'Все', all_items))

        rows = self.known_values_table.rowCount()
        self.known_values_table.insertRow(rows)

        self.check_add_opportunity()

        # Создание всех элементов строки
        cb = QComboBox()
        items = [self.find_type_cb.itemText(i) for i in range(self.find_type_cb.count())]
        cb.addItems(suitable_items(items))
        cb.currentTextChanged.connect(self.update_items)

        value_dsb = QDoubleSpinBox()
        value_dsb.setMaximum(variable_to_max_value[name_to_variable[cb.currentText()]])

        del_btn = QPushButton(delete_char)
        del_btn.clicked.connect(self.delete_row)
        #

        self.table_cbs.append(cb)
        self.delete_buttons.append(del_btn)

        # Добавление в таблицу
        self.known_values_table.setCellWidget(rows, 0, cb)
        self.known_values_table.setCellWidget(rows, 1, value_dsb)
        self.known_values_table.setCellWidget(rows, 2, del_btn)
        #

        self.update_items()

    def delete_row(self):
        """ Удаляет строку из таблицы известных величин (2 tab) """

        row_index = self.delete_buttons.index(self.sender())

        # Удаление из всех источников
        self.delete_buttons.pop(row_index)
        self.table_cbs.pop(row_index)
        self.known_values_table.removeRow(row_index + 1)
        #

        self.add_btn.setEnabled(True)  # Обновление состояния кнопки
        self.update_items()

    def check_add_opportunity(self):
        """ Проверка на возможность добавления новой величины """

        free_space = len(name_to_variable) - y0.is_known
        self.add_btn.setEnabled(self.known_values_table.rowCount() - 1 < free_space)

    def update_items(self):
        """ Обновление возможных item-ов в каждом QComboBox таблице в зависимости от выбранных """

        if not self.need_to_update_items:
            return

        self.need_to_update_items = False  # Флажок необходимый для предотвращения рекурсии

        # Получение возможных item-ов
        table_items = [table_cb.currentText() for table_cb in self.table_cbs]
        suitable_items = [item for item in name_to_variable.keys() if item not in table_items]
        if y0.is_known:
            suitable_items.remove(variable_to_name[y0])
        #

        # Заполнение возможными item-ами каждый QComboBox
        for cb in self.table_cbs:
            current_text = cb.currentText()
            cb.clear()
            cb.addItems([current_text] + suitable_items)
        #

        self.need_to_update_items = True

    def find_values(self):
        """ Функция "ищет" необходимые величины """

        # "Обнуление" значений переменных
        for var in variables:
            variables[var] = None
        #

        # Заполнение значениями известных переменных
        if self.find_type_cb.currentText() == 'Все':  # Загрузка информации со всей таблицы
            for i in range(1, self.known_values_table.rowCount()):
                item_name = self.known_values_table.cellWidget(i, 0).currentText()
                value = self.known_values_table.cellWidget(i, 1).value()

                variables[name_to_variable[item_name]] = value
        else:  # Если поиск конкретной величины, то находим первую заполненную комбинацию в таблице
            try:
                self.find_any_filled_combination()
            except ValueError as ve:  # Если нет заполненной комбинации - сообщаем пользователю
                self.error_message.setText(ve.__str__())
                self.error_message.show()
                return
        #

        # Поиск всевозможных величин по известным переменным
        try:
            known_values = {key: variables[key] for key in
                            filter(lambda key: variables[key] is not None, variables)}
            known_values, formulas = find(known_values)

            # Сортировка найденных значений по целевой переменной
            if self.find_type_cb.currentText() != 'Все':
                target_variable = name_to_variable[self.find_type_cb.currentText()]
                formulas = {key: formulas[key] for key in
                            sorted(formulas, key=lambda variable: variable != target_variable)}
            #

            info = [
                (variable_to_name[key], f'{key} = {formulas[key]}',
                 f'{float(known_values[key]):.2f}')
                for key in formulas
            ]  # Преобразование найденной информации для загрузки в таблицу
        except ValueError as ve:  # Вывод ошибки при введении некорректных данных
            self.error_message.setText(ve.__str__())
            self.error_message.show()
            return
        #

        # Если имеющихся данных недостаточно для поиска хотя бы 1 величины - сообщаем пользователю #
        if not info:
            text = 'С имеющимися данными невозможно рассчитать какую-либо величину'
            self.unknown_values_table.setRowCount(0)
            self.unknown_values_table.setRowCount(1)
            self.unknown_values_table.setItem(0, 1, QTableWidgetItem(text))
            return

        # Запись найденных данных в таблицу
        self.unknown_values_table.setRowCount(0)
        for i in range(len(info)):
            self.unknown_values_table.setRowCount(self.unknown_values_table.rowCount() + 1)
            for j in range(len(info[0])):
                self.unknown_values_table.setItem(i, j, QTableWidgetItem(str(info[i][j])))
                self.unknown_values_table.item(i, j).setFlags(Qt.ItemIsEditable)
                self.unknown_values_table.item(i, j).setForeground(QColor('black'))
        #

    def find_any_filled_combination(self):
        """ Метод находит заполненную комбинацию для поиска целевой переменной """

        start_index = 1
        for combination in self.combinations:  # Перебираем каждую комбинацию
            values = {}
            # Заполняем значения для каждой переменной из кобинации
            for i in range(start_index, start_index + len(combination)):
                var = name_to_variable[combination[i - start_index]]
                values[var] = self.known_values_table.cellWidget(i, 1).value()
            start_index += len(combination) + 1  # Обновление стартового счетчика для таблицы
            #

            if all(value != 0 for value in values.values()):  # Проверяем все значения комбинации
                for variable, value in values.items():
                    variables[variable] = value
                return

        # Если не находится ни одной полной комбинации порождаем ошибку #
        raise ValueError('Хотя бы одна комбинация должна быть заполнена ненулевыми значениями')

    def change_y0_fame(self):
        """ Метод обновляет известность y0 и обновляет таблицу """

        y0.is_known = self.var_fame_chb.isChecked()

        self.change_formulas()

        if self.find_type_cb.currentText() == variable_to_name[y0]:
            self.var_fame_chb.setCheckState(0)
            return

        if self.find_type_cb.currentText() != 'Все':  # Не обновляет таблицу если выбран поиск всего
            self.change_table()
        else:  # Регулирование доступности указывания начальной высоты
            if y0.is_known:
                start_height = variable_to_name[y0]
                for i in range(1, self.known_values_table.rowCount()):
                    if self.known_values_table.cellWidget(i, 0).currentText() == start_height:
                        self.known_values_table.cellWidget(i, 2).click()
                        break
            self.update_items()

        self.check_add_opportunity()

    def change_formulas(self):
        """ Метод изменяет формулы расчетов некоторых величин в зависимости от известности y0 """

        if self.var_fame_chb.isChecked():
            index_s = all_form.index(s_v0_a_t)
            index_vmx = all_form.index(vmx_v0_a_t)

            all_form[index_s] = s_v0_a_y00
            all_form[index_vmx] = vmx_v0_y00
        else:
            index_s = all_form.index(s_v0_a_y00)
            index_vmx = all_form.index(vmx_v0_y00)

            all_form[index_s] = s_v0_a_t
            all_form[index_vmx] = vmx_v0_a_t

    def change_table(self):
        """ Метод меняет отображение таблицы в зависимости от того, то хочет найти пользователь """

        # Обновление таблицы
        self.known_values_table.setRowCount(1)
        if self.find_type_cb.currentText() == 'Все':
            self.add_btn.setEnabled(True)
            self.table_cbs.clear()
            self.delete_buttons.clear()
            return
        #

        # Если выбран поиск y0 искусственно снимаем известность y0
        if self.find_type_cb.currentText() == variable_to_name[y0] and y0.is_known:
            y0.is_known = False
            self.var_fame_chb.disconnect()
            self.var_fame_chb.setCheckState(0)
            self.change_formulas()
            self.var_fame_chb.stateChanged.connect(self.change_y0_fame)
        #

        # Загрузка наборов переменных для поиска целевой переменной
        self.add_btn.setEnabled(False)
        variable = name_to_variable[self.find_type_cb.currentText()]
        combinations = get_data_from_db(MY_DB, 'variables_collections', 'required_values',
                                        {'variable': [str(variable)],
                                         'is_known': [str(int(y0.is_known))]})
        #

        # Добавление каждого набора в таблицу
        self.combinations = []
        for combination in combinations:
            values = [str_variable_to_name[var] for var in combination[0].split()]
            self.combinations.append(values)

            rows = self.known_values_table.rowCount()
            i = 0
            for i in range(rows, rows + len(values)):
                self.known_values_table.setRowCount(self.known_values_table.rowCount() + 1)

                cb = QComboBox()
                cb.addItem(values[i - rows])

                value_dsb = QDoubleSpinBox()
                value_dsb.setMaximum(variable_to_max_value[name_to_variable[values[i - rows]]])

                del_btn = QPushButton(delete_char)
                del_btn.setEnabled(False)

                self.known_values_table.setCellWidget(i, 0, cb)
                self.known_values_table.setCellWidget(i, 1, value_dsb)
                self.known_values_table.setCellWidget(i, 2, del_btn)

            self.known_values_table.setRowCount(self.known_values_table.rowCount() + 1)

            # Добавление разделителя наборов в таблице
            for j in range(3):
                self.known_values_table.setItem(i + 1, j, QTableWidgetItem('Или' if j == 1 else ''))
                self.known_values_table.item(i + 1, j).setFlags(Qt.ItemIsEditable)
                self.known_values_table.item(i + 1, j).setForeground(QColor('black'))
            #
        # Удаление последнего разделителя #
        self.known_values_table.setRowCount(self.known_values_table.rowCount() - 1)
        #
    #

    # tab 3
    def show_experiment(self):
        """ Метод открывает сохраненные файлы для выбранного эксперимента """

        # Получение информации
        row_index = self.show_buttons.index(self.sender())
        experiment_name = self.results_table.item(row_index, 0).text()
        info_file, graph_file = get_data_from_db(MY_DB, 'results', 'info_file, graph_file',
                                                 {'name': [experiment_name]})[0]
        #

        # Получение абсолютных путей
        info_file = os.path.abspath(f'{DATA_DIR}/results/info_files/{info_file}')
        graph_file = os.path.abspath(f'{DATA_DIR}/results/graph_files/{graph_file}')
        #

        # Запуск файлов
        os.startfile(graph_file)
        time.sleep(0.5)  # Задержка открытия, чтобы текстовый файл был выше графика
        os.startfile(info_file)
        #

    def load_experiment(self):
        """ Метод загружает с файла информацию в tab Построение траектории """

        # Получение информации
        row_index = self.load_buttons.index(self.sender())
        experiment_name = self.results_table.item(row_index, 0).text()
        info_file, = get_data_from_db(MY_DB, 'results', 'info_file', {'name': [experiment_name]})[0]
        info_file = f'{DATA_DIR}/results/info_files/{info_file}'
        #

        self.load_from_file(info_file)  # Загрузка информации

        self.build_btn.click()  # Запуск строительства графика
        self.tabWidget.setCurrentIndex(0)  # Переключение на 1 tab

    def load_exp_table(self):
        names = [res[1] for res in get_data_from_db(MY_DB, 'results', '*')]  # Получение информации

        # Очистка таблицы и необходимых массивов
        self.results_table.setRowCount(0)
        self.show_buttons = []
        self.load_buttons = []
        self.delete_buttons = []
        #

        # Заполнение таблицы
        for i in range(len(names)):
            # Установка названия эксперимента
            self.results_table.setRowCount(self.results_table.rowCount() + 1)
            self.results_table.setItem(i, 0, QTableWidgetItem(names[i]))
            self.results_table.item(i, 0).setFlags(Qt.ItemIsEditable)
            self.results_table.item(i, 0).setForeground(QColor('black'))
            #

            # Установка кнопок взаимодействия
            show_btn = QPushButton()
            show_btn.setText('Просмотреть')
            show_btn.clicked.connect(self.show_experiment)

            load_btn = QPushButton()
            load_btn.setText('Загрузить')
            load_btn.clicked.connect(self.load_experiment)

            delete_btn = QPushButton()
            delete_btn.setText('Удалить')
            delete_btn.clicked.connect(self.delete_experiment)
            #

            # Добавление виджетов
            self.show_buttons.append(show_btn)
            self.load_buttons.append(load_btn)
            self.delete_buttons.append(delete_btn)

            self.results_table.setCellWidget(i, 1, show_btn)
            self.results_table.setCellWidget(i, 2, load_btn)
            self.results_table.setCellWidget(i, 3, delete_btn)
            #
        #

    def delete_experiment(self):
        """ Метод удаляет эксперимент из базы данных """

        # Получение информации
        delete_index = self.delete_buttons.index(self.sender())
        delete_name = self.results_table.item(delete_index, 0).text()

        info_file, graph_file = get_data_from_db(MY_DB, 'results', 'info_file, graph_file',
                                                 {'name': [delete_name]})[0]
        info_file = os.path.abspath(f'{DATA_DIR}/results/info_files/{info_file}')
        graph_file = os.path.abspath(f'{DATA_DIR}/results/graph_files/{graph_file}')
        #

        # Удаление файлов
        os.remove(info_file)
        os.remove(graph_file)
        #

        # Удаление из таблицы и массивов
        self.show_buttons.pop(delete_index)
        self.load_buttons.pop(delete_index)
        self.delete_buttons.pop(delete_index)
        self.results_table.removeRow(delete_index)
        #

        delete_data_from_db(MY_DB, 'results', {'name': [delete_name]})  # Удаление из базы данных
    #

    def resizeEvent(self, a0) -> None:
        """ Обновление положения графика и кнопок при изменении размеров окна """

        self.graph.move(self.width() - self.graph.width(), 0)

        # Сдвиг для кнопки "Построить" #
        shift_centre = self.graph.width() // 2 - self.build_btn.width() // 2
        self.build_btn.move(self.graph.x() + shift_centre, self.graph.height() + 25)

        # Сдвиг для кнопки "Загрузить" и "Пример файла" #
        shift = shift_centre - self.about_shot_btn.width() - 25
        self.load_btn.move(self.graph.x() + shift, self.graph.height() + 25)
        self.example_btn.move(self.graph.x() + shift - 5, self.graph.height() + 50)

        # Сдвиг для кнопки "О броске" #
        shift = shift_centre + self.about_shot_btn.width() + 25
        self.about_shot_btn.move(self.graph.x() + shift, self.graph.height() + 25)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    update_constants()  # Обновление констант

    wnd = MainWindow()
    wnd.show()

    sys.excepthook = except_hook
    sys.exit(app.exec())
