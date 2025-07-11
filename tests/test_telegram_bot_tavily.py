#!/usr/bin/env python3
"""
Тест интеграции Tavily поиска в telegram_bot.py
"""
import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.append(str(PROJECT_ROOT))

from tg_bot.telegram_bot import process_user_query

async def test_tavily_integration():
    """
    Тестирует интеграцию Tavily поиска в основной поток обработки запросов.
    """
    print("="*60)
    print("ТЕСТ ИНТЕГРАЦИИ TAVILY В TELEGRAM BOT")
    print("="*60)
    
    # Тестовые запросы, которые скорее всего не найдутся в CSV
    test_queries = [
        "количество частных детских садов в России",
        "средняя зарплата учителей в московских школах",
        "число онлайн-курсов в российских университетах"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Тестовый запрос: {query}")
        print("-" * 50)
        
        try:
            # Выполняем запрос через основную функцию бота
            result = await process_user_query(query)
            
            print("РЕЗУЛЬТАТ:")
            print(result)
            
            # Проверяем, содержит ли результат информацию о Tavily
            if "Tavily" in result or "интернет-поиск" in result.lower():
                print("\n✅ Tavily интеграция работает!")
            else:
                print("\n❌ Tavily интеграция не сработала")
                
        except Exception as e:
            print(f"❌ Ошибка при выполнении запроса: {str(e)}")
        
        print("\n" + "="*60)

async def test_csv_fallback():
    """
    Тестирует, что обычные запросы по-прежнему работают с CSV данными.
    """
    print("\nТЕСТ ОБЫЧНЫХ CSV ЗАПРОСОВ")
    print("="*60)
    
    # Запрос, который должен найтись в CSV
    csv_query = "количество студентов высших учебных заведений"
    
    print(f"Тестовый запрос: {csv_query}")
    print("-" * 50)
    
    try:
        result = await process_user_query(csv_query)
        
        print("РЕЗУЛЬТАТ:")
        print(result)
        
        # Проверяем, что результат НЕ содержит информацию о Tavily
        if "Tavily" not in result and "интернет-поиск" not in result.lower():
            print("\n✅ CSV данные работают корректно!")
        else:
            print("\n⚠️  Возможно, запрос ушел в Tavily вместо CSV")
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {str(e)}")

async def main():
    """Основная функция тестирования."""
    print("Запуск тестов интеграции Tavily...")
    
    # Тест интеграции Tavily
    await test_tavily_integration()
    
    # Тест обычных CSV запросов
    await test_csv_fallback()
    
    print("\nТестирование завершено!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")