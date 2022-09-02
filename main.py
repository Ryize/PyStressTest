"""
Здесь вы можете написать свой код для стресс проверки ресурса.
Пример программы:

if __name__ == '__main__':
stress = StressTest('https://coursemc.space/api/v1/schedule/')
stress.timeout = 0.1
stress.max_thread_count = 100
stress.auto_create_connection()
for i in stress.auto_get_stats(0.2):
    print(f'Потоков: {len(stress.thread)}')
    print(f'Последние запросы: {len(i)}')
    print(f'Запросов всего: {len(stress.stats)}')
    print(f'Ошибок: {len(stress.errors)}', end='\n\n\n')
"""