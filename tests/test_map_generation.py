#!/usr/bin/env python3
"""
Тест генерации карты для диагностики проблем
"""

import sys
from pathlib import Path

# Добавляем путь для импорта модулей tg_bot
sys.path.append(str(Path(__file__).parent / 'tg_bot'))

from region_visualizer_neo4j import RegionVisualizerNeo4j

def test_map_generation():
    """Тестирует генерацию HTML карты"""
    print("=== Тест генерации карты ===")
    
    try:
        # Инициализируем визуализатор
        visualizer = RegionVisualizerNeo4j()
        visualizer.connect()
        print("✓ Подключение к Neo4j успешно")
        
        # Тестовый узел
        node_id = "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:171"
        year = "2024"
        
        print(f"Тестируем узел: {node_id}")
        print(f"Год: {year}")
        
        # Получаем информацию о узле
        node_info = visualizer.get_node_info(node_id)
        if node_info:
            print(f"✓ Узел найден: {node_info.get('name', 'Неизвестно')}")
        else:
            print("✗ Узел не найден")
            return False
        
        # Получаем региональные данные
        regional_data = visualizer.get_regional_data(node_id, year)
        if regional_data:
            print(f"✓ Получено региональных данных: {len(regional_data)}")
            # Показываем первые 3 региона
            for i, (region, value) in enumerate(list(regional_data.items())[:3]):
                print(f"  - {region}: {value}")
        else:
            print("✗ Региональные данные не получены")
            return False
        
        # Генерируем HTML карты
        print("Генерируем HTML карты...")
        map_html = visualizer.get_regional_map_html(node_id, year)
        
        if map_html:
            print(f"✓ HTML карты сгенерирован, длина: {len(map_html)}")
            print(f"✓ Содержит plotly-graph-div: {'plotly-graph-div' in map_html}")
            print(f"✓ Содержит Plotly.newPlot: {'Plotly.newPlot' in map_html}")
            
            # Сохраняем HTML для проверки
            with open('test_map.html', 'w', encoding='utf-8') as f:
                f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Тест карты</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Тест карты</h1>
    {map_html}
</body>
</html>
                """)
            print("✓ HTML сохранен в test_map.html")
            
        else:
            print("✗ HTML карты не сгенерирован")
            return False
        
        # Тестируем федеральный график
        print("Генерируем федеральный график...")
        chart_html = visualizer.get_federal_chart_html(node_id)
        
        if chart_html:
            print(f"✓ HTML графика сгенерирован, длина: {len(chart_html)}")
        else:
            print("✗ HTML графика не сгенерирован")
        
        print("=== Тест завершен успешно ===")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_map_generation()
    sys.exit(0 if success else 1)