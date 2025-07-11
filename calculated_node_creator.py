import json
import re
from typing import Dict, List, Optional, Any, Tuple
from neo4j_node_creator import Neo4jNodeCreator

class CalculatedNodeCreator(Neo4jNodeCreator):
    """
    Класс для создания расчетных узлов в Neo4j на основе существующих узлов "Счетное"
    """
    
    def __init__(self, config_path: str = "neo4j_config.json"):
        """
        Инициализация класса
        
        Args:
            config_path (str): Путь к файлу конфигурации Neo4j
        """
        super().__init__(config_path)
        self.processing_log = []
    
    def log_message(self, message: str) -> None:
        """
        Добавляет сообщение в лог обработки
        
        Args:
            message (str): Сообщение для логирования
        """
        print(message)
        self.processing_log.append(message)
    
    def get_node_data_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает данные узла "Счетное" по ID
        
        Args:
            node_id (str): ID узла
            
        Returns:
            Optional[Dict[str, Any]]: Данные узла или None если не найден
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                # Получаем федеральные данные
                federal_query = """
                MATCH (n)
                WHERE elementId(n) = $node_id AND (n:Счетное OR n:Расчетные)
                RETURN n.federal_values as federal_values, n.years as years, n.name as node_name, elementId(n) as node_id
                """
                
                result = session.run(federal_query, {"node_id": node_id})
                record = result.single()
                
                if not record:
                    self.log_message(f"Узел с ID '{node_id}' не найден в базе данных")
                    return None
                
                federal_values = record["federal_values"] or []
                years = record["years"] or []
                node_name = record["node_name"]
                
                # Получаем региональные данные
                regional_query = """
                MATCH (n)-[r:ПоРегион]->(reg:Регион)
                WHERE elementId(n) = $node_id AND (n:Счетное OR n:Расчетные)
                RETURN reg.name as region_name,
                       r.value_2016, r.value_2017, r.value_2018, r.value_2019, r.value_2020,
                       r.value_2021, r.value_2022, r.value_2023, r.value_2024
                ORDER BY reg.name
                """
                
                regional_result = session.run(regional_query, {"node_id": node_id})
                
                regions = []
                regional_values = []
                
                for reg_record in regional_result:
                    regions.append(reg_record["region_name"])
                    region_values = []
                    for year in years:
                        value = reg_record.get(f"r.value_{year}")  # Исправлено: возвращен правильный префикс "r."
                        region_values.append(value)
                    regional_values.append(region_values)
                
                return {
                    "node_id": node_id,
                    "node_name": node_name,
                    "federal_values": federal_values,
                    "years": years,
                    "regions": regions,
                    "regional_values": regional_values
                }
                
        except Exception as e:
            self.log_message(f"Ошибка получения данных узла с ID '{node_id}': {str(e)}")
            return None
    
    def parse_formula(self, formula: str) -> List[str]:
        """
        Парсит формулу и извлекает переменные node_id
        
        Args:
            formula (str): Математическая формула
            
        Returns:
            List[str]: Список переменных node_id в формуле
        """
        # Находим все переменные вида node_id1, node_id2, etc.
        node_pattern = r'\bnode_id\d+\b'
        nodes = re.findall(node_pattern, formula)
        
        return nodes
    
    def safe_divide(self, a: Optional[float], b: Optional[float]) -> Optional[float]:
        """
        Безопасное деление с обработкой None и деления на ноль
        
        Args:
            a: Делимое
            b: Делитель
            
        Returns:
            Optional[float]: Результат деления или None
        """
        if a is None or b is None or b == 0:
            return None
        return a / b
    
    def safe_multiply(self, a: Optional[float], b: Optional[float]) -> Optional[float]:
        """
        Безопасное умножение с обработкой None
        
        Args:
            a: Первый множитель
            b: Второй множитель
            
        Returns:
            Optional[float]: Результат умножения или None
        """
        if a is None or b is None:
            return None
        return a * b
    
    def safe_add(self, a: Optional[float], b: Optional[float]) -> Optional[float]:
        """
        Безопасное сложение с обработкой None
        
        Args:
            a: Первое слагаемое
            b: Второе слагаемое
            
        Returns:
            Optional[float]: Результат сложения или None
        """
        if a is None and b is None:
            return None
        if a is None:
            return b
        if b is None:
            return a
        return a + b
    
    def safe_subtract(self, a: Optional[float], b: Optional[float]) -> Optional[float]:
        """
        Безопасное вычитание с обработкой None
        
        Args:
            a: Уменьшаемое
            b: Вычитаемое
            
        Returns:
            Optional[float]: Результат вычитания или None
        """
        if a is None or b is None:
            return None
        return a - b
    
    def evaluate_formula_for_values(self, formula: str, node_values: List[Optional[float]]) -> Optional[float]:
        """
        Вычисляет формулу для конкретных значений узлов
        
        Args:
            formula (str): Математическая формула
            node_values (List[Optional[float]]): Значения узлов по порядку
            
        Returns:
            Optional[float]: Результат вычисления или None
        """
        try:
            # Проверяем, есть ли хотя бы одно не-None значение
            if all(v is None for v in node_values):
                return None
            
            # Проверяем синтаксис формулы
            try:
                compile(formula, '<string>', 'eval')
            except SyntaxError as se:
                self.log_message(f"ДИАГНОСТИКА: Синтаксическая ошибка в формуле: {str(se)}")
                return None
            
            # Заменяем None на 0 в соответствии с требованиями
            safe_values = {}
            for i, value in enumerate(node_values, 1):
                safe_values[f'node_id{i}'] = 0.0 if value is None else value
            
            # Проверяем деление на ноль для формул с делением
            if '/' in formula:
                # Находим знаменатель (предполагаем простые формулы вида (a / b))
                if 'node_id2' in safe_values and safe_values['node_id2'] == 0.0:
                    return None
            
            # Создаем безопасное окружение для eval
            safe_dict = {
                '__builtins__': {},
                **safe_values
            }
            
            # Вычисляем формулу
            result = eval(formula, safe_dict)
            
            return float(result) if result is not None else None
            
        except ZeroDivisionError:
            return None
        except Exception as e:
            self.log_message(f"Ошибка вычисления формулы '{formula}' с значениями {node_values}: {str(e)}")
            return None
    
    def calculate_values_for_all_years(self, formula: str, child_nodes_data: List[Dict[str, Any]]) -> List[Optional[float]]:
        """
        Вычисляет значения по формуле для всех лет
        
        Args:
            formula (str): Математическая формула
            child_nodes_data (List[Dict[str, Any]]): Данные дочерних узлов по порядку
            
        Returns:
            List[Optional[float]]: Список значений по годам
        """
        calculated_values = []
        
        # Получаем список лет (предполагаем, что у всех узлов одинаковые годы)
        years = self.years
        
        for year_index in range(len(years)):
            # Собираем значения для текущего года по порядку узлов
            year_values = []
            
            for node_data in child_nodes_data:
                federal_values = node_data.get("federal_values", [])
                if year_index < len(federal_values):
                    year_values.append(federal_values[year_index])
                else:
                    year_values.append(None)
            
            # Вычисляем значение для текущего года
            calculated_value = self.evaluate_formula_for_values(formula, year_values)
            calculated_values.append(calculated_value)
        
        return calculated_values
    
    def calculate_regional_values_for_all_years(self, formula: str, child_nodes_data: List[Dict[str, Any]]) -> Tuple[List[str], List[List[Optional[float]]]]:
        """
        Вычисляет региональные значения по формуле для всех лет и регионов
        
        Args:
            formula (str): Математическая формула
            child_nodes_data (List[Dict[str, Any]]): Данные дочерних узлов по порядку
            
        Returns:
            Tuple[List[str], List[List[Optional[float]]]]: Кортеж (список регионов, значения по регионам и годам)
        """
        # Получаем список регионов из первого узла (предполагаем, что у всех одинаковые регионы)
        regions = []
        for node_data in child_nodes_data:
            if node_data.get("regions"):
                regions = node_data["regions"]
                break
        
        if not regions:
            self.log_message("Не найдены регионы в дочерних узлах")
            return [], []
        
        regional_calculated_values = []
        
        for region_index in range(len(regions)):
            region_values_by_years = []
            
            for year_index in range(len(self.years)):
                # Собираем значения для текущего региона и года по порядку узлов
                year_region_values = []
                
                for node_data in child_nodes_data:
                    regional_values = node_data.get("regional_values", [])
                    if (region_index < len(regional_values) and
                        year_index < len(regional_values[region_index])):
                        year_region_values.append(regional_values[region_index][year_index])
                    else:
                        year_region_values.append(None)
                
                # Вычисляем значение для текущего региона и года
                calculated_value = self.evaluate_formula_for_values(formula, year_region_values)
                region_values_by_years.append(calculated_value)
            
            regional_calculated_values.append(region_values_by_years)
        
        return regions, regional_calculated_values
    
    def create_calculated_node(self, calc_config: Dict[str, Any]) -> Optional[str]:
        """
        Создает расчетный узел на основе конфигурации
        
        Args:
            calc_config (Dict[str, Any]): Конфигурация расчетного узла
            
        Returns:
            Optional[str]: ID созданного узла или None при ошибке
        """
        try:
            # Извлекаем параметры из конфигурации
            node_name = calc_config["node_name"]
            node_label = calc_config["node_label"]
            formula = calc_config["formula"]
            child_node_ids = calc_config["child_nodes"]
            
            self.log_message(f"Создание расчетного узла '{node_name}'")
            self.log_message(f"Формула: {formula}")
            self.log_message(f"Дочерние узлы (ID): {child_node_ids}")
            
            # Получаем данные всех дочерних узлов по порядку
            child_nodes_data = []
            missing_nodes = []
            
            for child_node_id in child_node_ids:
                node_data = self.get_node_data_by_id(child_node_id)
                if node_data:
                    child_nodes_data.append(node_data)
                    self.log_message(f"Данные узла '{node_data.get('node_name', child_node_id)}' получены")
                else:
                    missing_nodes.append(child_node_id)
                    # Создаем пустые данные для отсутствующего узла
                    child_nodes_data.append({
                        "node_id": child_node_id,
                        "node_name": f"Missing_{child_node_id}",
                        "federal_values": [0.0] * len(self.years),
                        "regional_values": []
                    })
                    self.log_message(f"Узел с ID '{child_node_id}' не найден, используются нулевые значения")
            
            if missing_nodes:
                self.log_message(f"Предупреждение: не найдены узлы с ID: {missing_nodes}")
            
            # Вычисляем федеральные значения
            federal_values = self.calculate_values_for_all_years(formula, child_nodes_data)
            self.log_message(f"Федеральные значения вычислены: {federal_values}")
            
            # Вычисляем региональные значения
            regions, regional_values = self.calculate_regional_values_for_all_years(formula, child_nodes_data)
            self.log_message(f"Региональные значения вычислены для {len(regions)} регионов")
            
            # Создаем узел в Neo4j
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                # Обрабатываем node_label
                if isinstance(node_label, list):
                    labels_str = ":".join(node_label)
                else:
                    labels_str = node_label
                
                # Подготавливаем свойства узла
                node_properties = {
                    "name": node_name,
                    "полное_название": calc_config.get("full_name", node_name),
                    "years": self.years,
                    "federal_values": federal_values,
                    "formula": formula,
                    "child_nodes": child_node_ids
                }
                
                # Очищаем null значения из списков
                cleaned_properties = {}
                for key, value in node_properties.items():
                    if isinstance(value, list):
                        # Заменяем None на 0.0 для числовых списков
                        if key == "federal_values":
                            cleaned_value = [0.0 if v is None else v for v in value]
                        else:
                            cleaned_value = [v for v in value if v is not None]
                        cleaned_properties[key] = cleaned_value
                    else:
                        cleaned_properties[key] = value
                
                # Формируем строку свойств для Cypher запроса
                properties_str = ", ".join([f"{key}: ${key}" for key in cleaned_properties.keys()])
                
                query = f"""
                CREATE (n:{labels_str} {{
                    {properties_str}
                }})
                RETURN elementId(n) as node_id
                """
                
                result = session.run(query, cleaned_properties)
                record = result.single()
                
                if record:
                    node_id = record["node_id"]
                    self.log_message(f"Расчетный узел '{node_name}' создан с ID: {node_id}")
                    
                    # Создаем связи с регионами
                    regional_links_created = self.create_regional_relationships(node_id, regions, regional_values)
                    self.log_message(f"Создано {regional_links_created} связей с регионами")
                    
                    # Создаем связи с дочерними узлами
                    child_links_created = self.create_child_relationships(node_id, child_nodes_data)
                    self.log_message(f"Создано {child_links_created} связей с дочерними узлами")
                    
                    return node_id
                else:
                    self.log_message(f"Ошибка создания расчетного узла '{node_name}'")
                    return None
                    
        except Exception as e:
            node_name = calc_config.get("node_name", "Unknown")
            self.log_message(f"Ошибка при создании расчетного узла '{node_name}': {str(e)}")
            return None
    
    def create_child_relationships(self, calculated_node_id: str, child_nodes_data: List[Dict[str, Any]]) -> int:
        """
        Создает связи между расчетным узлом и дочерними узлами
        
        Args:
            calculated_node_id (str): ID расчетного узла
            child_nodes_data (List[Dict[str, Any]]): Данные дочерних узлов
            
        Returns:
            int: Количество созданных связей
        """
        created_links = 0
        
        for child_data in child_nodes_data:
            child_node_id = child_data.get("node_id")
            child_node_name = child_data.get("node_name", "Unknown")
            
            if child_node_id:
                # Создаем связь "ОСНОВАН_НА" от расчетного к дочернему
                if self.create_relationship(calculated_node_id, child_node_id, "ОСНОВАН_НА"):
                    created_links += 1
                    self.log_message(f"Создана связь ОСНОВАН_НА: {calculated_node_id} -> {child_node_id} ({child_node_name})")
                
                # Создаем связь "ИСПОЛЬЗУЕТСЯ_В" от дочернего к расчетному
                if self.create_relationship(child_node_id, calculated_node_id, "ИСПОЛЬЗУЕТСЯ_В"):
                    created_links += 1
                    self.log_message(f"Создана связь ИСПОЛЬЗУЕТСЯ_В: {child_node_id} -> {calculated_node_id} ({child_node_name})")
        
        return created_links
    
    def process_calculated_node(self, calc_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает создание одного расчетного узла
        
        Args:
            calc_config (Dict[str, Any]): Конфигурация расчетного узла
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        self.processing_log = []  # Очищаем лог для нового узла
        
        try:
            # Подключаемся к Neo4j
            self.connect()
            
            # Создаем расчетный узел
            node_id = self.create_calculated_node(calc_config)
            
            result = {
                "success": node_id is not None,
                "node_id": node_id,
                "node_name": calc_config.get("node_name", "Unknown"),
                "processing_log": self.processing_log.copy()
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка обработки расчетного узла: {str(e)}",
                "node_name": calc_config.get("node_name", "Unknown"),
                "processing_log": self.processing_log.copy()
            }
        finally:
            self.disconnect()
    
    def process_calculated_nodes_batch(self, config_path: str) -> Dict[str, Any]:
        """
        Обрабатывает пакет расчетных узлов из JSON-конфигурации
        
        Args:
            config_path (str): Путь к файлу конфигурации пакета
            
        Returns:
            Dict[str, Any]: Результат обработки пакета
        """
        try:
            # Загружаем конфигурацию пакета
            with open(config_path, 'r', encoding='utf-8') as f:
                batch_config = json.load(f)
            
            calculated_nodes_config = batch_config.get("calculated_nodes", [])
            
            # Инициализируем результат
            result = {
                "success": True,
                "total_nodes": len(calculated_nodes_config),
                "created_nodes": 0,
                "failed_nodes": 0,
                "processing_log": [],
                "created_node_ids": []
            }
            
            result["processing_log"].append(f"Начинаем обработку {len(calculated_nodes_config)} расчетных узлов")
            
            # Подключаемся к Neo4j
            self.connect()
            
            # Обрабатываем каждый расчетный узел
            for i, calc_config in enumerate(calculated_nodes_config, 1):
                try:
                    node_name = calc_config.get("node_name", f"CalculatedNode_{i}")
                    result["processing_log"].append(f"Обработка расчетного узла {i}/{len(calculated_nodes_config)}: '{node_name}'")
                    
                    # Создаем расчетный узел
                    node_id = self.create_calculated_node(calc_config)
                    
                    if node_id:
                        result["created_nodes"] += 1
                        result["created_node_ids"].append(node_id)
                        result["processing_log"].append(f"Расчетный узел '{node_name}' создан успешно с ID: {node_id}")
                    else:
                        result["failed_nodes"] += 1
                        result["processing_log"].append(f"Ошибка создания расчетного узла '{node_name}'")
                        
                    # Добавляем лог обработки текущего узла
                    result["processing_log"].extend(self.processing_log)
                        
                except Exception as e:
                    result["failed_nodes"] += 1
                    result["processing_log"].append(f"Ошибка обработки расчетного узла {i}: {str(e)}")
            
            # Обновляем общий статус
            if result["failed_nodes"] > 0:
                result["success"] = False
            
            result["processing_log"].append(f"Обработка завершена: {result['created_nodes']}/{result['total_nodes']} расчетных узлов создано")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка обработки пакета расчетных узлов: {str(e)}",
                "processing_log": [f"Критическая ошибка: {str(e)}"]
            }
        finally:
            self.disconnect()


# Пример использования
if __name__ == "__main__":
    # Создаем экземпляр класса
    creator = CalculatedNodeCreator()
    
    try:
        # Обрабатываем пакет расчетных узлов из JSON-файла
        result = creator.process_calculated_nodes_batch("calculated_nodes_config.json")
        
        print("\n=== РЕЗУЛЬТАТ ОБРАБОТКИ ПАКЕТА РАСЧЕТНЫХ УЗЛОВ ===")
        print(f"Успех: {result['success']}")
        print(f"Создано узлов: {result.get('created_nodes', 0)}")
        print(f"Ошибок: {result.get('failed_nodes', 0)}")
        print(f"Всего узлов: {result.get('total_nodes', 0)}")
        
        if result.get('error'):
            print(f"Ошибка: {result['error']}")
        
        print("\n=== ЛОГ ОБРАБОТКИ ===")
        for log_entry in result.get('processing_log', []):
            print(log_entry)
            
        if result.get('created_node_ids'):
            print(f"\n=== СОЗДАННЫЕ РАСЧЕТНЫЕ УЗЛЫ ===")
            for node_id in result['created_node_ids']:
                print(f"ID: {node_id}")
                
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")