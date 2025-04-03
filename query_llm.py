from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import os
import csv
import json
import sys
sys.path.append('/Users/sergejkocemirov/stat_forms')
from table_schema import get_table_schema

# Настройка переменных окружения для LangChain
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "pr-untimely-licorice-46"

llm = ChatOpenAI(
    model="gpt-4o", 
    base_url="https://api.aitunnel.ru/v1/",
    api_key="sk-aitunnel-6dnjLye1zgdGdnSfmM7kuFp3hiPi9qKI"
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
        })
        return response["table_number"]
    except Exception:
        return "НЕТ ПОДХОДЯЩЕЙ ТАБЛИЦЫ"

def ask_llm_for_cells(user_query, schema):
    """Запрашивает у LLM информацию о релевантных ячейках."""
    # Настройка парсера
    parser = JsonOutputParser(pydantic_object=CellResponse)
    
    prompt = PromptTemplate(
        template="""На основе схемы таблицы укажи номера колонок и строк, которые содержат информацию для ответа на вопрос пользователя.

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
        return json.dumps({
            "column_name": response["column_name"],
            "column_number": response["column_number"],
            "row_name": response["row_name"],
            "row_number": response["row_number"]
        }, ensure_ascii=False)
    except Exception:
        return "НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ"

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
        
    try:
        # Получаем схему таблицы
        schema = get_table_schema(table_number)
        
        # Получаем информацию о релевантных ячейках
        cells_response = ask_llm_for_cells(user_query, schema)
        
        if cells_response == "НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ":
            print(f"Этап 1: Поиск таблицы - НАЙДЕНА ТАБЛИЦА {table_number}")
            print("Этап 2: Поиск ячеек - НЕ УДАЛОСЬ НАЙТИ НУЖНЫЕ ЯЧЕЙКИ В ТАБЛИЦЕ")
        else:
            print(f"Этап 1: Поиск таблицы - НАЙДЕНА ТАБЛИЦА {table_number}")
            print("Этап 2: Поиск ячеек - НАЙДЕНЫ СЛЕДУЮЩИЕ ЯЧЕЙКИ:")
            print(cells_response)
            
    except Exception as e:
        print(f"Этап 1: Поиск таблицы - НАЙДЕНА ТАБЛИЦА {table_number}")
        print(f"Этап 2: Поиск ячеек - ОШИБКА: {str(e)}")

if __name__ == "__main__":
    main()
