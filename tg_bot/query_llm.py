from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import os
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Получаем путь к директории проекта
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.append(str(PROJECT_ROOT))

# Импортируем config для инициализации переменных окружения
from tg_bot import config
from tg_bot.table_schema import get_table_schema
from tg_bot.excel_reader import get_cell_value_by_table

llm = ChatOpenAI(
    model="gpt-4o", 
    base_url="https://api.aitunnel.ru/v1/",
    api_key="sk-aitunnel-6dnjLye1zgdGdnSfmM7kuFp3hiPi9qKI",
)

# Определение структур данных для парсинга
class TableResponse(BaseModel):
    table_number: str = Field(description="номер подходящей таблицы. Пример: 1.1.1 или 1.1")
    table_name: str = Field(description="название подходящей таблицы")

class CellResponse(BaseModel):
    column_name: str = Field(description="название колонки")
    column_number: int = Field(description="номер колонки")
    row_name: str = Field(description="название строки")
    row_number: int = Field(description="номер строки")

class CellsResponse(BaseModel):
    cells: List[CellResponse] = Field(description="список релевантных ячеек")

class CombinedAnalysisResponse(BaseModel):
    result_type: str = Field(description="тип результата: both_periods, period_2016_2020, period_2021_2024, tavily_search, not_found")
    cell_info: Dict[str, Any] = Field(description="информация о ячейках с полями final_selection и all_sources")
    values_by_year: Dict[str, str] = Field(description="значения по годам в формате {год: значение}")
    analysis_notes: str = Field(description="объяснение принятого решения")

def load_tables_from_csv(file_path=None):
    """Загружает список таблиц из CSV файла."""
    if file_path is None:
        file_path = os.path.join(PROJECT_ROOT, 'Список таблиц_21-24.csv')
    """Загружает список таблиц из CSV файла."""
    tables = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2 and row[1] == 'Таблица':
                tables.append({"number": row[0], "name": row[0]})
    return tables

def ask_llm_for_table(user_query, tables):
    """Запрашивает у LLM номер подходящей таблицы."""
    tables_text = "\n".join([f"{t['number']}: {t['name']}" for t in tables])
    
    # Настройка парсера
    parser = JsonOutputParser(pydantic_object=TableResponse)
    
    prompt = PromptTemplate(
        template="""Выбери номер таблицы, которая наиболее подходит для ответа на вопрос пользователя.
        
{format_instructions}

Запрос пользователя: {query}

Доступные таблицы:
{tables}

Ответ должен включать номер таблицы и название. В качестве ответа подходят только таблицы, разделы не подходят.""",
        input_variables=["query", "tables"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    try:
        response = chain.invoke({
            "query": user_query,
            "tables": tables_text
        })
        return response["table_number"]
    except Exception:
        return "НЕТ ПОДХОДЯЩЕЙ ТАБЛИЦЫ"

def ask_llm_for_cells(user_query, schema):
    """Запрашивает у LLM информацию о релевантных ячейках."""
    # Настройка парсера
    parser = JsonOutputParser(pydantic_object=CellsResponse)
    
    prompt = PromptTemplate(
        template="""На основе схемы таблицы укажи все ячейки, которые содержат информацию для ответа на вопрос пользователя.
Если для ответа нужно несколько ячеек - верни их все в списке cells.

{format_instructions}

Запрос пользователя: {query}

Схема таблицы:
{schema}""",
        input_variables=["query", "schema"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    try:
        response = chain.invoke({
            "query": user_query,
            "schema": schema
        })
        print("\nОтвет LLM:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        print(f"\nОшибка при получении ответа от LLM: {str(e)}")
        return "НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ"

def analyze_combined_results(
    user_query: str,
    result_2124: Dict[str, Any],
    result_1620: Dict[str, Any],
    tavily_result: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Анализирует и объединяет результаты из двух периодов и Tavily поиска с помощью LLM.
    
    Args:
        user_query (str): Исходный запрос пользователя
        result_2124 (Dict[str, Any]): Результат обработки периода 2021-2024
        result_1620 (Dict[str, Any]): Результат обработки периода 2016-2020
        tavily_result (Dict[str, Any], optional): Результат поиска через Tavily
        
    Returns:
        Dict[str, Any]: Результат анализа LLM
    """
    # Настройка парсера
    parser = JsonOutputParser(pydantic_object=CombinedAnalysisResponse)
    
    # Подготовка данных для промпта
    period_2124_info = "НЕТ ДАННЫХ"
    period_1620_info = "НЕТ ДАННЫХ"
    tavily_info = "НЕТ ДАННЫХ"
    
    if result_2124["success"]:
        data_2124 = result_2124["data"]
        cells_info_2124 = []
        for cell in data_2124["cells_data"]:
            cells_info_2124.append(f"Колонка: {cell['column_name']}, Строка: {cell['row_name']}, Значения: {cell['values']}")
        
        period_2124_info = f"""
Таблица: {data_2124['table_number']} - {data_2124['table_name']}
Найденные ячейки:
{chr(10).join(cells_info_2124)}"""
    else:
        period_2124_info = f"ОШИБКИ: {'; '.join(result_2124['errors'])}"
    
    if result_1620["success"]:
        data_1620 = result_1620["data"]
        cells_info_1620 = []
        for cell in data_1620["cells_data"]:
            cells_info_1620.append(f"Колонка: {cell['column_name']}, Строка: {cell['row_name']}, Значения: {cell['values']}")
        
        period_1620_info = f"""
Таблица: {data_1620['table_number']} - {data_1620['table_name']}
Найденные ячейки:
{chr(10).join(cells_info_1620)}"""
    else:
        period_1620_info = f"ОШИБКИ: {'; '.join(result_1620['errors'])}"
    
    # Обработка данных Tavily, если они есть
    if tavily_result and tavily_result.get("success"):
        data_tavily = tavily_result["data"]
        cells_info_tavily = []
        for cell in data_tavily["cells_data"]:
            cells_info_tavily.append(f"Колонка: {cell['column_name']}, Строка: {cell['row_name']}, Значения: {cell['values']}")
        
        tavily_info = f"""
Источник: {data_tavily['table_number']} - {data_tavily['table_name']}
Качество данных: {data_tavily.get('data_quality', 'unknown')}
Анализ: {data_tavily.get('analysis_summary', 'Нет анализа')}
Найденные данные:
{chr(10).join(cells_info_tavily)}"""
    elif tavily_result and not tavily_result.get("success"):
        tavily_info = f"ОШИБКИ TAVILY: {'; '.join(tavily_result.get('errors', ['Неизвестная ошибка']))}"
    
    prompt = PromptTemplate(
        template="""Проанализируй результаты поиска данных за два периода и данные Tavily поиска, прими решение о том, как лучше ответить на запрос пользователя.

{format_instructions}

Запрос пользователя: {query}

Результаты за период 2021-2024:
{period_2124}

Результаты за период 2016-2020:
{period_1620}

Результаты поиска Tavily:
{tavily_data}

Твоя задача:
1. Оценить релевантность данных из каждого источника
2. Принять одно из решений:
   - "both_periods": если данные из обоих периодов одинаковые/совместимые - объедини их в одну серию 2016-2024
   - "period_2021_2024": если релевантны только данные 2021-2024
   - "period_2016_2020": если релевантны только данные 2016-2020
   - "tavily_search": если наиболее релевантны данные из Tavily поиска
   - "not_found": если все данные нерелевантны или есть критические ошибки

3. Если найдено несколько ячеек, выбери одну наиболее подходящую для ответа
4. В cell_info.final_selection укажи выбранные ячейки, в cell_info.all_sources - все исходные данные
5. В values_by_year верни только итоговые значения для выбранного периода/источника
6. В analysis_notes объясни свое решение и укажи источник данных""",
        input_variables=["query", "period_2124", "period_1620", "tavily_data"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    try:
        response = chain.invoke({
            "query": user_query,
            "period_2124": period_2124_info,
            "period_1620": period_1620_info,
            "tavily_data": tavily_info
        })
        print("\nОтвет LLM анализа:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return response
    except Exception as e:
        print(f"\nОшибка при анализе объединенных результатов: {str(e)}")
        return {
            "result_type": "not_found",
            "cell_info": {"final_selection": [], "all_sources": []},
            "values_by_year": {},
            "analysis_notes": f"Ошибка анализа: {str(e)}"
        }


def format_terminal_output(table_number: str, table_name: str, cells_data: List[Dict]) -> str:
    """
    Форматирует данные для вывода в терминал.
    
    Args:
        table_number (str): Номер таблицы
        table_name (str): Название таблицы
        cells_data (List[Dict]): Список словарей с данными ячеек
        
    Returns:
        str: Отформатированный текст для вывода
    """
    output = [f"Таблица {table_number}: {table_name}\n"]
    output.append("\nНайденные значения:\n")
    
    for cell_data in cells_data:
        output.append(f"Колонка: {cell_data['column_name']}")
        output.append(f"Строка: {cell_data['row_name']}")
        for year, value in cell_data['values'].items():
            output.append(f"{year}: {value}")
        output.append("")  # Пустая строка между ячейками
    
    return "\n".join(output)

def format_combined_analysis_output(analysis_result: Dict[str, Any]) -> str:
    """
    Форматирует результат итогового анализа для вывода в терминал.
    
    Args:
        analysis_result (Dict[str, Any]): Результат анализа LLM
        
    Returns:
        str: Отформатированный текст для вывода
    """
    output = ["\n" + "="*60]
    output.append("ИТОГОВЫЙ АНАЛИЗ")
    output.append("="*60)
    
    result_type = analysis_result.get("result_type", "not_found")
    
    # Определяем описание типа результата
    type_descriptions = {
        "both_periods": "Данные объединены из обоих периодов (2016-2024)",
        "period_2021_2024": "Релевантны данные только за период 2021-2024",
        "period_2016_2020": "Релевантны данные только за период 2016-2020",
        "tavily_search": "Данные найдены через интернет-поиск (Tavily)",
        "not_found": "Подходящие данные не найдены"
    }
    
    output.append(f"Результат: {type_descriptions.get(result_type, result_type)}")
    
    # Информация о выбранных ячейках
    cell_info = analysis_result.get("cell_info", {})
    final_selection = cell_info.get("final_selection", [])
    
    if final_selection:
        output.append("\nВыбранные данные:")
        for cell in final_selection:
            if isinstance(cell, dict):
                column = cell.get("column_name", "Неизвестно")
                row = cell.get("row_name", "Неизвестно")
                output.append(f"  Колонка: {column}")
                output.append(f"  Строка: {row}")
    
    # Значения по годам
    values_by_year = analysis_result.get("values_by_year", {})
    if values_by_year:
        output.append("\nЗначения по годам:")
        for year in sorted(values_by_year.keys()):
            output.append(f"  {year}: {values_by_year[year]}")
    
    # Дополнительная информация для результатов Tavily
    if result_type == "tavily_search":
        output.append("\n📡 ИСТОЧНИК: Интернет-поиск через Tavily API")
        output.append("⚠️  Данные получены из открытых источников в интернете")
        output.append("🔍 Рекомендуется проверить актуальность информации")
    
    # Обоснование
    analysis_notes = analysis_result.get("analysis_notes", "")
    if analysis_notes:
        output.append(f"\nОбоснование: {analysis_notes}")
    
    return "\n".join(output)

def process_cell_values(
    table_number: str, 
    cells_response: str,
    start_year: str,
    end_year: str
) -> List[Dict]:
    """
    Обрабатывает ответ LLM и получает значения ячеек.
    
    Args:
        table_number (str): Номер таблицы
        cells_response (str): JSON-ответ от LLM с информацией о ячейках
        start_year (str): Год начала периода
        end_year (str): Год окончания периода
        
    Returns:
        List[Dict]: Список словарей с данными ячеек
    """
    cells_data = []
    response_data = json.loads(cells_response)
    
    for cell_info in response_data['cells']:
        # Получаем значения для каждой ячейки
        values = get_cell_value_by_table(
            table_number,
            cell_info['column_number'],
            cell_info['row_number'],
            start_year,
            end_year
        )
        
        cells_data.append({
            'column_name': cell_info['column_name'],
            'row_name': cell_info['row_name'],
            'values': values
        })
    
    return cells_data

def process_query(
    tables_csv_path: str,
    start_year: str,
    end_year: str,
    user_query: str
) -> Dict[str, Any]:
    """
    Обрабатывает запрос пользователя и возвращает результаты.
    
    Args:
        tables_csv_path (str): Путь к CSV файлу со списком таблиц
        start_year (str): Год начала периода
        end_year (str): Год окончания периода
        user_query (str): Запрос пользователя
        
    Returns:
        Dict[str, Any]: Словарь с результатами обработки запроса
    """
    errors = []
    result = {
        "success": False,
        "errors": errors,
        "data": None
    }
    
    try:
        # Загружаем список таблиц
        tables = load_tables_from_csv(tables_csv_path)
        
        # Получаем номер подходящей таблицы
        table_number = ask_llm_for_table(user_query, tables)
        
        if table_number == "НЕТ ПОДХОДЯЩЕЙ ТАБЛИЦЫ":
            errors.append("Этап 1: Поиск таблицы - НЕТ ПОДХОДЯЩЕЙ ТАБЛИЦЫ")
            return result
        
        # Находим название таблицы
        table_name = next((t['name'] for t in tables if t['number'] == table_number), '')
            
        # Получаем схему таблицы
        schema = get_table_schema(table_number, year=end_year)
        
        # Получаем информацию о релевантных ячейках
        cells_response = ask_llm_for_cells(user_query, schema)
        
        if cells_response == "НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ":
            errors.append(f"Этап 1: Поиск таблицы - НАЙДЕНА ТАБЛИЦА {table_number}")
            errors.append("Этап 2: Поиск ячеек - НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ")
            return result
            
        # Получаем значения ячеек
        cells_data = process_cell_values(table_number, cells_response, start_year, end_year)
        
        result["success"] = True
        result["data"] = {
            "table_number": table_number,
            "table_name": table_name,
            "cells_data": cells_data
        }
        
    except Exception as e:
        errors.append(f"Произошла ошибка: {str(e)}")
    
    result["errors"] = errors
    return result

def main():
    """Основная функция программы."""
    user_query = input("Введите ваш запрос: ")
    
    # Запрос для периода 2021-2024
    print("\n" + "="*60)
    print("ПЕРИОД 2021-2024")
    print("="*60)
    
    tables_csv_path_2124 = os.path.join(PROJECT_ROOT, 'Список таблиц_21-24.csv')
    result_2124 = process_query(
        tables_csv_path=tables_csv_path_2124,
        start_year="2021",
        end_year="2024",
        user_query=user_query
    )
    
    # Выводим результаты для периода 2021-2024
    if result_2124["success"]:
        print("\nРезультаты запроса для периода 2021-2024:")
        print(format_terminal_output(
            result_2124["data"]["table_number"],
            result_2124["data"]["table_name"],
            result_2124["data"]["cells_data"]
        ))
    else:
        print("\nОшибки при обработке запроса для периода 2021-2024:")
        for error in result_2124["errors"]:
            print(error)
    
    # Запрос для периода 2016-2020
    print("\n" + "="*60)
    print("ПЕРИОД 2016-2020")
    print("="*60)
    
    tables_csv_path_1620 = os.path.join(PROJECT_ROOT, 'Список таблиц_16-20.csv')
    result_1620 = process_query(
        tables_csv_path=tables_csv_path_1620,
        start_year="2016",
        end_year="2020",
        user_query=user_query
    )
    
    # Выводим результаты для периода 2016-2020
    if result_1620["success"]:
        print("\nРезультаты запроса для периода 2016-2020:")
        print(format_terminal_output(
            result_1620["data"]["table_number"],
            result_1620["data"]["table_name"],
            result_1620["data"]["cells_data"]
        ))
    else:
        print("\nОшибки при обработке запроса для периода 2016-2020:")
        for error in result_1620["errors"]:
            print(error)
    
    # Итоговый анализ объединенных результатов
    print("\n" + "="*60)
    print("АНАЛИЗ ОБЪЕДИНЕННЫХ РЕЗУЛЬТАТОВ")
    print("="*60)
    
    combined_analysis = analyze_combined_results(user_query, result_2124, result_1620)
    print(format_combined_analysis_output(combined_analysis))

if __name__ == "__main__":
    main()
