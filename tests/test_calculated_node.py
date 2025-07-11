#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый файл для проверки работы модуля создания расчетных узлов
"""

from calculated_node_creator import CalculatedNodeCreator
import json

def test_simple_calculation():
    """
    Тест простого расчетного узла
    """
    print("=== ТЕСТ ПРОСТОГО РАСЧЕТНОГО УЗЛА ===")
    
    # Конфигурация простого расчетного узла
    calc_config = {
        "node_name": "ТестРасчет1",
        "full_name": "Тестовый расчетный узел - сумма школьников и классов",
        "node_label": "Расчетные",
        "formula": "Школьники + КлсШкл",
        "child_nodes": ["Школьники", "КлсШкл"]
    }
    
    # Создаем экземпляр класса
    creator = CalculatedNodeCreator()
    
    try:
        # Обрабатываем расчетный узел
        result = creator.process_calculated_node(calc_config)
        
        print(f"Результат: {result['success']}")
        print(f"Имя узла: {result['node_name']}")
        
        if result['success']:
            print(f"ID созданного узла: {result['node_id']}")
        else:
            print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        
        print("\nЛог обработки:")
        for log_entry in result.get('processing_log', []):
            print(f"  {log_entry}")
            
        return result['success']
        
    except Exception as e:
        print(f"Ошибка теста: {str(e)}")
        return False

def test_complex_calculation():
    """
    Тест сложного расчетного узла с скобками
    """
    print("\n=== ТЕСТ СЛОЖНОГО РАСЧЕТНОГО УЗЛА ===")
    
    # Конфигурация сложного расчетного узла
    calc_config = {
        "node_name": "ТестРасчет2",
        "full_name": "Тестовый сложный расчетный узел",
        "node_label": "Расчетные",
        "formula": "((Школьники + БзУглВс) - УглКлВс) * 1.1",
        "child_nodes": ["Школьники", "БзУглВс", "УглКлВс"]
    }
    
    # Создаем экземпляр класса
    creator = CalculatedNodeCreator()
    
    try:
        # Обрабатываем расчетный узел
        result = creator.process_calculated_node(calc_config)
        
        print(f"Результат: {result['success']}")
        print(f"Имя узла: {result['node_name']}")
        
        if result['success']:
            print(f"ID созданного узла: {result['node_id']}")
        else:
            print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        
        print("\nЛог обработки:")
        for log_entry in result.get('processing_log', []):
            print(f"  {log_entry}")
            
        return result['success']
        
    except Exception as e:
        print(f"Ошибка теста: {str(e)}")
        return False

def test_with_missing_nodes():
    """
    Тест с отсутствующими узлами
    """
    print("\n=== ТЕСТ С ОТСУТСТВУЮЩИМИ УЗЛАМИ ===")
    
    # Конфигурация с несуществующими узлами
    calc_config = {
        "node_name": "ТестРасчет3",
        "full_name": "Тестовый расчетный узел с отсутствующими узлами",
        "node_label": "Расчетные",
        "formula": "Школьники + НесуществующийУзел1 + НесуществующийУзел2",
        "child_nodes": ["Школьники", "НесуществующийУзел1", "НесуществующийУзел2"]
    }
    
    # Создаем экземпляр класса
    creator = CalculatedNodeCreator()
    
    try:
        # Обрабатываем расчетный узел
        result = creator.process_calculated_node(calc_config)
        
        print(f"Результат: {result['success']}")
        print(f"Имя узла: {result['node_name']}")
        
        if result['success']:
            print(f"ID созданного узла: {result['node_id']}")
        else:
            print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        
        print("\nЛог обработки:")
        for log_entry in result.get('processing_log', []):
            print(f"  {log_entry}")
            
        return result['success']
        
    except Exception as e:
        print(f"Ошибка теста: {str(e)}")
        return False

def test_division_calculation():
    """
    Тест расчетного узла с делением
    """
    print("\n=== ТЕСТ РАСЧЕТНОГО УЗЛА С ДЕЛЕНИЕМ ===")
    
    # Конфигурация с делением
    calc_config = {
        "node_name": "ТестРасчет4",
        "full_name": "Тестовый расчетный узел с делением - соотношение педагогов к школьникам",
        "node_label": "Расчетные",
        "formula": "ПедгШкл / Школьники * 1000",  # Количество педагогов на 1000 школьников
        "child_nodes": ["ПедгШкл", "Школьники"]
    }
    
    # Создаем экземпляр класса
    creator = CalculatedNodeCreator()
    
    try:
        # Обрабатываем расчетный узел
        result = creator.process_calculated_node(calc_config)
        
        print(f"Результат: {result['success']}")
        print(f"Имя узла: {result['node_name']}")
        
        if result['success']:
            print(f"ID созданного узла: {result['node_id']}")
        else:
            print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        
        print("\nЛог обработки:")
        for log_entry in result.get('processing_log', []):
            print(f"  {log_entry}")
            
        return result['success']
        
    except Exception as e:
        print(f"Ошибка теста: {str(e)}")
        return False

def main():
    """
    Основная функция для запуска всех тестов
    """
    print("ЗАПУСК ТЕСТОВ МОДУЛЯ СОЗДАНИЯ РАСЧЕТНЫХ УЗЛОВ")
    print("=" * 60)
    
    tests = [
        ("Простой расчет", test_simple_calculation),
        ("Сложный расчет", test_complex_calculation),
        ("Отсутствующие узлы", test_with_missing_nodes),
        ("Расчет с делением", test_division_calculation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Критическая ошибка в тесте '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    # Выводим итоговые результаты
    print("\n" + "=" * 60)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТОВ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "ПРОЙДЕН" if success else "ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✅ Все тесты успешно пройдены!")
    else:
        print("❌ Некоторые тесты провалены")
    
    return passed == total

if __name__ == "__main__":
    main()