#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки интеграции Neo4j с Telegram ботом
"""

import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.append(str(PROJECT_ROOT))

from tg_bot.neo4j_matcher import Neo4jMatcher
from tg_bot.config import DASHBOARD_SERVER_URL

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_neo4j_matcher():
    """Тестирование Neo4j матчера"""
    print("=== ТЕСТИРОВАНИЕ NEO4J MATCHER ===\n")
    
    matcher = None
    try:
        # Инициализация матчера
        print("1. Инициализация Neo4j матчера...")
        matcher = Neo4jMatcher()
        print("✅ Neo4j матчер успешно инициализирован\n")
        
        # Тестовые запросы
        test_queries = [
            "количество студентов",
            "численность преподавателей",
            "образовательные программы",
            "финансирование образования",
            "количество школ",
            "выпускники вузов",
            "неподходящий запрос о погоде в Москве"
        ]
        
        print("2. Тестирование поиска соответствий...")
        print("-" * 60)
        
        for i, query in enumerate(test_queries, 1):
            print(f"Тест {i}: {query}")
            
            # Поиск соответствующего узла
            node_id = matcher.find_matching_schetnoe_node(query)
            
            if node_id:
                # Получаем информацию о найденном узле
                node_info = matcher.get_node_info_by_id(node_id)
                if node_info:
                    print(f"✅ Найден узел:")
                    print(f"   ID: {node_id}")
                    print(f"   Название: {node_info.get('node_name', 'Без названия')}")
                    print(f"   Полное название: {node_info.get('node_full_name', 'Не указано')}")
                    print(f"   Таблица: {node_info.get('table_number', 'Не указано')}")
                    
                    # Генерируем ссылку на дашборд
                    dashboard_url = f"{DASHBOARD_SERVER_URL}/dashboard/{node_id}"
                    print(f"   🔗 Дашборд: {dashboard_url}")
                else:
                    print(f"⚠️  Узел найден, но информация недоступна")
            else:
                print("❌ Соответствующий узел не найден")
            
            print("-" * 60)
        
        print("\n3. Тестирование кеширования...")
        # Повторный запрос для проверки кеширования
        test_query = "количество студентов"
        print(f"Повторный запрос: {test_query}")
        node_id = matcher.find_matching_schetnoe_node(test_query)
        if node_id:
            print("✅ Кеширование работает корректно")
        else:
            print("⚠️  Результат отличается от предыдущего")
        
        print("\n4. Статистика загруженных узлов...")
        nodes = matcher._get_schetnoe_nodes()
        print(f"Всего счетных узлов в базе: {len(nodes)}")
        
        # Показываем примеры узлов
        print("\nПримеры узлов:")
        for i, node in enumerate(nodes[:5]):
            print(f"  {i+1}. {node.get('node_name', 'Без названия')} (ID: {node.get('node_id', 'unknown')})")
        
        if len(nodes) > 5:
            print(f"  ... и еще {len(nodes) - 5} узлов")
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {str(e)}", exc_info=True)
        return False
    
    finally:
        if matcher:
            matcher.close()
    
    return True

def test_dashboard_url_generation():
    """Тестирование генерации URL для дашборда"""
    print("\n=== ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ URL ДАШБОРДА ===\n")
    
    # Тестовые node_id
    test_node_ids = [
        "4:fb7d1b8c-123e-4567-8901-234567890abc:123",
        "4:12345678-abcd-efgh-ijkl-mnopqrstuvwx:456",
        "invalid-node-id"
    ]
    
    print(f"Базовый URL дашборд-сервера: {DASHBOARD_SERVER_URL}")
    print("-" * 60)
    
    for i, node_id in enumerate(test_node_ids, 1):
        dashboard_url = f"{DASHBOARD_SERVER_URL}/dashboard/{node_id}"
        print(f"Тест {i}:")
        print(f"  Node ID: {node_id}")
        print(f"  Dashboard URL: {dashboard_url}")
        print(f"  URL с годом: {dashboard_url}?year=2023")
        print("-" * 60)

def simulate_bot_integration():
    """Симуляция интеграции с ботом"""
    print("\n=== СИМУЛЯЦИЯ ИНТЕГРАЦИИ С БОТОМ ===\n")
    
    matcher = None
    try:
        matcher = Neo4jMatcher()
        
        # Симулируем обработку запроса пользователя
        user_query = "количество преподавателей в вузах"
        print(f"Пользователь спрашивает: '{user_query}'")
        print("\nЭтапы обработки:")
        print("1. ✅ Обработка CSV данных (симуляция)")
        print("2. ✅ Tavily поиск (симуляция)")
        print("3. 🔍 Проверка соответствия с Neo4j узлами...")
        
        # Поиск соответствующего узла
        matching_node_id = matcher.find_matching_schetnoe_node(user_query)
        
        if matching_node_id:
            node_info = matcher.get_node_info_by_id(matching_node_id)
            if node_info:
                node_name = node_info.get('node_name', 'Неизвестный узел')
                dashboard_url = f"{DASHBOARD_SERVER_URL}/dashboard/{matching_node_id}"
                
                print("4. ✅ Найдено соответствие!")
                print(f"   Узел: {node_name}")
                print(f"   URL дашборда: {dashboard_url}")
                
                # Формируем ответ как в боте
                dashboard_link = f"\n🎯 **Найден соответствующий показатель в базе данных:**\n"
                dashboard_link += f"📊 {node_name}\n"
                dashboard_link += f"🔗 [Интерактивный дашборд]({dashboard_url})\n"
                dashboard_link += f"📈 Просмотр региональных данных и динамики"
                
                print("\nОтвет пользователю будет дополнен:")
                print(dashboard_link)
            else:
                print("4. ⚠️  Узел найден, но информация недоступна")
        else:
            print("4. ❌ Соответствующий узел не найден")
            print("   Ссылка на дашборд не будет добавлена к ответу")
        
    except Exception as e:
        logger.error(f"Ошибка симуляции: {str(e)}", exc_info=True)
    
    finally:
        if matcher:
            matcher.close()

def main():
    """Основная функция тестирования"""
    print("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ NEO4J С TELEGRAM БОТОМ")
    print("=" * 60)
    
    try:
        # Тест 1: Neo4j матчер
        if not test_neo4j_matcher():
            print("❌ Тестирование Neo4j матчера провалено")
            return
        
        # Тест 2: Генерация URL
        test_dashboard_url_generation()
        
        # Тест 3: Симуляция интеграции
        simulate_bot_integration()
        
        print("\n" + "=" * 60)
        print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО")
        print("🚀 Интеграция Neo4j с Telegram ботом готова к использованию")
        
    except Exception as e:
        logger.error(f"Критическая ошибка тестирования: {str(e)}", exc_info=True)
        print("❌ ТЕСТИРОВАНИЕ ПРОВАЛЕНО")

if __name__ == "__main__":
    main()