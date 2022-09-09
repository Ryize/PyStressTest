"""
Здесь вы можете написать свой код для стресс проверки ресурса.
Пример программы:

if __name__ == '__main__':
    stress = StressTest('http://127.0.0.1:8000')
    stress.timeout = 0.5
    stress.max_execution_time = 60
    stress.max_thread_count = 100
    monitor = ChartMonitor(stress)
    monitor.start()
    monitor.build_graph()
"""

if __name__ == '__main__':
    from stress_test import StressTest
    from monitor import ChartMonitor

    stress = StressTest('http://127.0.0.1:8000')
    stress.timeout = 0.5
    stress.max_execution_time = 10
    stress.max_thread_count = 100
    monitor = ChartMonitor(stress)
    monitor.start()
    monitor.build_graph()
