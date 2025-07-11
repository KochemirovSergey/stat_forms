import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Получаем путь к директории проекта (БД находится в корне проекта)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
BASE_DIR = os.path.join(PROJECT_ROOT, "БД")

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

    #Удалить последний символ
    
    
    # Проверяем на NaN и конвертируем в строку
    if pd.isna(cell_value):
        return ""
    return str(cell_value)



def get_cell_value_by_table(table_number: str, column_number: int, row_number: int, start_year: str, end_year: str) -> Dict[str, str]:
    """
    Получает значение ячейки из файлов за указанный период для указанной таблицы.
    
    Args:
        table_number (str): Номер таблицы (например, "2.1.1")
        column_number (int): Номер колонки (начиная с 1)
        row_number (int): Номер строки (начиная с 1)
        start_year (str): Начальный год (например, "2021")
        end_year (str): Конечный год (например, "2024")
    
    Returns:
        Dict[str, str]: Словарь, где ключ - год, значение - содержимое ячейки
    """
    result = {}
    
    # Генерируем список годов в указанном диапазоне
    years = [str(year) for year in range(int(start_year), int(end_year) + 1)]
    
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
        result = get_cell_value_by_table("2.5.1", 3, 3, "2021", "2024")
        print("Результаты по годам:")
        for year, value in result.items():
            print(f"{year}: {value}")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

class ExcelReader:
    """Класс для чтения данных из Excel/CSV файлов"""
    
    def __init__(self):
        """Инициализация читателя"""
        pass
    
    def search_data(self, query: str, csv_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Поиск данных в CSV файле по запросу
        
        Args:
            query (str): Поисковый запрос
            csv_path (str): Путь к CSV файлу
            
        Returns:
            Optional[List[Dict[str, Any]]]: Список найденных результатов или None
        """
        try:
            if not os.path.exists(csv_path):
                return None
                
            # Читаем CSV файл
            df = pd.read_csv(csv_path, encoding='utf-8', sep=';')
            
            # Простой поиск по всем столбцам
            results = []
            query_lower = query.lower()
            
            for idx, row in df.iterrows():
                for col in df.columns:
                    cell_value = str(row[col]).lower()
                    if query_lower in cell_value:
                        results.append({
                            'row': idx,
                            'column': col,
                            'value': str(row[col]),
                            'match_type': 'contains'
                        })
                        break  # Найдено совпадение в строке, переходим к следующей
            
            return results if results else None
            
        except Exception as e:
            print(f"Ошибка при поиске в CSV: {e}")
            return None