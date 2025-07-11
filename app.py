from flask import Flask, render_template, request, jsonify
import json
from region_visualizer_neo4j import RegionVisualizerNeo4j
from neo4j import GraphDatabase
from query_schetnoe_nodes import SchetnoeNodesQuery

app = Flask(__name__)

# Глобальная переменная для хранения экземпляра визуализатора
visualizer = None

def get_visualizer():
    """Получить экземпляр визуализатора с подключением"""
    global visualizer
    if visualizer is None:
        visualizer = RegionVisualizerNeo4j()
        visualizer.connect()
    return visualizer

@app.route('/')
def index():
    """Главная страница с формой"""
    return render_template('index.html')

@app.route('/visualize', methods=['POST'])
def visualize():
    """Построение графиков по ID узла"""
    try:
        node_id = request.form.get('node_id', '').strip()
        
        if not node_id:
            return render_template('index.html', error="Пожалуйста, введите ID узла")
        
        viz = get_visualizer()
        
        # Получаем информацию о узле
        node_info = viz.get_node_info(node_id)
        if not node_info:
            return render_template('index.html', error=f"Узел с ID '{node_id}' не найден")
        
        # Создаем карту для 2024 года (по умолчанию)
        map_html = viz.get_regional_map_html(node_id, "2024")
        if not map_html:
            return render_template('index.html', error="Не удалось построить карту регионов")
        
        # Создаем федеральный график
        chart_html = viz.get_federal_chart_html(node_id)
        if not chart_html:
            return render_template('index.html', error="Не удалось построить график федеральных данных")
        
        return render_template('index.html', 
                             map_html=map_html, 
                             chart_html=chart_html,
                             node_id=node_id,
                             node_info=node_info,
                             current_year="2024")
    
    except Exception as e:
        error_msg = f"Ошибка при построении графиков: {str(e)}"
        return render_template('index.html', error=error_msg)

@app.route('/update_map', methods=['POST'])
def update_map():
    """AJAX эндпоинт для обновления карты при изменении года"""
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        year = data.get('year')
        
        if not node_id or not year:
            return jsonify({'error': 'Отсутствуют обязательные параметры'})
        
        viz = get_visualizer()
        map_html = viz.get_regional_map_html(node_id, year)
        
        if not map_html:
            return jsonify({'error': f'Не удалось построить карту для {year} года'})
        
        return jsonify({'map_html': map_html})
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при обновлении карты: {str(e)}'})

@app.route('/graph_data', methods=['GET'])
def get_graph_data():
    """API endpoint для получения расширенных данных графа узлов 'Счетное' с дополнительными узлами и связями"""
    query_handler = SchetnoeNodesQuery()
    
    try:
        # Подключаемся к базе данных
        query_handler.connect()
        
        # Получаем расширенные данные
        extended_data = query_handler.get_extended_schetnoe_data()
        
        # Преобразуем данные в формат для vis.js
        nodes = {}
        edges = []
        
        print("=== DEBUG: Преобразование расширенных данных в формат vis.js ===")
        
        # Обрабатываем узлы "Счетное"
        schetnoe_nodes = extended_data.get('schetnoe_nodes', [])
        print(f"Получено узлов 'Счетное': {len(schetnoe_nodes)}")
        
        for node_data in schetnoe_nodes:
            node_id = node_data['node_id']
            node_name = node_data['node_name']
            node_full_name = node_data['node_full_name']
            
            # Добавляем основной узел "Счетное" (серый цвет, меньший размер)
            if node_id not in nodes:
                nodes[node_id] = {
                    'id': node_id,
                    'label': node_name or 'Без названия',
                    'title': f"<b>{node_name or 'Без названия'}</b><br>" +
                            f"Полное название: {node_full_name or 'Не указано'}<br>" +
                            f"Таблица: {node_data.get('table_number', 'Не указано')}<br>" +
                            f"Столбец: {node_data.get('column', 'Не указано')}<br>" +
                            f"Строка: {node_data.get('row', 'Не указано')}<br>" +
                            f"Годы: {', '.join(map(str, node_data.get('years', []))) if node_data.get('years') else 'Не указано'}<br>" +
                            f"Метки: Счетное",
                    'group': 'Счетное',
                    'color': '#808080',  # Серый цвет
                    'size': 12  # Меньший размер
                }
            
        
        # Обрабатываем дополнительные узлы
        additional_nodes = extended_data.get('additional_nodes', [])
        print(f"Получено дополнительных узлов: {len(additional_nodes)}")
        
        # Получаем динамическую цветовую схему из метаданных
        metadata = extended_data.get('metadata', {})
        label_colors = metadata.get('color_mapping', {})
        
        print(f"Используется цветовая схема: {label_colors}")
        
        for node_data in additional_nodes:
            node_id = node_data['node_id']
            node_name = node_data['node_name']
            node_full_name = node_data['node_full_name']
            node_labels = node_data['node_labels']
            
            if node_id not in nodes:
                # Определяем группу и цвет на основе первой метки
                primary_label = node_labels[0] if node_labels else 'Другое'
                group = primary_label
                
                # Используем цвет из динамической схемы или генерируем fallback
                if label_colors and primary_label in label_colors:
                    color = label_colors[primary_label]
                else:
                    # Fallback цвета для известных меток
                    fallback_colors = {
                        'Регион': '#ff6b6b',
                        'Отрасль': '#4ecdc4',
                        'Период': '#45b7d1',
                        'УровеньОбразования': '#96ceb4',
                        'Класс': '#feca57',
                        'Работник': '#ff9ff3',
                        'Обучающийся': '#54a0ff',
                        'Организация': '#5f27cd',
                        'Программа': '#00d2d3',
                        'Специальность': '#ff6348'
                    }
                    color = fallback_colors.get(primary_label, '#a8a8a8')
                
                nodes[node_id] = {
                    'id': node_id,
                    'label': node_name or 'Без названия',
                    'title': f"<b>{node_name or 'Без названия'}</b><br>" +
                            f"Полное название: {node_full_name or 'Не указано'}<br>" +
                            f"Описание: {node_data['node_properties'].get('описание', 'Не указано')}<br>" +
                            f"Метки: {', '.join(node_labels)}",
                    'group': group,
                    'color': color,
                    'size': 15
                }
        
        # Обрабатываем связи между дополнительными узлами
        relations_between_additional = extended_data.get('relations_between_additional', [])
        print(f"Получено связей между дополнительными узлами: {len(relations_between_additional)}")
        
        for relation in relations_between_additional:
            source_id = relation['source_id']
            target_id = relation['target_id']
            relation_type = relation['relation_type']
            
            edge_id = f"{source_id}-{target_id}"
            if edge_id not in [e['id'] for e in edges]:
                edge = {
                    'id': edge_id,
                    'from': source_id,
                    'to': target_id,
                    'label': relation_type,
                    'title': f"Связь: {relation_type}",
                    'color': '#666666'  # Приглушенный цвет для связей между дополнительными узлами
                }
                edges.append(edge)
        
        # Преобразуем словарь узлов в список
        nodes_list = list(nodes.values())
        
        print(f"=== DEBUG: Итоговые результаты ===")
        print(f"Узлов создано: {len(nodes_list)}")
        print(f"Связей создано: {len(edges)}")
        print(f"Узлы 'Счетное': {len([n for n in nodes_list if n['group'] == 'Счетное'])}")
        print(f"Дополнительные узлы: {len([n for n in nodes_list if n['group'] != 'Счетное'])}")
        
        # Выводим статистику по группам
        groups = {}
        for node in nodes_list:
            group = node['group']
            groups[group] = groups.get(group, 0) + 1
        print(f"Статистика по группам: {groups}")
        
        return jsonify({
            'nodes': nodes_list,
            'edges': edges,
            'color_mapping': label_colors,
            'metadata': extended_data.get('metadata', {})
        })
    
    except Exception as e:
        print(f"Ошибка при получении данных графа: {str(e)}")
        return jsonify({'error': f'Ошибка при получении данных графа: {str(e)}'})
    
    finally:
        # Закрываем соединение
        query_handler.disconnect()

@app.teardown_appcontext
def close_db(error):
    """Закрытие соединения с Neo4j при завершении контекста приложения"""
    global visualizer
    if visualizer:
        visualizer.disconnect()
        visualizer = None

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5001)