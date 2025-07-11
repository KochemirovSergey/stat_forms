"""
Конфигурация для Telegram бота
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем абсолютный путь к директории проекта
PROJECT_ROOT = Path(__file__).parent.absolute()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', '7998703507:AAE_o2RHhU_pHbKy2q2fW7dVMxyvThQVfIs')

# Настройки LangChain
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "pr-untimely-licorice-46"

# Настройки Tavily
os.environ["TAVILY_API_KEY"] = "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"

# Настройки Dashboard Server
DASHBOARD_SERVER_URL = os.getenv('DASHBOARD_SERVER_URL', 'http://localhost:5003')

# Пути к файлам с таблицами (относительные)
TABLES_CSV_PATH_2124 = os.path.join(PROJECT_ROOT, 'Список таблиц_21-24.csv')
TABLES_CSV_PATH_1620 = os.path.join(PROJECT_ROOT, 'Список таблиц_16-20.csv')

# Настройки периодов
PERIOD_2124 = {
    'start_year': '2021',
    'end_year': '2024',
    'name': '2021-2024'
}

PERIOD_1620 = {
    'start_year': '2016',
    'end_year': '2020',
    'name': '2016-2020'
}

# Сообщения бота
MESSAGES = {
    'start': """
👋 Добро пожаловать в бот анализа статистических данных!

Я помогу вам найти и проанализировать данные из статистических таблиц за периоды 2016-2020 и 2021-2024.

Просто отправьте мне ваш запрос, например:
• "Количество предприятий в 2023 году"
• "Динамика экспорта за последние годы"
• "Статистика по регионам"

Используйте /help для получения дополнительной информации.
""",
    
    'help': """
🔍 Как пользоваться ботом:

1. Отправьте текстовый запрос о нужных вам данных
2. Бот найдет подходящие таблицы и ячейки
3. Получите объединенный анализ данных за оба периода

📊 Доступные данные:
• Период 2016-2020
• Период 2021-2024

⚡ Примеры запросов:
• "Количество классов по физико-математическому профилю"
• "Численность преподавателей имеющих степень докутора наук"
• "Общая численность обучающихся"

❓ Если данные не найдены, попробуйте переформулировать запрос.
""",
    
    'processing': '🔄 Анализирую данные...',
    
    'error': '❌ Произошла ошибка при обработке запроса:\n\n{error}',
    
    'no_data': '📭 По вашему запросу не найдено подходящих данных. Попробуйте переформулировать запрос.'
}