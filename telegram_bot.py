"""
Telegram бот для анализа статистических данных
Использует модуль query_llm.py для обработки запросов пользователей
"""
import asyncio
import logging
import sys
from typing import Dict, Any

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

# Импорт конфигурации и модуля анализа
from config import BOT_TOKEN, MESSAGES, TABLES_CSV_PATH_2124, TABLES_CSV_PATH_1620, PERIOD_2124, PERIOD_1620
from query_llm import process_query, analyze_combined_results, format_combined_analysis_output

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

async def process_user_query(user_query: str) -> str:
    """
    Обрабатывает запрос пользователя через модуль query_llm.py
    
    Args:
        user_query (str): Запрос пользователя
        
    Returns:
        str: Отформатированный результат анализа
    """
    try:
        logger.info(f"Обработка запроса: {user_query}")
        
        # Обработка запроса для периода 2021-2024
        result_2124 = process_query(
            tables_csv_path=TABLES_CSV_PATH_2124,
            start_year=PERIOD_2124['start_year'],
            end_year=PERIOD_2124['end_year'],
            user_query=user_query
        )
        
        # Обработка запроса для периода 2016-2020
        result_1620 = process_query(
            tables_csv_path=TABLES_CSV_PATH_1620,
            start_year=PERIOD_1620['start_year'],
            end_year=PERIOD_1620['end_year'],
            user_query=user_query
        )
        
        # Объединение и анализ результатов
        combined_analysis = analyze_combined_results(user_query, result_2124, result_1620)
        
        # Форматирование результата для пользователя
        formatted_result = format_combined_analysis_output(combined_analysis)
        
        logger.info("Запрос успешно обработан")
        return formatted_result
        
    except Exception as e:
        error_msg = f"Ошибка при обработке запроса: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return MESSAGES['error'].format(error=str(e))

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await message.answer(MESSAGES['start'])

@router.message(Command('help'))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    logger.info(f"Пользователь {message.from_user.id} запросил помощь")
    await message.answer(MESSAGES['help'])

@router.message(F.text)
async def handle_text_query(message: Message):
    """
    Обработчик текстовых запросов пользователей
    """
    user_id = message.from_user.id
    user_query = message.text.strip()
    
    logger.info(f"Получен запрос от пользователя {user_id}: {user_query}")
    
    # Отправляем сообщение о начале обработки
    processing_message = await message.answer(MESSAGES['processing'])
    
    try:
        # Обрабатываем запрос
        result = await process_user_query(user_query)
        
        # Проверяем, есть ли результат
        if not result or result.strip() == "":
            result = MESSAGES['no_data']
        
        # Отправляем результат
        await message.answer(result)
        
        # Удаляем сообщение о обработке (опционально)
        try:
            await processing_message.delete()
        except Exception:
            pass  # Игнорируем ошибки удаления сообщения
            
    except Exception as e:
        error_msg = MESSAGES['error'].format(error=str(e))
        logger.error(f"Ошибка при обработке запроса пользователя {user_id}: {str(e)}", exc_info=True)
        
        try:
            await message.answer(error_msg)
            await processing_message.delete()
        except Exception:
            pass

@router.message()
async def handle_other_messages(message: Message):
    """Обработчик всех остальных типов сообщений"""
    await message.answer("Я обрабатываю только текстовые запросы. Отправьте мне ваш вопрос текстом.")

async def main():
    """Основная функция запуска бота"""
    logger.info("Запуск бота...")
    
    # Регистрируем роутер
    dp.include_router(router)
    
    try:
        # Удаляем webhook и запускаем polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот запущен и готов к работе")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)