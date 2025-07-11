"""
Системная конфигурация для координации всех компонентов
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Получаем абсолютный путь к директории проекта
PROJECT_ROOT = Path(__file__).parent.absolute()

# Настройки логирования
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'system.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': 'system_errors.log',
            'mode': 'a',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'telegram_bot': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'dashboard_server': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'system_coordinator': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

# Настройки компонентов системы
SYSTEM_COMPONENTS = {
    'telegram_bot': {
        'name': 'Telegram Bot',
        'module': 'tg_bot.telegram_bot',
        'main_function': 'main',
        'type': 'async',
        'required': True,
        'health_check': 'check_bot_health',
        'startup_timeout': 30,
        'shutdown_timeout': 10
    },
    'dashboard_server': {
        'name': 'Dashboard Server',
        'module': 'dashboard_server',
        'main_function': 'run_server',
        'type': 'sync',
        'required': True,
        'health_check': 'check_server_health',
        'startup_timeout': 20,
        'shutdown_timeout': 5,
        'host': '0.0.0.0',
        'port': int(os.environ.get('DASHBOARD_PORT', 5001)),
        'debug': os.environ.get('DEBUG', 'False').lower() == 'true'
    }
}

# Настройки Neo4j
NEO4J_CONFIG_PATH = PROJECT_ROOT / 'neo4j_config.json'

def load_neo4j_config() -> Dict[str, str]:
    """Загрузка конфигурации Neo4j"""
    try:
        with open(NEO4J_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Не удалось загрузить конфигурацию Neo4j: {e}")

# Настройки проверки готовности системы
HEALTH_CHECK_CONFIG = {
    'neo4j': {
        'timeout': 10,
        'retry_count': 3,
        'retry_delay': 2
    },
    'files': {
        'required_files': [
            'neo4j_config.json',
            'tg_bot/config.py',
            'dashboard_server.py',
            'requirements.txt'
        ],
        'required_directories': [
            'tg_bot',
            'templates',
            'static'
        ]
    },
    'environment': {
        'required_env_vars': [
            # Опциональные переменные окружения
        ],
        'optional_env_vars': [
            'BOT_TOKEN',
            'DASHBOARD_PORT',
            'DEBUG',
            'LANGCHAIN_API_KEY',
            'TAVILY_API_KEY'
        ]
    }
}

# Настройки graceful shutdown
SHUTDOWN_CONFIG = {
    'timeout': 30,  # Общий таймаут для завершения всех компонентов
    'force_timeout': 5,  # Таймаут для принудительного завершения
    'signals': ['SIGINT', 'SIGTERM']
}

# Настройки CLI
CLI_CONFIG = {
    'commands': {
        'start': 'Запустить все компоненты системы',
        'bot': 'Запустить только Telegram бота',
        'dashboard': 'Запустить только Dashboard сервер',
        'check': 'Проверить готовность системы',
        'status': 'Показать статус компонентов'
    },
    'default_command': 'start'
}

# Пути к файлам логов
LOG_FILES = {
    'system': PROJECT_ROOT / 'system.log',
    'errors': PROJECT_ROOT / 'system_errors.log',
    'bot': PROJECT_ROOT / 'bot.log',
    'dashboard': PROJECT_ROOT / 'dashboard_server.log'
}

# Настройки мониторинга
MONITORING_CONFIG = {
    'health_check_interval': 60,  # секунд
    'restart_on_failure': True,
    'max_restart_attempts': 3,
    'restart_delay': 10  # секунд
}

# Информация о системе
SYSTEM_INFO = {
    'name': 'Statistical Forms Analysis System',
    'version': '1.0.0',
    'description': 'Система анализа статистических форм с Telegram ботом и веб-дашбордом',
    'author': 'System Coordinator',
    'components': list(SYSTEM_COMPONENTS.keys())
}

def get_system_status() -> Dict[str, Any]:
    """Получение текущего статуса системы"""
    return {
        'system_info': SYSTEM_INFO,
        'components': SYSTEM_COMPONENTS,
        'log_files': {k: str(v) for k, v in LOG_FILES.items()},
        'project_root': str(PROJECT_ROOT)
    }

def validate_system_config() -> bool:
    """Валидация системной конфигурации"""
    try:
        # Проверяем наличие Neo4j конфигурации
        neo4j_config = load_neo4j_config()
        required_neo4j_keys = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'NEO4J_DATABASE']
        
        for key in required_neo4j_keys:
            if key not in neo4j_config:
                raise ValueError(f"Отсутствует обязательный ключ Neo4j: {key}")
        
        # Проверяем наличие обязательных файлов
        for file_path in HEALTH_CHECK_CONFIG['files']['required_files']:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"Отсутствует обязательный файл: {file_path}")
        
        # Проверяем наличие обязательных директорий
        for dir_path in HEALTH_CHECK_CONFIG['files']['required_directories']:
            full_path = PROJECT_ROOT / dir_path
            if not full_path.exists():
                raise FileNotFoundError(f"Отсутствует обязательная директория: {dir_path}")
        
        return True
        
    except Exception as e:
        logging.error(f"Ошибка валидации системной конфигурации: {e}")
        return False