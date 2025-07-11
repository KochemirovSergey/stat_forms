import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, url_for, redirect
from werkzeug.exceptions import NotFound, InternalServerError
import uuid
import json
import sys
from pathlib import Path
from region_visualizer_neo4j import RegionVisualizerNeo4j

# Добавляем путь для импорта модулей tg_bot
sys.path.append(str(Path(__file__).parent / 'tg_bot'))
from neo4j_matcher import Neo4jMatcher

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dashboard-secret-key-2025')

# Глобальные переменные
visualizer = None
neo4j_matcher = None
dashboard_cache = {}
AVAILABLE_YEARS = ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]

def init_visualizer():
    """Инициализация визуализатора Neo4j"""
    global visualizer
    try:
        visualizer = RegionVisualizerNeo4j()
        visualizer.connect()
        logger.info("Визуализатор Neo4j успешно инициализирован")
        return True
    except Exception as e:
        logger.error(f"Ошибка инициализации визуализатора: {str(e)}")
        return False

def init_neo4j_matcher():
    """Инициализация Neo4j матчера для выбора узлов"""
    global neo4j_matcher
    try:
        neo4j_matcher = Neo4jMatcher()
        logger.info("Neo4j матчер успешно инициализирован")
        return True
    except Exception as e:
        logger.error(f"Ошибка инициализации Neo4j матчера: {str(e)}")
        return False

def get_default_node_id():
    """Получение ID узла по умолчанию через LLM"""
    try:
        if not neo4j_matcher:
            logger.error("Neo4j матчер не инициализирован")
            return None
        
        # Используем общий запрос для получения подходящего узла
        default_query = "Показать общую статистику по образованию"
        
        # Получаем все счетные узлы
        schetnoe_nodes = neo4j_matcher._get_schetnoe_nodes()
        
        if not schetnoe_nodes:
            logger.error("Не найдено счетных узлов")
            return None
        
        # Берем первый доступный узел как пример
        default_node = schetnoe_nodes[0]
        node_id = default_node.get('node_id')
        
        logger.info(f"Выбран узел по умолчанию: {node_id}")
        return node_id
        
    except Exception as e:
        logger.error(f"Ошибка получения узла по умолчанию: {str(e)}")
        return None

def get_node_dashboard_data(node_id: str, year: str = "2024") -> Dict[str, Any]:
    """
    Получение данных для дашборда узла
    
    Args:
        node_id (str): ID узла в Neo4j
        year (str): Год для карты
        
    Returns:
        Dict[str, Any]: Данные дашборда
    """
    try:
        if not visualizer:
            raise Exception("Визуализатор не инициализирован")
        
        # Получаем информацию о узле
        node_info = visualizer.get_node_info(node_id)
        if not node_info:
            raise Exception(f"Узел с ID {node_id} не найден")
        
        # Получаем HTML карты для указанного года без встроенной Plotly
        map_html = visualizer.get_regional_map_html(node_id, year, include_plotlyjs=False)
        
        # Получаем HTML графика федеральных данных
        chart_html = visualizer.get_federal_chart_html(node_id)
        
        # Получаем региональные данные для всех доступных лет
        regional_data_by_year = {}
        for yr in AVAILABLE_YEARS:
            regional_data = visualizer.get_regional_data(node_id, yr)
            if regional_data:
                regional_data_by_year[yr] = regional_data
        
        dashboard_data = {
            'node_id': node_id,
            'node_info': node_info,
            'current_year': year,
            'available_years': AVAILABLE_YEARS,
            'map_html': map_html,
            'chart_html': chart_html,
            'regional_data_by_year': regional_data_by_year,
            'generated_at': datetime.now().isoformat(),
            'dashboard_url': url_for('dashboard_by_node', node_id=node_id, _external=True)
        }
        
        logger.info(f"Данные дашборда для узла {node_id} успешно сгенерированы")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Ошибка получения данных дашборда для узла {node_id}: {str(e)}")
        raise

def generate_dashboard_id() -> str:
    """Генерация уникального ID для дашборда"""
    return str(uuid.uuid4())

@app.route('/')
def index():
    """Главная страница с автоматическим выбором узла через LLM и построением дашборда"""
    try:
        logger.info("=== DEBUG: Запрос к главной странице дашборда ===")
        
        # Получаем узел по умолчанию
        node_id = get_default_node_id()
        if not node_id:
            logger.error("DEBUG: Не удалось получить узел по умолчанию")
            return render_template('dashboard_error.html',
                                 error="Не удалось выбрать узел для отображения"), 500
        
        logger.info(f"DEBUG: Выбран узел: {node_id}")
        
        # Получаем информацию о узле
        node_info = visualizer.get_node_info(node_id)
        if not node_info:
            logger.error(f"DEBUG: Узел с ID '{node_id}' не найден")
            return render_template('dashboard_error.html',
                                 error=f"Узел с ID '{node_id}' не найден"), 500
        
        # Создаем карту для 2024 года (по умолчанию) с встроенной Plotly для первого рендера
        current_year = "2024"
        map_html = visualizer.get_regional_map_html(node_id, current_year, include_plotlyjs=True)
        if not map_html:
            logger.error("DEBUG: Не удалось построить карту регионов")
            return render_template('dashboard_error.html',
                                 error="Не удалось построить карту регионов"), 500
        
        # Создаем федеральный график
        chart_html = visualizer.get_federal_chart_html(node_id)
        if not chart_html:
            logger.error("DEBUG: Не удалось построить график федеральных данных")
            return render_template('dashboard_error.html',
                                 error="Не удалось построить график федеральных данных"), 500
        
        logger.info("DEBUG: Успешно построены карта и график, возвращаем index.html")
        
        # Возвращаем страницу index.html с готовыми графиками
        return render_template('index.html',
                             map_html=map_html,
                             chart_html=chart_html,
                             node_id=node_id,
                             node_info=node_info,
                             current_year=current_year)
        
    except Exception as e:
        logger.error(f"DEBUG: Ошибка в главном маршруте: {str(e)}")
        return render_template('dashboard_error.html',
                             error=f"Ошибка загрузки главной страницы: {str(e)}"), 500

@app.route('/dashboard/<node_id>')
def dashboard_by_node(node_id: str):
    """
    Генерация дашборда по node_id
    
    Args:
        node_id (str): ID узла в Neo4j
    """
    try:
        year = request.args.get('year', '2024')
        
        # Проверяем валидность года
        if year not in AVAILABLE_YEARS:
            year = '2024'
        
        # Проверяем кеш
        cache_key = f"{node_id}_{year}"
        if cache_key in dashboard_cache:
            logger.info(f"Возвращаем дашборд из кеша для {cache_key}")
            dashboard_data = dashboard_cache[cache_key]
        else:
            # Генерируем новые данные
            dashboard_data = get_node_dashboard_data(node_id, year)
            # Кешируем данные (простой кеш в памяти)
            dashboard_cache[cache_key] = dashboard_data
        
        return render_template('index.html', **dashboard_data)
        
    except Exception as e:
        logger.error(f"Ошибка генерации дашборда для узла {node_id}: {str(e)}")
        return render_template('dashboard_error.html',
                             error=str(e),
                             node_id=node_id,
                             datetime=datetime), 500

@app.route('/dashboard/<node_id>/<year>')
def dashboard_by_node_year(node_id: str, year: str):
    """
    Генерация дашборда по node_id и году
    
    Args:
        node_id (str): ID узла в Neo4j
        year (str): Год для отображения
    """
    try:
        # Проверяем валидность года
        if year not in AVAILABLE_YEARS:
            return redirect(url_for('dashboard_by_node', node_id=node_id))
        
        return dashboard_by_node(node_id)
        
    except Exception as e:
        logger.error(f"Ошибка генерации дашборда для узла {node_id}, год {year}: {str(e)}")
        return render_template('dashboard_error.html', 
                             error=str(e), 
                             node_id=node_id,
                             year=year), 500

@app.route('/api/dashboard/<node_id>')
def api_dashboard_data(node_id: str):
    """
    API эндпоинт для получения данных дашборда в JSON формате
    
    Args:
        node_id (str): ID узла в Neo4j
    """
    try:
        year = request.args.get('year', '2024')
        
        # Проверяем валидность года
        if year not in AVAILABLE_YEARS:
            return jsonify({'error': f'Недопустимый год: {year}'}), 400
        
        dashboard_data = get_node_dashboard_data(node_id, year)
        
        # Убираем HTML из JSON ответа для уменьшения размера
        api_data = {
            'node_id': dashboard_data['node_id'],
            'node_info': dashboard_data['node_info'],
            'current_year': dashboard_data['current_year'],
            'available_years': dashboard_data['available_years'],
            'regional_data_by_year': dashboard_data['regional_data_by_year'],
            'generated_at': dashboard_data['generated_at'],
            'dashboard_url': dashboard_data['dashboard_url']
        }
        
        return jsonify(api_data)
        
    except Exception as e:
        logger.error(f"Ошибка API получения данных для узла {node_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/<node_id>/<year>')
def api_map_data(node_id: str, year: str):
    """
    API эндпоинт для получения HTML карты
    
    Args:
        node_id (str): ID узла в Neo4j
        year (str): Год для карты
    """
    try:
        # Проверяем валидность года
        if year not in AVAILABLE_YEARS:
            return jsonify({'error': f'Недопустимый год: {year}'}), 400
        
        if not visualizer:
            return jsonify({'error': 'Визуализатор не инициализирован'}), 500
        
        map_html = visualizer.get_regional_map_html(node_id, year)
        
        if not map_html:
            return jsonify({'error': 'Не удалось сгенерировать карту'}), 500
        
        return jsonify({
            'node_id': node_id,
            'year': year,
            'map_html': map_html,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Ошибка API получения карты для узла {node_id}, год {year}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart/<node_id>')
def api_chart_data(node_id: str):
    """
    API эндпоинт для получения HTML графика федеральных данных
    
    Args:
        node_id (str): ID узла в Neo4j
    """
    try:
        if not visualizer:
            return jsonify({'error': 'Визуализатор не инициализирован'}), 500
        
        chart_html = visualizer.get_federal_chart_html(node_id)
        
        if not chart_html:
            return jsonify({'error': 'Не удалось сгенерировать график'}), 500
        
        return jsonify({
            'node_id': node_id,
            'chart_html': chart_html,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Ошибка API получения графика для узла {node_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-cache')
def api_clear_cache():
    """API эндпоинт для очистки кеша"""
    try:
        global dashboard_cache
        cache_size = len(dashboard_cache)
        dashboard_cache.clear()
        logger.info(f"Кеш очищен, удалено {cache_size} записей")
        return jsonify({
            'message': f'Кеш очищен, удалено {cache_size} записей',
            'cleared_at': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Ошибка очистки кеша: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Проверка состояния сервера"""
    try:
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'visualizer_connected': visualizer is not None,
            'cache_size': len(dashboard_cache),
            'available_years': AVAILABLE_YEARS
        }
        
        # Проверяем подключение к Neo4j
        if visualizer:
            try:
                # Простой тест подключения
                test_result = visualizer.get_node_info("test")
                status['neo4j_connection'] = 'connected'
            except:
                status['neo4j_connection'] = 'disconnected'
        else:
            status['neo4j_connection'] = 'not_initialized'
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Ошибка проверки состояния: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/visualize', methods=['POST'])
def visualize():
    """Построение графиков по ID узла (совместимость с app.py)"""
    try:
        node_id = request.form.get('node_id', '').strip()
        
        if not node_id:
            return render_template('index.html', error="Пожалуйста, введите ID узла")
        
        # Получаем информацию о узле
        node_info = visualizer.get_node_info(node_id)
        if not node_info:
            return render_template('index.html', error=f"Узел с ID '{node_id}' не найден")
        
        # Создаем карту для 2024 года (по умолчанию)
        map_html = visualizer.get_regional_map_html(node_id, "2024")
        if not map_html:
            return render_template('index.html', error="Не удалось построить карту регионов")
        
        # Создаем федеральный график
        chart_html = visualizer.get_federal_chart_html(node_id)
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
        logger.error(error_msg)
        return render_template('index.html', error=error_msg)

@app.route('/update_map', methods=['POST'])
def update_map():
    """AJAX эндпоинт для обновления карты при изменении года (совместимость с app.py)"""
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        year = data.get('year')
        
        if not node_id or not year:
            return jsonify({'error': 'Отсутствуют обязательные параметры'})
        
        map_html = visualizer.get_regional_map_html(node_id, year, include_plotlyjs=False)
        
        if not map_html:
            return jsonify({'error': f'Не удалось построить карту для {year} года'})
        
        return jsonify({'map_html': map_html})
    
    except Exception as e:
        error_msg = f"Ошибка при обновлении карты: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg})

@app.errorhandler(404)
def not_found_error(error):
    """Обработчик ошибки 404"""
    return render_template('dashboard_error.html',
                         error="Страница не найдена",
                         error_code=404,
                         datetime=datetime), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик ошибки 500"""
    logger.error(f"Внутренняя ошибка сервера: {str(error)}")
    return render_template('dashboard_error.html',
                         error="Внутренняя ошибка сервера",
                         error_code=500,
                         datetime=datetime), 500

@app.route('/api/map/<node_id>')
def get_map_html(node_id):
    """API эндпоинт для получения только HTML карты"""
    try:
        year = request.args.get('year', '2024')
        
        if not visualizer:
            return jsonify({'error': 'Визуализатор не инициализирован'}), 500
        
        # Получаем HTML карты без встроенной Plotly для API
        map_html = visualizer.get_regional_map_html(node_id, year, include_plotlyjs=False)
        
        return jsonify({
            'map_html': map_html,
            'year': year,
            'node_id': node_id
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения HTML карты для узла {node_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Инициализация при запуске
    if init_visualizer() and init_neo4j_matcher():
        logger.info("Запуск Dashboard Server...")
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5001)),
            debug=os.environ.get('DEBUG', 'False').lower() == 'true'
        )
    else:
        logger.error("Не удалось инициализировать компоненты. Сервер не запущен.")