import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import plotly.express as px
from fuzzywuzzy import fuzz, process
from map_figure import mapFigure
import warnings

# Подавляем предупреждения pandas
warnings.filterwarnings('ignore')

__version__ = "1.0.0"
__author__ = "Regional Data Visualizer"

# Получаем путь к директории проекта
PROJECT_ROOT = Path(__file__).parent.absolute()
REGIONS_DATA_DIR = os.path.join(PROJECT_ROOT, "2024")

def get_region_file_path(region_name: str, table_number: str) -> str:
    """
    Формирует путь к файлу для конкретного региона и номера таблицы.
    
    Args:
        region_name (str): Название региона
        table_number (str): Номер таблицы
    
    Returns:
        str: Полный путь к файлу
    """
    return os.path.join(REGIONS_DATA_DIR, region_name, f"Раздел {table_number}.csv")

def get_cell_value_from_region(file_path: str, column_number: int, row_number: int) -> Optional[str]:
    """
    Получает значение ячейки из CSV файла региона по заданным параметрам.
    
    Args:
        file_path (str): Путь к CSV файлу
        column_number (int): Номер колонки (начиная с 1)
        row_number (int): Номер строки (начиная с 1)
    
    Returns:
        Optional[str]: Значение ячейки или None при ошибке
    """
    try:
        # Читаем CSV файл
        df = pd.read_csv(file_path, header=None, encoding='utf-8', sep=';')
        
        # Находим строку с заголовком (содержит "№ строки")
        header_row_index = None
        for idx, row in df.iterrows():
            if isinstance(row[0], str) and "№ строки" in str(row[0]):
                header_row_index = idx
                break
        
        if header_row_index is None:
            return None
        
        # Данные начинаются со следующей строки после заголовка
        data_start_index = header_row_index + 1
        
        # Получаем реальный индекс строки с учетом смещения
        actual_row_index = data_start_index + row_number - 1
        
        # Проверяем, что индексы в пределах DataFrame
        if actual_row_index >= len(df) or column_number - 1 >= len(df.columns):
            return None
        
        # Получаем значение ячейки (column_number - 1, так как в pandas индексация с 0)
        cell_value = df.iloc[actual_row_index, column_number - 1]
        
        # Проверяем на NaN и конвертируем в строку
        if pd.isna(cell_value):
            return None
        
        return str(cell_value).strip()
        
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {str(e)}")
        return None

def match_region_names(folder_names: List[str], map_regions: List[str]) -> Dict[str, str]:
    """
    Сопоставляет названия папок с названиями регионов на карте используя нечеткий поиск.
    
    Args:
        folder_names (List[str]): Список названий папок
        map_regions (List[str]): Список названий регионов на карте
    
    Returns:
        Dict[str, str]: Словарь сопоставления {folder_name: map_region_name}
    """
    matches = {}
    
    for folder_name in folder_names:
        # Используем нечеткий поиск для нахождения наиболее похожего названия
        best_match = process.extractOne(folder_name, map_regions, scorer=fuzz.ratio)
        
        if best_match and best_match[1] >= 70:  # Порог схожести 70%
            matches[folder_name] = best_match[0]
        else:
            print(f"Не удалось сопоставить регион: {folder_name}")
    
    return matches

def validate_numeric_value(value_str: str) -> Optional[float]:
    """
    Валидирует и преобразует строковое значение в число.
    
    Args:
        value_str (str): Строковое значение
    
    Returns:
        Optional[float]: Числовое значение или None при ошибке
    """
    if not value_str or value_str.strip() == "":
        return None
    
    try:
        # Убираем лишние пробелы и заменяем запятые на точки
        cleaned_value = value_str.strip().replace(',', '.')
        
        # Пытаемся преобразовать в число
        numeric_value = float(cleaned_value)
        
        return numeric_value
        
    except (ValueError, TypeError):
        return None

def collect_regional_data(table_number: str, column_number: int, row_number: int) -> Dict[str, float]:
    """
    Собирает данные по всем регионам для указанной таблицы и ячейки.
    
    Args:
        table_number (str): Номер таблицы (например, "2.5.1")
        column_number (int): Номер колонки (начиная с 1)
        row_number (int): Номер строки (начиная с 1)
    
    Returns:
        Dict[str, float]: Словарь {region_name: value}
    """
    regional_data = {}
    
    # Получаем список папок регионов
    if not os.path.exists(REGIONS_DATA_DIR):
        print(f"Директория {REGIONS_DATA_DIR} не найдена")
        return regional_data
    
    folder_names = [name for name in os.listdir(REGIONS_DATA_DIR) 
                   if os.path.isdir(os.path.join(REGIONS_DATA_DIR, name)) and not name.startswith('.')]
    
    print(f"Найдено {len(folder_names)} папок регионов")
    
    # Загружаем данные карты для сопоставления названий
    try:
        regions_df = pd.read_parquet("russia_regions.parquet")
        map_regions = regions_df['region'].tolist()
    except Exception as e:
        print(f"Ошибка при загрузке данных карты: {str(e)}")
        return regional_data
    
    # Сопоставляем названия
    region_matches = match_region_names(folder_names, map_regions)
    
    # Собираем данные по каждому региону
    for folder_name, map_region_name in region_matches.items():
        file_path = get_region_file_path(folder_name, table_number)
        
        if os.path.exists(file_path):
            cell_value = get_cell_value_from_region(file_path, column_number, row_number)
            
            if cell_value is not None:
                numeric_value = validate_numeric_value(cell_value)
                
                if numeric_value is not None:
                    regional_data[map_region_name] = numeric_value
                    print(f"{map_region_name}: {numeric_value}")
                else:
                    print(f"Некорректное значение для {map_region_name}: '{cell_value}'")
            else:
                print(f"Не удалось извлечь данные для {map_region_name}")
        else:
            print(f"Файл не найден: {file_path}")
    
    return regional_data

def create_regional_map(table_number: str, column_number: int, row_number: int) -> None:
    """
    Создает интерактивную карту России с цветовым градиентом по регионам.
    
    Args:
        table_number (str): Номер таблицы (например, "2.5.1")
        column_number (int): Номер колонки (начиная с 1)
        row_number (int): Номер строки (начиная с 1)
    """
    print(f"Создание карты для таблицы {table_number}, колонка {column_number}, строка {row_number}")
    
    # Собираем данные по регионам
    regional_data = collect_regional_data(table_number, column_number, row_number)
    
    if not regional_data:
        print("Не удалось собрать данные по регионам")
        return
    
    print(f"Собрано данных по {len(regional_data)} регионам")
    
    # Создаем базовую карту
    russia_map = mapFigure()
    
    # Загружаем данные регионов для карты
    try:
        regions_df = pd.read_parquet("russia_regions.parquet")
    except Exception as e:
        print(f"Ошибка при загрузке данных карты: {str(e)}")
        return
    
    # Определяем диапазон значений для градиента
    values = list(regional_data.values())
    min_value = min(values)
    max_value = max(values)
    
    print(f"Диапазон значений: {min_value:.2f} - {max_value:.2f}")
    
    # Создаем цветовую шкалу (красный -> зеленый)
    def get_color(value: float, min_val: float, max_val: float) -> str:
        """Возвращает цвет в градиенте от красного к зеленому"""
        if max_val == min_val:
            return 'rgb(255, 255, 0)'  # Желтый, если все значения одинаковые
        
        # Нормализуем значение от 0 до 1
        normalized = (value - min_val) / (max_val - min_val)
        
        # Интерполируем между красным (255,0,0) и зеленым (0,255,0)
        red = int(255 * (1 - normalized))
        green = int(255 * normalized)
        blue = 0
        
        return f'rgb({red}, {green}, {blue})'
    
    # Обновляем карту с данными
    for i, r in regions_df.iterrows():
        region_name = r.region
        
        if region_name in regional_data:
            value = regional_data[region_name]
            color = get_color(value, min_value, max_value)
            
            # Форматируем текст для подсказки
            value_text = f"Значение: <b>{value:,.2f}</b>".replace(',', ' ')
            text = f'<b>{region_name}</b><br>Таблица {table_number}<br>Колонка {column_number}, Строка {row_number}<br>{value_text}'
            
            russia_map.update_traces(
                selector=dict(name=region_name),
                text=text,
                fillcolor=color
            )
        else:
            # Регион без данных остается с базовым цветом
            text = f'<b>{region_name}</b><br>Нет данных'
            russia_map.update_traces(
                selector=dict(name=region_name),
                text=text
            )
    
    # Добавляем заголовок
    russia_map.update_layout(
        title=f"Региональные данные - Таблица {table_number}, Колонка {column_number}, Строка {row_number}"
    )
    
    # Отображаем карту
    russia_map.show()

# Пример использования
if __name__ == "__main__":
    # Пример: создание карты для таблицы 2.8, колонка 3, строка 1
    create_regional_map("2.8", 3, 1)