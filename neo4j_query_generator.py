import json
import os
import pandas as pd
from typing import Dict, List, Any

class Neo4jQueryGenerator:
    def __init__(self, base_path: str = "БД"):
        self.base_path = base_path
        self.years = [2021, 2022, 2023, 2024]
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Загружает JSON-конфигурацию"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_regions_list(self) -> List[str]:
        """Получает список всех регионов из структуры папок"""
        regions = []
        # Берем список регионов из любого доступного года
        for year in self.years:
            year_path = os.path.join(self.base_path, str(year), str(year))
            if os.path.exists(year_path):
                regions = [d for d in os.listdir(year_path) 
                          if os.path.isdir(os.path.join(year_path, d))]
                break
        return sorted(regions)
    
    def extract_data_from_csv(self, file_path: str, table_number: int, 
                             column: int, row: int) -> float:
        """Извлекает данные из CSV файла по координатам"""
        try:
            if not os.path.exists(file_path):
                return None
                
            # Читаем CSV файл
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Получаем значение по координатам (учитываем, что нумерация с 1)
            if row-1 < len(df) and column-1 < len(df.columns):
                value = df.iloc[row-1, column-1]
                
                # Проверяем, что значение числовое
                if pd.isna(value) or value == '':
                    return None
                    
                try:
                    return float(str(value).replace(',', '.').replace(' ', ''))
                except:
                    return None
            return None
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {e}")
            return None
    
    def collect_federal_data(self, config: Dict[str, Any]) -> Dict[int, float]:
        """Собирает федеральные данные по годам"""
        federal_data = {}
        table_name = f"Раздел {config['номер_таблицы']}.csv"
        
        for year in self.years:
            file_path = os.path.join(self.base_path, str(year), table_name)
            value = self.extract_data_from_csv(
                file_path, 
                config['номер_таблицы'], 
                config['номер_колонки'], 
                config['номер_строки']
            )
            if value is not None:
                federal_data[year] = value
                
        return federal_data
    
    def collect_regional_data(self, config: Dict[str, Any]) -> Dict[str, Dict[int, float]]:
        """Собирает региональные данные по годам и регионам"""
        regional_data = {}
        regions = self.get_regions_list()
        table_name = f"Раздел {config['номер_таблицы']}.csv"
        
        for region in regions:
            regional_data[region] = {}
            for year in self.years:
                file_path = os.path.join(
                    self.base_path, str(year), str(year), region, table_name
                )
                value = self.extract_data_from_csv(
                    file_path,
                    config['номер_таблицы'],
                    config['номер_колонки'],
                    config['номер_строки']
                )
                if value is not None:
                    regional_data[region][year] = value
                    
        return regional_data
    
    def generate_cypher_query(self, config: Dict[str, Any]) -> str:
        """Генерирует Cypher-запрос для создания узла и связей"""
        
        # Собираем данные
        federal_data = self.collect_federal_data(config)
        regional_data = self.collect_regional_data(config)
        
        # Начинаем формировать запрос
        query_parts = []
        
        # 1. Создаем основной узел с федеральными данными
        node_name = config['название_узла']
        node_type = config['тип']
        
        # Формируем свойства узла (федеральные данные)
        federal_props = []
        for year, value in federal_data.items():
            federal_props.append(f"year_{year}: {value}")
        
        federal_props_str = ", ".join(federal_props)
        
        create_node_query = f"""
// Создание основного узла с федеральными данными
CREATE (n:{node_type} {{name: '{node_name}', {federal_props_str}}})"""
        
        query_parts.append(create_node_query)
        
        # 2. Создаем связи с регионами
        relationships_queries = []
        
        for region, year_data in regional_data.items():
            if year_data:  # Если есть данные для региона
                # Формируем свойства связи (региональные данные)
                regional_props = []
                for year, value in year_data.items():
                    regional_props.append(f"year_{year}: {value}")
                
                if regional_props:
                    regional_props_str = ", ".join(regional_props)
                    
                    relationship_query = f"""
// Связь с регионом {region}
MATCH (n:{node_type} {{name: '{node_name}'}})
MATCH (r:Регион {{name: '{region}'}})
CREATE (n)-[:ПоРегион {{{regional_props_str}}}]->(r)"""
                    
                    relationships_queries.append(relationship_query)
        
        # Объединяем все части запроса
        full_query = "\n".join(query_parts + relationships_queries)
        
        return full_query
    
    def generate_query_from_config(self, config_path: str) -> str:
        """Основной метод для генерации запроса из конфигурации"""
        config = self.load_config(config_path)
        return self.generate_cypher_query(config)
    
    def save_query_to_file(self, query: str, output_path: str):
        """Сохраняет сгенерированный запрос в файл"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(query)
        print(f"Запрос сохранен в файл: {output_path}")

# Пример использования
if __name__ == "__main__":
    generator = Neo4jQueryGenerator()
    
    # Пример конфигурации
    example_config = {
        "название_узла": "Численность_населения",
        "тип": "Демография", 
        "номер_таблицы": 1,
        "номер_колонки": 3,
        "номер_строки": 5
    }
    
    # Сохраняем пример конфигурации
    with open('example_config.json', 'w', encoding='utf-8') as f:
        json.dump(example_config, f, ensure_ascii=False, indent=2)
    
    print("Создан файл example_config.json с примером конфигурации")
    print("\nДля генерации запроса:")
    print("1. Отредактируйте example_config.json")
    print("2. Запустите: python neo4j_query_generator.py")