import pandas as pd
import numpy as np
import os
from typing import Dict, List, Optional

BASE_DIR = "/Users/sergejkocemirov/stat_forms/БД"

def get_available_years() -> List[str]:
    """
    Получает список доступных годов из базовой директории.
    
    Returns:
        List[str]: Список годов в порядке убывания
    """
    years = []
    for item in os.listdir(BASE_DIR):
        if item.isdigit() and os.path.isdir(os.path.join(BASE_DIR, item)):
            years.append(item)
    return sorted(years, reverse=True)

def get_file_path(year: str, table_number: str) -> str:
    """
    Формирует путь к файлу для конкретного года и номера таблицы.
    
    Args:
        year (str): Год
        table_number (str): Номер таблицы
    
    Returns:
        str: Полный путь к файлу
    """
    return os.path.join(BASE_DIR, year, f"Раздел {table_number}.csv")

def get_cell_value(file_path: str, column_number: int, row_number: int) -> str:
    """
    Получает значение ячейки из CSV файла по заданным параметрам.
    
    Args:
        file_path (str): Путь к CSV файлу
        column_number (int): Номер колонки (начиная с 1)
        row_number (int): Номер строки (начиная с 1)
    
    Returns:
        str: Значение ячейки
    """
    # Читаем CSV файл
    df = pd.read_csv(file_path, header=None, encoding='utf-8', sep=';')
    
    # Находим строку с заголовком (содержит "№ строки")
    header_row_index = None
    for idx, row in df.iterrows():
        if isinstance(row[0], str) and "№ строки" in str(row[0]):
            header_row_index = idx
            break
    
    if header_row_index is None:
        raise ValueError("Не удалось найти строку заголовка с '№ строки'")
    
    # Данные начинаются со следующей строки после заголовка
    data_start_index = header_row_index + 1
    
    # Получаем реальный индекс строки с учетом смещения
    actual_row_index = data_start_index + row_number - 1
    
    # Получаем значение ячейки (column_number - 1, так как в pandas индексация с 0)
    cell_value = df.iloc[actual_row_index, column_number - 1]
    
    # Проверяем на NaN и конвертируем в строку
    if pd.isna(cell_value):
        return ""
    return str(cell_value)

def get_cell_value_by_table(table_number: str, column_number: int, row_number: int) -> Dict[str, str]:
    """
    Получает значение ячейки из всех доступных годовых файлов для указанной таблицы.
    
    Args:
        table_number (str): Номер таблицы (например, "2.1.1")
        column_number (int): Номер колонки (начиная с 1)
        row_number (int): Номер строки (начиная с 1)
    
    Returns:
        Dict[str, str]: Словарь, где ключ - год, значение - содержимое ячейки
    """
    result = {}
    years = get_available_years()
    
    for year in years:
        file_path = get_file_path(year, table_number)
        try:
            if os.path.exists(file_path):
                value = get_cell_value(file_path, column_number, row_number)
                result[year] = value
            else:
                result[year] = ""
        except Exception as e:
            print(f"Ошибка при чтении файла за {year} год: {str(e)}")
            result[year] = ""
    
    return result

# Пример использования
if __name__ == "__main__":
    try:
        # Пример использования новой функции
        result = get_cell_value_by_table("2.5.1", 3, 3)
        print("Результаты по годам:")
        for year, value in result.items():
            print(f"{year}: {value}")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}") 