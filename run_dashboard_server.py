#!/usr/bin/env python3
"""
Скрипт для запуска Dashboard Server
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def check_dependencies():
    """Проверка зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    required_files = [
        "dashboard_server.py",
        "region_visualizer_neo4j.py",
        "neo4j_config.json",
        "templates/dashboard.html",
        "templates/dashboard_index.html",
        "templates/dashboard_error.html",
        "static/dashboard.css",
        "static/dashboard.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Отсутствуют необходимые файлы:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ Все необходимые файлы найдены")
    return True

def check_neo4j_config():
    """Проверка конфигурации Neo4j"""
    print("🔍 Проверка конфигурации Neo4j...")
    
    config_file = Path("neo4j_config.json")
    if not config_file.exists():
        print("❌ Файл neo4j_config.json не найден")
        return False
    
    try:
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "NEO4J_DATABASE"]
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            print(f"❌ В конфигурации отсутствуют ключи: {missing_keys}")
            return False
        
        print("✅ Конфигурация Neo4j корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка чтения конфигурации Neo4j: {str(e)}")
        return False

def check_python_packages():
    """Проверка Python пакетов"""
    print("🔍 Проверка Python пакетов...")
    
    required_packages = [
        "flask",
        "neo4j",
        "pandas",
        "plotly",
        "fuzzywuzzy"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Отсутствуют необходимые пакеты:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nУстановите зависимости: pip install -r requirements.txt")
        return False
    
    print("✅ Все необходимые пакеты установлены")
    return True

def test_neo4j_connection():
    """Тест подключения к Neo4j"""
    print("🔍 Тестирование подключения к Neo4j...")
    
    try:
        from region_visualizer_neo4j import RegionVisualizerNeo4j
        
        visualizer = RegionVisualizerNeo4j()
        visualizer.connect()
        
        # Простой тест запроса
        with visualizer.driver.session(database=visualizer.config["NEO4J_DATABASE"]) as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("✅ Подключение к Neo4j успешно")
                visualizer.disconnect()
                return True
        
        visualizer.disconnect()
        return False
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Neo4j: {str(e)}")
        return False

def start_server(port=5001, debug=False):
    """Запуск сервера"""
    print(f"🚀 Запуск Dashboard Server на порту {port}...")
    
    # Устанавливаем переменные окружения
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['DEBUG'] = str(debug).lower()
    
    try:
        # Запускаем сервер
        process = subprocess.Popen(
            [sys.executable, "dashboard_server.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"✅ Сервер запущен (PID: {process.pid})")
        print(f"🌐 Доступен по адресу: http://localhost:{port}")
        print("📋 Для остановки нажмите Ctrl+C")
        print("-" * 50)
        
        # Обработчик сигнала для корректного завершения
        def signal_handler(sig, frame):
            print("\n🛑 Получен сигнал завершения...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("⚠️ Принудительное завершение процесса...")
                process.kill()
            print("✅ Сервер остановлен")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Читаем вывод сервера
        for line in process.stdout:
            print(line.rstrip())
        
        # Ждем завершения процесса
        return_code = process.wait()
        if return_code != 0:
            print(f"❌ Сервер завершился с кодом ошибки: {return_code}")
        
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал прерывания...")
        if 'process' in locals():
            process.terminate()
        print("✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {str(e)}")

def main():
    """Основная функция"""
    print("=" * 50)
    print("🚀 Dashboard Server Launcher")
    print("=" * 50)
    
    # Проверяем аргументы командной строки
    port = 5001
    debug = False
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ Некорректный порт: {sys.argv[1]}")
            sys.exit(1)
    
    if len(sys.argv) > 2 and sys.argv[2].lower() in ['true', '1', 'yes', 'debug']:
        debug = True
    
    # Выполняем проверки
    checks = [
        ("Зависимости", check_dependencies),
        ("Конфигурация Neo4j", check_neo4j_config),
        ("Python пакеты", check_python_packages),
        ("Подключение к Neo4j", test_neo4j_connection)
    ]
    
    print("🔍 Выполнение предварительных проверок...")
    print("-" * 30)
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        if not check_func():
            print(f"\n❌ Проверка '{check_name}' не пройдена")
            print("🛑 Запуск сервера отменен")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Все проверки пройдены успешно!")
    print("=" * 50)
    
    # Небольшая пауза перед запуском
    time.sleep(1)
    
    # Запускаем сервер
    start_server(port, debug)

if __name__ == "__main__":
    main()