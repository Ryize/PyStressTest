import time
from statistics import mean
from typing import Optional, Union, Tuple

from matplotlib import pyplot as plt

from abstarct.monitor import AbstractMonitor
from abstarct.stress_test import AbstractStressTest


class BaseMonitor(AbstractMonitor):
    def __init__(self, stress: AbstractStressTest):
        self._stress = stress

    def start(self, timeout: Union[int, float] = 0.2) -> None:
        """
        Запускает тест.
        :param timeout: Union[int, float] (время задержки, используется при создании потоков и отправки запросов)
        :return: None
        """
        self._stress.auto_create_connection()
        for _ in self._stress.auto_get_stats(timeout):
            print(f'Всего запросов: {len(self._stress.stats)}')

    def set_params(self, kill: Optional[bool] = None, timeout: Optional[Union[float, int]] = None,
                   max_thread_count: Optional[int] = None, max_execution_time: Optional[int] = None) -> None:
        """
        Устанавливает параметры стресс-теста.
        :param kill: bool (True - убить потоки, False - продолжить тестирование)
        :param timeout: Union[int, float] (время задержки, используется при создании потоков и отправки запросов)
        :param max_thread_count: int (максимальное кол-во потоков,
        реальное кол-во может незначительно отличаться от заданного)
        :param max_execution_time: int (максимальное время выполнения теста)
        :return: None
        """
        self._stress.kill = kill or self._stress.kill
        self._stress.timeout = timeout or self._stress.timeout
        self._stress.max_thread_count = max_thread_count or self._stress.max_thread_count
        self._stress.max_execution_time = max_execution_time or self._stress.max_execution_time

    def stop(self) -> None:
        """
        Останавливает работу теста и запускает построение статистики.
        :return: None
        """
        self._stress.kill_all_connections()
        self.build_graph()


class ChartMonitor(BaseMonitor):
    def build_graph(self) -> None:
        """
        Построить статистику в виде графика. Используется matplotlib.
        Первый график - зависимость времени выполнения запроса от кол-ва запросов.
        Второй график - зависимость кол-ва ошибок от кол-ва запросов.
        :return: None
        """
        stats = sorted(self._stress.stats.items(), key=lambda i: i[0])
        x_time_request = list(map(lambda i: round(time.time() - i[0], 4), stats))
        y_time_request = list(map(lambda i: round(i[1], 4), stats))
        self._draw_plot(x_time_request, y_time_request, [2, 1, 1], 'Время отправки запроса')
        plt.ylabel('Время выполнения запроса')

        self._draw_plot(*self._get_x_y_error_coord(), [2, 1, 2], color='r')
        plt.xlabel('Время ошибки')
        plt.ylabel('Кол-во ошибок')
        plt.show()

    def _get_x_y_error_coord(self) -> Tuple[list, list]:
        """
        Получение кортежа с координатами ошибок x, y.
        tuple[0] - list (координата x)
        tuple[1] - list (координата y)
        В качестве координат x, идёт время, когда проищошла ошибка.
        В качестве координат y, идёт кол-во ошибок, которое проищошло за время указанное в x (по умолчанию за 1 секунду)
        :return: Tuple[list, list]
        """
        res = [[]]
        x_error = y_error = []
        if len(self._stress.errors) > 0:
            back = int(self._stress.errors[0][0])
            # Группируем ошибки. Ошибки за одну секунду будут в своём списке
            for i in self._stress.errors:
                i[0] = int(i[0])
                # Если время ошибки совпадает с предыдущим, добавляем в один список
                if i[0] == back:
                    res[-1].append(i)
                # Иначе создаём список с новым временем ошибки
                else:
                    res.append([i])
                    back = i[0]
            # Получаем время когда проихошла ошибка
            x_error = list(map(lambda el: round(time.time() - el, 4), [i[0][0] for i in res]))
            # Получаем кол-во ошибок
            y_error = [len(i) for i in res]
        return x_error, y_error

    def _draw_plot(self, x: list, y: list, coord: Optional[list] = None, title: Optional[str] = None,
                   color: str = 'b') -> None:
        """
        Строит график по указанным координатам x, y.
        :param x: list (координаты x (работает при условии len(x) == len(y)))
        :param y: list (координаты y (работает при условии len(x) == len(y)))
        :param coord: Optional[list] (координаты разбивания графика (matplotlib.subplot))
        :param title: Optional[str] (название графика (matplotlib.title))
        :param color: str (цвет графика)
        :return: None
        """
        if coord:
            plt.subplot(*coord)
        plt.plot(x, y, c=color)
        if title:
            plt.title(title)
        plt.ticklabel_format(useOffset=False)


class CMDMonitor(BaseMonitor):
    def start(self, timeout: Union[int, float] = 0.2) -> None:
        """
        Запускает тест, отобрадение статистики происходит в терминале.
        :param timeout: Union[int, float] (время задержки, используется при создании потоков и отправки запросов)
        :return: None
        """
        self._stress.auto_create_connection()
        for i in self._stress.auto_get_stats(0.2):
            if isinstance(i, int):
                continue
            print(f'Потоков: {len(self._stress.thread)}')
            print(f'Последние запросы: {len(i)}')
            print(f'Запросов всего: {len(self._stress.stats)}')
            print(f'Ошибок: {len(self._stress.errors)}', end='\n\n\n')

    def build_graph(self) -> None:
        """
        Строит график в терминале.
        Параметры вывода:
        1) Всего потоков
        2) Всего запросов
        3) Среднее время на запрос
        4) Всего ошибок
        :return: None
        """
        stats = self._stress.stats.items()
        average_time_per_request = mean([i[1] for i in stats])
        print(f'\n\n\nВсего потоков: {len(self._stress.thread)}')
        print(f'Всего запросов: {len(stats)}')
        print(f'Среднее время на запрос: {average_time_per_request}')
        print(f'Всего ошибок: {len(self._stress.errors)}', end='\n\n\n')
