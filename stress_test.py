import time
import threading
import warnings
from typing import Optional, NoReturn, Union

import requests

from abstarct.stress_test import AbstractStressTest


class StressTest(AbstractStressTest):
    """
    Класс для стресс-тестирования интернет-ресурсов.
    (с помощью отправки большого кол-ва запросов и проверки,
    через сколько ресурс перестанет отвечать).
    Имеется возможность ручного и автоматического создания потоков для отправки запросов.
    Есть встроенная автоматическая и ручная статистика.
    """

    def __init__(self, host: str = '127.0.0.1'):
        """
        :param host: str. Хост куда будут отправляться запросы
        :param _func_increase_connections: Функция отвечающая за кол-во потоков,
        которое необходимо создать. По умолчанию + 5%
        :param _kill: bool. При значении True потоки перестанут отправлять запросы
        :param _thread: list. Список с потоками (threading.Thread)
        :param _stats: dict. Словарь, в котором:
        key - Время добавления в словарь
        value - За сколько ресурс обработал запрос (время)
        :param _errors: list. Список с ошибками.
        При использовании auto_get_stats, будет отчищаться после каждого успешного запроса.
        [0] - Время ошибки
        [1] - Список с потоками (self._thread)
        [2] - Список с запросами (self._stats)
        :param _timeout: int. Задержка. Используется:
        1) При создании потоков;
        2) При отправке запросов.
        :param max_thread_count: int. Максимальное кол-во создаваемых потоков (не менее 20).
        Реальное кол-во потоков может быть незначительно больше указанного.
        """
        self._host = host
        self._func_increase_connections = lambda count_con: int(count_con / 100 * 5)
        self._kill = False
        self._thread = []
        self._stats = {}
        self._errors = []
        self._timeout = 3
        self._max_thread_count = 99999
        self._time_start = 0
        self._previous_count_errors = 0
        self._max_execution_time = 60 * 60 * 24 * 31  # 1 месяц

    def auto_create_connection(self, timeout: Optional[Union[int, float]] = None) -> None:
        """
        Автоматическое создание соединений к ресурсу.
        :return: None
        """
        self._time_start = time.time()
        th = threading.Thread(target=self._auto_create_connection, args=(timeout or self.timeout,))
        th.start()

    def auto_get_stats(self, timeout: Union[int, float] = 5) -> Union[list, int]:
        """
        Метод для автоматического получения статистики по работе класса.
        В случае убийства всех запросов или возникновения ошибки, метод сообщит об этом
        с помощью warnings.warn.
        Если произошло событие (был отправлен запрос), вернёт stats с последними событиями
        (см. в __init__ расшифровку stats).
        Время задержки перед каждыми сбором статистики определяется передаваемым timeout.
        :param max_thread_count: int (максимальное кол-во поток, приоритетнее чем self._max_thread_count)
        :param timeout: Union[int, float]
        :return: list
        """
        previous_count_connection = len(self.stats)
        while True:
            if self.kill:
                warnings.warn('Все соединения убиты!')
                break
            if time.time() > self._time_start + self._max_execution_time:
                print(f'Время выполнения теста закончилось.\nВыполнялся: {self._max_execution_time} секунд.')
                self.kill_all_connections()
            error_quantity = self._get_last_number_errors()
            if error_quantity:
                warnings.warn(f"Прозошла(и) {error_quantity} ошибок!")
                yield error_quantity
            if previous_count_connection == len(self.stats):
                continue
            yield list(self._stats.items())[previous_count_connection:]
            previous_count_connection = len(self.stats)
            time.sleep(timeout)

    def create_connection(self, connection_type: str = 'GET') -> None:
        """
        Используется для создания соединения.
        Можно создавать несколько одновременных соединений, так как используются потоки.
        При вызове автоматически добавляет поток в список threads.
        :param connection_type:
        :return:
        """
        th = threading.Thread(target=self._start_connection_stress_test, args=(connection_type,))
        self._thread.append(th)
        th.start()

    def set_increase_connections(self, func) -> None:
        """
        Устанавливает функцию для увелечения кол-ва потоков.
        :param func: function (Любая функция принимающая 1 параметр
        (текущее кол-во потоков и возвращающая число))
        :return: int (Число потоков, которое необходимо создать, 0 - допускается)
        """
        self._func_increase_connections = func

    def kill_all_connections(self) -> None:
        """
        Закрывает все соединения.
        :return: None
        """
        self._kill = True

    def _start_connection_stress_test(self, connection_type: str) -> None:
        """
        Отправка запросов, с задержкой указанной в self._timeout.
        Если соединения убиты или словарь self._errors содержит более 250 ошибок,
        отправка запросов прекращается.
        Добавляет запрос в self._errors, если возникла ConnectionError
        или код ответа от сервера != 200.
        :param connection_type: str (тип запроса 'GET', 'POST' и т.д.)
        :return: None
        """
        while not self._kill:
            func = requests.request
            kwargs = {'method': connection_type, 'url': self._host}
            time_now = time.time()
            try:
                response, runtime = self._get_runtime(func, **kwargs)
            except requests.ConnectionError:
                self._errors.append([time.time(), len(self._thread), len(self._stats)])
                continue
            self._stats[time_now - runtime] = runtime
            self._check_response_status_code(response)
            time.sleep(self._timeout)

    def _check_response_status_code(self, response) -> None:
        """
        Если код ответа != 200, записывает в self._errors
        (см. в __init__, что записывается в self._errors).
        :param response:
        :return:
        """
        if response.status_code != 200:
            self._errors.append([time.time(), len(self._thread), len(self._stats)])

    def _auto_create_connection(self, timeout: int) -> None:
        """
        Автоматически создаёт 20 потоков,
        после чего создаёт их по правилу функции self._func_increase_connections.
        Если потоки убиты (self._kill = True), прекращает созание потоков
        :return: None
        """
        for _ in range(20):
            self.create_connection()
        while not self._kill:
            if len(self.thread) <= self.max_thread_count:
                for _ in range(self._func_increase_connections(len(self._thread))):
                    self.create_connection()
            time.sleep(timeout)

    @staticmethod
    def _get_runtime(func, *args, **kwargs) -> tuple:
        """
        Возвращает результат запроса и время, за которое этот запрос был выполнен.
        :param func: Любая функция (она и будет запускаться).
        :param args: Аргументы передаваемые в функцию.
        :param kwargs: Именованные аргументы передаваемые в функцию.
        :return: tuple (первый параметр - результат выполнения функции,
        второй параметр - время выполнения в секундах)
        """
        time_start = time.time()
        response = func(*args, **kwargs)
        return response, time.time() - time_start

    def _get_last_number_errors(self) -> int:
        """
        Получить последние ошибки.
        :return: None
        """
        result = len(self._errors) - self._previous_count_errors
        self._previous_count_errors = len(self._errors)
        return result

    @property
    def thread(self) -> list:
        return self._thread

    @property
    def stats(self) -> dict:
        return self._stats

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, value: Union[int, float]) -> Optional[NoReturn]:
        """
        Устанавливает переменную _timeout.
        Значение должны быть int|float и > 0.
        :param value: Union[int, float]
        :return: None
        """
        if not isinstance(value, (int, float)) or value != abs(value):
            raise ValueError('Задержка должна быть числом (int, float) > 0')
        self._timeout = value

    @property
    def max_execution_time(self) -> Union[int, float]:
        return self._max_execution_time

    @max_execution_time.setter
    def max_execution_time(self, value: Union[int, float]) -> None:
        """
        Устанавливает максимальное время тестирования.
        :param value: Union[int, float](value >= 0)
        :return: None
        """
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError('Значение max_execution_time может быть только типа int, float > 0')
        self._max_execution_time = value

    @property
    def max_thread_count(self):
        return self._max_thread_count

    @max_thread_count.setter
    def max_thread_count(self, value: int):
        """
        Устанавливает максимальное кол-во потоков.
        :param value: int (value > 20)
        :return: None
        """
        if not isinstance(value, int) or value != abs(value) or value < 20:
            raise ValueError('Максимальное кол-во потоков должно быть числом (int) > 20')
        self._max_thread_count = value

    @property
    def kill(self):
        return self._kill

    @kill.setter
    def kill(self, value: bool) -> Optional[NoReturn]:
        """
        Устанавливает параметр _kill.
        Если = True, запросы перестанут посылаться.
        :param value: bool
        :return: None
        """
        if not isinstance(value, bool):
            raise ValueError('Значение kill может быть только типа bool')
        self._kill = value

    @property
    def errors(self):
        return self._errors
