// Основной класс приложения
class RegionalMapApp {
    constructor() {
        this.form = document.getElementById('mapForm');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.errorContainer = document.getElementById('errorContainer');
        this.mapContainer = document.getElementById('mapContainer');
        this.statsContainer = document.getElementById('statsContainer');
        this.generateBtn = document.getElementById('generateBtn');
        this.yearSlider = document.getElementById('year');
        this.yearDisplay = document.getElementById('yearDisplay');
        
        // Массив доступных годов
        this.availableYears = [2022, 2023, 2024];
        
        this.init();
    }
    
    init() {
        // Привязываем обработчики событий
        this.form.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Валидация формы в реальном времени
        this.setupFormValidation();
        
        // Настройка слайдера года
        this.setupYearSlider();
        
        // Инициализация
        console.log('Приложение инициализировано');
    }
    
    setupFormValidation() {
        const inputs = this.form.querySelectorAll('input[required], select[required]');
        
        inputs.forEach(input => {
            // Пропускаем слайдер года, он обрабатывается отдельно
            if (input.id === 'year') return;
            
            input.addEventListener('input', () => {
                this.validateField(input);
                this.checkFormCompleteness();
            });
            
            input.addEventListener('blur', () => {
                this.validateField(input);
                this.checkFormCompleteness();
            });
        });
    }
    
    setupYearSlider() {
        // Обработчик изменения слайдера
        this.yearSlider.addEventListener('input', (e) => {
            const yearIndex = parseInt(e.target.value);
            const selectedYear = this.availableYears[yearIndex];
            this.yearDisplay.textContent = selectedYear;
            
            // Если форма заполнена и карта уже построена, перестраиваем её
            if (!this.yearSlider.disabled && this.isMapGenerated()) {
                this.handleYearChange(selectedYear);
            }
        });
        
        // Инициализация отображения года
        const initialYearIndex = parseInt(this.yearSlider.value);
        this.yearDisplay.textContent = this.availableYears[initialYearIndex];
    }
    
    checkFormCompleteness() {
        const tableNumber = document.getElementById('tableNumber').value.trim();
        const columnNumber = document.getElementById('columnNumber').value;
        const rowNumber = document.getElementById('rowNumber').value;
        
        const isComplete = tableNumber && columnNumber && rowNumber;
        
        if (isComplete && this.yearSlider.disabled) {
            // Активируем слайдер
            this.yearSlider.disabled = false;
            this.yearSlider.parentElement.classList.add('active');
            console.log('Слайдер года активирован');
        } else if (!isComplete && !this.yearSlider.disabled) {
            // Деактивируем слайдер
            this.yearSlider.disabled = true;
            this.yearSlider.parentElement.classList.remove('active');
            console.log('Слайдер года деактивирован');
        }
    }
    
    isMapGenerated() {
        // Проверяем, есть ли уже построенная карта
        return document.getElementById('plotly-map') !== null;
    }
    
    async handleYearChange(newYear) {
        console.log('Изменение года на:', newYear);
        
        // Собираем данные формы с новым годом
        const formData = new FormData(this.form);
        const data = {
            table_number: formData.get('table_number').trim(),
            column_number: parseInt(formData.get('column_number')),
            row_number: parseInt(formData.get('row_number')),
            year: newYear
        };
        
        try {
            await this.generateMap(data);
        } catch (error) {
            console.error('Ошибка при смене года:', error);
            this.showError('Ошибка при обновлении карты для нового года');
        }
    }
    
    validateField(field) {
        const isValid = field.checkValidity();
        
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
        }
        
        return isValid;
    }
    
    validateForm() {
        const inputs = this.form.querySelectorAll('input[required], select[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            // Пропускаем слайдер года в валидации, он не обязателен
            if (input.id === 'year') return;
            
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    async handleFormSubmit(event) {
        event.preventDefault();
        
        // Валидация формы
        if (!this.validateForm()) {
            this.form.classList.add('was-validated');
            return;
        }
        
        // Собираем данные формы
        const formData = new FormData(this.form);
        const yearIndex = parseInt(this.yearSlider.value);
        const selectedYear = this.availableYears[yearIndex];
        
        const data = {
            table_number: formData.get('table_number').trim(),
            column_number: parseInt(formData.get('column_number')),
            row_number: parseInt(formData.get('row_number')),
            year: selectedYear
        };
        
        console.log('Отправка данных:', data);
        
        try {
            await this.generateMap(data);
        } catch (error) {
            console.error('Ошибка при генерации карты:', error);
            this.showError('Произошла неожиданная ошибка при создании карты');
        }
    }
    
    async generateMap(data) {
        // Показываем индикатор загрузки
        this.showLoading();
        
        try {
            const response = await fetch('/api/generate_map', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            console.log('Ответ от сервера:', {
                success: result.success,
                graphJsonLength: result.graph_json ? result.graph_json.length : 0,
                error: result.error,
                stats: result.stats
            });
            
            if (result.success) {
                console.log('JSON первые 200 символов:', result.graph_json ? result.graph_json.substring(0, 200) : 'JSON пустой');
                this.showMap(result.graph_json);
                this.updateStats(result.stats);
                this.hideError();
            } else {
                this.showError(result.error);
                this.hideStats();
            }
            
        } catch (error) {
            console.error('Ошибка сети:', error);
            this.showError('Ошибка соединения с сервером. Проверьте подключение к интернету.');
        } finally {
            this.hideLoading();
        }
    }
    
    showLoading() {
        this.loadingIndicator.style.display = 'flex';
        this.generateBtn.disabled = true;
        this.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Создание карты...';
    }
    
    hideLoading() {
        this.loadingIndicator.style.display = 'none';
        this.generateBtn.disabled = false;
        this.generateBtn.innerHTML = '<i class="fas fa-map"></i> Создать карту';
    }
    
    showMap(graphJson) {
        console.log('showMap вызван с JSON длиной:', graphJson ? graphJson.length : 0);
        console.log('Контейнер карты найден:', !!this.mapContainer);
        
        if (!graphJson) {
            console.error('JSON карты пустой!');
            this.showError('Получен пустой JSON карты');
            return;
        }
        
        try {
            // Парсим JSON
            const graphData = JSON.parse(graphJson);
            console.log('JSON успешно распарсен');
            
            // Очищаем контейнер и создаем div для карты
            this.mapContainer.innerHTML = '<div id="plotly-map" style="width:100%; height:600px;"></div>';
            
            // Проверяем доступность Plotly
            if (!window.Plotly) {
                console.error('Plotly не загружен!');
                this.showError('Библиотека Plotly не загружена. Проверьте подключение к интернету.');
                return;
            }
            
            // Отрисовываем карту с помощью Plotly
            window.Plotly.newPlot('plotly-map', graphData.data, graphData.layout || {}, {
                responsive: true,
                displayModeBar: true
            });
            
            console.log('Карта успешно отрисована с помощью Plotly');
            
            // Добавляем анимацию появления
            this.mapContainer.classList.add('fade-in');
            
            // Убираем класс анимации через некоторое время
            setTimeout(() => {
                this.mapContainer.classList.remove('fade-in');
            }, 500);
            
            console.log('Карта успешно отображена');
            
        } catch (error) {
            console.error('Ошибка при обработке JSON карты:', error);
            this.showError('Ошибка при отображении карты: ' + error.message);
        }
    }
    
    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.innerHTML = message;
        this.errorContainer.style.display = 'block';
        
        // Прокручиваем к ошибке
        this.errorContainer.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
    
    hideError() {
        this.errorContainer.style.display = 'none';
    }
    
    updateStats(stats) {
        if (!stats) return;
        
        document.getElementById('totalRegions').textContent = stats.total_regions || '-';
        document.getElementById('regionsWithData').textContent = stats.regions_with_data || '-';
        document.getElementById('processedRegions').textContent = stats.processed_regions || '-';
        
        this.statsContainer.style.display = 'block';
    }
    
    hideStats() {
        this.statsContainer.style.display = 'none';
    }
    
    resizeMap() {
        // Принудительно обновляем размеры Plotly карты
        const plotlyDiv = document.getElementById('plotly-map');
        console.log('resizeMap - Plotly div найден:', !!plotlyDiv);
        console.log('resizeMap - window.Plotly доступен:', !!window.Plotly);
        
        if (plotlyDiv && window.Plotly) {
            setTimeout(() => {
                window.Plotly.Plots.resize('plotly-map');
            }, 100);
        } else if (!window.Plotly) {
            console.error('Plotly библиотека не загружена!');
        }
    }
}

// Утилиты для работы с формой
class FormUtils {
    static formatTableNumber(input) {
        // Автоматическое форматирование номера таблицы
        let value = input.value.replace(/[^\d.]/g, '');
        
        // Ограничиваем количество точек
        const parts = value.split('.');
        if (parts.length > 3) {
            value = parts.slice(0, 3).join('.');
        }
        
        input.value = value;
    }
    
    static restrictNumericInput(input, min = 1, max = 1000) {
        let value = parseInt(input.value);
        
        if (isNaN(value) || value < min) {
            input.value = min;
        } else if (value > max) {
            input.value = max;
        }
    }
}

// Обработчики событий для улучшения UX
document.addEventListener('DOMContentLoaded', function() {
    // Инициализируем приложение
    const app = new RegionalMapApp();
    
    // Автоформатирование номера таблицы
    const tableNumberInput = document.getElementById('tableNumber');
    tableNumberInput.addEventListener('input', function() {
        FormUtils.formatTableNumber(this);
    });
    
    // Ограничения для числовых полей
    const columnNumberInput = document.getElementById('columnNumber');
    columnNumberInput.addEventListener('change', function() {
        FormUtils.restrictNumericInput(this, 1, 100);
    });
    
    const rowNumberInput = document.getElementById('rowNumber');
    rowNumberInput.addEventListener('change', function() {
        FormUtils.restrictNumericInput(this, 1, 1000);
    });
    
    // Начальная проверка полноты формы
    app.checkFormCompleteness();
    
    // Обработка изменения размера окна
    window.addEventListener('resize', function() {
        app.resizeMap();
    });
    
    // Горячие клавиши
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + Enter для отправки формы
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            app.form.dispatchEvent(new Event('submit'));
        }
        
        // Escape для скрытия ошибок
        if (event.key === 'Escape') {
            app.hideError();
        }
    });
    
    // Мобильная адаптация
    if (window.innerWidth <= 768) {
        setupMobileInterface();
    }
});

// Мобильный интерфейс
function setupMobileInterface() {
    // Создаем кнопку для открытия боковой панели
    const toggleButton = document.createElement('button');
    toggleButton.className = 'mobile-toggle';
    toggleButton.innerHTML = '<i class="fas fa-bars"></i>';
    toggleButton.addEventListener('click', toggleSidebar);
    
    document.body.appendChild(toggleButton);
    
    // Закрытие боковой панели при клике вне её
    document.addEventListener('click', function(event) {
        const sidebar = document.querySelector('.sidebar');
        const isClickInsideSidebar = sidebar.contains(event.target);
        const isToggleButton = event.target.closest('.mobile-toggle');
        
        if (!isClickInsideSidebar && !isToggleButton && sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
        }
    });
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

// Обработка ошибок JavaScript
window.addEventListener('error', function(event) {
    console.error('JavaScript ошибка:', event.error);
    
    // Показываем пользователю общее сообщение об ошибке
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    
    if (errorContainer && errorMessage) {
        errorMessage.innerHTML = 'Произошла ошибка в работе приложения. Попробуйте обновить страницу.';
        errorContainer.style.display = 'block';
    }
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { RegionalMapApp, FormUtils };
}