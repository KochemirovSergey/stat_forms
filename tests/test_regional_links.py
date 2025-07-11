#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый файл для проверки создания связей ПоРегион у расчетных узлов
"""

from calculated_node_creator import CalculatedNodeCreator
import json

def test_regional_links_with_real_nodes():
    """
    Тест создания расчетного узла с реальными узлами для проверки связей ПоРегион
    """
    print("=== ТЕСТ СВЯЗЕЙ ПоРегион С РЕАЛЬНЫМИ УЗЛАМИ ===")
    
    # Конфигурация расчетного узла с реальными ID
    calc_config = {
        "node_name": "ТестРегиональныеСвязиДиагностика",
        "full_name": "Тестовый расчетный узел для диагностики региональных связей",
        "node_label": "Расчетные",
        "formula": "node_id1 + node_id2",  # Используем правильный формат переменных
        "child_nodes": [
            "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:171",  # Школьники
            "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:174"   # ПедгШкл
        ]
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
            
            # Проверяем созданные связи ПоРегион
            print("\n=== ПРОВЕРКА СОЗДАННЫХ СВЯЗЕЙ ПоРегион ===")
            creator.connect()
            
            try:
                with creator.driver.session(database=creator.config["NEO4J_DATABASE"]) as session:
                    # Проверяем связи ПоРегион
                    query = """
                    MATCH (calc)-[r:ПоРегион]->(reg:Регион)
                    WHERE elementId(calc) = $calc_id
                    RETURN reg.name as region_name,
                           r.value_2016, r.value_2017, r.value_2018, r.value_2019, r.value_2020,
                           r.value_2021, r.value_2022, r.value_2023, r.value_2024
                    ORDER BY reg.name
                    LIMIT 3
                    """
                    
                    regional_result = session.run(query, {"calc_id": result['node_id']})
                    
                    regional_links = list(regional_result)
                    
                    if regional_links:
                        print(f"Найдено {len(regional_links)} связей ПоРегион:")
                        for link in regional_links:
                            print(f"  Регион: {link['region_name']}")
                            values = []
                            for year in ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]:
                                value = link.get(f'r.value_{year}')
                                values.append(str(value) if value is not None else "None")
                            print(f"    Значения: {', '.join(values)}")
                    else:
                        print("❌ ПРОБЛЕМА: Связи ПоРегион не найдены!")
                        
                        # Дополнительная диагностика - проверяем, создался ли узел
                        node_check_query = """
                        MATCH (n)
                        WHERE elementId(n) = $calc_id
                        RETURN n.name as name, labels(n) as labels
                        """
                        
                        node_result = session.run(node_check_query, {"calc_id": result['node_id']})
                        node_record = node_result.single()
                        
                        if node_record:
                            print(f"✅ Узел найден: {node_record['name']} с метками {node_record['labels']}")
                        else:
                            print("❌ Узел не найден в базе данных!")
                            
            finally:
                creator.disconnect()
        else:
            print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        
        print("\nЛог обработки:")
        for log_entry in result.get('processing_log', []):
            print(f"  {log_entry}")
            
        return result['success']
        
    except Exception as e:
        print(f"Ошибка теста: {str(e)}")
        return False

if __name__ == "__main__":
    test_regional_links_with_real_nodes()