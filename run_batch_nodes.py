#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска создания узлов Neo4j из batch_nodes_config.json
"""

import json
import sys
from neo4j_node_creator import Neo4jNodeCreator

def main():
    """Основная функция запуска"""
    print("🚀 Запуск создания узлов Neo4j...")
    print("=" * 50)
    
    config_file = "batch_nodes_config.json"
    
    try:
        # Проверяем существование файла конфигурации
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"📄 Загружена конфигурация из {config_file}")
        print(f"📊 Количество узлов для создания: {len(config['nodes'])}")
        
        # Показываем информацию о узлах
        for i, node in enumerate(config['nodes'], 1):
            print(f"   {i}. {node['node_name']} (типы: {node['node_label']})")
        
        print("\n🔗 Подключение к Neo4j...")
        
        # Создаем экземпляр Neo4jNodeCreator
        creator = Neo4jNodeCreator()
        
        # Обрабатываем пакет узлов
        print("⚙️  Обработка узлов...")
        result = creator.process_batch(config_file)
        
        print("\n" + "=" * 50)
        print("📋 РЕЗУЛЬТАТ ОБРАБОТКИ:")
        print("=" * 50)
        
        if result['success']:
            print(f"✅ Успешно создано узлов: {result['created_nodes']}")
            print(f"🔗 Создано связей: {result['total_relationships']}")
            
            if result['created_node_ids']:
                print("\n🆔 ID созданных узлов:")
                for node_id in result['created_node_ids']:
                    print(f"   • {node_id}")
        else:
            print("❌ Ошибка при создании узлов")
            
        if result['failed_nodes'] > 0:
            print(f"⚠️  Неудачных попыток: {result['failed_nodes']}")
            
        print(f"\n📊 Общая статистика: {result['created_nodes']}/{result['total_nodes']} узлов создано")
        
        print("\n📝 Подробный лог обработки:")
        print("-" * 30)
        for log_entry in result['processing_log']:
            print(f"   {log_entry}")
        
        # Показываем Cypher запросы для проверки
        print("\n" + "=" * 50)
        print("🔍 ПРОВЕРКА РЕЗУЛЬТАТА:")
        print("=" * 50)
        print("Выполните эти запросы в Neo4j Browser для проверки:")
        print()
        
        for node in config['nodes']:
            node_name = node['node_name']
            labels = node['node_label']
            
            print(f"// Найти узел '{node_name}'")
            if isinstance(labels, list):
                labels_str = ":".join(labels)
                print(f"MATCH (n:{labels_str} {{name: \"{node_name}\"}})")
            else:
                print(f"MATCH (n:{labels} {{name: \"{node_name}\"}})")
            print("RETURN n")
            print()
            
            if 'relationships' in node:
                print(f"// Проверить связи для '{node_name}'")
                if isinstance(labels, list):
                    labels_str = ":".join(labels)
                    print(f"MATCH (source)-[r]->(n:{labels_str} {{name: \"{node_name}\"}})")
                else:
                    print(f"MATCH (source)-[r]->(n:{labels} {{name: \"{node_name}\"}})")
                print("RETURN source, type(r), n")
                print()
        
        print("// Проверить региональные данные")
        for node in config['nodes']:
            node_name = node['node_name']
            labels = node['node_label']
            
            if isinstance(labels, list):
                labels_str = ":".join(labels)
                print(f"MATCH (n:{labels_str} {{name: \"{node_name}\"}})-[:ПоРегион]->(region:Регион)")
            else:
                print(f"MATCH (n:{labels} {{name: \"{node_name}\"}})-[:ПоРегион]->(region:Регион)")
            print("RETURN n.name, region.name LIMIT 5")
            break  # Показываем только для первого узла
        
        print("\n🎉 Обработка завершена!")
        
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл {config_file} не найден!")
        print("Убедитесь, что файл существует в текущей директории.")
        sys.exit(1)
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка: Некорректный JSON в файле {config_file}")
        print(f"Детали: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("Проверьте:")
        print("1. Настройки подключения к Neo4j в neo4j_config.json")
        print("2. Доступность базы данных Neo4j")
        print("3. Наличие данных в папке БД/")
        sys.exit(1)

if __name__ == "__main__":
    main()