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
        df = pd.DataFrame(columns=range(len(remaining_cols.columns) + 1), dtype=object)
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
        
        # Добавляем 5 пустых строк в начало таблицы
        empty_rows = pd.DataFrame([[None] * len(df.columns)] * 5, columns=df.columns, dtype=object)
        df = pd.concat([empty_rows, df], ignore_index=True)
        
        # Объединяем строки заголовков
        df = merge_header_rows(df)
        
        # Меняем местами значения "1" и "2" в строке после пустых строк (индекс 5)
        if str(df.iloc[5, 0]).strip() == "2" and str(df.iloc[5, 1]).strip() == "1":
            temp = df.iloc[5, 0]
            df.iloc[5, 0] = df.iloc[5, 1]
            df.iloc[5, 1] = temp
        
        return df
        
    except Exception as e:
        return None

def merge_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Объединяет строки заголовков между строками с номерами.
    
    Args:
        df: DataFrame с данными
    
    Returns:
        DataFrame с объединенными строками заголовков
    """
    # Находим индексы строк с '№ строки'
    num_row_indices = []
    for idx, value in enumerate(df.iloc[:, 0]):
        if isinstance(value, str) and value == '№ строки':
            num_row_indices.append(idx)
    
    if len(num_row_indices) < 2:
        return df
    
    # Получаем строки заголовков между строками с номерами
    header_rows = df.iloc[num_row_indices[0]:num_row_indices[-1]+1]
    
    # Создаем новую строку с объединенными значениями
    merged_row = pd.Series(index=df.columns, dtype=object)
    
    # Для каждой колонки объединяем уникальные значения
    for col in df.columns:
        # Получаем все непустые значения из колонки
        values = [str(val).strip() for val in header_rows[col] 
                 if pd.notna(val) and str(val).strip()]
        # Оставляем только уникальные значения, сохраняя порядок
        unique_values = []
        for val in values:
            if val not in unique_values:
                unique_values.append(val)
        # Объединяем значения через пробел
        merged_row[col] = ' '.join(unique_values) if unique_values else ''
    
    # Создаем новый DataFrame с одной строкой
    merged_df = pd.DataFrame([merged_row], dtype=object)
    
    # Собираем финальный DataFrame
    result = pd.concat([
        df.iloc[:num_row_indices[0]],
        merged_df,
        df.iloc[num_row_indices[-1]+1:]
    ], ignore_index=True)
    
    return result

def process_directory(directory_path: str) -> None:
    """
    Обрабатывает все Excel файлы в указанной директории и сохраняет их в формате CSV
    
    Args:
        directory_path: путь к директории с Excel файлами
    """
    # Получаем список всех Excel файлов
    excel_files = [f for f in os.listdir(directory_path) 
                  if f.endswith(('.xlsx', '.xls'))]
    
    for file in excel_files:
        file_path = os.path.join(directory_path, file)
        
        # Создаем имя для CSV файла
        csv_file = os.path.splitext(file)[0] + '.csv'
        temp_path = os.path.join(directory_path, f"temp_{csv_file}")
        csv_path = os.path.join(directory_path, csv_file)
        
        df = process_excel_file(file_path)
        if df is not None:
            # Сохраняем во временный CSV файл
            df.to_csv(temp_path, index=False, header=False, encoding='utf-8-sig', sep=';')
            
            # Если CSV файл уже существует, удаляем его
            if os.path.exists(csv_path):
                os.remove(csv_path)
            
            # Переименовываем временный файл
            os.rename(temp_path, csv_path)
            
            # Удаляем исходный Excel файл
            os.remove(file_path)

if __name__ == "__main__":
    # Пример использования с указанной директорией
    input_dir = "/Users/sergejkocemirov/stat_forms/Таблицы_исходники/2016"
    process_directory(input_dir) 