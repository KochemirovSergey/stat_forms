#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки расширенной функциональности query_schetnoe_nodes.py
"""

import json
from query_schetnoe_nodes import SchetnoeNodesQuery
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_extended_functionality():
    """
    Тестирует новую расширенную функциональность
    """
    query_handler = SchetnoeNodesQuery()
    
    try:
        # Подключаемся к базе данных
        print("Подключение к Neo4j...")
        query_handler.connect()
        
        # Тестируем получение уникальных типов связей
        print("\n=== Тест 1: Получение уникальных типов связей ===")
        relation_types = query_handler.get_unique_relation_types_from_schetnoe()
        print(f"Найдено типов связей: {len(relation_types)}")
        print(f"Типы связей: {relation_types}")
        
        # Тестируем извлечение меток
        print("\n=== Тест 2: Извлечение меток из типов связей ===")
        labels = query_handler.extract_labels_from_relation_types(relation_types)
        print(f"Извлечено меток: {len(labels)}")
        print(f"Метки: {labels}")
        
        # Тестируем получение узлов по меткам
        print("\n=== Тест 3: Получение узлов по меткам ===")
        additional_nodes = query_handler.get_nodes_by_labels(labels)
        print(f"Найдено дополнительных узлов: {len(additional_nodes)}")
        
        # Показываем примеры узлов по каждой метке
        for label in labels:
            nodes_for_label = [node for node in additional_nodes if label in node['node_labels']]
            print(f"  Метка '{label}': {len(nodes_for_label)} узлов")
            if nodes_for_label:
                example = nodes_for_label[0]
                print(f"    Пример: {example['node_name']} (ID: {example['node_id']})")
        
        # Тестируем получение связей между дополнительными узлами
        print("\n=== Тест 4: Получение связей между дополнительными узлами ===")
        relations_between = query_handler.get_relations_between_nodes_by_labels(labels)
        print(f"Найдено связей между дополнительными узлами: {len(relations_between)}")
        
        # Показываем примеры связей
        if relations_between:
            print("Примеры связей:")
            for i, rel in enumerate(relations_between[:5]):  # Показываем первые 5
                print(f"  {i+1}. {rel['source_name']} -> {rel['target_name']} ({rel['relation_type']})")
        
        # Тестируем получение расширенных данных
        print("\n=== Тест 5: Получение расширенных данных ===")
        extended_data = query_handler.get_extended_schetnoe_data()
        
        metadata = extended_data['metadata']
        print(f"Узлов 'Счетное': {metadata['schetnoe_nodes_count']}")
        print(f"Дополнительных узлов: {metadata['additional_nodes_count']}")
        print(f"Связей между дополнительными: {metadata['relations_between_additional_count']}")
        print(f"Всего входящих связей к 'Счетное': {metadata['total_incoming_relations']}")
        
        # Сохраняем результаты тестирования
        print("\n=== Сохранение результатов тестирования ===")
        with open('test_extended_results.json', 'w', encoding='utf-8') as f:
            json.dump(extended_data, f, ensure_ascii=False, indent=2)
        print("Результаты сохранены в test_extended_results.json")
        
        # Проверяем структуру данных
        print("\n=== Проверка структуры данных ===")
        required_keys = ['schetnoe_nodes', 'additional_nodes', 'relations_between_additional', 'metadata']
        for key in required_keys:
            if key in extended_data:
                print(f"✓ Ключ '{key}' присутствует")
            else:
                print(f"✗ Ключ '{key}' отсутствует")
        
        print("\n=== Тестирование завершено успешно! ===")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {str(e)}")
        print(f"Ошибка: {str(e)}")
        return False
    
    finally:
        # Закрываем соединение
        query_handler.disconnect()

def test_api_compatibility():
    """
    Тестирует совместимость с API
    """
    print("\n=== Тест совместимости с API ===")
    
    try:
        # Имитируем вызов API
        from app import app
        with app.test_client() as client:
            response = client.get('/graph_data')
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✓ API вернул данные успешно")
                print(f"  Узлов: {len(data.get('nodes', []))}")
                print(f"  Связей: {len(data.get('edges', []))}")
                
                # Проверяем наличие метаданных
                if 'metadata' in data:
                    print(f"✓ Метаданные присутствуют")
                    metadata = data['metadata']
                    print(f"  Обнаруженные метки: {metadata.get('discovered_labels', [])}")
                else:
                    print(f"✗ Метаданные отсутствуют")
                
                return True
            else:
                print(f"✗ API вернул ошибку: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Ошибка при тестировании API: {str(e)}")
        return False

if __name__ == "__main__":
    print("Запуск тестирования расширенной функциональности...")
    
    # Тестируем основную функциональность
    success1 = test_extended_functionality()
    
    # Тестируем совместимость с API
    success2 = test_api_compatibility()
    
    if success1 and success2:
        print("\n🎉 Все тесты прошли успешно!")
    else:
        print("\n❌ Некоторые тесты не прошли")