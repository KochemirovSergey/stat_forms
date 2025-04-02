import pandas as pd
import numpy as np

def get_cell_value(file_path: str, column_number: int, row_number: int) -> str:
    """
    Получает значение ячейки из Excel файла по заданным параметрам.
    
    Args:
        file_path (str): Путь к Excel файлу
        column_number (int): Номер колонки (начиная с 1)
        row_number (int): Номер строки (начиная с 1)
    
    Returns:
        str: Значение ячейки
    """
    # Читаем Excel файл
    df = pd.read_excel(file_path, header=None)
    
    # Находим строку, где начинается нумерация (ищем вторую "1" в первой колонке)
    first_one_found = False
    first_row_index = None
    
    for idx, value in enumerate(df[0]):
        if isinstance(value, (int, float)) and value == 1:
            if first_one_found:
                # Нашли вторую единицу
                first_row_index = idx
                break
            else:
                # Нашли первую единицу (относится к нумерации колонок)
                first_one_found = True
    
    if first_row_index is None:
        raise ValueError("Не удалось найти начало нумерации строк (вторую '1' в первой колонке)")
    
    # Получаем реальный индекс строки с учетом смещения
    actual_row_index = first_row_index + row_number - 1
    
    # Получаем значение ячейки (column_number - 1, так как в pandas индексация с 0)
    cell_value = df.iloc[actual_row_index, column_number - 1]
    
    # Проверяем на NaN и конвертируем в строку
    if pd.isna(cell_value):
        return ""
    return str(cell_value)

# Пример использования
if __name__ == "__main__":
    file_path = "/Users/sergejkocemirov/test/Россия_(ГОУ)_(город+село) 2023/все разделы/Раздел 2.1.1.xlsx"
    try:
        result = get_cell_value(file_path, 2, 2)
        print(f"Значение ячейки: {result}")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}") 