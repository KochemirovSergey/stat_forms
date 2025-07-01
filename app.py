from flask import Flask, render_template, request, jsonify
import os
import sys
from pathlib import Path
import traceback
import logging

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from region_visualizer_flask import create_regional_map_json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['DEBUG'] = True

@app.route('/')
def index():
    """Главная страница с формой для ввода параметров"""
    return render_template('index.html')

@app.route('/api/generate_map', methods=['POST'])
def generate_map():
    """API endpoint для генерации карты"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Не получены данные запроса',
                'html': None
            }), 400
        
        # Валидация входных параметров
        table_number = data.get('table_number', '').strip()
        column_number = data.get('column_number')
        row_number = data.get('row_number')
        year = data.get('year', 2024)
        
        # Проверка обязательных параметров
        if not table_number:
            return jsonify({
                'success': False,
                'error': 'Номер таблицы не может быть пустым',
                'html': None
            }), 400
        
        if not isinstance(column_number, int) or column_number < 1:
            return jsonify({
                'success': False,
                'error': 'Номер колонки должен быть положительным числом',
                'html': None
            }), 400
        
        if not isinstance(row_number, int) or row_number < 1:
            return jsonify({
                'success': False,
                'error': 'Номер строки должен быть положительным числом',
                'html': None
            }), 400
        
        logger.info(f"Генерация карты: таблица {table_number}, колонка {column_number}, строка {row_number}, год {year}")
        
        # Генерируем карту
        result = create_regional_map_json(table_number, column_number, row_number, year)
        
        if result['success']:
            return jsonify({
                'success': True,
                'graph_json': result['graph_json'],
                'error': None,
                'stats': result.get('stats', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'graph_json': None
            }), 400
            
    except Exception as e:
        logger.error(f"Ошибка при генерации карты: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}',
            'graph_json': None
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({
        'status': 'ok',
        'message': 'Flask приложение работает'
    })

@app.errorhandler(404)
def not_found(error):
    """Обработчик 404 ошибки"""
    return jsonify({
        'success': False,
        'error': 'Страница не найдена'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик 500 ошибки"""
    return jsonify({
        'success': False,
        'error': 'Внутренняя ошибка сервера'
    }), 500

if __name__ == '__main__':
    # Проверяем наличие необходимых файлов
    required_files = ['russia_regions.parquet', 'map_figure.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.warning(f"Отсутствуют файлы: {', '.join(missing_files)}")
    
    # Проверяем наличие директорий с данными
    data_dirs = ["2022", "2023", "2024"]
    missing_dirs = []
    
    for data_dir in data_dirs:
        if not os.path.exists(data_dir):
            missing_dirs.append(data_dir)
    
    if missing_dirs:
        logger.warning(f"Отсутствуют директории с данными: {', '.join(missing_dirs)}")
    else:
        logger.info(f"Найдены директории с данными: {', '.join(data_dirs)}")
    
    logger.info("Запуск Flask приложения...")
    app.run(host='0.0.0.0', port=5001, debug=False)