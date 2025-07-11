#!/usr/bin/env python3
"""
Тесты производительности системы анализа статистических форм
Проверяет производительность всех компонентов под нагрузкой
"""
import asyncio
import sys
import time
import logging
import threading
import subprocess
import requests
import psutil
import json
import statistics
from pathlib import Path
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from dataclasses import dataclass
import gc

# Настройка логирования для тестов производительности
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_tests.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('performance_test')

@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    operation: str
    duration: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error_message: str = ""

class PerformanceTester:
    """Класс для тестирования производительности системы"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.dashboard_process = None
        self.test_queries = [
            "количество студентов",
            "численность преподавателей",
            "образовательные программы",
            "высшие учебные заведения",
            "научные исследования",
            "аспирантура и докторантура",
            "международное сотрудничество",
            "финансирование образования",
            "региональная статистика",
            "динамика показателей"
        ]
    
    def measure_performance(self, operation_name: str, func, *args, **kwargs) -> PerformanceMetrics:
        """Измерение производительности операции"""
        # Получаем начальные метрики системы
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        start_time = time.time()
        success = True
        error_message = ""
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = asyncio.run(func(*args, **kwargs))
            else:
                result = func(*args, **kwargs)
        except Exception as e:
            success = False
            error_message = str(e)
            result = None
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Получаем финальные метрики
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        memory_usage = final_memory - initial_memory
        cpu_usage = max(final_cpu - initial_cpu, 0)
        
        metrics = PerformanceMetrics(
            operation=operation_name,
            duration=duration,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            success=success,
            error_message=error_message
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def test_neo4j_query_performance(self) -> bool:
        """Тест производительности запросов к Neo4j"""
        try:
            from tg_bot.neo4j_matcher import Neo4jMatcher
            
            logger.info("🔍 Тестирование производительности Neo4j запросов...")
            
            matcher = Neo4jMatcher()
            durations = []
            
            # Тестируем множественные запросы
            for i, query in enumerate(self.test_queries):
                metrics = self.measure_performance(
                    f"neo4j_query_{i+1}",
                    matcher.find_matching_nodes,
                    query
                )
                durations.append(metrics.duration)
                
                if metrics.success:
                    logger.info(f"  Запрос {i+1}: {metrics.duration:.3f}s, память: {metrics.memory_usage:.1f}MB")
                else:
                    logger.error(f"  Запрос {i+1}: ОШИБКА - {metrics.error_message}")
            
            # Анализируем результаты
            if durations:
                avg_duration = statistics.mean(durations)
                max_duration = max(durations)
                min_duration = min(durations)
                
                logger.info(f"📊 Neo4j производительность:")
                logger.info(f"  Среднее время: {avg_duration:.3f}s")
                logger.info(f"  Максимальное время: {max_duration:.3f}s")
                logger.info(f"  Минимальное время: {min_duration:.3f}s")
                
                # Проверяем, что запросы выполняются достаточно быстро
                if avg_duration > 5.0:  # 5 секунд - максимальное приемлемое время
                    logger.warning("⚠️ Neo4j запросы выполняются медленно")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка в тесте производительности Neo4j: {e}")
            return False
    
    def test_csv_processing_performance(self) -> bool:
        """Тест производительности обработки CSV"""
        try:
            from tg_bot.excel_reader import ExcelReader
            from tg_bot.config import TABLES_CSV_PATH_2124, TABLES_CSV_PATH_1620
            
            logger.info("📊 Тестирование производительности обработки CSV...")
            
            if not Path(TABLES_CSV_PATH_2124).exists():
                logger.warning("CSV файл не найден, пропускаем тест")
                return True
            
            reader = ExcelReader()
            durations = []
            
            # Тестируем обработку CSV для разных запросов
            for i, query in enumerate(self.test_queries[:5]):  # Ограничиваем количество для CSV
                metrics = self.measure_performance(
                    f"csv_processing_{i+1}",
                    reader.search_data,
                    query,
                    TABLES_CSV_PATH_2124
                )
                durations.append(metrics.duration)
                
                if metrics.success:
                    logger.info(f"  CSV запрос {i+1}: {metrics.duration:.3f}s, память: {metrics.memory_usage:.1f}MB")
                else:
                    logger.error(f"  CSV запрос {i+1}: ОШИБКА - {metrics.error_message}")
            
            # Анализируем результаты
            if durations:
                avg_duration = statistics.mean(durations)
                logger.info(f"📊 CSV обработка - среднее время: {avg_duration:.3f}s")
                
                if avg_duration > 10.0:  # 10 секунд для CSV
                    logger.warning("⚠️ CSV обработка выполняется медленно")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка в тесте производительности CSV: {e}")
            return False
    
    def test_dashboard_response_time(self) -> bool:
        """Тест времени отклика Dashboard сервера"""
        try:
            logger.info("🌐 Тестирование производительности Dashboard сервера...")
            
            # Запускаем Dashboard сервер
            self.dashboard_process = subprocess.Popen([
                sys.executable, 'dashboard_server.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Ждем запуска
            time.sleep(5)
            
            base_url = 'http://localhost:5001'
            endpoints = [
                '/',
                '/api/status'
            ]
            
            response_times = []
            
            # Тестируем время отклика эндпоинтов
            for endpoint in endpoints:
                for i in range(5):  # 5 запросов к каждому эндпоинту
                    start_time = time.time()
                    try:
                        response = requests.get(f"{base_url}{endpoint}", timeout=10)
                        end_time = time.time()
                        
                        response_time = end_time - start_time
                        response_times.append(response_time)
                        
                        logger.info(f"  {endpoint} запрос {i+1}: {response_time:.3f}s, код: {response.status_code}")
                        
                    except requests.exceptions.RequestException as e:
                        logger.error(f"  {endpoint} запрос {i+1}: ОШИБКА - {e}")
            
            # Анализируем результаты
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                
                logger.info(f"📊 Dashboard производительность:")
                logger.info(f"  Среднее время отклика: {avg_response_time:.3f}s")
                logger.info(f"  Максимальное время отклика: {max_response_time:.3f}s")
                
                if avg_response_time > 2.0:  # 2 секунды максимум для веб-интерфейса
                    logger.warning("⚠️ Dashboard отвечает медленно")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка в тесте производительности Dashboard: {e}")
            return False
    
    def test_concurrent_requests(self) -> bool:
        """Тест производительности при конкурентных запросах"""
        try:
            logger.info("⚡ Тестирование производительности при конкурентных запросах...")
            
            from tg_bot.neo4j_matcher import Neo4jMatcher
            
            def single_query(query_id: int, query: str) -> Tuple[int, float, bool]:
                """Выполнение одного запроса"""
                start_time = time.time()
                try:
                    matcher = Neo4jMatcher()
                    result = matcher.find_matching_nodes(query)
                    success = True
                except Exception as e:
                    logger.error(f"Ошибка в конкурентном запросе {query_id}: {e}")
                    success = False
                
                duration = time.time() - start_time
                return query_id, duration, success
            
            # Запускаем конкурентные запросы
            num_concurrent = min(5, len(self.test_queries))  # Ограничиваем нагрузку
            
            with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = []
                
                for i in range(num_concurrent):
                    query = self.test_queries[i % len(self.test_queries)]
                    future = executor.submit(single_query, i, query)
                    futures.append(future)
                
                # Собираем результаты
                results = []
                for future in as_completed(futures):
                    query_id, duration, success = future.result()
                    results.append((query_id, duration, success))
                    logger.info(f"  Конкурентный запрос {query_id}: {duration:.3f}s, успех: {success}")
            
            # Анализируем результаты
            successful_results = [duration for _, duration, success in results if success]
            
            if successful_results:
                avg_concurrent_time = statistics.mean(successful_results)
                max_concurrent_time = max(successful_results)
                success_rate = len(successful_results) / len(results) * 100
                
                logger.info(f"📊 Конкурентные запросы:")
                logger.info(f"  Среднее время: {avg_concurrent_time:.3f}s")
                logger.info(f"  Максимальное время: {max_concurrent_time:.3f}s")
                logger.info(f"  Успешность: {success_rate:.1f}%")
                
                if success_rate < 80:  # Минимум 80% успешных запросов
                    logger.warning("⚠️ Низкая успешность конкурентных запросов")
                    return False
                
                if avg_concurrent_time > 10.0:  # 10 секунд максимум при конкуренции
                    logger.warning("⚠️ Конкурентные запросы выполняются медленно")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка в тесте конкурентных запросов: {e}")
            return False
    
    def test_memory_usage(self) -> bool:
        """Тест использования памяти"""
        try:
            logger.info("💾 Тестирование использования памяти...")
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            logger.info(f"  Начальное использование памяти: {initial_memory:.1f}MB")
            
            # Выполняем операции, потребляющие память
            from tg_bot.neo4j_matcher import Neo4jMatcher
            from tg_bot.excel_reader import ExcelReader
            
            # Создаем множественные объекты
            matchers = []
            readers = []
            
            for i in range(10):  # Создаем 10 объектов каждого типа
                try:
                    matcher = Neo4jMatcher()
                    matchers.append(matcher)
                    
                    reader = ExcelReader()
                    readers.append(reader)
                    
                    # Выполняем запросы
                    if i < len(self.test_queries):
                        matcher.find_matching_nodes(self.test_queries[i])
                    
                except Exception as e:
                    logger.warning(f"Ошибка при создании объекта {i}: {e}")
            
            # Проверяем использование памяти
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            logger.info(f"  Пиковое использование памяти: {peak_memory:.1f}MB")
            logger.info(f"  Увеличение памяти: {memory_increase:.1f}MB")
            
            # Очищаем объекты
            del matchers
            del readers
            gc.collect()
            
            # Проверяем память после очистки
            time.sleep(2)  # Даем время на очистку
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            logger.info(f"  Память после очистки: {final_memory:.1f}MB")
            
            # Проверяем, что память не растет неконтролируемо
            if memory_increase > 500:  # 500MB максимум
                logger.warning("⚠️ Высокое потребление памяти")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка в тесте использования памяти: {e}")
            return False
    
    def test_system_resources(self) -> bool:
        """Тест системных ресурсов"""
        try:
            logger.info("🖥️ Тестирование системных ресурсов...")
            
            # CPU использование
            cpu_percent = psutil.cpu_percent(interval=1)
            logger.info(f"  CPU использование: {cpu_percent:.1f}%")
            
            # Память системы
            memory = psutil.virtual_memory()
            logger.info(f"  Системная память: {memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f}GB из {memory.total/1024/1024/1024:.1f}GB)")
            
            # Дисковое пространство
            disk = psutil.disk_usage('.')
            logger.info(f"  Дисковое пространство: {disk.percent:.1f}% ({disk.used/1024/1024/1024:.1f}GB из {disk.total/1024/1024/1024:.1f}GB)")
            
            # Проверяем критические пороги
            if memory.percent > 90:
                logger.warning("⚠️ Высокое использование системной памяти")
                return False
            
            if disk.percent > 95:
                logger.warning("⚠️ Мало свободного места на диске")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка в тесте системных ресурсов: {e}")
            return False
    
    def cleanup(self):
        """Очистка после тестов"""
        try:
            if self.dashboard_process:
                self.dashboard_process.terminate()
                try:
                    self.dashboard_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.dashboard_process.kill()
                    
        except Exception as e:
            logger.error(f"Ошибка при очистке: {e}")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Генерация отчета о производительности"""
        if not self.metrics:
            return {"error": "Нет данных для отчета"}
        
        # Группируем метрики по операциям
        operations = {}
        for metric in self.metrics:
            op_type = metric.operation.split('_')[0]
            if op_type not in operations:
                operations[op_type] = []
            operations[op_type].append(metric)
        
        report = {
            "summary": {
                "total_operations": len(self.metrics),
                "successful_operations": sum(1 for m in self.metrics if m.success),
                "failed_operations": sum(1 for m in self.metrics if not m.success),
                "total_duration": sum(m.duration for m in self.metrics),
                "average_duration": statistics.mean([m.duration for m in self.metrics]),
                "total_memory_usage": sum(m.memory_usage for m in self.metrics)
            },
            "operations": {}
        }
        
        # Анализируем каждый тип операций
        for op_type, metrics in operations.items():
            durations = [m.duration for m in metrics if m.success]
            memory_usage = [m.memory_usage for m in metrics if m.success]
            
            if durations:
                report["operations"][op_type] = {
                    "count": len(metrics),
                    "success_rate": len(durations) / len(metrics) * 100,
                    "avg_duration": statistics.mean(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "avg_memory_usage": statistics.mean(memory_usage) if memory_usage else 0
                }
        
        return report
    
    async def run_all_performance_tests(self):
        """Запуск всех тестов производительности"""
        logger.info("🚀 Запуск тестирования производительности...")
        logger.info("=" * 80)
        
        tests = [
            ("Neo4j запросы", self.test_neo4j_query_performance),
            ("Обработка CSV", self.test_csv_processing_performance),
            ("Dashboard сервер", self.test_dashboard_response_time),
            ("Конкурентные запросы", self.test_concurrent_requests),
            ("Использование памяти", self.test_memory_usage),
            ("Системные ресурсы", self.test_system_resources)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Тест производительности: {test_name}")
            
            try:
                result = test_func()
                if result:
                    logger.info(f"✅ {test_name}: PASSED")
                    passed_tests += 1
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"💥 {test_name}: ERROR - {e}")
            
            time.sleep(2)  # Пауза между тестами
        
        # Очистка
        self.cleanup()
        
        # Генерируем отчет
        report = self.generate_performance_report()
        
        # Сохраняем отчет
        with open('performance_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Выводим результаты
        logger.info("=" * 80)
        logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ПРОИЗВОДИТЕЛЬНОСТИ:")
        logger.info(f"✅ Пройдено: {passed_tests}/{total_tests}")
        logger.info(f"❌ Провалено: {total_tests - passed_tests}/{total_tests}")
        
        if "summary" in report:
            summary = report["summary"]
            logger.info(f"📈 Общая статистика:")
            logger.info(f"  Всего операций: {summary['total_operations']}")
            logger.info(f"  Успешных операций: {summary['successful_operations']}")
            logger.info(f"  Среднее время операции: {summary['average_duration']:.3f}s")
            logger.info(f"  Общее использование памяти: {summary['total_memory_usage']:.1f}MB")
        
        logger.info("📄 Подробный отчет сохранен в performance_report.json")
        
        if passed_tests == total_tests:
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ ПРОЙДЕНЫ!")
            return True
        else:
            logger.error("💥 НЕКОТОРЫЕ ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ НЕ ПРОЙДЕНЫ!")
            return False

def main():
    """Главная функция"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ                     ║
║                    Система анализа статистических форм                      ║
║                            Нагрузочные тесты                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    tester = PerformanceTester()
    
    try:
        success = asyncio.run(tester.run_all_performance_tests())
        
        if success:
            print("\n🎉 Все тесты производительности пройдены успешно!")
            print("💡 Система показывает хорошую производительность!")
            sys.exit(0)
        else:
            print("\n💥 Обнаружены проблемы с производительностью!")
            print("💡 Проверьте отчет и оптимизируйте систему")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⌨️ Тестирование прервано пользователем")
        tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка при тестировании производительности: {e}")
        tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()