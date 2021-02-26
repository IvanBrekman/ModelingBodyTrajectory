from database_requests import get_data_from_db

DATA_DIR = "resources"
MY_DB = f"{DATA_DIR}/database/results.db"

CONSTANTS = {
    'g': 10,
    'graph_time_ms': 2_000,
    'is_animated': 1
}

y0_const = 0
delete_char = chr(10_005)


def update_constants():
    """ Обновление глобального словаря констант """

    for param, value in get_data_from_db(MY_DB, 'settings', 'param, value'):
        CONSTANTS[param] = value
