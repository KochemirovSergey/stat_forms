import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import plotly.express as px
import plotly.graph_objects as go
from fuzzywuzzy import fuzz, process
from map_figure import mapFigure
from neo4j import GraphDatabase
import warnings

# Подавляем предупреждения pandas
warnings.filterwarnings('ignore')

__version__ = "1.0.0"
__author__ = "Regional Data Visualizer Neo4j"

class RegionVisualizerNeo4j:
    """
    Класс для визуализации региональных данных из базы данных Neo4j
    """
    
    def __init__(self, config_path: str = "neo4j_config.json"):
        """
        Инициализация подключения к Neo4j
        
        Args:
            config_path (str): Путь к файлу конфигурации Neo4j
        """
        self.config = self._load_neo4j_config(config_path)
        self.driver = None
        self.years = ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]
        print(f"Инициализирован RegionVisualizerNeo4j с годами: {self.years}")
        
    def _load_neo4j_config(self, config_path: str) -> Dict[str, str]:
        """
        Загружает конфигурацию Neo4j из файла
        
        Args:
            config_path (str): Путь к файлу конфигурации
            
        Returns:
            Dict[str, str]: Конфигурация подключения
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Ошибка загрузки конфигурации Neo4j: {str(e)}")
    
    def connect(self) -> None:
        """
        Устанавливает соединение с Neo4j
        """
        try:
            self.driver = GraphDatabase.driver(
                self.config["NEO4J_URI"],
                auth=(self.config["NEO4J_USERNAME"], self.config["NEO4J_PASSWORD"])
            )
            # Проверяем соединение
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                session.run("RETURN 1")
            print("Успешное подключение к Neo4j")
        except Exception as e:
            raise Exception(f"Ошибка подключения к Neo4j: {str(e)}")
    
    def disconnect(self) -> None:
        """
        Закрывает соединение с Neo4j
        """
        if self.driver:
            self.driver.close()
            print("Соединение с Neo4j закрыто")
    
    def get_node_info(self, node_id: str) -> Dict[str, Any]:
        """
        Получение информации о узле
        
        Args:
            node_id (str): ID узла в Neo4j
            
        Returns:
            Dict[str, Any]: Информация о узле
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                query = """
                MATCH (n) 
                WHERE elementId(n) = $node_id 
                RETURN n.name as name, n.полное_название as full_name, 
                       n.table_number as table_number, n.column as column, 
                       n.row as row, n.years as years, n.federal_values as federal_values
                """
                
                result = session.run(query, {"node_id": node_id})
                record = result.single()
                
                if record:
                    return {
                        "name": record["name"],
                        "full_name": record["full_name"],
                        "table_number": record["table_number"],
                        "column": record["column"],
                        "row": record["row"],
                        "years": record["years"],
                        "federal_values": record["federal_values"]
                    }
                else:
                    print(f"Узел с ID {node_id} не найден")
                    return {}
                    
        except Exception as e:
            print(f"Ошибка при получении информации о узле {node_id}: {str(e)}")
            return {}
    
    def get_regional_data(self, node_id: str, year: str) -> Dict[str, float]:
        """
        Получение региональных данных для указанного узла и года
        
        Args:
            node_id (str): ID узла в Neo4j
            year (str): Год для получения данных
            
        Returns:
            Dict[str, float]: Словарь {region_name: value}
        """
        try:
            with self.driver.session(database=self.config["NEO4J_DATABASE"]) as session:
                query = f"""
                MATCH (n)-[r:ПоРегион]->(region:Регион)
                WHERE elementId(n) = $node_id
                RETURN region.name as region_name, r.value_{year} as value
                """
                
                print(f"Выполняется запрос для года {year}: {query}")
                result = session.run(query, {"node_id": node_id})
                
                regional_data = {}
                for record in result:
                    region_name = record["region_name"]
                    value = record["value"]
                    
                    if value is not None:
                        try:
                            numeric_value = float(value)
                            regional_data[region_name] = numeric_value
                        except (ValueError, TypeError):
                            print(f"Некорректное значение для региона {region_name}: {value}")
                
                print(f"Получено данных по {len(regional_data)} регионам за {year} год")
                if len(regional_data) == 0:
                    print(f"ВНИМАНИЕ: Нет данных для года {year}. Проверьте структуру данных в Neo4j.")
                    # Попробуем альтернативный запрос для диагностики
                    debug_query = """
                    MATCH (n)-[r:ПоРегион]->(region:Регион)
                    WHERE elementId(n) = $node_id
                    RETURN region.name as region_name, keys(r) as available_keys
                    LIMIT 5
                    """
                    debug_result = session.run(debug_query, {"node_id": node_id})
                    print("Доступные ключи в связях:")
                    for record in debug_result:
                        print(f"  Регион: {record['region_name']}, Ключи: {record['available_keys']}")
                
                return regional_data
                
        except Exception as e:
            print(f"Ошибка при получении региональных данных: {str(e)}")
            return {}
    
    def match_region_names(self, neo4j_regions: List[str], map_regions: List[str]) -> Dict[str, str]:
        """
        Сопоставляет названия регионов из Neo4j с названиями регионов на карте используя нечеткий поиск.
        
        Args:
            neo4j_regions (List[str]): Список названий регионов из Neo4j
            map_regions (List[str]): Список названий регионов на карте
        
        Returns:
            Dict[str, str]: Словарь сопоставления {neo4j_region: map_region_name}
        """
        matches = {}
        
        for neo4j_region in neo4j_regions:
            # Используем нечеткий поиск для нахождения наиболее похожего названия
            best_match = process.extractOne(neo4j_region, map_regions, scorer=fuzz.ratio)
            
            if best_match and best_match[1] >= 70:  # Порог схожести 70%
                matches[neo4j_region] = best_match[0]
                print(f"Сопоставлен регион: {neo4j_region} -> {best_match[0]} (схожесть: {best_match[1]}%)")
            else:
                print(f"Не удалось сопоставить регион: {neo4j_region}")
        
        return matches
    
    def get_color(self, value: float, min_val: float, max_val: float) -> str:
        """
        Возвращает цвет в градиенте от красного к зеленому
        
        Args:
            value (float): Значение для окрашивания
            min_val (float): Минимальное значение в диапазоне
            max_val (float): Максимальное значение в диапазоне
            
        Returns:
            str: RGB цвет в формате 'rgb(r, g, b)'
        """
        if max_val == min_val:
            return 'rgb(255, 255, 0)'  # Желтый, если все значения одинаковые
        
        # Нормализуем значение от 0 до 1
        normalized = (value - min_val) / (max_val - min_val)
        
        # Интерполируем между красным (255,0,0) и зеленым (0,255,0)
        red = int(255 * (1 - normalized))
        green = int(255 * normalized)
        blue = 0
        
        return f'rgb({red}, {green}, {blue})'
    
    def create_regional_map(self, node_id: str, year: str) -> None:
        """
        Создает интерактивную карту России с региональными данными из Neo4j
        
        Args:
            node_id (str): ID узла в Neo4j
            year (str): Год для отображения данных (2021, 2022, 2023, 2024)
        """
        print(f"Создание карты для узла {node_id}, год {year}")
        
        # Подключаемся к Neo4j
        if not self.driver:
            self.connect()
        
        # Получаем информацию о узле
        node_info = self.get_node_info(node_id)
        if not node_info:
            print("Не удалось получить информацию о узле")
            return
        
        # Получаем региональные данные
        regional_data = self.get_regional_data(node_id, year)
        
        if not regional_data:
            print("Не удалось получить региональные данные")
            return
        
        # Загружаем данные карты для сопоставления названий
        try:
            regions_df = pd.read_parquet("russia_regions.parquet")
            map_regions = regions_df['region'].tolist()
        except Exception as e:
            print(f"Ошибка при загрузке данных карты: {str(e)}")
            return
        
        # Сопоставляем названия регионов
        neo4j_regions = list(regional_data.keys())
        region_matches = self.match_region_names(neo4j_regions, map_regions)
        
        # Создаем сопоставленные данные для карты
        map_data = {}
        for neo4j_region, map_region in region_matches.items():
            if neo4j_region in regional_data:
                map_data[map_region] = regional_data[neo4j_region]
        
        if not map_data:
            print("Не удалось сопоставить данные с регионами карты")
            return
        
        print(f"Сопоставлено данных по {len(map_data)} регионам")
        
        # Создаем базовую карту
        russia_map = mapFigure()
        
        # Определяем диапазон значений для градиента
        values = list(map_data.values())
        min_value = min(values)
        max_value = max(values)
        
        print(f"Диапазон значений: {min_value:.2f} - {max_value:.2f}")
        
        # Обновляем карту с данными
        for i, r in regions_df.iterrows():
            region_name = r.region
            
            if region_name in map_data:
                value = map_data[region_name]
                color = self.get_color(value, min_value, max_value)
                
                # Форматируем текст для подсказки
                value_text = f"Значение: <b>{value:,.2f}</b>".replace(',', ' ')
                text = f'<b>{region_name}</b><br>{node_info.get("full_name", node_info.get("name", ""))}<br>Год: {year}<br>{value_text}'
                
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
        title = f"{node_info.get('full_name', node_info.get('name', 'Узел'))} - {year} год"
        russia_map.update_layout(title=title)
        
        # Отображаем карту
        russia_map.show()
    
    def create_federal_chart(self, node_id: str) -> None:
        """
        Создает линейный график федеральных данных по годам
        
        Args:
            node_id (str): ID узла в Neo4j
        """
        print(f"Создание графика федеральных данных для узла {node_id}")
        
        # Подключаемся к Neo4j
        if not self.driver:
            self.connect()
        
        # Получаем информацию о узле
        node_info = self.get_node_info(node_id)
        if not node_info:
            print("Не удалось получить информацию о узле")
            return
        
        federal_values = node_info.get("federal_values", [])
        years = node_info.get("years", self.years)
        
        if not federal_values:
            print("Федеральные данные отсутствуют")
            return
        
        # Подготавливаем данные для графика
        chart_data = []
        for i, year in enumerate(years):
            if i < len(federal_values) and federal_values[i] is not None:
                chart_data.append({
                    'year': year,
                    'value': federal_values[i]
                })
        
        if not chart_data:
            print("Нет валидных федеральных данных для отображения")
            return
        
        # Создаем DataFrame для plotly
        df = pd.DataFrame(chart_data)
        
        # Создаем линейный график
        fig = px.line(
            df, 
            x='year', 
            y='value',
            title=f"Федеральные данные: {node_info.get('full_name', node_info.get('name', 'Узел'))}",
            labels={'year': 'Год', 'value': 'Значение'},
            markers=True
        )
        
        # Настраиваем внешний вид
        fig.update_layout(
            xaxis_title="Год",
            yaxis_title="Значение",
            hovermode='x unified'
        )
        
        # Добавляем значения на точки
        fig.update_traces(
            mode='lines+markers+text',
            text=[f'{val:.2f}' for val in df['value']],
            textposition='top center'
        )
        
        # Отображаем график
        fig.show()
    
    def get_regional_map_html(self, node_id: str, year: str, include_plotlyjs: bool = False) -> str:
        """
        Создает интерактивную карту России и возвращает HTML для веб-интеграции
        
        Args:
            node_id (str): ID узла в Neo4j
            year (str): Год для отображения данных (2021, 2022, 2023, 2024)
            include_plotlyjs (bool): Включать ли Plotly библиотеку в HTML (для первого рендера)
            
        Returns:
            str: HTML-код карты или пустая строка при ошибке
        """
        try:
            print(f"Создание HTML карты для узла {node_id}, год {year}")
            
            # Подключаемся к Neo4j
            if not self.driver:
                self.connect()
            
            # Получаем информацию о узле
            node_info = self.get_node_info(node_id)
            if not node_info:
                print("Не удалось получить информацию о узле")
                return ""
            
            # Получаем региональные данные
            regional_data = self.get_regional_data(node_id, year)
            
            if not regional_data:
                print("Не удалось получить региональные данные")
                return ""
            
            # Загружаем данные карты для сопоставления названий
            try:
                regions_df = pd.read_parquet("russia_regions.parquet")
                map_regions = regions_df['region'].tolist()
            except Exception as e:
                print(f"Ошибка при загрузке данных карты: {str(e)}")
                return ""
            
            # Сопоставляем названия регионов
            neo4j_regions = list(regional_data.keys())
            region_matches = self.match_region_names(neo4j_regions, map_regions)
            
            # Создаем сопоставленные данные для карты
            map_data = {}
            for neo4j_region, map_region in region_matches.items():
                if neo4j_region in regional_data:
                    map_data[map_region] = regional_data[neo4j_region]
            
            if not map_data:
                print("Не удалось сопоставить данные с регионами карты")
                return ""
            
            print(f"Сопоставлено данных по {len(map_data)} регионам")
            
            # Создаем базовую карту
            russia_map = mapFigure()
            
            # Определяем диапазон значений для градиента
            values = list(map_data.values())
            min_value = min(values)
            max_value = max(values)
            
            print(f"Диапазон значений: {min_value:.2f} - {max_value:.2f}")
            
            # Обновляем карту с данными
            for i, r in regions_df.iterrows():
                region_name = r.region
                
                if region_name in map_data:
                    value = map_data[region_name]
                    color = self.get_color(value, min_value, max_value)
                    
                    # Форматируем текст для подсказки
                    value_text = f"Значение: <b>{value:,.2f}</b>".replace(',', ' ')
                    text = f'<b>{region_name}</b><br>{node_info.get("full_name", node_info.get("name", ""))}<br>Год: {year}<br>{value_text}'
                    
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
            
            # Добавляем заголовок и настраиваем размеры
            title = f"{node_info.get('full_name', node_info.get('name', 'Узел'))} - {year} год"
            russia_map.update_layout(
                title=title,
                autosize=False,
                width=810,
                height=600,
                margin=dict(l=0, r=0, t=50, b=0),
                showlegend=False,
                dragmode='pan'
            )
            
            # Возвращаем HTML вместо показа
            # Для первого рендера включаем Plotly, для AJAX - используем уже загруженную
            plotly_js_setting = 'inline' if include_plotlyjs else False
            
            html_content = russia_map.to_html(
                full_html=False,
                include_plotlyjs=plotly_js_setting,
                config={
                    'responsive': True,
                    'displayModeBar': True,
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'russia_map',
                        'height': 600,
                        'width': 810,
                        'scale': 1
                    }
                }
            )
            print(f"Сгенерирован HTML карты, длина: {len(html_content)}")
            print(f"HTML содержит plotly-graph-div: {'plotly-graph-div' in html_content}")
            
            # Добавляем дополнительную диагностику
            if 'Plotly.newPlot' in html_content:
                print("✓ HTML содержит Plotly.newPlot")
            else:
                print("✗ HTML НЕ содержит Plotly.newPlot")
                
            if 'data' in html_content and 'layout' in html_content:
                print("✓ HTML содержит data и layout")
            else:
                print("✗ HTML НЕ содержит data или layout")
            
            return html_content
            
        except Exception as e:
            print(f"Ошибка при создании HTML карты: {str(e)}")
            return ""
    
    def get_federal_chart_html(self, node_id: str) -> str:
        """
        Создает линейный график федеральных данных и возвращает HTML для веб-интеграции
        
        Args:
            node_id (str): ID узла в Neo4j
            
        Returns:
            str: HTML-код графика или пустая строка при ошибке
        """
        try:
            print(f"Создание HTML графика федеральных данных для узла {node_id}")
            
            # Подключаемся к Neo4j
            if not self.driver:
                self.connect()
            
            # Получаем информацию о узле
            node_info = self.get_node_info(node_id)
            if not node_info:
                print("Не удалось получить информацию о узле")
                return ""
            
            federal_values = node_info.get("federal_values", [])
            years = node_info.get("years", self.years)
            
            if not federal_values:
                print("Федеральные данные отсутствуют")
                return ""
            
            # Подготавливаем данные для графика
            chart_data = []
            for i, year in enumerate(years):
                if i < len(federal_values) and federal_values[i] is not None:
                    chart_data.append({
                        'year': year,
                        'value': federal_values[i]
                    })
            
            if not chart_data:
                print("Нет валидных федеральных данных для отображения")
                return ""
            
            # Создаем DataFrame для plotly
            df = pd.DataFrame(chart_data)
            
            # Создаем линейный график
            fig = px.line(
                df,
                x='year',
                y='value',
                title=f"Федеральные данные: {node_info.get('full_name', node_info.get('name', 'Узел'))}",
                labels={'year': 'Год', 'value': 'Значение'},
                markers=True
            )
            
            # Настраиваем внешний вид
            fig.update_layout(
                xaxis_title="Год",
                yaxis_title="Значение",
                hovermode='x unified'
            )
            
            # Добавляем значения на точки
            fig.update_traces(
                mode='lines+markers+text',
                text=[f'{val:.2f}' for val in df['value']],
                textposition='top center'
            )
            
            # Возвращаем HTML вместо показа
            return fig.to_html(full_html=False, include_plotlyjs='inline')
            
        except Exception as e:
            print(f"Ошибка при создании HTML графика: {str(e)}")
            return ""
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        self.disconnect()

# Пример использования
if __name__ == "__main__":
    # Создание экземпляра класса с использованием контекстного менеджера
    with RegionVisualizerNeo4j() as visualizer:
        # ID узла для тестирования
        test_node_id = "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:156"
        
        # Получение информации о узле
        node_info = visualizer.get_node_info(test_node_id)
        print("Информация о узле:")
        for key, value in node_info.items():
            print(f"  {key}: {value}")
        
        # Создание региональной карты за 2024 год
        visualizer.create_regional_map(test_node_id, "2024")
        
        # Создание графика федеральных данных
        visualizer.create_federal_chart(test_node_id)