"""
Модуль для сопоставления запросов пользователей с счетными узлами в Neo4j
Использует LLM для семантического поиска соответствий
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Добавляем корневую директорию в путь для импорта
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

from query_schetnoe_nodes import SchetnoeNodesQuery

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация LLM
llm = ChatOpenAI(
    model="gpt-4o", 
    base_url="https://api.aitunnel.ru/v1/",
    api_key="sk-aitunnel-6dnjLye1zgdGdnSfmM7kuFp3hiPi9qKI",
)

class NodeMatchResponse(BaseModel):
    """Структура ответа для сопоставления узлов"""
    is_match: bool = Field(description="найдено ли соответствие")
    node_id: Optional[str] = Field(description="ID найденного узла")
    node_name: Optional[str] = Field(description="название найденного узла")
    confidence: float = Field(description="уверенность в соответствии от 0.0 до 1.0")
    reasoning: str = Field(description="обоснование решения")

class Neo4jMatcher:
    """
    Класс для сопоставления запросов пользователей с счетными узлами в Neo4j
    """
    
    def __init__(self, neo4j_config_path: str = "neo4j_config.json"):
        """
        Инициализация матчера
        
        Args:
            neo4j_config_path (str): Путь к конфигурации Neo4j
        """
        self.query_handler = SchetnoeNodesQuery(neo4j_config_path)
        self.schetnoe_nodes_cache = None
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """Инициализация соединения с Neo4j"""
        try:
            self.query_handler.connect()
            logger.info("Соединение с Neo4j для матчера успешно установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к Neo4j в матчере: {str(e)}")
            raise
    
    def _get_schetnoe_nodes(self) -> List[Dict[str, Any]]:
        """
        Получает все счетные узлы из Neo4j с кешированием
        
        Returns:
            List[Dict[str, Any]]: Список счетных узлов
        """
        if self.schetnoe_nodes_cache is None:
            try:
                self.schetnoe_nodes_cache = self.query_handler.get_schetnoe_nodes()
                logger.info(f"Загружено {len(self.schetnoe_nodes_cache)} счетных узлов")
            except Exception as e:
                logger.error(f"Ошибка получения счетных узлов: {str(e)}")
                raise
        
        return self.schetnoe_nodes_cache
    
    def _prepare_nodes_for_matching(self, nodes: List[Dict[str, Any]]) -> str:
        """
        Подготавливает список узлов для передачи в LLM
        
        Args:
            nodes (List[Dict[str, Any]]): Список узлов
            
        Returns:
            str: Отформатированный список узлов
        """
        formatted_nodes = []
        
        for node in nodes:
            node_id = node.get('node_id', 'unknown')
            node_name = node.get('node_name', 'Без названия')
            node_full_name = node.get('node_full_name', '')
            table_number = node.get('table_number', '')
            
            # Формируем описание узла
            description_parts = [f"ID: {node_id}"]
            description_parts.append(f"Название: {node_name}")
            
            if node_full_name and node_full_name != node_name:
                description_parts.append(f"Полное название: {node_full_name}")
            
            if table_number:
                description_parts.append(f"Таблица: {table_number}")
            
            formatted_nodes.append(" | ".join(description_parts))
        
        return "\n".join(formatted_nodes)
    
    def find_matching_schetnoe_node(self, user_query: str) -> Optional[str]:
        """
        Находит соответствующий счетный узел для запроса пользователя
        
        Args:
            user_query (str): Запрос пользователя
            
        Returns:
            Optional[str]: node_id найденного узла или None
        """
        try:
            logger.info(f"Поиск соответствующего узла для запроса: {user_query}")
            
            # Получаем все счетные узлы
            nodes = self._get_schetnoe_nodes()
            
            if not nodes:
                logger.warning("Нет доступных счетных узлов для сопоставления")
                return None
            
            # Подготавливаем данные для LLM
            nodes_text = self._prepare_nodes_for_matching(nodes)
            
            # Настройка парсера
            parser = JsonOutputParser(pydantic_object=NodeMatchResponse)
            
            # Создаем промпт для LLM
            prompt = PromptTemplate(
                template="""Проанализируй запрос пользователя и найди наиболее подходящий счетный узел из списка.

{format_instructions}

Запрос пользователя: {user_query}

Доступные счетные узлы:
{nodes_list}

Критерии для сопоставления:
1. Семантическое соответствие между запросом и названием/полным названием узла
2. Ключевые слова и термины
3. Контекст и предметная область

Правила принятия решения:
- is_match = true только если есть явное семантическое соответствие
- confidence должна быть >= 0.7 для положительного результата
- Если несколько узлов подходят, выбери наиболее релевантный
- Если нет подходящих узлов, верни is_match = false

Обязательно объясни свое решение в поле reasoning.""",
                input_variables=["user_query", "nodes_list"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # Создаем цепочку обработки
            chain = prompt | llm | parser
            
            # Выполняем запрос к LLM
            response = chain.invoke({
                "user_query": user_query,
                "nodes_list": nodes_text
            })
            
            logger.info(f"Результат сопоставления: {response}")
            
            # Проверяем результат
            if response.get("is_match", False) and response.get("confidence", 0.0) >= 0.7:
                node_id = response.get("node_id")
                node_name = response.get("node_name", "")
                confidence = response.get("confidence", 0.0)
                reasoning = response.get("reasoning", "")
                
                logger.info(f"Найдено соответствие: узел '{node_name}' (ID: {node_id}) с уверенностью {confidence}")
                logger.info(f"Обоснование: {reasoning}")
                
                return node_id
            else:
                logger.info("Соответствующий узел не найден или уверенность слишком низкая")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при поиске соответствующего узла: {str(e)}")
            return None
    
    def get_node_info_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о узле по его ID
        
        Args:
            node_id (str): ID узла
            
        Returns:
            Optional[Dict[str, Any]]: Информация о узле или None
        """
        try:
            nodes = self._get_schetnoe_nodes()
            for node in nodes:
                if node.get('node_id') == node_id:
                    return node
            return None
        except Exception as e:
            logger.error(f"Ошибка получения информации о узле {node_id}: {str(e)}")
            return None
    
    def refresh_cache(self) -> None:
        """Обновляет кеш счетных узлов"""
        self.schetnoe_nodes_cache = None
        logger.info("Кеш счетных узлов очищен")
    
    def close(self) -> None:
        """Закрывает соединение с Neo4j"""
        if self.query_handler:
            self.query_handler.disconnect()
            logger.info("Соединение с Neo4j в матчере закрыто")

def test_matcher():
    """Функция для тестирования матчера"""
    matcher = Neo4jMatcher()
    
    try:
        # Тестовые запросы
        test_queries = [
            "количество студентов",
            "численность преподавателей",
            "образовательные программы",
            "финансирование образования",
            "неподходящий запрос о погоде"
        ]
        
        print("=== ТЕСТИРОВАНИЕ NEO4J MATCHER ===\n")
        
        for query in test_queries:
            print(f"Запрос: {query}")
            node_id = matcher.find_matching_schetnoe_node(query)
            
            if node_id:
                node_info = matcher.get_node_info_by_id(node_id)
                print(f"✅ Найден узел: {node_info.get('node_name', 'Без названия')}")
                print(f"   ID: {node_id}")
                print(f"   Полное название: {node_info.get('node_full_name', 'Не указано')}")
            else:
                print("❌ Соответствующий узел не найден")
            
            print("-" * 50)
            
    finally:
        matcher.close()

if __name__ == "__main__":
    test_matcher()