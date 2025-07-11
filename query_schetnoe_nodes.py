#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для расширенного запроса узлов с меткой "Счетное" из базы данных Neo4j
с получением всех связанных узлов и их полных связей
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from neo4j import GraphDatabase
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schetnoe_query.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SchetnoeNodesQuery:
    """
    Класс для расширенного запроса узлов с меткой "Счетное" из Neo4j
    с получением всех связанных узлов и их полных связей
    """
    
    def __init__(self, config_path: str = "neo4j_config.json"):
        """
        Инициализация подключения к Neo4j
        
        Args:
            config_path (str): Путь к файлу конфигурации Neo4j
        """
        self.config = self._load_neo4j_config(config_path)
        self.driver = None
        
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
            logger.error(f"Ошибка загрузки конфигурации Neo4j: {str(e)}")
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
            logger.info("Успешное подключение к Neo4j")
        except Exception as e:
            logger.error(f"Ошибка подключения к Neo4j: {str(e)}")
            raise Exception(f"Ошибка подключения к Neo4j: {str(e)}")
    
    def disconnect(self) -> None:
        """
        Закрывает соединение с Neo4j
        """
        if self.driver:
            self.driver.close()
            logger.info("Соединение с Neo4j закрыто")
    
    def _generate_color_from_label(self, label: str) -> str:
        """
        Генерирует уникальный цвет для метки на основе хеша
        
        Args:
            label (str): Метка узла
            
        Returns:
            str: HEX цвет
        """
        # Создаем хеш от названия метки
        hash_object = hashlib.md5(label.encode('utf-8'))
        hex_dig = hash_object.hexdigest()
        
        # Берем первые 6 символов как цвет
        color = '#' + hex_dig[:6]
        
        # Убеждаемся, что цвет достаточно яркий (не слишком темный)
        r = int(hex_dig[0:2], 16)
        g = int(hex_dig[2:4], 16)
        b = int(hex_dig[4:6], 16)
        
        # Если цвет слишком темный, осветляем его
        if (r + g + b) < 200:
            r = min(255, r + 100)
            g = min(255, g + 100)
            b = min(255, b + 100)
            color = f'#{r:02x}{g:02x}{b:02x}'
        
        return color
    
    def get_schetnoe_nodes(self) -> List[Dict[str, Any]]:
        """
        Получает все узлы с меткой "Счетное"
        
        Returns:
            List[Dict[str, Any]]: Список узлов "Счетное"
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                query = """
                MATCH (schetnoe:Счетное)
                RETURN 
                    elementId(schetnoe) as node_id,
                    schetnoe.name as node_name,
                    schetnoe.полное_название as node_full_name,
                    schetnoe.table_number as table_number,
                    schetnoe.column as column,
                    schetnoe.row as row,
                    schetnoe.years as years,
                    schetnoe.federal_values as federal_values,
                    labels(schetnoe) as node_labels,
                    properties(schetnoe) as node_properties
                ORDER BY schetnoe.name
                """
                
                result = session.run(query)
                nodes_data = []
                
                for record in result:
                    node_info = {
                        'node_id': record['node_id'],
                        'node_name': record['node_name'],
                        'node_full_name': record['node_full_name'],
                        'table_number': record['table_number'],
                        'column': record['column'],
                        'row': record['row'],
                        'years': record['years'],
                        'federal_values': record['federal_values'],
                        'node_labels': record['node_labels'],
                        'node_properties': dict(record['node_properties']) if record['node_properties'] else {}
                    }
                    nodes_data.append(node_info)
                
                logger.info(f"Найдено {len(nodes_data)} узлов с меткой 'Счетное'")
                return nodes_data
                
        except Exception as e:
            logger.error(f"Ошибка при получении узлов 'Счетное': {str(e)}")
            raise Exception(f"Ошибка при получении узлов 'Счетное': {str(e)}")
    
    def get_external_nodes(self) -> List[Dict[str, Any]]:
        """
        Получает все узлы, которые имеют исходящие связи к счетным узлам
        
        Returns:
            List[Dict[str, Any]]: Список внешних узлов
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                query = """
                MATCH (external)-[rel]->(schetnoe:Счетное)
                WHERE NOT external:Счетное
                RETURN DISTINCT
                    elementId(external) as node_id,
                    external.name as node_name,
                    external.полное_название as node_full_name,
                    labels(external) as node_labels,
                    properties(external) as node_properties
                ORDER BY external.name
                """
                
                result = session.run(query)
                nodes_data = []
                
                for record in result:
                    node_info = {
                        'node_id': record['node_id'],
                        'node_name': record['node_name'],
                        'node_full_name': record['node_full_name'],
                        'node_labels': record['node_labels'],
                        'node_properties': dict(record['node_properties']) if record['node_properties'] else {}
                    }
                    nodes_data.append(node_info)
                
                logger.info(f"Найдено {len(nodes_data)} внешних узлов, связанных со счетными")
                return nodes_data
                
        except Exception as e:
            logger.error(f"Ошибка при получении внешних узлов: {str(e)}")
            raise Exception(f"Ошибка при получении внешних узлов: {str(e)}")
    
    def get_all_relations_for_external_nodes(self, external_node_ids: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Получает все связи (входящие и исходящие) для внешних узлов
        
        Args:
            external_node_ids (List[str]): Список ID внешних узлов
            
        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (связи, дополнительные узлы)
        """
        if not external_node_ids:
            return [], []
            
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                # Создаем параметры для запроса
                query = """
                MATCH (source)-[rel]->(target)
                WHERE (elementId(source) IN $external_ids OR elementId(target) IN $external_ids)
                AND type(rel) <> 'ПоРегион'
                RETURN DISTINCT
                    elementId(source) as source_id,
                    source.name as source_name,
                    source.полное_название as source_full_name,
                    labels(source) as source_labels,
                    properties(source) as source_properties,
                    elementId(target) as target_id,
                    target.name as target_name,
                    target.полное_название as target_full_name,
                    labels(target) as target_labels,
                    properties(target) as target_properties,
                    type(rel) as relation_type,
                    properties(rel) as relation_properties
                ORDER BY source.name, target.name
                """
                
                result = session.run(query, external_ids=external_node_ids)
                relations_data = []
                additional_nodes = {}  # Используем словарь для избежания дубликатов
                
                for record in result:
                    # Добавляем связь
                    relation_info = {
                        'source_id': record['source_id'],
                        'source_name': record['source_name'],
                        'source_full_name': record['source_full_name'],
                        'source_labels': record['source_labels'],
                        'source_properties': dict(record['source_properties']) if record['source_properties'] else {},
                        'target_id': record['target_id'],
                        'target_name': record['target_name'],
                        'target_full_name': record['target_full_name'],
                        'target_labels': record['target_labels'],
                        'target_properties': dict(record['target_properties']) if record['target_properties'] else {},
                        'relation_type': record['relation_type'],
                        'relation_properties': dict(record['relation_properties']) if record['relation_properties'] else {}
                    }
                    relations_data.append(relation_info)
                    
                    # Добавляем узлы источника и цели в дополнительные узлы
                    for node_type in ['source', 'target']:
                        node_id = record[f'{node_type}_id']
                        if node_id not in additional_nodes:
                            additional_nodes[node_id] = {
                                'node_id': node_id,
                                'node_name': record[f'{node_type}_name'],
                                'node_full_name': record[f'{node_type}_full_name'],
                                'node_labels': record[f'{node_type}_labels'],
                                'node_properties': dict(record[f'{node_type}_properties']) if record[f'{node_type}_properties'] else {}
                            }
                
                additional_nodes_list = list(additional_nodes.values())
                
                logger.info(f"Найдено {len(relations_data)} связей для внешних узлов")
                logger.info(f"Найдено {len(additional_nodes_list)} дополнительных узлов")
                
                return relations_data, additional_nodes_list
                
        except Exception as e:
            logger.error(f"Ошибка при получении связей внешних узлов: {str(e)}")
            raise Exception(f"Ошибка при получении связей внешних узлов: {str(e)}")
    
    def get_relations_to_schetnoe_nodes(self) -> List[Dict[str, Any]]:
        """
        Получает все связи к счетным узлам
        
        Returns:
            List[Dict[str, Any]]: Список связей к счетным узлам
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                query = """
                MATCH (source)-[rel]->(schetnoe:Счетное)
                RETURN
                    elementId(source) as source_id,
                    source.name as source_name,
                    source.полное_название as source_full_name,
                    labels(source) as source_labels,
                    properties(source) as source_properties,
                    elementId(schetnoe) as target_id,
                    schetnoe.name as target_name,
                    schetnoe.полное_название as target_full_name,
                    labels(schetnoe) as target_labels,
                    properties(schetnoe) as target_properties,
                    type(rel) as relation_type,
                    properties(rel) as relation_properties
                ORDER BY source.name, schetnoe.name
                """
                
                result = session.run(query)
                relations_data = []
                
                for record in result:
                    relation_info = {
                        'source_id': record['source_id'],
                        'source_name': record['source_name'],
                        'source_full_name': record['source_full_name'],
                        'source_labels': record['source_labels'],
                        'source_properties': dict(record['source_properties']) if record['source_properties'] else {},
                        'target_id': record['target_id'],
                        'target_name': record['target_name'],
                        'target_full_name': record['target_full_name'],
                        'target_labels': record['target_labels'],
                        'target_properties': dict(record['target_properties']) if record['target_properties'] else {},
                        'relation_type': record['relation_type'],
                        'relation_properties': dict(record['relation_properties']) if record['relation_properties'] else {}
                    }
                    relations_data.append(relation_info)
                
                logger.info(f"Найдено {len(relations_data)} связей к счетным узлам")
                return relations_data
                
        except Exception as e:
            logger.error(f"Ошибка при получении связей к счетным узлам: {str(e)}")
            raise Exception(f"Ошибка при получении связей к счетным узлам: {str(e)}")
    
    def generate_dynamic_color_mapping(self, all_nodes: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Генерирует динамическую цветовую схему для всех найденных меток
        
        Args:
            all_nodes (List[Dict[str, Any]]): Все узлы
            
        Returns:
            Dict[str, str]: Маппинг метка -> цвет
        """
        # Собираем все уникальные метки
        all_labels = set()
        for node in all_nodes:
            if 'node_labels' in node and node['node_labels']:
                all_labels.update(node['node_labels'])
        
        # Генерируем цвета для каждой метки
        color_mapping = {}
        
        # Фиксированный цвет для счетных узлов
        if 'Счетное' in all_labels:
            color_mapping['Счетное'] = '#808080'  # Серый
            all_labels.remove('Счетное')
        
        # Генерируем цвета для остальных меток
        for label in sorted(all_labels):  # Сортируем для стабильности
            color_mapping[label] = self._generate_color_from_label(label)
        
        logger.info(f"Сгенерирована цветовая схема для {len(color_mapping)} меток")
        return color_mapping
    
    def get_extended_schetnoe_data(self) -> Dict[str, Any]:
        """
        Получает расширенные данные согласно новой логике:
        1. Все счетные узлы
        2. Все внешние узлы (связанные со счетными)
        3. Все связи внешних узлов с любыми узлами
        4. Динамическая цветовая схема
        
        Returns:
            Dict[str, Any]: Расширенная структура данных
        """
        try:
            logger.info("Начинаем получение расширенных данных по новой логике")
            
            # 1. Получаем все счетные узлы
            logger.info("Этап 1: Получение счетных узлов")
            schetnoe_nodes = self.get_schetnoe_nodes()
            
            # 2. Получаем все внешние узлы (которые связаны со счетными)
            logger.info("Этап 2: Получение внешних узлов")
            external_nodes = self.get_external_nodes()
            external_node_ids = [node['node_id'] for node in external_nodes]
            
            # 3. Получаем все связи внешних узлов
            logger.info("Этап 3: Получение всех связей внешних узлов")
            external_relations, additional_nodes_from_relations = self.get_all_relations_for_external_nodes(external_node_ids)
            
            # 4. Получаем связи к счетным узлам
            logger.info("Этап 4: Получение связей к счетным узлам")
            schetnoe_relations = self.get_relations_to_schetnoe_nodes()
            
            # 5. Объединяем все узлы для генерации цветовой схемы
            all_nodes = schetnoe_nodes + external_nodes + additional_nodes_from_relations
            
            # Удаляем дубликаты узлов по ID
            unique_nodes = {}
            for node in all_nodes:
                node_id = node['node_id']
                if node_id not in unique_nodes:
                    unique_nodes[node_id] = node
            
            all_unique_nodes = list(unique_nodes.values())
            
            # 6. Генерируем динамическую цветовую схему
            logger.info("Этап 5: Генерация динамической цветовой схемы")
            color_mapping = self.generate_dynamic_color_mapping(all_unique_nodes)
            
            # 7. Объединяем все связи
            all_relations = schetnoe_relations + external_relations
            
            # 8. Собираем метаданные
            all_labels = set()
            for node in all_unique_nodes:
                if 'node_labels' in node and node['node_labels']:
                    all_labels.update(node['node_labels'])
            
            # 9. Формируем итоговую структуру данных
            extended_data = {
                'schetnoe_nodes': schetnoe_nodes,
                'additional_nodes': [node for node in all_unique_nodes if not any(label == 'Счетное' for label in node.get('node_labels', []))],
                'relations_between_additional': all_relations,
                'metadata': {
                    'schetnoe_nodes_count': len(schetnoe_nodes),
                    'external_nodes_count': len(external_nodes),
                    'additional_nodes_count': len(all_unique_nodes) - len(schetnoe_nodes),
                    'total_relations_count': len(all_relations),
                    'schetnoe_relations_count': len(schetnoe_relations),
                    'external_relations_count': len(external_relations),
                    'discovered_labels': sorted(list(all_labels)),
                    'color_mapping': color_mapping,
                    'total_unique_nodes': len(all_unique_nodes)
                }
            }
            
            logger.info("Расширенные данные успешно сформированы:")
            logger.info(f"- Счетных узлов: {len(schetnoe_nodes)}")
            logger.info(f"- Внешних узлов: {len(external_nodes)}")
            logger.info(f"- Всего уникальных узлов: {len(all_unique_nodes)}")
            logger.info(f"- Всего связей: {len(all_relations)}")
            logger.info(f"- Обнаруженных меток: {len(all_labels)}")
            logger.info(f"- Цветов в схеме: {len(color_mapping)}")
            
            return extended_data
            
        except Exception as e:
            logger.error(f"Ошибка при получении расширенных данных: {str(e)}")
            raise Exception(f"Ошибка при получении расширенных данных: {str(e)}")
    
    def save_results_to_json(self, data: Any, filename: str = "schetnoe_nodes_results.json") -> None:
        """
        Сохраняет результаты в JSON файл
        
        Args:
            data (Any): Данные для сохранения
            filename (str): Имя файла для сохранения
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Результаты сохранены в файл: {filename}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в файл {filename}: {str(e)}")
            raise Exception(f"Ошибка при сохранении в файл {filename}: {str(e)}")
    
    def print_extended_summary(self, extended_data: Dict[str, Any]) -> None:
        """
        Выводит расширенную сводку по данным
        
        Args:
            extended_data (Dict[str, Any]): Расширенные данные
        """
        metadata = extended_data.get('metadata', {})
        
        print(f"\n=== РАСШИРЕННАЯ СВОДКА ПО ДАННЫМ ===")
        print(f"Счетных узлов: {metadata.get('schetnoe_nodes_count', 0)}")
        print(f"Внешних узлов: {metadata.get('external_nodes_count', 0)}")
        print(f"Дополнительных узлов: {metadata.get('additional_nodes_count', 0)}")
        print(f"Всего уникальных узлов: {metadata.get('total_unique_nodes', 0)}")
        print(f"Всего связей: {metadata.get('total_relations_count', 0)}")
        print(f"  - Связей к счетным: {metadata.get('schetnoe_relations_count', 0)}")
        print(f"  - Связей внешних узлов: {metadata.get('external_relations_count', 0)}")
        
        discovered_labels = metadata.get('discovered_labels', [])
        print(f"\nОбнаруженные метки ({len(discovered_labels)}):")
        for label in discovered_labels:
            color = metadata.get('color_mapping', {}).get(label, '#000000')
            print(f"  - {label}: {color}")
        
        print(f"\nПримеры счетных узлов:")
        schetnoe_nodes = extended_data.get('schetnoe_nodes', [])
        for i, node in enumerate(schetnoe_nodes[:3]):
            print(f"  {i+1}. {node.get('node_name', 'Без названия')}")
            print(f"     ID: {node.get('node_id')}")
            print(f"     Полное название: {node.get('node_full_name', 'Не указано')}")
        
        print(f"\nПримеры дополнительных узлов:")
        additional_nodes = extended_data.get('additional_nodes', [])
        for i, node in enumerate(additional_nodes[:3]):
            labels = ', '.join(node.get('node_labels', []))
            print(f"  {i+1}. {node.get('node_name', 'Без названия')} [{labels}]")
            print(f"     ID: {node.get('node_id')}")


def main():
    """
    Основная функция для выполнения запроса по новой логике
    """
    query_handler = SchetnoeNodesQuery()
    
    try:
        # Подключаемся к базе данных
        query_handler.connect()
        
        # Получаем расширенные данные по новой логике
        print("Получение расширенных данных по новой логике...")
        extended_data = query_handler.get_extended_schetnoe_data()
        
        # Сохраняем расширенные результаты
        query_handler.save_results_to_json(
            extended_data,
            "schetnoe_extended_data.json"
        )
        
        # Выводим расширенную сводку
        query_handler.print_extended_summary(extended_data)
        
        print(f"\nРезультаты сохранены в файл:")
        print(f"- schetnoe_extended_data.json (расширенные данные)")
        print(f"- schetnoe_query.log (лог выполнения)")
        
    except Exception as e:
        logger.error(f"Ошибка выполнения: {str(e)}")
        print(f"Ошибка: {str(e)}")
    
    finally:
        # Закрываем соединение
        query_handler.disconnect()


if __name__ == "__main__":
    main()