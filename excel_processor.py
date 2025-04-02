import pandas as pd
import os
from typing import Union, List

def process_excel_file(file_path: str) -> Union[pd.DataFrame, None]:
    """
    Обрабатывает Excel файл согласно требованиям:
    1. Находит строку с "Наименование" или "Профили" в первой колонке
    2. Удаляет все строки выше
    3. Находит колонку с "№ строки"
    4. Удаляет все колонки между первой и колонкой с "№ строки"
    5. Перемещает колонку "№ строки" на первое место
    6. Перемещает строку со значением "2" в первой колонке на самое первое место
    7. Меняет местами значения в первой строке между первой и второй колонкой
    8. Добавляет 5 пустых строк в начало таблицы
    
    Args:
        file_path: путь к Excel файлу
    
    Returns:
        DataFrame: обработанный датафрейм или None в случае ошибки
    """
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        # Находим индекс строки с "Наименование" или "Профили"
        target_row = -1
        for idx, value in enumerate(df.iloc[:, 0]):
            if isinstance(value, str) and (value.startswith('Наименование') or value.startswith('Профили')):
                target_row = idx
                break
                
        if target_row == -1:
            print(f"В файле {file_path} не найдена строка с 'Наименование' или 'Профили'")
            return None
            
        # Удаляем все строки выше
        df = df.iloc[target_row:].reset_index(drop=True)
        
        # Находим колонку с "№ строки"
        number_col = -1
        for idx, col in enumerate(df.iloc[0]):
            if isinstance(col, str) and col == '№ строки':
                number_col = idx
                break
                
        if number_col == -1:
            print(f"В файле {file_path} не найдена колонка '№ строки'")
            return None
            
        # Оставляем только первую колонку и колонки начиная с "№ строки"
        first_col = df.iloc[:, 0].copy()
        remaining_cols = df.iloc[:, number_col:].copy()
        
        # Перемещаем колонку с "№ строки" на первое место
        header_row = remaining_cols.iloc[0]
        num_col_idx = None
        for idx, value in enumerate(header_row):
            if isinstance(value, str) and value == '№ строки':
                num_col_idx = idx
                break
        
        # Находим строку со значением "2" и сохраняем её индекс
        target_row_idx = None
        for idx, value in enumerate(remaining_cols.iloc[1:, num_col_idx]):
            if str(value).strip() == "2":
                target_row_idx = idx + 1  # +1 так как пропустили первую строку
                break
        
        # Создаем новый DataFrame с нужными колонками и числовыми названиями
        df = pd.DataFrame()
        df[0] = first_col
        for i in range(remaining_cols.shape[1]):
            df[i + 1] = remaining_cols.iloc[:, i]
        
        # Перемещаем колонку "№ строки" на первое место
        if num_col_idx is not None:
            cols = list(df.columns)
            col_to_move = num_col_idx + 1  # +1 because we added first column
            cols.remove(col_to_move)
            cols = [col_to_move] + cols
            df = df[cols]
                
        if target_row_idx is not None:
            # Перемещаем найденную строку на самое первое место
            row_to_move = df.iloc[target_row_idx:target_row_idx+1]
            df_without_row = df.drop(target_row_idx)
            df = pd.concat([row_to_move, df_without_row], ignore_index=True)
        
        # Меняем местами значения в первой строке между первой и второй колонкой
        temp = df.iloc[0, 0]
        df.iloc[0, 0] = df.iloc[0, 1]
        df.iloc[0, 1] = temp
        
        # Добавляем 5 пустых строк в начало таблицы
        empty_rows = pd.DataFrame([[None] * len(df.columns)] * 5, columns=df.columns)
        df = pd.concat([empty_rows, df], ignore_index=True)
        
        return df
        
    except Exception as e:
        print(f"Ошибка при обработке файла {file_path}: {str(e)}")
        return None

def process_directory(directory_path: str) -> None:
    """
    Обрабатывает все Excel файлы в указанной директории и сохраняет их в той же директории
    
    Args:
        directory_path: путь к директории с Excel файлами
    """
    # Получаем список всех Excel файлов
    excel_files = [f for f in os.listdir(directory_path) 
                  if f.endswith(('.xlsx', '.xls'))]
    
    for file in excel_files:
        file_path = os.path.join(directory_path, file)
        
        # Создаем временную копию файла
        temp_path = os.path.join(directory_path, f"temp_{file}")
        
        df = process_excel_file(file_path)
        if df is not None:
            # Сохраняем во временный файл
            df.to_excel(temp_path, index=False, header=False)
            
            # Удаляем оригинальный файл и переименовываем временный
            os.remove(file_path)
            os.rename(temp_path, file_path)
            print(f"Файл {file} успешно обработан")

if __name__ == "__main__":
    # Пример использования с указанной директорией
    input_dir = "/Users/sergejkocemirov/test/2020/все разделы"
    process_directory(input_dir) 