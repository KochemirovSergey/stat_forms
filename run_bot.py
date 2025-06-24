#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота
"""
import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        from telegram_bot import main
        import asyncio
        
        print("🚀 Запуск Telegram бота...")
        print("📱 Бот: @stat_forms_bot")
        print("⏹️  Для остановки нажмите Ctrl+C")
        print("-" * 50)
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n✅ Бот остановлен пользователем")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)