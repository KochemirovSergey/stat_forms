#!/usr/bin/env python3
"""
Скрипт для первоначальной настройки системы анализа статистических форм
Автоматизирует процесс установки и конфигурации
"""
import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any

def print_header():
    """Вывод заголовка установки"""
    header = """
╔══════════════════════════════════════════════════════════════╗
║                    УСТАНОВКА СИСТЕМЫ                        ║
║              Система анализа статистических форм             ║
║                           v1.0.0                            ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(header)

def check_python_version() -> bool:
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"   Текущая версия: {sys.version}")
        return False
    print(f"✅ Python версия: {sys.version.split()[0]}")
    return True

def install_dependencies() -> bool:
    """Установка зависимостей"""
    print("\n📦 Установка зависимостей Python...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True, capture_output=True)
        
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        
        print("✅ Зависимости установлены успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def setup_neo4j_config() -> bool:
    """Настройка конфигурации Neo4j"""
    print("\n🗄️ Настройка конфигурации Neo4j...")
    
    config_file = Path("neo4j_config.json")
    
    if config_file.exists():
        print("⚠️ Файл neo4j_config.json уже существует")
        choice = input("Хотите перенастроить? (y/N): ").strip().lower()
        if choice != 'y':
            print("✅ Используется существующая конфигурация Neo4j")
            return True
    
    print("\n📝 Введите данные для подключения к Neo4j:")
    
    neo4j_uri = input("Neo4j URI (например, neo4j+s://xxx.databases.neo4j.io): ").strip()
    if not neo4j_uri:
        print("❌ URI не может быть пустым")
        return False
    
    neo4j_username = input("Имя пользователя (по умолчанию 'neo4j'): ").strip() or "neo4j"
    
    neo4j_password = input("Пароль: ").strip()
    if not neo4j_password:
        print("❌ Пароль не может быть пустым")
        return False
    
    neo4j_database = input("База данных (по умолчанию 'neo4j'): ").strip() or "neo4j"
    
    config = {
        "NEO4J_URI": neo4j_uri,
        "NEO4J_USERNAME": neo4j_username,
        "NEO4J_PASSWORD": neo4j_password,
        "NEO4J_DATABASE": neo4j_database
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Конфигурация Neo4j сохранена")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения конфигурации: {e}")
        return False

def setup_env_file() -> bool:
    """Настройка файла переменных окружения"""
    print("\n🔧 Настройка переменных окружения...")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️ Файл .env уже существует")
        choice = input("Хотите перенастроить? (y/N): ").strip().lower()
        if choice != 'y':
            print("✅ Используется существующий файл .env")
            return True
    
    print("\n📝 Введите настройки (оставьте пустым для пропуска):")
    
    bot_token = input("Telegram Bot Token: ").strip()
    dashboard_port = input("Порт Dashboard сервера (по умолчанию 5001): ").strip() or "5001"
    debug_mode = input("Режим отладки (true/false, по умолчанию false): ").strip() or "false"
    
    # Опциональные настройки
    print("\n🔑 Опциональные API ключи:")
    langchain_key = input("LangChain API Key (опционально): ").strip()
    tavily_key = input("Tavily API Key (опционально): ").strip()
    openai_key = input("OpenAI API Key (опционально): ").strip()
    
    env_content = f"""# Конфигурация системы анализа статистических форм
# Сгенерировано автоматически

# Telegram Bot
BOT_TOKEN={bot_token}

# Dashboard Server
DASHBOARD_PORT={dashboard_port}
DEBUG={debug_mode}

# Flask
SECRET_KEY=stat_forms_secret_key_{hash(str(Path.cwd()))}
"""
    
    if langchain_key:
        env_content += f"""
# LangChain
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY={langchain_key}
LANGCHAIN_PROJECT=stat_forms_project
"""
    
    if tavily_key:
        env_content += f"""
# Tavily Search
TAVILY_API_KEY={tavily_key}
"""
    
    if openai_key:
        env_content += f"""
# OpenAI
OPENAI_API_KEY={openai_key}
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Файл .env создан")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания файла .env: {e}")
        return False

def test_neo4j_connection() -> bool:
    """Тест подключения к Neo4j"""
    print("\n🔍 Тестирование подключения к Neo4j...")
    
    try:
        from neo4j import GraphDatabase
        
        with open("neo4j_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        driver = GraphDatabase.driver(
            config['NEO4J_URI'],
            auth=(config['NEO4J_USERNAME'], config['NEO4J_PASSWORD'])
        )
        
        with driver.session(database=config['NEO4J_DATABASE']) as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()['test']
        
        driver.close()
        
        if test_value == 1:
            print("✅ Подключение к Neo4j успешно")
            return True
        else:
            print("❌ Подключение к Neo4j неуспешно")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Neo4j: {e}")
        return False

def create_startup_scripts() -> bool:
    """Создание скриптов для запуска"""
    print("\n📜 Создание скриптов запуска...")
    
    # Скрипт для Windows
    windows_script = """@echo off
echo Starting Statistical Forms Analysis System...
python main.py start
pause
"""
    
    # Скрипт для Unix/Linux/macOS
    unix_script = """#!/bin/bash
echo "Starting Statistical Forms Analysis System..."
python3 main.py start
"""
    
    try:
        # Windows batch файл
        with open("start_system.bat", 'w', encoding='utf-8') as f:
            f.write(windows_script)
        
        # Unix shell скрипт
        with open("start_system.sh", 'w', encoding='utf-8') as f:
            f.write(unix_script)
        
        # Делаем shell скрипт исполняемым
        if os.name != 'nt':  # Не Windows
            os.chmod("start_system.sh", 0o755)
        
        print("✅ Скрипты запуска созданы:")
        print("   - start_system.bat (Windows)")
        print("   - start_system.sh (Unix/Linux/macOS)")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания скриптов: {e}")
        return False

def run_system_test() -> bool:
    """Запуск тестирования системы"""
    print("\n🧪 Запуск тестирования системы...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_system.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Все тесты пройдены успешно")
            return True
        else:
            print("❌ Некоторые тесты не пройдены")
            print("Вывод тестов:")
            print(result.stdout)
            if result.stderr:
                print("Ошибки:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запуска тестов: {e}")
        return False

def show_final_instructions():
    """Показать финальные инструкции"""
    instructions = """
╔══════════════════════════════════════════════════════════════╗
║                    УСТАНОВКА ЗАВЕРШЕНА                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🚀 ЗАПУСК СИСТЕМЫ:                                         ║
║     python main.py start                                    ║
║     или                                                     ║
║     python run_system.py                                    ║
║                                                              ║
║  🤖 ТОЛЬКО TELEGRAM БОТ:                                    ║
║     python main.py bot                                      ║
║                                                              ║
║  🌐 ТОЛЬКО DASHBOARD:                                       ║
║     python main.py dashboard                                ║
║     URL: http://localhost:5001                              ║
║                                                              ║
║  🔍 ПРОВЕРКА СИСТЕМЫ:                                       ║
║     python main.py check                                    ║
║                                                              ║
║  🧪 ТЕСТИРОВАНИЕ:                                           ║
║     python test_system.py                                   ║
║                                                              ║
║  📚 ДОКУМЕНТАЦИЯ:                                           ║
║     Смотрите README.md для подробной информации             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(instructions)

def main():
    """Главная функция установки"""
    print_header()
    
    # Проверяем версию Python
    if not check_python_version():
        sys.exit(1)
    
    print("\n🔧 Начинаем установку системы...")
    
    steps = [
        ("Установка зависимостей", install_dependencies),
        ("Настройка Neo4j", setup_neo4j_config),
        ("Настройка переменных окружения", setup_env_file),
        ("Тестирование Neo4j", test_neo4j_connection),
        ("Создание скриптов запуска", create_startup_scripts),
        ("Тестирование системы", run_system_test)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"📋 Этап: {step_name}")
        print('='*60)
        
        if not step_func():
            failed_steps.append(step_name)
            choice = input(f"\n⚠️ Этап '{step_name}' не выполнен. Продолжить? (y/N): ").strip().lower()
            if choice != 'y':
                print("❌ Установка прервана")
                sys.exit(1)
    
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ УСТАНОВКИ:")
    print("="*60)
    
    if failed_steps:
        print(f"⚠️ Установка завершена с предупреждениями")
        print(f"❌ Проблемные этапы: {', '.join(failed_steps)}")
        print("💡 Рекомендуется исправить проблемы перед запуском")
    else:
        print("🎉 Установка завершена успешно!")
        print("✅ Все компоненты настроены и готовы к работе")
    
    show_final_instructions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⌨️ Установка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка установки: {e}")
        sys.exit(1)