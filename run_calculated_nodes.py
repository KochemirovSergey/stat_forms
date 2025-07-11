#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для запуска создания расчетных узлов в Neo4j
"""

from calculated_node_creator import CalculatedNodeCreator
import sys

def main():
    """
    Основная функция для создания расчетных узлов
    """
    print("СОЗДАНИЕ РАСЧЕТНЫХ УЗЛОВ В NEO4J")
    print("=" * 50)
    
    # Создаем экземпляр класса
    creator = CalculatedNodeCreator()
    
    try:
        # Обрабатываем пакет расчетных узлов из JSON-файла
        config_file = "calculated_nodes_config.json"
        print(f"Загружаем конфигурацию из файла: {config_file}")
        
        result = creator.process_calculated_nodes_batch(config_file)
        
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТ ОБРАБОТКИ")
        print("=" * 50)
        
        print(f"Статус: {'✅ УСПЕШНО' if result['success'] else '❌ ОШИБКА'}")
        print(f"Создано узлов: {result.get('created_nodes', 0)}")
        print(f"Ошибок: {result.get('failed_nodes', 0)}")
        print(f"Всего узлов: {result.get('total_nodes', 0)}")
        
        if result.get('error'):
            print(f"Критическая ошибка: {result['error']}")
        
        print("\n" + "=" * 50)
        print("ПОДРОБНЫЙ ЛОГ ОБРАБОТКИ")
        print("=" * 50)
        
        for log_entry in result.get('processing_log', []):
            print(f"  {log_entry}")
            
        if result.get('created_node_ids'):
            print("\n" + "=" * 50)
            print("СОЗДАННЫЕ РАСЧЕТНЫЕ УЗЛЫ")
            print("=" * 50)
            
            for i, node_id in enumerate(result['created_node_ids'], 1):
                print(f"  {i}. ID: {node_id}")
        
        # Возвращаем код выхода
        return 0 if result['success'] else 1
                
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)