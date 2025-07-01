#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для модуля создания узлов Neo4j
"""

import json
from neo4j_node_creator import Neo4jNodeCreator

def test_single_node():
    """
    Тест создания одного узла
    """
    print("=== ТЕСТ СОЗДАНИЯ ОДНОГО УЗЛА ===")
    
    creator = Neo4jNodeCreator()
    
    # Конфигурация одного узла
    node_config = {
        "node_name": "Тест_население",
        "node_label": "TestNode",
        "table_number": "2.1.1",
        "column": 3,
        "row": 5
    }
    
    try:
        creator.connect()
        node_id = creator.create_node(node_config)
        
        if node_id:
            print(f"✅ Узел создан успешно с ID: {node_id}")
        else:
            print("❌ Ошибка создания узла")
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
    finally:
        creator.disconnect()

def test_data_collection():
    """
    Тест сбора данных без создания узла
    """
    print("\n=== ТЕСТ СБОРА ДАННЫХ ===")
    
    creator = Neo4jNodeCreator()
    
    table_number = "2.1.1"
    column = 3
    row = 5
    
    print(f"Тестируем сбор данных для таблицы {table_number}, колонка {column}, строка {row}")
    
    # Тест федеральных данных
    print("\n--- Федеральные данные ---")
    federal_data = creator.collect_federal_data(table_number, column, row)
    print(f"Федеральные данные по годам: {federal_data}")
    
    # Тест региональных данных
    print("\n--- Региональные данные ---")
    regions, regional_data = creator.collect_regional_data(table_number, column, row)
    print(f"Найдено регионов: {len(regions)}")
    print(f"Первые 5 регионов: {regions[:5]}")
    print(f"Данные первых 3 регионов: {regional_data[:3]}")

def test_batch_processing():
    """
    Тест пакетной обработки узлов
    """
    print("\n=== ТЕСТ ПАКЕТНОЙ ОБРАБОТКИ ===")
    
    creator = Neo4jNodeCreator()
    
    # Создаем тестовую конфигурацию
    test_config = {
        "nodes": [
            {
                "node_name": "Тест_узел_1",
                "node_label": "TestBatch",
                "table_number": "2.1.1",
                "column": 3,
                "row": 5
            },
            {
                "node_name": "Тест_узел_2",
                "node_label": "TestBatch",
                "table_number": "2.1.1",
                "column": 4,
                "row": 5
            }
        ]
    }
    
    # Сохраняем тестовую конфигурацию
    test_config_path = "test_batch_config.json"
    with open(test_config_path, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, ensure_ascii=False, indent=2)
    
    try:
        result = creator.process_batch(test_config_path)
        
        print(f"✅ Результат обработки:")
        print(f"   Успех: {result['success']}")
        print(f"   Создано узлов: {result.get('created_nodes', 0)}")
        print(f"   Ошибок: {result.get('failed_nodes', 0)}")
        
        print(f"\n📋 Лог обработки:")
        for log_entry in result.get('processing_log', []):
            print(f"   {log_entry}")
            
        if result.get('created_node_ids'):
            print(f"\n🆔 Созданные узлы:")
            for node_id in result['created_node_ids']:
                print(f"   {node_id}")
                
    except Exception as e:
        print(f"❌ Ошибка пакетной обработки: {str(e)}")

def test_connection():
    """
    Тест подключения к Neo4j
    """
    print("=== ТЕСТ ПОДКЛЮЧЕНИЯ К NEO4J ===")
    
    creator = Neo4jNodeCreator()
    
    try:
        creator.connect()
        print("✅ Подключение к Neo4j успешно")
        creator.disconnect()
        print("✅ Отключение от Neo4j успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения: {str(e)}")

def main():
    """
    Основная функция тестирования
    """
    print("🚀 ЗАПУСК ТЕСТОВ МОДУЛЯ NEO4J NODE CREATOR")
    print("=" * 50)
    
    # Тест подключения
    test_connection()
    
    # Тест сбора данных
    test_data_collection()
    
    # Тест создания одного узла
    test_single_node()
    
    # Тест пакетной обработки
    test_batch_processing()
    
    print("\n" + "=" * 50)
    print("🏁 ТЕСТЫ ЗАВЕРШЕНЫ")

if __name__ == "__main__":
    main()