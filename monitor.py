import time
from typing import Optional, Union, Tuple

from matplotlib import pyplot as plt

from abstarct.monitor import AbstractMonitor
from abstarct.stress_test import AbstractStressTest


class BaseMonitor(AbstractMonitor):
    def __init__(self, stress: AbstractStressTest):
        self._stress = stress

    def start(self, timeout: Union[int, float] = 0.2):
        self._stress.auto_create_connection()
        for _ in self._stress.auto_get_stats(timeout):
            print(f'Запросов всего: {len(self._stress.stats)}')

    def set_params(self, kill: Optional[bool] = None, timeout: Optional[Union[float, int]] = None,
                   max_thread_count: Optional[int] = None, max_execution_time: Optional[int] = None):
        self._stress.kill = kill or self._stress.kill
        self._stress.timeout = timeout or self._stress.timeout
        self._stress.max_thread_count = max_thread_count or self._stress.max_thread_count
        self._stress.max_execution_time = max_execution_time or self._stress.max_execution_time

    def stop(self):
        self._stress.kill_all_connections()
        self.build_graph()


class ChartMonitor(BaseMonitor):
    def build_graph(self):
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
            x_error = list(map(lambda i: round(time.time() - i, 4), [i[0][0] for i in res]))
            # Получаем кол-во ошибок
            y_error = [len(i) for i in res]
        return x_error, y_error

    def _draw_plot(self, x: list, y: list, coord: Optional[list] = None, title: Optional[str] = None, color: str = 'b'):
        if coord:
            plt.subplot(*coord)
        plt.plot(x, y, c=color)
        if title:
            plt.title(title)
        plt.ticklabel_format(useOffset=False)


class CMDMonitor(BaseMonitor):
    def start(self, timeout: Union[int, float] = 0.2):
        self._stress.auto_create_connection()
        for i in self._stress.auto_get_stats(0.2):
            if isinstance(i, int):
                continue
            print(f'Потоков: {len(self._stress.thread)}')
            print(f'Последние запросы: {len(i)}')
            print(f'Запросов всего: {len(self._stress.stats)}')
            print(f'Ошибок: {len(self._stress.errors)}', end='\n\n\n')

    def build_graph(self):
        stats = self._stress.stats.items()
        total_runtime = 0
        for i in stats:
            total_runtime += i[1]
        print(f'\n\n\nВсего потоков: {len(self._stress.thread)}')
        print(f'Всего запросов: {len(stats)}')
        print(f'Среднее время на запрос: {len(stats) / total_runtime}')
        print(f'Всего ошибок: {len(self._stress.errors)}', end='\n\n\n')
