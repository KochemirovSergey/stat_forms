#!/usr/bin/env python3
"""
Главный координатор системы анализа статистических форм
Управляет запуском и координацией всех компонентов системы
"""
import asyncio
import signal
import sys
import threading
import time
import argparse
import logging
import logging.config
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import subprocess
import psutil
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

# Импорт системной конфигурации
from system_config import (
    LOGGING_CONFIG, SYSTEM_COMPONENTS, HEALTH_CHECK_CONFIG, 
    SHUTDOWN_CONFIG, CLI_CONFIG, SYSTEM_INFO, load_neo4j_config,
    validate_system_config, get_system_status
)

# Настройка логирования
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('system_coordinator')

class SystemCoordinator:
    """Координатор системы для управления всеми компонентами"""
    
    def __init__(self):
        self.components: Dict[str, Any] = {}
        self.running = False
        self.shutdown_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.health_checks_enabled = True
        
    async def check_neo4j_connection(self) -> bool:
        """Проверка подключения к Neo4j"""
        try:
            from neo4j import GraphDatabase
            
            config = load_neo4j_config()
            driver = GraphDatabase.driver(
                config['NEO4J_URI'],
                auth=(config['NEO4J_USERNAME'], config['NEO4J_PASSWORD'])
            )
            
            # Проверяем подключение
            with driver.session(database=config['NEO4J_DATABASE']) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()['test']
                
            driver.close()
            
            if test_value == 1:
                logger.info("✅ Neo4j подключение успешно")
                return True
            else:
                logger.error("❌ Neo4j подключение неуспешно")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Neo4j: {e}")
            return False
    
    def check_required_files(self) -> bool:
        """Проверка наличия всех необходимых файлов"""
        try:
            missing_files = []
            missing_dirs = []
            
            # Проверяем файлы
            for file_path in HEALTH_CHECK_CONFIG['files']['required_files']:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            # Проверяем директории
            for dir_path in HEALTH_CHECK_CONFIG['files']['required_directories']:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)
            
            if missing_files:
                logger.error(f"❌ Отсутствуют файлы: {missing_files}")
                return False
                
            if missing_dirs:
                logger.error(f"❌ Отсутствуют директории: {missing_dirs}")
                return False
            
            logger.info("✅ Все необходимые файлы и директории найдены")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки файлов: {e}")
            return False
    
    def check_environment(self) -> bool:
        """Проверка переменных окружения"""
        try:
            import os
            
            missing_vars = []
            
            # Проверяем обязательные переменные
            for var in HEALTH_CHECK_CONFIG['environment']['required_env_vars']:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.error(f"❌ Отсутствуют переменные окружения: {missing_vars}")
                return False
            
            # Проверяем опциональные переменные
            optional_vars = HEALTH_CHECK_CONFIG['environment']['optional_env_vars']
            found_optional = [var for var in optional_vars if os.getenv(var)]
            
            logger.info(f"✅ Переменные окружения проверены")
            if found_optional:
                logger.info(f"📋 Найдены опциональные переменные: {found_optional}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки переменных окружения: {e}")
            return False
    
    async def system_health_check(self) -> bool:
        """Полная проверка готовности системы"""
        logger.info("🔍 Запуск проверки готовности системы...")
        
        checks = [
            ("Конфигурация системы", validate_system_config),
            ("Необходимые файлы", self.check_required_files),
            ("Переменные окружения", self.check_environment),
            ("Neo4j подключение", self.check_neo4j_connection)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                if result:
                    logger.info(f"✅ {check_name}: OK")
                else:
                    logger.error(f"❌ {check_name}: FAILED")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ {check_name}: ERROR - {e}")
                all_passed = False
        
        if all_passed:
            logger.info("🎉 Все проверки пройдены успешно!")
        else:
            logger.error("💥 Некоторые проверки не пройдены!")
        
        return all_passed
    
    async def start_telegram_bot(self) -> bool:
        """Запуск Telegram бота"""
        try:
            logger.info("🤖 Запуск Telegram бота...")
            
            # Импортируем и запускаем бот
            from tg_bot.telegram_bot import main as bot_main
            
            # Создаем задачу для бота
            bot_task = asyncio.create_task(bot_main())
            self.components['telegram_bot'] = {
                'task': bot_task,
                'status': 'running',
                'start_time': time.time()
            }
            
            logger.info("✅ Telegram бот запущен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
            return False
    
    def start_dashboard_server(self) -> bool:
        """Запуск Dashboard сервера в отдельном потоке"""
        try:
            logger.info("🌐 Запуск Dashboard сервера...")
            
            def run_dashboard():
                try:
                    from dashboard_server import app, init_visualizer, init_neo4j_matcher
                    import os
                    
                    # Инициализируем визуализатор
                    if not init_visualizer():
                        logger.error("❌ Не удалось инициализировать визуализатор")
                        return False
                    
                    # Инициализируем Neo4j матчер
                    if not init_neo4j_matcher():
                        logger.error("❌ Не удалось инициализировать Neo4j матчер")
                        return False
                    
                    # Запускаем сервер
                    config = SYSTEM_COMPONENTS['dashboard_server']
                    app.run(
                        host=config['host'],
                        port=config['port'],
                        debug=config['debug'],
                        use_reloader=False,  # Отключаем reloader для избежания конфликтов
                        threaded=True
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка в Dashboard сервере: {e}")
            
            # Запускаем в отдельном потоке
            dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
            dashboard_thread.start()
            
            self.components['dashboard_server'] = {
                'thread': dashboard_thread,
                'status': 'running',
                'start_time': time.time()
            }
            
            # Даем время на запуск
            time.sleep(2)
            
            logger.info("✅ Dashboard сервер запущен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Dashboard сервера: {e}")
            return False
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов для graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"📡 Получен сигнал {signum}, начинаем graceful shutdown...")
            self.shutdown_event.set()
            asyncio.create_task(self.shutdown())
        
        for sig_name in SHUTDOWN_CONFIG['signals']:
            if hasattr(signal, sig_name):
                signal.signal(getattr(signal, sig_name), signal_handler)
    
    async def shutdown(self):
        """Graceful shutdown всех компонентов"""
        if not self.running:
            return
        
        logger.info("🛑 Начинаем остановку системы...")
        self.running = False
        self.health_checks_enabled = False
        
        # Останавливаем компоненты
        shutdown_tasks = []
        
        # Останавливаем Telegram бота
        if 'telegram_bot' in self.components:
            component = self.components['telegram_bot']
            if 'task' in component and not component['task'].done():
                logger.info("🤖 Остановка Telegram бота...")
                component['task'].cancel()
                shutdown_tasks.append(component['task'])
        
        # Останавливаем Dashboard сервер
        if 'dashboard_server' in self.components:
            component = self.components['dashboard_server']
            logger.info("🌐 Остановка Dashboard сервера...")
            component['status'] = 'stopping'
        
        # Ждем завершения задач
        if shutdown_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*shutdown_tasks, return_exceptions=True),
                    timeout=SHUTDOWN_CONFIG['timeout']
                )
            except asyncio.TimeoutError:
                logger.warning("⚠️ Таймаут при остановке компонентов")
        
        # Закрываем executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ Система остановлена")
    
    async def start_system(self, components: Optional[List[str]] = None):
        """Запуск всей системы или отдельных компонентов"""
        try:
            self.running = True
            self.setup_signal_handlers()
            
            logger.info(f"🚀 Запуск системы: {SYSTEM_INFO['name']} v{SYSTEM_INFO['version']}")
            
            # Проверяем готовность системы
            if not await self.system_health_check():
                logger.error("💥 Система не готова к запуску!")
                return False
            
            # Определяем какие компоненты запускать
            if components is None:
                components = list(SYSTEM_COMPONENTS.keys())
            
            # Запускаем компоненты
            success = True
            
            if 'dashboard_server' in components:
                if not self.start_dashboard_server():
                    success = False
            
            if 'telegram_bot' in components:
                if not await self.start_telegram_bot():
                    success = False
            
            if not success:
                logger.error("💥 Не удалось запустить все компоненты!")
                await self.shutdown()
                return False
            
            logger.info("🎉 Все компоненты запущены успешно!")
            
            # Основной цикл работы
            try:
                while self.running and not self.shutdown_event.is_set():
                    await asyncio.sleep(1)
                    
                    # Проверяем статус компонентов
                    if self.health_checks_enabled:
                        await self.monitor_components()
                        
            except KeyboardInterrupt:
                logger.info("⌨️ Получен сигнал прерывания от клавиатуры")
            
            await self.shutdown()
            return True
            
        except Exception as e:
            logger.error(f"💥 Критическая ошибка системы: {e}")
            await self.shutdown()
            return False
    
    async def monitor_components(self):
        """Мониторинг состояния компонентов"""
        try:
            for name, component in self.components.items():
                if component['status'] == 'running':
                    # Проверяем Telegram бота
                    if name == 'telegram_bot' and 'task' in component:
                        if component['task'].done():
                            logger.warning(f"⚠️ {name} завершился неожиданно")
                            component['status'] = 'failed'
                    
                    # Проверяем Dashboard сервер
                    elif name == 'dashboard_server' and 'thread' in component:
                        if not component['thread'].is_alive():
                            logger.warning(f"⚠️ {name} завершился неожиданно")
                            component['status'] = 'failed'
                            
        except Exception as e:
            logger.error(f"❌ Ошибка мониторинга компонентов: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            'system_info': SYSTEM_INFO,
            'running': self.running,
            'components': {
                name: {
                    'status': comp.get('status', 'unknown'),
                    'start_time': comp.get('start_time'),
                    'uptime': time.time() - comp.get('start_time', time.time()) if comp.get('start_time') else 0
                }
                for name, comp in self.components.items()
            }
        }

async def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description=f"{SYSTEM_INFO['name']} v{SYSTEM_INFO['version']}"
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        default=CLI_CONFIG['default_command'],
        choices=CLI_CONFIG['commands'].keys(),
        help='Команда для выполнения'
    )
    
    parser.add_argument(
        '--components',
        nargs='+',
        choices=list(SYSTEM_COMPONENTS.keys()),
        help='Запустить только указанные компоненты'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включить отладочный режим'
    )
    
    args = parser.parse_args()
    
    # Настраиваем уровень логирования
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    coordinator = SystemCoordinator()
    
    try:
        if args.command == 'start':
            await coordinator.start_system(args.components)
            
        elif args.command == 'bot':
            await coordinator.start_system(['telegram_bot'])
            
        elif args.command == 'dashboard':
            await coordinator.start_system(['dashboard_server'])
            
        elif args.command == 'check':
            success = await coordinator.system_health_check()
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            status = coordinator.get_system_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
            
    except KeyboardInterrupt:
        logger.info("⌨️ Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Система остановлена пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)