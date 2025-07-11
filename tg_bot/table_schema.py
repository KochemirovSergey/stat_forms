import os
import csv
from typing import Dict, Optional, Tuple

class TableSchemaError(Exception):
    """Пользовательское исключение для ошибок при работе со схемой таблицы"""
    pass

def get_table_schema(table_number: str, year: str) -> Dict[str, Dict[str, str]]:
    """
    Получает схему таблицы по её номеру.
    
    Args:
        table_number (str): Номер таблицы (например, "2.5.1")
        year (str): Год данных
        
    Returns:
        Dict[str, Dict[str, str]]: Словарь с двумя ключами:
            - columns: Dict[str, str] - словарь номеров и названий колонок
            - rows: Dict[str, str] - словарь номеров и названий строк
            
    Raises:
        TableSchemaError: Если файл не найден или возникла ошибка при чтении
    """
    try:
        # Формируем путь к файлу (БД находится в корне проекта)
        project_root = os.path.dirname(os.path.dirname(__file__))
        base_dir = os.path.join(project_root, 'БД', year)
        file_name = f"Раздел {table_number}.csv"
        file_path = os.path.join(base_dir, file_name)
        
        if not os.path.exists(file_path):
            raise TableSchemaError(f"Файл таблицы {file_name} не найден")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            
            # Пропускаем первые 5 строк
            for _ in range(5):
                next(reader)
                
            # Читаем номера колонок (6-я строка)
            column_numbers = next(reader)
            # Читаем названия колонок (7-я строка)
            column_names = next(reader)
            
            # Формируем словарь колонок, пропуская пустые значения
            columns = {
                num: name 
                for num, name in zip(column_numbers, column_names) 
                if num and name
            }
            
            # Читаем строки начиная с 8-й строки
            rows = {}
            for row in reader:
                if row[0] and row[1]:  # Проверяем что номер и название строки не пустые
                    rows[row[0]] = row[1]
            
            return {
                "columns": columns,
                "rows": rows
            }
            
    except (IOError, csv.Error) as e:
        raise TableSchemaError(f"Ошибка при чтении файла: {str(e)}")
    except Exception as e:
        raise TableSchemaError(f"Неожиданная ошибка: {str(e)}") 