"""
Модуль поиска через Tavily API для анализа статистических данных в сфере образования
"""
import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from tavily import TavilyClient

# Импортируем config для инициализации переменных окружения
from tg_bot import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация LLM
llm = ChatOpenAI(
    model="gpt-4o", 
    base_url="https://api.aitunnel.ru/v1/",
    api_key="sk-aitunnel-6dnjLye1zgdGdnSfmM7kuFp3hiPi9qKI",
)

# Структуры данных для парсинга результатов LLM
class YearlyDataAnalysis(BaseModel):
    year: str = Field(description="год данных")
    value: str = Field(description="найденное значение показателя")
    source_info: str = Field(description="краткая информация об источнике")
    relevance_score: float = Field(description="оценка релевантности от 0 до 1")

class TavilyAnalysisResponse(BaseModel):
    yearly_data: List[YearlyDataAnalysis] = Field(description="данные по годам")
    summary: str = Field(description="общий анализ найденной информации")
    data_quality: str = Field(description="оценка качества данных: high, medium, low")

def get_tavily_client() -> TavilyClient:
    """
    Создает и возвращает клиент Tavily API.
    
    Returns:
        TavilyClient: Инициализированный клиент Tavily
    """
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        raise ValueError("TAVILY_API_KEY не найден в переменных окружения")
    
    return TavilyClient(api_key=api_key)

def search_year_data(client: TavilyClient, base_query: str, year: str) -> Dict[str, Any]:
    """
    Выполняет поиск данных для конкретного года через Tavily API.
    
    Args:
        client (TavilyClient): Клиент Tavily API
        base_query (str): Базовый запрос пользователя
        year (str): Год для поиска
        
    Returns:
        Dict[str, Any]: Результаты поиска для года
    """
    # Формируем запрос для конкретного года
    search_query = f"{base_query} в российской федерации в сфере образования в {year} году"
    
    try:
        logger.info(f"Поиск данных за {year} год: {search_query}")
        
        # Выполняем поиск через Tavily
        search_result = client.search(
            query=search_query,
            search_depth="advanced",
            max_results=5,
            include_domains=["rosstat.gov.ru", "edu.ru", "government.ru", "minobrnauki.gov.ru"],
            include_answer=True
        )
        
        return {
            "year": year,
            "query": search_query,
            "success": True,
            "results": search_result.get("results", []),
            "answer": search_result.get("answer", ""),
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Ошибка поиска для {year} года: {str(e)}")
        return {
            "year": year,
            "query": search_query,
            "success": False,
            "results": [],
            "answer": "",
            "error": str(e)
        }

def analyze_search_results_with_llm(user_query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует результаты поиска с помощью LLM и извлекает структурированные данные.
    
    Args:
        user_query (str): Исходный запрос пользователя
        search_results (List[Dict[str, Any]]): Результаты поиска по годам
        
    Returns:
        Dict[str, Any]: Структурированный анализ данных
    """
    # Настройка парсера
    parser = JsonOutputParser(pydantic_object=TavilyAnalysisResponse)
    
    # Подготавливаем данные для анализа
    search_data_text = []
    for result in search_results:
        if result["success"]:
            year_info = [f"\n=== ГОД {result['year']} ==="]
            
            if result["answer"]:
                year_info.append(f"Краткий ответ: {result['answer']}")
            
            for i, res in enumerate(result["results"][:3], 1):  # Берем только первые 3 результата
                year_info.append(f"\nИсточник {i}:")
                year_info.append(f"Заголовок: {res.get('title', 'Без заголовка')}")
                year_info.append(f"URL: {res.get('url', 'Нет URL')}")
                year_info.append(f"Содержание: {res.get('content', 'Нет содержания')[:500]}...")
        else:
            year_info = [f"\n=== ГОД {result['year']} ==="]
            year_info.append(f"ОШИБКА: {result['error']}")
        
        search_data_text.extend(year_info)
    
    search_data_combined = "\n".join(search_data_text)
    
    prompt = PromptTemplate(
        template="""Проанализируй результаты поиска по запросу пользователя и извлеки структурированные данные по годам.

{format_instructions}

Запрос пользователя: {query}

Результаты поиска по годам:
{search_data}

Твоя задача:
1. Для каждого года (2014-2024) найди конкретные числовые значения или показатели
2. Оцени релевантность найденной информации (0-1)
3. Укажи краткую информацию об источнике
4. Дай общую оценку качества найденных данных
5. Если для года нет данных, укажи value как "Нет данных"

Обрати внимание на:
- Точные числовые значения и статистические показатели
- Официальные источники (Росстат, Минобрнауки и т.д.)
- Соответствие запросу пользователя
- Актуальность и достоверность информации""",
        input_variables=["query", "search_data"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    try:
        logger.info("Анализ результатов поиска с помощью LLM...")
        response = chain.invoke({
            "query": user_query,
            "search_data": search_data_combined
        })
        
        logger.info("LLM анализ завершен успешно")
        return response
        
    except Exception as e:
        logger.error(f"Ошибка анализа LLM: {str(e)}")
        return {
            "yearly_data": [],
            "summary": f"Ошибка анализа: {str(e)}",
            "data_quality": "low"
        }

def format_tavily_results(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Форматирует результаты анализа в формат, совместимый с CSV-модулем.
    
    Args:
        analysis_result (Dict[str, Any]): Результат анализа LLM
        
    Returns:
        Dict[str, Any]: Отформатированные данные в стандартном формате
    """
    # Создаем структуру данных, совместимую с CSV-модулем
    cells_data = []
    values_by_year = {}
    
    yearly_data = analysis_result.get("yearly_data", [])
    
    if yearly_data:
        # Создаем единую "ячейку" с данными из Tavily
        for year_data in yearly_data:
            year = year_data.get("year", "")
            value = year_data.get("value", "Нет данных")
            values_by_year[year] = value
        
        # Формируем информацию о "ячейке"
        cells_data.append({
            "column_name": "Данные Tavily Search",
            "row_name": "Результаты поиска в интернете",
            "values": values_by_year
        })
    
    return {
        "table_number": "TAVILY_SEARCH",
        "table_name": "Поиск через Tavily API",
        "cells_data": cells_data,
        "analysis_summary": analysis_result.get("summary", ""),
        "data_quality": analysis_result.get("data_quality", "unknown"),
        "search_timestamp": datetime.now().isoformat()
    }

def search_with_tavily(user_query: str) -> Dict[str, Any]:
    """
    Основная функция поиска через Tavily API.
    
    Args:
        user_query (str): Запрос пользователя
        
    Returns:
        Dict[str, Any]: Результат в формате {"success": bool, "data": {...}, "errors": [...]}
    """
    errors = []
    result = {
        "success": False,
        "errors": errors,
        "data": None
    }
    
    try:
        logger.info(f"Начинаем поиск через Tavily для запроса: {user_query}")
        
        # Инициализируем клиент Tavily
        try:
            client = get_tavily_client()
        except Exception as e:
            errors.append(f"Ошибка инициализации Tavily API: {str(e)}")
            return result
        
        # Выполняем поиск для каждого года (2014-2024)
        years = [str(year) for year in range(2014, 2025)]
        search_results = []
        
        for year in years:
            year_result = search_year_data(client, user_query, year)
            search_results.append(year_result)
            
            # Небольшая пауза между запросами, чтобы не превысить лимиты API
            import time
            time.sleep(0.5)
        
        # Проверяем, есть ли хотя бы один успешный результат
        successful_searches = [r for r in search_results if r["success"]]
        if not successful_searches:
            errors.append("Не удалось получить данные ни для одного года")
            return result
        
        # Анализируем результаты с помощью LLM
        analysis_result = analyze_search_results_with_llm(user_query, search_results)
        
        # Форматируем результаты для совместимости
        formatted_data = format_tavily_results(analysis_result)
        
        result["success"] = True
        result["data"] = formatted_data
        
        logger.info("Поиск через Tavily завершен успешно")
        
    except Exception as e:
        error_msg = f"Общая ошибка поиска через Tavily: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    result["errors"] = errors
    return result

def test_tavily_search():
    """
    Тестовая функция для проверки работы модуля.
    """
    test_query = "количество студентов высших учебных заведений"
    
    print(f"Тестируем поиск для запроса: {test_query}")
    print("="*60)
    
    result = search_with_tavily(test_query)
    
    if result["success"]:
        data = result["data"]
        print(f"Таблица: {data['table_number']} - {data['table_name']}")
        print(f"Качество данных: {data['data_quality']}")
        print(f"Время поиска: {data['search_timestamp']}")
        print(f"\nАнализ: {data['analysis_summary']}")
        
        print("\nНайденные данные по годам:")
        for cell_data in data["cells_data"]:
            print(f"\nКолонка: {cell_data['column_name']}")
            print(f"Строка: {cell_data['row_name']}")
            for year, value in cell_data['values'].items():
                print(f"  {year}: {value}")
    else:
        print("Ошибки при поиске:")
        for error in result["errors"]:
            print(f"  - {error}")

if __name__ == "__main__":
    test_tavily_search()