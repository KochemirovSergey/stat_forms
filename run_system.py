#!/usr/bin/env python3
"""
Удобный скрипт для запуска системы анализа статистических форм
Предоставляет простой интерфейс для управления системой
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Вывод баннера системы"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              Система анализа статистических форм             ║
║                           v1.0.0                            ║
╠══════════════════════════════════════════════════════════════╣
║  🤖 Telegram Bot + 🌐 Web Dashboard + 📊 Neo4j Database     ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"   Текущая версия: {sys.version}")
        return False
    print(f"✅ Python версия: {sys.version.split()[0]}")
    return True

def check_requirements():
    """Проверка установленных зависимостей"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ Файл requirements.txt не найден")
        return False
    
    print("🔍 Проверка зависимостей...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "check"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Все зависимости установлены корректно")
            return True
        else:
            print("⚠️ Обнаружены проблемы с зависимостями:")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки зависимостей: {e}")
        return False

def install_requirements():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Зависимости установлены успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def run_system_check():
    """Запуск проверки готовности системы"""
    print("🔍 Проверка готовности системы...")
    try:
        result = subprocess.run([
            sys.executable, "main.py", "check"
        ], check=True)
        print("✅ Система готова к запуску")
        return True
    except subprocess.CalledProcessError:
        print("❌ Система не готова к запуску")
        print("💡 Проверьте конфигурацию Neo4j и другие настройки")
        return False

def show_menu():
    """Показать главное меню"""
    menu = """
╔══════════════════════════════════════════════════════════════╗
║                        ГЛАВНОЕ МЕНЮ                         ║
╠══════════════════════════════════════════════════════════════╣
║  1. 🚀 Запустить всю систему                                ║
║  2. 🤖 Запустить только Telegram бота                       ║
║  3. 🌐 Запустить только Dashboard сервер                    ║
║  4. 🔍 Проверить готовность системы                         ║
║  5. 📊 Показать статус компонентов                          ║
║  6. 📦 Установить/обновить зависимости                      ║
║  7. 📝 Показать логи                                        ║
║  8. ❓ Помощь                                               ║
║  9. 🚪 Выход                                               ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(menu)

def run_command(cmd_args):
    """Запуск команды main.py"""
    try:
        subprocess.run([sys.executable, "main.py"] + cmd_args, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⌨️ Команда прервана пользователем")
        return True

def show_logs():
    """Показать доступные логи"""
    log_files = {
        "1": ("system.log", "Системные логи"),
        "2": ("system_errors.log", "Логи ошибок"),
        "3": ("bot.log", "Логи Telegram бота"),
        "4": ("dashboard_server.log", "Логи Dashboard сервера")
    }
    
    print("\n📝 Доступные файлы логов:")
    for key, (filename, description) in log_files.items():
        status = "✅" if Path(filename).exists() else "❌"
        print(f"  {key}. {status} {description} ({filename})")
    
    choice = input("\nВыберите файл лога (1-4) или Enter для возврата: ").strip()
    
    if choice in log_files:
        filename, _ = log_files[choice]
        if Path(filename).exists():
            print(f"\n📄 Последние 50 строк из {filename}:")
            print("-" * 60)
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-50:]:
                        print(line.rstrip())
            except Exception as e:
                print(f"❌ Ошибка чтения файла: {e}")
        else:
            print(f"❌ Файл {filename} не найден")
    
    input("\nНажмите Enter для продолжения...")

def show_help():
    """Показать справку"""
    help_text = """
╔══════════════════════════════════════════════════════════════╗
║                           СПРАВКА                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🚀 ЗАПУСК СИСТЕМЫ                                          ║
║     Запускает все компоненты: Telegram бот + Dashboard      ║
║     Порт Dashboard: http://localhost:5001                   ║
║                                                              ║
║  🤖 TELEGRAM БОТ                                            ║
║     Интерактивный бот для анализа данных                    ║
║     Поддерживает текстовые запросы на русском языке         ║
║                                                              ║
║  🌐 DASHBOARD СЕРВЕР                                        ║
║     Веб-интерфейс для визуализации данных                   ║
║     Интерактивные карты и графики                           ║
║                                                              ║
║  📊 ТРЕБОВАНИЯ                                              ║
║     • Python 3.8+                                          ║
║     • Neo4j Database                                        ║
║     • Telegram Bot Token                                    ║
║                                                              ║
║  🔧 КОНФИГУРАЦИЯ                                            ║
║     • neo4j_config.json - настройки базы данных            ║
║     • .env - переменные окружения (опционально)             ║
║                                                              ║
║  📝 ЛОГИ                                                    ║
║     • system.log - общие логи                              ║
║     • system_errors.log - только ошибки                    ║
║     • bot.log - логи бота                                  ║
║     • dashboard_server.log - логи веб-сервера               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(help_text)
    input("Нажмите Enter для продолжения...")

def main():
    """Главная функция"""
    print_banner()
    
    # Проверяем версию Python
    if not check_python_version():
        sys.exit(1)
    
    while True:
        show_menu()
        choice = input("Выберите действие (1-9): ").strip()
        
        if choice == "1":
            print("\n🚀 Запуск всей системы...")
            print("💡 Для остановки нажмите Ctrl+C")
            print("-" * 50)
            run_command(["start"])
            
        elif choice == "2":
            print("\n🤖 Запуск Telegram бота...")
            print("💡 Для остановки нажмите Ctrl+C")
            print("-" * 50)
            run_command(["bot"])
            
        elif choice == "3":
            print("\n🌐 Запуск Dashboard сервера...")
            print("💡 Для остановки нажмите Ctrl+C")
            print("🌍 URL: http://localhost:5001")
            print("-" * 50)
            run_command(["dashboard"])
            
        elif choice == "4":
            print("\n🔍 Проверка готовности системы...")
            print("-" * 50)
            run_command(["check"])
            input("\nНажмите Enter для продолжения...")
            
        elif choice == "5":
            print("\n📊 Статус компонентов...")
            print("-" * 50)
            run_command(["status"])
            input("\nНажмите Enter для продолжения...")
            
        elif choice == "6":
            print("\n📦 Установка/обновление зависимостей...")
            print("-" * 50)
            if install_requirements():
                print("✅ Зависимости обновлены")
            input("\nНажмите Enter для продолжения...")
            
        elif choice == "7":
            show_logs()
            
        elif choice == "8":
            show_help()
            
        elif choice == "9":
            print("\n👋 До свидания!")
            break
            
        else:
            print("\n❌ Неверный выбор. Попробуйте снова.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа завершена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)