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
from typing import Dict, List, Optional
sys.path.append('/Users/sergejkocemirov/stat_forms')
from table_schema import get_table_schema
from excel_reader import get_cell_value_by_table

# Настройка переменных окружения для LangChain
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "pr-untimely-licorice-46"

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

def load_tables_from_csv(file_path='/Users/sergejkocemirov/stat_forms/Список_таблиц_20-24.csv'):
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
        }, config={"max_tokens": 1000})
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
        }, config={"max_tokens": 1000})
        print("\nОтвет LLM:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        print(f"\nОшибка при получении ответа от LLM: {str(e)}")
        return "НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ"

def save_to_csv(table_number: str, table_name: str, cells_data: List[Dict]) -> str:
    """
    Сохраняет результаты запроса в CSV файл.
    
    Args:
        table_number (str): Номер таблицы
        table_name (str): Название таблицы
        cells_data (List[Dict]): Список словарей с данными ячеек
        
    Returns:
        str: Путь к созданному файлу
    """
    # Создаем директорию для логов, если её нет
    log_dir = "/Users/sergejkocemirov/stat_forms/query_log"
    os.makedirs(log_dir, exist_ok=True)
    
    # Формируем имя файла с timestamp
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    file_name = f"query_result_{timestamp}.csv"
    file_path = os.path.join(log_dir, file_name)
    
    # Записываем данные в CSV
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        # Записываем заголовки
        writer.writerow(['Таблица', 'Название таблицы', 'Название колонки', 'Название строки', 'Год', 'Значение'])
        
        # Записываем данные
        for cell_data in cells_data:
            for year, value in cell_data['values'].items():
                writer.writerow([
                    table_number,
                    table_name,
                    cell_data['column_name'],
                    cell_data['row_name'],
                    year,
                    value
                ])
    
    return file_path

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

def process_cell_values(table_number: str, cells_response: str) -> List[Dict]:
    """
    Обрабатывает ответ LLM и получает значения ячеек.
    
    Args:
        table_number (str): Номер таблицы
        cells_response (str): JSON-ответ от LLM с информацией о ячейках
        
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
            cell_info['row_number']
        )
        
        cells_data.append({
            'column_name': cell_info['column_name'],
            'row_name': cell_info['row_name'],
            'values': values
        })
    
    return cells_data

def main():
    """Основная функция программы."""
    user_query = input("Введите ваш запрос: ")
    
    # Загружаем список таблиц
    tables = load_tables_from_csv()
    
    # Получаем номер подходящей таблицы
    table_number = ask_llm_for_table(user_query, tables)
    
    if table_number == "НЕТ ПОДХОДЯЩЕЙ ТАБЛИЦЫ":
        print("Этап 1: Поиск таблицы - НЕТ ПОДХОДЯЩЕЙ ТАБЛИЦЫ")
        return
    
    # Находим название таблицы
    table_name = next((t['name'] for t in tables if t['number'] == table_number), '')
        
    try:
        # Получаем схему таблицы
        schema = get_table_schema(table_number)
        
        # Получаем информацию о релевантных ячейках
        cells_response = ask_llm_for_cells(user_query, schema)
        
        if cells_response == "НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ":
            print(f"Этап 1: Поиск таблицы - НАЙДЕНА ТАБЛИЦА {table_number}")
            print("Этап 2: Поиск ячеек - НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ")
            return
            
        print(f"Этап 1: Поиск таблицы - НАЙДЕНА ТАБЛИЦА {table_number}")
        print("Этап 2: Поиск ячеек - НАЙДЕНЫ СЛЕДУЮЩИЕ ЯЧЕЙКИ:")
        
        # Получаем значения ячеек
        cells_data = process_cell_values(table_number, cells_response)
        
        # Форматируем и выводим результат
        print("\nРезультаты запроса:")
        print(format_terminal_output(table_number, table_name, cells_data))
        
        # Сохраняем результаты в CSV
        csv_path = save_to_csv(table_number, table_name, cells_data)
        print(f"\nРезультаты сохранены в файл: {csv_path}")
            
    except Exception as e:
        print(f"Этап 1: Поиск таблицы - НАЙДЕНА ТАБЛИЦА {table_number}")
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    main()
