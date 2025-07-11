# Модуль Tavily поиска

## Описание

Модуль `tavily_search.py` предназначен для поиска статистических данных в сфере образования через Tavily API. Модуль интегрируется с основным потоком обработки запросов и обеспечивает совместимость с CSV-модулем.

## Основные возможности

- **Поиск по годам**: Автоматически выполняет 11 запросов для периода 2014-2024
- **LLM анализ**: Использует GPT-4 для анализа и структурирования найденной информации
- **Совместимость**: Возвращает данные в том же формате, что и CSV-модуль
- **Обработка ошибок**: Включает логирование и обработку исключений
- **Качественная оценка**: LLM оценивает качество найденных данных

## Установка зависимостей

```bash
pip install tavily-python langchain-openai langchain-core pydantic
```

## Конфигурация

Модуль использует переменную окружения `TAVILY_API_KEY`, которая настраивается в `config.py`:

```python
os.environ["TAVILY_API_KEY"] = "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"
```

## Основная функция

### `search_with_tavily(user_query: str) -> Dict[str, Any]`

Выполняет поиск через Tavily API для заданного запроса пользователя.

**Параметры:**
- `user_query` (str): Запрос пользователя

**Возвращает:**
```python
{
    "success": bool,           # Успешность выполнения
    "data": {                  # Данные (если success=True)
        "table_number": "TAVILY_SEARCH",
        "table_name": "Поиск через Tavily API",
        "cells_data": [
            {
                "column_name": "Данные Tavily Search",
                "row_name": "Результаты поиска в интернете",
                "values": {
                    "2014": "значение",
                    "2015": "значение",
                    # ... остальные годы
                }
            }
        ],
        "analysis_summary": "общий анализ",
        "data_quality": "high|medium|low",
        "search_timestamp": "ISO timestamp"
    },
    "errors": []               # Список ошибок (если есть)
}
```

## Алгоритм работы

1. **Инициализация**: Создание клиента Tavily API
2. **Поиск по годам**: Для каждого года (2014-2024):
   - Формирование запроса: "{user_query} в российской федерации в сфере образования в {год} году"
   - Выполнение поиска через Tavily API
   - Пауза 0.5 сек между запросами
3. **LLM анализ**: Анализ всех результатов поиска с помощью GPT-4
4. **Форматирование**: Приведение к стандартному формату

## Интеграция с основным потоком

Модуль полностью совместим с существующим CSV-модулем и может использоваться в функции `analyze_combined_results()`:

```python
from tg_bot.tavily_search import search_with_tavily
from tg_bot.query_llm import analyze_combined_results

# Поиск через Tavily
tavily_result = search_with_tavily(user_query)

# Объединение с CSV результатами
combined_analysis = analyze_combined_results(
    user_query=user_query,
    result_2124=csv_result_2124,
    result_1620=tavily_result  # или наоборот
)
```

## Примеры использования

### Базовое использование

```python
from tg_bot.tavily_search import search_with_tavily

result = search_with_tavily("количество студентов высших учебных заведений")

if result["success"]:
    data = result["data"]
    print(f"Качество данных: {data['data_quality']}")
    
    for cell_data in data["cells_data"]:
        for year, value in cell_data['values'].items():
            print(f"{year}: {value}")
else:
    print("Ошибки:", result["errors"])
```

### Тестирование

```python
# Запуск встроенного теста
python -m tg_bot.tavily_search

# Запуск теста интеграции
python test_tavily_integration.py
```

## Логирование

Модуль использует стандартное логирование Python:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Логи включают:
- Начало поиска
- Поиск данных для каждого года
- Анализ LLM
- Завершение поиска
- Ошибки на всех этапах

## Ограничения и рекомендации

1. **API лимиты**: Между запросами установлена пауза 0.5 сек
2. **Качество данных**: LLM может оценить качество как low при противоречивых данных
3. **Источники**: Приоритет отдается официальным источникам (rosstat.gov.ru, edu.ru и т.д.)
4. **Обработка ошибок**: При ошибке API продолжается поиск для остальных лет

## Структуры данных

### YearlyDataAnalysis
```python
class YearlyDataAnalysis(BaseModel):
    year: str
    value: str
    source_info: str
    relevance_score: float  # 0-1
```

### TavilyAnalysisResponse
```python
class TavilyAnalysisResponse(BaseModel):
    yearly_data: List[YearlyDataAnalysis]
    summary: str
    data_quality: str  # "high", "medium", "low"
```

## Файлы модуля

- `tg_bot/tavily_search.py` - Основной модуль
- `test_tavily_integration.py` - Тест интеграции
- `tg_bot/README_tavily.md` - Данная документация

## Поддержка

При возникновении проблем проверьте:
1. Наличие TAVILY_API_KEY в переменных окружения
2. Установку всех зависимостей
3. Доступность API Tavily
4. Логи для диагностики ошибок

## ЭТАП 3: ЗАВЕРШЕН ✅

### Модификация логики обработки запросов в telegram_bot.py

**Выполненные изменения:**

1. **Модификация `process_user_query()` в `telegram_bot.py`:**
   - Добавлен импорт `from tg_bot.tavily_search import search_with_tavily`
   - Добавлена проверка `result_type == "not_found"` после `analyze_combined_results()`
   - При отсутствии данных в CSV автоматически запускается Tavily поиск
   - Повторный анализ результатов с учетом данных Tavily

2. **Обновление `analyze_combined_results()` в `query_llm.py`:**
   - Добавлен параметр `tavily_result: Dict[str, Any] = None`
   - Добавлена обработка третьего источника данных (Tavily)
   - Обновлен промпт для анализа трех источников данных
   - Добавлена передача `tavily_data` в LLM

3. **Расширение модели `CombinedAnalysisResponse`:**
   - Добавлен новый тип результата `"tavily_search"`
   - Обновлено описание поля `result_type`

4. **Обновление `format_combined_analysis_output()`:**
   - Добавлено описание для типа `"tavily_search"`
   - Добавлено специальное форматирование для результатов Tavily
   - Добавлены предупреждения об источнике данных

### Логика работы интеграции:

1. Выполняется поиск в CSV файлах (периоды 2016-2020 и 2021-2024)
2. LLM анализирует результаты и определяет `result_type`
3. Если `result_type = "not_found"` → запускается `search_with_tavily()`
4. Повторный анализ с учетом всех трех источников данных
5. Форматирование и отображение результатов пользователю

### Отображение результатов Tavily:

При использовании Tavily пользователь видит:
- 📡 ИСТОЧНИК: Интернет-поиск через Tavily API
- ⚠️ Данные получены из открытых источников в интернете
- 🔍 Рекомендуется проверить актуальность информации

### Тестирование интеграции:

```bash
python test_telegram_bot_tavily.py
```

**Результат:** Telegram бот корректно интегрирует Tavily поиск в основной поток обработки запросов и отображает результаты пользователю.