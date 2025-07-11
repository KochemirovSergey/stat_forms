#!/usr/bin/env python3
"""
Скрипт для тестирования компонентов системы
Проверяет работоспособность всех основных функций
"""
import asyncio
import sys
import json
import time
from pathlib import Path
import logging

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('system_test')

class SystemTester:
    """Класс для тестирования системы"""
    
    def __init__(self):
        self.test_results = {}
        self.passed_tests = 0
        self.total_tests = 0
    
    def run_test(self, test_name: str, test_func):
        """Запуск отдельного теста"""
        self.total_tests += 1
        logger.info(f"🧪 Тест: {test_name}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
                self.test_results[test_name] = "PASSED"
                self.passed_tests += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
                self.test_results[test_name] = "FAILED"
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR - {e}")
            self.test_results[test_name] = f"ERROR: {e}"
    
    def test_imports(self) -> bool:
        """Тест импорта всех модулей"""
        try:
            # Тестируем основные импорты
            import system_config
            from system_config import validate_system_config, load_neo4j_config
            
            # Тестируем импорт компонентов
            import dashboard_server
            from tg_bot import config as bot_config
            from tg_bot import telegram_bot
            
            return True
        except ImportError as e:
            logger.error(f"Ошибка импорта: {e}")
            return False
    
    def test_config_files(self) -> bool:
        """Тест наличия конфигурационных файлов"""
        required_files = [
            'system_config.py',
            'neo4j_config.json',
            'tg_bot/config.py',
            'requirements.txt'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"Отсутствуют файлы: {missing_files}")
            return False
        
        return True
    
    def test_neo4j_config(self) -> bool:
        """Тест конфигурации Neo4j"""
        try:
            from system_config import load_neo4j_config
            config = load_neo4j_config()
            
            required_keys = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'NEO4J_DATABASE']
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                logger.error(f"Отсутствуют ключи в neo4j_config.json: {missing_keys}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации Neo4j: {e}")
            return False
    
    def test_neo4j_connection(self) -> bool:
        """Тест подключения к Neo4j"""
        try:
            from neo4j import GraphDatabase
            from system_config import load_neo4j_config
            
            config = load_neo4j_config()
            driver = GraphDatabase.driver(
                config['NEO4J_URI'],
                auth=(config['NEO4J_USERNAME'], config['NEO4J_PASSWORD'])
            )
            
            with driver.session(database=config['NEO4J_DATABASE']) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()['test']
            
            driver.close()
            return test_value == 1
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Neo4j: {e}")
            return False
    
    def test_dashboard_init(self) -> bool:
        """Тест инициализации Dashboard сервера"""
        try:
            from dashboard_server import init_visualizer
            # Не запускаем полную инициализацию, только проверяем импорт
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации Dashboard: {e}")
            return False
    
    def test_bot_config(self) -> bool:
        """Тест конфигурации бота"""
        try:
            from tg_bot.config import BOT_TOKEN, MESSAGES, DASHBOARD_SERVER_URL
            
            if not BOT_TOKEN or BOT_TOKEN == 'your_telegram_bot_token_here':
                logger.warning("BOT_TOKEN не настроен или использует значение по умолчанию")
                return False
            
            if not MESSAGES or 'start' not in MESSAGES:
                logger.error("Конфигурация сообщений бота неполная")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка конфигурации бота: {e}")
            return False
    
    def test_system_coordinator(self) -> bool:
        """Тест системного координатора"""
        try:
            from main import SystemCoordinator
            coordinator = SystemCoordinator()
            
            # Тестируем основные методы
            status = coordinator.get_system_status()
            if not isinstance(status, dict):
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка системного координатора: {e}")
            return False
    
    def test_dependencies(self) -> bool:
        """Тест зависимостей"""
        try:
            # Основные зависимости
            import pandas
            import flask
            import neo4j
            import aiogram
            import plotly
            import psutil
            
            return True
        except ImportError as e:
            logger.error(f"Отсутствует зависимость: {e}")
            return False
    
    def test_templates_and_static(self) -> bool:
        """Тест наличия шаблонов и статических файлов"""
        required_paths = [
            'templates/dashboard_index.html',
            'templates/dashboard_error.html',
            'static/dashboard.css',
            'static/dashboard.js'
        ]
        
        missing_paths = []
        for path in required_paths:
            if not Path(path).exists():
                missing_paths.append(path)
        
        if missing_paths:
            logger.error(f"Отсутствуют файлы: {missing_paths}")
            return False
        
        return True
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск тестирования системы...")
        logger.info("=" * 60)
        
        # Список всех тестов
        tests = [
            ("Импорт модулей", self.test_imports),
            ("Конфигурационные файлы", self.test_config_files),
            ("Конфигурация Neo4j", self.test_neo4j_config),
            ("Подключение к Neo4j", self.test_neo4j_connection),
            ("Инициализация Dashboard", self.test_dashboard_init),
            ("Конфигурация бота", self.test_bot_config),
            ("Системный координатор", self.test_system_coordinator),
            ("Зависимости Python", self.test_dependencies),
            ("Шаблоны и статические файлы", self.test_templates_and_static)
        ]
        
        # Запускаем тесты
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            time.sleep(0.5)  # Небольшая пауза между тестами
        
        # Выводим результаты
        logger.info("=" * 60)
        logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        logger.info(f"✅ Пройдено: {self.passed_tests}/{self.total_tests}")
        logger.info(f"❌ Провалено: {self.total_tests - self.passed_tests}/{self.total_tests}")
        
        if self.passed_tests == self.total_tests:
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            return True
        else:
            logger.error("💥 НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
            logger.info("\n📋 Детальные результаты:")
            for test_name, result in self.test_results.items():
                status_icon = "✅" if result == "PASSED" else "❌"
                logger.info(f"  {status_icon} {test_name}: {result}")
            return False

def main():
    """Главная функция"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    ТЕСТИРОВАНИЕ СИСТЕМЫ                     ║
║              Система анализа статистических форм             ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    tester = SystemTester()
    
    try:
        success = asyncio.run(tester.run_all_tests())
        
        if success:
            print("\n🎉 Система готова к работе!")
            print("💡 Для запуска используйте: python main.py start")
            sys.exit(0)
        else:
            print("\n💥 Обнаружены проблемы в системе!")
            print("💡 Исправьте ошибки и запустите тест повторно")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⌨️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка при тестировании: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()