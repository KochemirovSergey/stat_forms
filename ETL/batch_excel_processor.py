import os
import time
from pathlib import Path
from typing import Dict, List, Any

# Поддержка как относительных, так и абсолютных импортов
try:
    from .excel_processor import process_directory
except ImportError:
    from excel_processor import process_directory


def process_all_regions(base_directory: str = "2024/") -> Dict[str, Any]:
    """
    Обрабатывает все папки в указанной директории, используя excel_processor.
    
    Args:
        base_directory: путь к директории с региональными папками
        
    Returns:
        Словарь с результатами обработки:
        {
            "total_folders": int,
            "successful": int, 
            "failed": int,
            "errors": [{"folder": str, "error": str}],
            "execution_time": float,
            "folder_times": {"folder_name": float}
        }
    """
    start_time = time.time()
    
    # Инициализация результатов
    result = {
        "total_folders": 0,
        "successful": 0,
        "failed": 0,
        "errors": [],
        "execution_time": 0.0,
        "folder_times": {}
    }
    
    # Проверяем существование базовой директории
    if not os.path.exists(base_directory):
        result["errors"].append({
            "folder": base_directory,
            "error": f"Базовая директория '{base_directory}' не найдена"
        })
        result["execution_time"] = time.time() - start_time
        return result
    
    # Получаем список всех папок в базовой директории
    try:
        items = os.listdir(base_directory)
        folders = []
        
        for item in items:
            item_path = os.path.join(base_directory, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                folders.append(item)
        
        result["total_folders"] = len(folders)
        
        print(f"Найдено {len(folders)} папок для обработки в директории '{base_directory}'")
        print("=" * 60)
        
    except Exception as e:
        result["errors"].append({
            "folder": base_directory,
            "error": f"Ошибка при сканировании директории: {str(e)}"
        })
        result["execution_time"] = time.time() - start_time
        return result
    
    # Обрабатываем каждую папку
    for folder_name in sorted(folders):
        folder_path = os.path.join(base_directory, folder_name)
        folder_start_time = time.time()
        
        print(f"Обработка папки: {folder_name}")
        
        try:
            # Вызываем функцию обработки из excel_processor
            process_directory(folder_path)
            
            # Записываем время обработки
            folder_execution_time = time.time() - folder_start_time
            result["folder_times"][folder_name] = folder_execution_time
            result["successful"] += 1
            
            print(f"✓ Успешно обработана за {folder_execution_time:.2f} сек")
            
        except Exception as e:
            folder_execution_time = time.time() - folder_start_time
            result["folder_times"][folder_name] = folder_execution_time
            result["failed"] += 1
            result["errors"].append({
                "folder": folder_name,
                "error": str(e)
            })
            
            print(f"✗ Ошибка при обработке: {str(e)}")
        
        print("-" * 40)
    
    # Записываем общее время выполнения
    result["execution_time"] = time.time() - start_time
    
    return result


def print_summary_report(result: Dict[str, Any]) -> None:
    """
    Выводит итоговый отчет о результатах обработки.
    
    Args:
        result: словарь с результатами обработки
    """
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    print(f"Общее количество папок: {result['total_folders']}")
    print(f"Успешно обработано: {result['successful']}")
    print(f"Обработано с ошибками: {result['failed']}")
    print(f"Общее время выполнения: {result['execution_time']:.2f} сек")
    
    if result['successful'] > 0:
        avg_time = sum(result['folder_times'].values()) / len(result['folder_times'])
        print(f"Среднее время обработки папки: {avg_time:.2f} сек")
    
    # Выводим ошибки, если они есть
    if result['errors']:
        print(f"\nОШИБКИ ({len(result['errors'])}):")
        print("-" * 40)
        for error in result['errors']:
            print(f"Папка: {error['folder']}")
            print(f"Ошибка: {error['error']}")
            print("-" * 40)
    
    # Выводим топ самых медленных папок
    if result['folder_times']:
        print(f"\nВРЕМЯ ОБРАБОТКИ ПО ПАПКАМ:")
        print("-" * 40)
        sorted_times = sorted(result['folder_times'].items(), 
                            key=lambda x: x[1], reverse=True)
        
        for folder, exec_time in sorted_times[:10]:  # Топ 10
            status = "✓" if folder not in [e['folder'] for e in result['errors']] else "✗"
            print(f"{status} {folder}: {exec_time:.2f} сек")
    
    print("=" * 60)


if __name__ == "__main__":
    print("Запуск массовой обработки Excel файлов...")
    print("Обрабатываются все папки в директории '2024/'")
    print()
    
    # Запускаем обработку
    result = process_all_regions()
    
    # Выводим итоговый отчет
    print_summary_report(result)
    
    # Выводим финальное сообщение
    if result['failed'] == 0:
        print(f"\n🎉 Все {result['successful']} папок успешно обработаны!")
    else:
        print(f"\n⚠️  Обработка завершена с ошибками:")
        print(f"   Успешно: {result['successful']}")
        print(f"   С ошибками: {result['failed']}")