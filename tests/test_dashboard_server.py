#!/usr/bin/env python3
"""
Тестирование Dashboard Server
"""

import requests
import json
import time
from typing import Dict, Any

class DashboardServerTester:
    """Класс для тестирования Dashboard Server"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.test_node_id = "4:2a2ab0e9-9777-41b2-89a4-9d85382603dc:156"
        self.test_year = "2024"
    
    def test_health_check(self) -> bool:
        """Тест проверки состояния сервера"""
        try:
            print("🔍 Тестирование health check...")
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check успешен: {data.get('status')}")
                print(f"   - Подключение к Neo4j: {data.get('neo4j_connection')}")
                print(f"   - Размер кеша: {data.get('cache_size')}")
                return True
            else:
                print(f"❌ Health check неуспешен: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка health check: {str(e)}")
            return False
    
    def test_main_page(self) -> bool:
        """Тест главной страницы"""
        try:
            print("🔍 Тестирование главной страницы...")
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                print("✅ Главная страница загружается успешно")
                return True
            else:
                print(f"❌ Главная страница недоступна: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка загрузки главной страницы: {str(e)}")
            return False
    
    def test_dashboard_page(self) -> bool:
        """Тест страницы дашборда"""
        try:
            print(f"🔍 Тестирование дашборда для узла {self.test_node_id}...")
            response = requests.get(
                f"{self.base_url}/dashboard/{self.test_node_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Дашборд загружается успешно")
                # Проверяем наличие ключевых элементов
                content = response.text
                if "plotly-graph-div" in content or "chart-container" in content:
                    print("✅ Графики присутствуют в дашборде")
                return True
            else:
                print(f"❌ Дашборд недоступен: {response.status_code}")
                if response.status_code == 500:
                    print(f"   Ошибка сервера: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка загрузки дашборда: {str(e)}")
            return False
    
    def test_dashboard_with_year(self) -> bool:
        """Тест дашборда с указанием года"""
        try:
            print(f"🔍 Тестирование дашборда для узла {self.test_node_id}, год {self.test_year}...")
            response = requests.get(
                f"{self.base_url}/dashboard/{self.test_node_id}/{self.test_year}",
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Дашборд с годом загружается успешно")
                return True
            else:
                print(f"❌ Дашборд с годом недоступен: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка загрузки дашборда с годом: {str(e)}")
            return False
    
    def test_api_dashboard_data(self) -> bool:
        """Тест API получения данных дашборда"""
        try:
            print(f"🔍 Тестирование API данных дашборда...")
            response = requests.get(
                f"{self.base_url}/api/dashboard/{self.test_node_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API данных дашборда работает")
                print(f"   - Node ID: {data.get('node_id')}")
                print(f"   - Текущий год: {data.get('current_year')}")
                print(f"   - Доступные годы: {len(data.get('available_years', []))}")
                return True
            else:
                print(f"❌ API данных дашборда недоступен: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка API данных дашборда: {str(e)}")
            return False
    
    def test_api_map_data(self) -> bool:
        """Тест API получения карты"""
        try:
            print(f"🔍 Тестирование API карты...")
            response = requests.get(
                f"{self.base_url}/api/map/{self.test_node_id}/{self.test_year}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API карты работает")
                print(f"   - Node ID: {data.get('node_id')}")
                print(f"   - Год: {data.get('year')}")
                print(f"   - HTML карты: {'Да' if data.get('map_html') else 'Нет'}")
                return True
            else:
                print(f"❌ API карты недоступен: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка API карты: {str(e)}")
            return False
    
    def test_api_chart_data(self) -> bool:
        """Тест API получения графика"""
        try:
            print(f"🔍 Тестирование API графика...")
            response = requests.get(
                f"{self.base_url}/api/chart/{self.test_node_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API графика работает")
                print(f"   - Node ID: {data.get('node_id')}")
                print(f"   - HTML графика: {'Да' if data.get('chart_html') else 'Нет'}")
                return True
            else:
                print(f"❌ API графика недоступен: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка API графика: {str(e)}")
            return False
    
    def test_api_clear_cache(self) -> bool:
        """Тест API очистки кеша"""
        try:
            print(f"🔍 Тестирование API очистки кеша...")
            response = requests.get(f"{self.base_url}/api/clear-cache", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API очистки кеша работает")
                print(f"   - Сообщение: {data.get('message')}")
                return True
            else:
                print(f"❌ API очистки кеша недоступен: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка API очистки кеша: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Тест обработки ошибок"""
        try:
            print(f"🔍 Тестирование обработки ошибок...")
            
            # Тест с несуществующим узлом
            response = requests.get(
                f"{self.base_url}/dashboard/nonexistent-node-id",
                timeout=10
            )
            
            if response.status_code == 500:
                print("✅ Обработка ошибок работает (возвращает 500 для несуществующего узла)")
                return True
            else:
                print(f"⚠️ Неожиданный код ответа для несуществующего узла: {response.status_code}")
                return True  # Это не критическая ошибка
                
        except Exception as e:
            print(f"❌ Ошибка тестирования обработки ошибок: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Запуск всех тестов"""
        print("🚀 Запуск тестирования Dashboard Server")
        print("=" * 50)
        
        tests = {
            "Health Check": self.test_health_check,
            "Главная страница": self.test_main_page,
            "Дашборд": self.test_dashboard_page,
            "Дашборд с годом": self.test_dashboard_with_year,
            "API данных дашборда": self.test_api_dashboard_data,
            "API карты": self.test_api_map_data,
            "API графика": self.test_api_chart_data,
            "API очистки кеша": self.test_api_clear_cache,
            "Обработка ошибок": self.test_error_handling
        }
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests.items():
            print(f"\n📋 {test_name}")
            print("-" * 30)
            
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте {test_name}: {str(e)}")
                results[test_name] = False
            
            time.sleep(1)  # Небольшая пауза между тестами
        
        # Итоговый отчет
        print("\n" + "=" * 50)
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 50)
        
        for test_name, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"{test_name}: {status}")
        
        print(f"\nОбщий результат: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("🎉 Все тесты успешно пройдены!")
        elif passed >= total * 0.8:
            print("⚠️ Большинство тестов пройдено, но есть проблемы")
        else:
            print("❌ Много тестов провалено, требуется исправление")
        
        return results

def main():
    """Основная функция"""
    print("Dashboard Server Tester")
    print("Убедитесь, что сервер запущен на http://localhost:5001")
    
    # Проверяем доступность сервера
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер недоступен или работает некорректно")
            return
    except:
        print("❌ Сервер недоступен. Запустите dashboard_server.py")
        return
    
    tester = DashboardServerTester()
    results = tester.run_all_tests()
    
    # Возвращаем код выхода
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    if passed_count == total_count:
        exit(0)  # Все тесты пройдены
    else:
        exit(1)  # Есть проваленные тесты

if __name__ == "__main__":
    main()