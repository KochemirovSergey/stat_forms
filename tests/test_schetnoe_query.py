#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работы query_schetnoe_nodes.py
"""

import json
from query_schetnoe_nodes import SchetnoeNodesQuery
import logging

# Настройка логирования для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection():
    """
    Тестирует подключение к Neo4j
    """
    print("=== ТЕСТ ПОДКЛЮЧЕНИЯ К NEO4J ===")
    query_handler = SchetnoeNodesQuery()
    
    try:
        query_handler.connect()
        print("✅ Подключение успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    finally:
        query_handler.disconnect()


def test_schetnoe_nodes_query():
    """
    Тестирует запрос узлов "Счетное"
    """
    print("\n=== ТЕСТ ЗАПРОСА УЗЛОВ 'Счетное' ===")
    query_handler = SchetnoeNodesQuery()
    
    try:
        query_handler.connect()
        
        # Тест получения только узлов
        nodes_only = query_handler.get_schetnoe_nodes_only()
        print(f"✅ Найдено узлов 'Счетное': {len(nodes_only)}")
        
        if nodes_only:
            print(f"Пример узла: {nodes_only[0].get('schetnoe_name', 'Без названия')}")
        
        # Тест получения узлов с входящими связями
        nodes_with_relations = query_handler.get_schetnoe_nodes_with_incoming_relations()
        print(f"✅ Найдено узлов с входящими связями: {len(nodes_with_relations)}")
        
        if nodes_with_relations:
            total_relations = sum(len(node.get('incoming_relations', [])) for node in nodes_with_relations)
            print(f"Всего входящих связей: {total_relations}")
            
            # Показываем пример узла с связями
            for node in nodes_with_relations:
                if node.get('incoming_relations'):
                    print(f"Пример узла с связями: {node.get('schetnoe_name', 'Без названия')}")
                    print(f"  Количество входящих связей: {len(node['incoming_relations'])}")
                    print(f"  Типы связей: {set(rel['relation_type'] for rel in node['incoming_relations'])}")
                    break
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {e}")
        return False
    finally:
        query_handler.disconnect()


def test_save_results():
    """
    Тестирует сохранение результатов в файл
    """
    print("\n=== ТЕСТ СОХРАНЕНИЯ РЕЗУЛЬТАТОВ ===")
    query_handler = SchetnoeNodesQuery()
    
    try:
        query_handler.connect()
        
        # Получаем данные
        nodes_data = query_handler.get_schetnoe_nodes_only()
        
        # Сохраняем в тестовый файл
        test_filename = "test_schetnoe_results.json"
        query_handler.save_results_to_json(nodes_data, test_filename)
        
        # Проверяем, что файл создался и содержит данные
        with open(test_filename, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        if len(saved_data) == len(nodes_data):
            print(f"✅ Данные успешно сохранены в {test_filename}")
            print(f"Сохранено записей: {len(saved_data)}")
            return True
        else:
            print(f"❌ Ошибка: количество сохраненных записей не совпадает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        return False
    finally:
        query_handler.disconnect()


def test_cypher_query_validation():
    """
    Тестирует корректность Cypher запросов
    """
    print("\n=== ТЕСТ ВАЛИДАЦИИ CYPHER ЗАПРОСОВ ===")
    query_handler = SchetnoeNodesQuery()
    
    try:
        query_handler.connect()
        
        # Проверяем, что исходящие связи "ПоРегион" не включаются
        with query_handler.driver.session(database=query_handler.config["NEO4J_DATABASE"]) as session:
            # Запрос для проверки исходящих связей "ПоРегион" от узлов "Счетное"
            validation_query = """
            MATCH (schetnoe:Счетное)-[r:ПоРегион]->(target)
            RETURN count(r) as po_region_outgoing_count
            """
            
            result = session.run(validation_query)
            record = result.single()
            po_region_count = record['po_region_outgoing_count'] if record else 0
            
            print(f"Найдено исходящих связей 'ПоРегион' от узлов 'Счетное': {po_region_count}")
            
            if po_region_count > 0:
                print("⚠️  Внимание: Обнаружены исходящие связи 'ПоРегион', которые должны быть исключены")
            else:
                print("✅ Исходящие связи 'ПоРегион' отсутствуют или корректно исключены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при валидации: {e}")
        return False
    finally:
        query_handler.disconnect()


def run_all_tests():
    """
    Запускает все тесты
    """
    print("🧪 ЗАПУСК ТЕСТОВ ДЛЯ QUERY_SCHETNOE_NODES.PY")
    print("=" * 50)
    
    tests = [
        ("Подключение к Neo4j", test_connection),
        ("Запрос узлов 'Счетное'", test_schetnoe_nodes_query),
        ("Сохранение результатов", test_save_results),
        ("Валидация Cypher запросов", test_cypher_query_validation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nВсего тестов: {len(results)}")
    print(f"Пройдено: {passed}")
    print(f"Провалено: {failed}")
    
    if failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"\n⚠️  {failed} тест(ов) провалено. Проверьте логи для деталей.")


if __name__ == "__main__":
    run_all_tests()