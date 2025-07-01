import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from neo4j import GraphDatabase
import warnings

# Подавляем предупреждения pandas
warnings.filterwarnings('ignore')

__version__ = "1.0.0"
__author__ = "Neo4j Node Creator"

# Получаем путь к директории проекта
PROJECT_ROOT = Path(__file__).parent.absolute()
BASE_DIR = os.path.join(PROJECT_ROOT, "БД")

class Neo4jNodeCreator:
    """
    Класс для создания узлов Neo4j из статистических данных
    """
    
    def __init__(self, config_path: str = "neo4j_config.json"):
        """
        Инициализация подключения к Neo4j
        
        Args:
            config_path (str): Путь к файлу конфигурации Neo4j
        """
        self.config = self._load_neo4j_config(config_path)
        self.driver = None
        self.years = ["2021", "2022", "2023", "2024"]
        
    def _load_neo4j_config(self, config_path: str) -> Dict[str, str]:
        """
        Загружает конфигурацию Neo4j из файла
        
        Args:
            config_path (str): Путь к файлу конфигурации
            
        Returns:
            Dict[str, str]: Конфигурация подключения
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Ошибка загрузки конфигурации Neo4j: {str(e)}")
    
    def connect(self) -> None:
        """
        Устанавливает соединение с Neo4j
        """
        try:
            self.driver = GraphDatabase.driver(
                self.config["NEO4J_URI"],
                auth=(self.config["NEO4J_USERNAME"], self.config["NEO4J_PASSWORD"])
            )
            # Проверяем соединение
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                session.run("RETURN 1")
            print("Успешное подключение к Neo4j")
        except Exception as e:
            raise Exception(f"Ошибка подключения к Neo4j: {str(e)}")
    
    def disconnect(self) -> None:
        """
        Закрывает соединение с Neo4j
        """
        if self.driver:
            self.driver.close()
            print("Соединение с Neo4j закрыто")
    
    def get_federal_file_path(self, year: str, table_number: str) -> str:
        """
        Формирует путь к федеральному файлу для конкретного года и номера таблицы.
        
        Args:
            year (str): Год
            table_number (str): Номер таблицы
        
        Returns:
            str: Полный путь к файлу
        """
        return os.path.join(BASE_DIR, year, f"Раздел {table_number}.csv")
    
    def get_regional_file_path(self, year: str, region_name: str, table_number: str) -> str:
        """
        Формирует путь к региональному файлу для конкретного года, региона и номера таблицы.
        
        Args:
            year (str): Год
            region_name (str): Название региона
            table_number (str): Номер таблицы
        
        Returns:
            str: Полный путь к файлу
        """
        return os.path.join(BASE_DIR, year, year, region_name, f"Раздел {table_number}.csv")
    
    def get_cell_value(self, file_path: str, column_number: int, row_number: int) -> Optional[str]:
        """
        Получает значение ячейки из CSV файла по заданным параметрам.
        
        Args:
            file_path (str): Путь к CSV файлу
            column_number (int): Номер колонки (начиная с 1)
            row_number (int): Номер строки (начиная с 1)
        
        Returns:
            Optional[str]: Значение ячейки или None при ошибке
        """
        try:
            # Читаем CSV файл
            df = pd.read_csv(file_path, header=None, encoding='utf-8', sep=';')
            
            # Находим строку с заголовком (содержит "№ строки")
            header_row_index = None
            for idx, row in df.iterrows():
                if isinstance(row[0], str) and "№ строки" in str(row[0]):
                    header_row_index = idx
                    break
            
            if header_row_index is None:
                return None
            
            # Данные начинаются со следующей строки после заголовка
            data_start_index = header_row_index + 1
            
            # Получаем реальный индекс строки с учетом смещения
            actual_row_index = data_start_index + row_number - 1
            
            # Проверяем, что индексы в пределах DataFrame
            if actual_row_index >= len(df) or column_number - 1 >= len(df.columns):
                return None
            
            # Получаем значение ячейки (column_number - 1, так как в pandas индексация с 0)
            cell_value = df.iloc[actual_row_index, column_number - 1]
            
            # Проверяем на NaN и конвертируем в строку
            if pd.isna(cell_value):
                return None
            
            return str(cell_value).strip()
            
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {str(e)}")
            return None
    
    def validate_numeric_value(self, value_str: str) -> Optional[float]:
        """
        Валидирует и преобразует строковое значение в число.
        
        Args:
            value_str (str): Строковое значение
        
        Returns:
            Optional[float]: Числовое значение или None при ошибке
        """
        if not value_str or value_str.strip() == "":
            return None
        
        try:
            # Убираем лишние пробелы и заменяем запятые на точки
            cleaned_value = value_str.strip().replace(',', '.')
            
            # Пытаемся преобразовать в число
            numeric_value = float(cleaned_value)
            
            return numeric_value
            
        except (ValueError, TypeError):
            return None
    
    def collect_federal_data(self, table_number: str, column_number: int, row_number: int) -> List[Optional[float]]:
        """
        Собирает федеральные данные за все годы для указанной таблицы и ячейки.
        
        Args:
            table_number (str): Номер таблицы (например, "2.1.1")
            column_number (int): Номер колонки (начиная с 1)
            row_number (int): Номер строки (начиная с 1)
        
        Returns:
            List[Optional[float]]: Список значений по годам (None для отсутствующих данных)
        """
        federal_values = []
        
        for year in self.years:
            file_path = self.get_federal_file_path(year, table_number)
            
            if os.path.exists(file_path):
                cell_value = self.get_cell_value(file_path, column_number, row_number)
                
                if cell_value is not None:
                    numeric_value = self.validate_numeric_value(cell_value)
                    federal_values.append(numeric_value)
                else:
                    federal_values.append(None)
            else:
                print(f"Федеральный файл не найден: {file_path}")
                federal_values.append(None)
        
        return federal_values
    
    def get_regions_list(self, year: str = "2024") -> List[str]:
        """
        Получает список регионов из файловой системы.
        
        Args:
            year (str): Год для получения списка регионов
        
        Returns:
            List[str]: Список названий регионов
        """
        regions_dir = os.path.join(BASE_DIR, year, year)
        
        if not os.path.exists(regions_dir):
            print(f"Директория регионов не найдена: {regions_dir}")
            return []
        
        regions = [name for name in os.listdir(regions_dir) 
                  if os.path.isdir(os.path.join(regions_dir, name)) and not name.startswith('.')]
        
        print(f"Найдено {len(regions)} регионов")
        return regions
    
    def collect_regional_data(self, table_number: str, column_number: int, row_number: int) -> Tuple[List[str], List[List[Optional[float]]]]:
        """
        Собирает региональные данные по всем регионам и годам для указанной таблицы и ячейки.
        
        Args:
            table_number (str): Номер таблицы (например, "2.1.1")
            column_number (int): Номер колонки (начиная с 1)
            row_number (int): Номер строки (начиная с 1)
        
        Returns:
            Tuple[List[str], List[List[Optional[float]]]]: Кортеж (список регионов, список значений по годам для каждого региона)
        """
        regions = self.get_regions_list()
        regional_values = []
        
        for region in regions:
            region_values = []
            
            for year in self.years:
                file_path = self.get_regional_file_path(year, region, table_number)
                
                if os.path.exists(file_path):
                    cell_value = self.get_cell_value(file_path, column_number, row_number)
                    
                    if cell_value is not None:
                        numeric_value = self.validate_numeric_value(cell_value)
                        region_values.append(numeric_value)
                    else:
                        region_values.append(None)
                else:
                    region_values.append(None)
            
            regional_values.append(region_values)
            print(f"Регион {region}: {region_values}")
        
        return regions, regional_values
    
    def create_node(self, node_config: Dict[str, Any]) -> Optional[str]:
        """
        Создает узел в Neo4j с собранными данными.
        
        Args:
            node_config (Dict[str, Any]): Конфигурация узла
        
        Returns:
            Optional[str]: ID созданного узла или None при ошибке
        """
        try:
            # Извлекаем параметры из конфигурации
            node_name = node_config["node_name"]
            node_label = node_config["node_label"]
            table_number = str(node_config["table_number"])
            column_number = node_config["column"]
            row_number = node_config["row"]
            
            print(f"Создание узла '{node_name}' для таблицы {table_number}, колонка {column_number}, строка {row_number}")
            
            # Собираем федеральные данные
            federal_values = self.collect_federal_data(table_number, column_number, row_number)
            print(f"Федеральные данные: {federal_values}")
            
            # Собираем региональные данные
            regions, regional_values = self.collect_regional_data(table_number, column_number, row_number)
            print(f"Региональные данные собраны для {len(regions)} регионов")
            
            # Создаем основной узел в Neo4j (без региональных данных)
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                # Обрабатываем node_label - может быть строкой или списком
                if isinstance(node_label, list):
                    labels_str = ":".join(node_label)
                else:
                    labels_str = node_label
                
                query = f"""
                CREATE (n:{labels_str} {{
                    name: $name,
                    years: $years,
                    federal_values: $federal_values,
                    table_number: $table_number,
                    column: $column,
                    row: $row
                }})
                RETURN elementId(n) as node_id
                """
                
                result = session.run(query, {
                    "name": node_name,
                    "years": self.years,
                    "federal_values": federal_values,
                    "table_number": table_number,
                    "column": column_number,
                    "row": row_number
                })
                
                record = result.single()
                if record:
                    node_id = record["node_id"]
                    print(f"Узел '{node_name}' создан с ID: {node_id}")
                    
                    # Создаем связи с регионами
                    regional_links_created = self.create_regional_relationships(node_id, regions, regional_values)
                    print(f"Создано {regional_links_created} связей с регионами")
                    
                    return node_id
                else:
                    print(f"Ошибка создания узла '{node_name}'")
                    return None
                    
        except Exception as e:
            print(f"Ошибка при создании узла '{node_name}': {str(e)}")
            return None
    
    def find_or_create_region_node(self, region_name: str) -> Optional[str]:
        """
        Находит существующий узел региона или создает новый.
        
        Args:
            region_name (str): Название региона
        
        Returns:
            Optional[str]: ID узла региона или None при ошибке
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                # Сначала ищем существующий узел региона
                find_query = """
                MATCH (r:Регион {name: $region_name})
                RETURN elementId(r) as region_id
                """
                
                result = session.run(find_query, {"region_name": region_name})
                record = result.single()
                
                if record:
                    return record["region_id"]
                
                # Если не найден, создаем новый
                create_query = """
                CREATE (r:Регион {name: $region_name})
                RETURN elementId(r) as region_id
                """
                
                result = session.run(create_query, {"region_name": region_name})
                record = result.single()
                
                if record:
                    region_id = record["region_id"]
                    print(f"Создан узел региона '{region_name}' с ID: {region_id}")
                    return region_id
                else:
                    print(f"Ошибка создания узла региона '{region_name}'")
                    return None
                    
        except Exception as e:
            print(f"Ошибка при работе с узлом региона '{region_name}': {str(e)}")
            return None
    
    def create_regional_relationships(self, main_node_id: str, regions: List[str], regional_values: List[List[Optional[float]]]) -> int:
        """
        Создает связи от основного узла к узлам регионов с данными по годам в свойствах связей.
        
        Args:
            main_node_id (str): ID основного узла
            regions (List[str]): Список регионов
            regional_values (List[List[Optional[float]]]): Данные по регионам и годам
        
        Returns:
            int: Количество созданных связей
        """
        created_links = 0
        
        for i, region in enumerate(regions):
            try:
                # Находим или создаем узел региона
                region_id = self.find_or_create_region_node(region)
                
                if region_id and i < len(regional_values):
                    # Подготавливаем данные по годам для свойств связи
                    region_data = regional_values[i]
                    
                    # Создаем словарь со значениями по годам
                    year_values = {}
                    for j, year in enumerate(self.years):
                        if j < len(region_data):
                            year_values[f"value_{year}"] = region_data[j]
                        else:
                            year_values[f"value_{year}"] = None
                    
                    # Создаем связь с данными по годам в свойствах
                    if self.create_relationship_with_properties(main_node_id, region_id, "ПоРегион", year_values):
                        created_links += 1
                        print(f"Создана связь ПоРегион: {main_node_id} -> {region_id} ({region})")
                    
            except Exception as e:
                print(f"Ошибка при создании связи с регионом '{region}': {str(e)}")
        
        return created_links
    
    def create_relationship_with_properties(self, from_node_id: str, to_node_id: str, relationship_type: str, properties: Dict[str, Any]) -> bool:
        """
        Создает связь между узлами с дополнительными свойствами.
        
        Args:
            from_node_id (str): ID исходного узла
            to_node_id (str): ID целевого узла
            relationship_type (str): Тип связи
            properties (Dict[str, Any]): Свойства связи
        
        Returns:
            bool: True если связь создана успешно, False иначе
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                query = f"""
                MATCH (from_node), (to_node)
                WHERE elementId(from_node) = $from_id AND elementId(to_node) = $to_id
                CREATE (from_node)-[r:{relationship_type} $properties]->(to_node)
                RETURN r
                """
                
                result = session.run(query, {
                    "from_id": from_node_id,
                    "to_id": to_node_id,
                    "properties": properties
                })
                
                if result.single():
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Ошибка при создании связи '{relationship_type}' со свойствами: {str(e)}")
            return False
    
    def create_relationship(self, from_node_id: str, to_node_id: str, relationship_type: str) -> bool:
        """
        Создает связь между узлами в Neo4j.
        
        Args:
            from_node_id (str): ID исходного узла
            to_node_id (str): ID целевого узла
            relationship_type (str): Тип связи
        
        Returns:
            bool: True если связь создана успешно, False иначе
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                query = f"""
                MATCH (from_node), (to_node)
                WHERE elementId(from_node) = $from_id AND elementId(to_node) = $to_id
                CREATE (from_node)-[r:{relationship_type}]->(to_node)
                RETURN r
                """
                
                result = session.run(query, {
                    "from_id": from_node_id,
                    "to_id": to_node_id
                })
                
                if result.single():
                    print(f"Связь '{relationship_type}' создана: {from_node_id} -> {to_node_id}")
                    return True
                else:
                    print(f"Ошибка создания связи '{relationship_type}': {from_node_id} -> {to_node_id}")
                    return False
                    
        except Exception as e:
            print(f"Ошибка при создании связи '{relationship_type}': {str(e)}")
            return False
    
    def process_batch(self, batch_config_path: str) -> Dict[str, Any]:
        """
        Обрабатывает пакет узлов из JSON-конфигурации.
        
        Args:
            batch_config_path (str): Путь к файлу конфигурации пакета
        
        Returns:
            Dict[str, Any]: Результат обработки пакета
        """
        try:
            # Загружаем конфигурацию пакета
            with open(batch_config_path, 'r', encoding='utf-8') as f:
                batch_config = json.load(f)
            
            nodes_config = batch_config.get("nodes", [])
            
            # Инициализируем результат
            result = {
                "success": True,
                "total_nodes": len(nodes_config),
                "created_nodes": 0,
                "failed_nodes": 0,
                "total_relationships": 0,
                "processing_log": [],
                "created_node_ids": []
            }
            
            # Подключаемся к Neo4j
            self.connect()
            
            # Обрабатываем каждый узел
            for i, node_config in enumerate(nodes_config, 1):
                try:
                    node_name = node_config.get("node_name", f"Node_{i}")
                    result["processing_log"].append(f"Обработка узла {i}/{len(nodes_config)}: '{node_name}'")
                    
                    # Создаем узел
                    node_id = self.create_node(node_config)
                    
                    if node_id:
                        result["created_nodes"] += 1
                        result["created_node_ids"].append(node_id)
                        result["processing_log"].append(f"Узел '{node_name}' создан успешно")
                        
                        # Создаем связи, если они указаны
                        relationships = node_config.get("relationships", [])
                        for rel in relationships:
                            from_id = rel.get("from_id")
                            rel_type = rel.get("type")
                            
                            if from_id and rel_type:
                                if self.create_relationship(from_id, node_id, rel_type):
                                    result["total_relationships"] += 1
                                    result["processing_log"].append(f"Связь '{rel_type}' создана для узла '{node_name}'")
                                else:
                                    result["processing_log"].append(f"Ошибка создания связи '{rel_type}' для узла '{node_name}'")
                    else:
                        result["failed_nodes"] += 1
                        result["processing_log"].append(f"Ошибка создания узла '{node_name}'")
                        
                except Exception as e:
                    result["failed_nodes"] += 1
                    result["processing_log"].append(f"Ошибка обработки узла {i}: {str(e)}")
            
            # Обновляем общий статус
            if result["failed_nodes"] > 0:
                result["success"] = False
            
            result["processing_log"].append(f"Обработка завершена: {result['created_nodes']}/{result['total_nodes']} узлов создано")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка обработки пакета: {str(e)}",
                "processing_log": [f"Критическая ошибка: {str(e)}"]
            }
        finally:
            self.disconnect()

# Пример использования
if __name__ == "__main__":
    # Создаем экземпляр класса
    creator = Neo4jNodeCreator()
    
    try:
        # Пример обработки пакета узлов
        result = creator.process_batch("batch_nodes_config.json")
        
        print("\n=== РЕЗУЛЬТАТ ОБРАБОТКИ ===")
        print(f"Успех: {result['success']}")
        print(f"Создано узлов: {result.get('created_nodes', 0)}")
        print(f"Ошибок: {result.get('failed_nodes', 0)}")
        print(f"Создано связей: {result.get('total_relationships', 0)}")
        
        print("\n=== ЛОГ ОБРАБОТКИ ===")
        for log_entry in result.get('processing_log', []):
            print(log_entry)
            
        if result.get('created_node_ids'):
            print(f"\n=== СОЗДАННЫЕ УЗЛЫ ===")
            for node_id in result['created_node_ids']:
                print(f"ID: {node_id}")
                
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")