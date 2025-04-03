from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
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
    
    messages = [
        SystemMessage(content="""Ты - помощник по выбору статистических таблиц. 
        Выбери номер таблицы, которая наиболее подходит для ответа на вопрос пользователя.
        Верни только номер таблицы без дополнительного текста.
        Если не найдешь подходящую таблицу, верни "Нет информации"."""),
        HumanMessage(content=f"""Запрос пользователя: {user_query}

Доступные таблицы:
{tables_text}""")
    ]
    
    response = llm.invoke(messages)
    return response.content.strip()

def ask_llm_for_cells(user_query, schema):
    """Запрашивает у LLM информацию о релевантных ячейках."""
    messages = [
        SystemMessage(content="""Ты - помощник по анализу данных в таблицах.
        На основе схемы таблицы укажи номера колонок и строк, которые содержат информацию для ответа на вопрос пользователя.
        Если информации нет, верни "Нет информации".
        Ответ дай в формате JSON с полями: column_name, column_number, row_name, row_number."""),
        HumanMessage(content=f"""Запрос пользователя: {user_query}

Схема таблицы:
{schema}""")
    ]
    
    response = llm.invoke(messages)
    return response.content.strip()

def main():
    """Основная функция программы."""
    user_query = input("Введите ваш запрос: ")
    
    # Загружаем список таблиц
    tables = load_tables_from_csv()
    
    # Получаем номер подходящей таблицы
    table_number = ask_llm_for_table(user_query, tables)
    
    if table_number == "Нет информации":
        print("Нет информации")
        return
        
    try:
        # Получаем схему таблицы
        schema = get_table_schema(table_number)
        
        # Получаем информацию о релевантных ячейках
        cells_response = ask_llm_for_cells(user_query, schema)
        
        if cells_response == "Нет информации":
            print("Нет информации")
        else:
            print(cells_response)
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    main()
