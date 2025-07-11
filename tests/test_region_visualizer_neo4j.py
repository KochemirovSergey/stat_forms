#!/usr/bin/env python3
"""
Тестовый файл для модуля region_visualizer_neo4j.py
"""

import sys
import os
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

from region_visualizer_neo4j import RegionVisualizerNeo4j

def test_connection():
    """Тест подключения к Neo4j"""
    print("=== Тест подключения к Neo4j ===")
    try:
        visualizer = RegionVisualizerNeo4j()
        visualizer.connect()
        print("✅ Подключение успешно")
        visualizer.disconnect()
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {str(e)}")
        return False

def test_get_node_info():
    """Тест получения информации о узле"""
    print("\n=== Тест получения информации о узле ===")
    test_node_id = "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:156"
    
    try:
        with RegionVisualizerNeo4j() as visualizer:
            node_info = visualizer.get_node_info(test_node_id)
            
            if node_info:
                print("✅ Информация о узле получена:")
                for key, value in node_info.items():
                    print(f"  {key}: {value}")
                return True
            else:
                print("❌ Узел не найден или данные отсутствуют")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при получении информации о узле: {str(e)}")
        return False

def test_get_regional_data():
    """Тест получения региональных данных"""
    print("\n=== Тест получения региональных данных ===")
    test_node_id = "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:156"
    test_year = "2024"
    
    try:
        with RegionVisualizerNeo4j() as visualizer:
            regional_data = visualizer.get_regional_data(test_node_id, test_year)
            
            if regional_data:
                print(f"✅ Получено данных по {len(regional_data)} регионам за {test_year} год:")
                # Показываем первые 5 регионов
                for i, (region, value) in enumerate(regional_data.items()):
                    if i < 5:
                        print(f"  {region}: {value}")
                    else:
                        print(f"  ... и еще {len(regional_data) - 5} регионов")
                        break
                return True
            else:
                print("❌ Региональные данные не найдены")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при получении региональных данных: {str(e)}")
        return False

def test_create_regional_map():
    """Тест создания региональной карты"""
    print("\n=== Тест создания региональной карты ===")
    test_node_id = "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:156"
    test_year = "2024"
    
    try:
        with RegionVisualizerNeo4j() as visualizer:
            print(f"Создание карты для узла {test_node_id}, год {test_year}")
            visualizer.create_regional_map(test_node_id, test_year)
            print("✅ Карта создана успешно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при создании карты: {str(e)}")
        return False

def test_create_federal_chart():
    """Тест создания графика федеральных данных"""
    print("\n=== Тест создания графика федеральных данных ===")
    test_node_id = "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:156"
    
    try:
        with RegionVisualizerNeo4j() as visualizer:
            print(f"Создание графика для узла {test_node_id}")
            visualizer.create_federal_chart(test_node_id)
            print("✅ График создан успешно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при создании графика: {str(e)}")
        return False

def test_all_years():
    """Тест создания карт для всех доступных лет"""
    print("\n=== Тест создания карт для всех лет ===")
    test_node_id = "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:156"
    years = ["2021", "2022", "2023", "2024"]
    
    try:
        with RegionVisualizerNeo4j() as visualizer:
            for year in years:
                print(f"\nСоздание карты за {year} год...")
                regional_data = visualizer.get_regional_data(test_node_id, year)
                if regional_data:
                    print(f"  Данные за {year}: {len(regional_data)} регионов")
                else:
                    print(f"  Данные за {year}: отсутствуют")
            
            print("✅ Тест для всех лет завершен")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании всех лет: {str(e)}")
        return False

def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов для RegionVisualizerNeo4j")
    print("=" * 50)
    
    tests = [
        ("Подключение к Neo4j", test_connection),
        ("Получение информации о узле", test_get_node_info),
        ("Получение региональных данных", test_get_regional_data),
        ("Создание региональной карты", test_create_regional_map),
        ("Создание графика федеральных данных", test_create_federal_chart),
        ("Тест всех лет", test_all_years)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты успешно пройдены!")
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте конфигурацию и данные.")

if __name__ == "__main__":
    run_all_tests()