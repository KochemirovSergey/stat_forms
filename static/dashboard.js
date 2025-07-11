// Dashboard JavaScript функциональность
class DashboardManager {
    constructor() {
        this.currentNodeId = null;
        this.currentYear = '2024';
        this.isLoading = false;
        this.init();
    }

    init() {
        // Инициализация при загрузке страницы
        if (window.dashboardConfig) {
            this.currentNodeId = window.dashboardConfig.nodeId;
            this.currentYear = window.dashboardConfig.currentYear;
        }
        
        this.setupEventListeners();
        this.initializeTooltips();
    }

    setupEventListeners() {
        // Обработчик изменения года
        const yearSelector = document.getElementById('year-selector');
        if (yearSelector) {
            yearSelector.addEventListener('change', (e) => {
                this.changeYear(e.target.value);
            });
        }

        // Обработчик клавиатурных сокращений
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshDashboard();
                        break;
                    case 'k':
                        e.preventDefault();
                        this.showShareModal();
                        break;
                }
            }
        });

        // Закрытие модальных окон по клику вне их
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeAllModals();
            }
        });

        // Обработчик ESC для закрытия модальных окон
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    initializeTooltips() {
        // Инициализация подсказок для кнопок
        const tooltipElements = document.querySelectorAll('[title]');
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', this.showTooltip);
            element.addEventListener('mouseleave', this.hideTooltip);
        });
    }

    showTooltip(e) {
        // Простая реализация подсказок
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = e.target.getAttribute('title');
        tooltip.style.position = 'absolute';
        tooltip.style.background = 'rgba(0, 0, 0, 0.8)';
        tooltip.style.color = 'white';
        tooltip.style.padding = '8px 12px';
        tooltip.style.borderRadius = '4px';
        tooltip.style.fontSize = '14px';
        tooltip.style.zIndex = '9999';
        tooltip.style.pointerEvents = 'none';
        
        document.body.appendChild(tooltip);
        
        const rect = e.target.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.bottom + 8 + 'px';
        
        e.target.tooltipElement = tooltip;
        e.target.removeAttribute('title');
    }

    hideTooltip(e) {
        if (e.target.tooltipElement) {
            document.body.removeChild(e.target.tooltipElement);
            e.target.setAttribute('title', e.target.tooltipElement.textContent);
            e.target.tooltipElement = null;
        }
    }

    async changeYear(year) {
        if (this.isLoading || !this.currentNodeId || year === this.currentYear) {
            return;
        }

        this.isLoading = true;
        this.currentYear = year;
        
        try {
            this.showMapLoading();
            this.updateCurrentYearDisplay(year);
            
            // Получаем новую карту через API
            const response = await fetch(`/api/map/${this.currentNodeId}/${year}`);
            const data = await response.json();
            
            if (response.ok && data.map_html) {
                this.updateMapContainer(data.map_html);
                this.updateRegionsCount(year);
                this.showNotification('Карта успешно обновлена', 'success');
                
                // Обновляем URL без перезагрузки страницы
                const newUrl = `/dashboard/${this.currentNodeId}?year=${year}`;
                window.history.pushState({nodeId: this.currentNodeId, year: year}, '', newUrl);
            } else {
                throw new Error(data.error || 'Ошибка загрузки карты');
            }
        } catch (error) {
            console.error('Ошибка при изменении года:', error);
            this.showNotification('Ошибка при загрузке карты: ' + error.message, 'error');
        } finally {
            this.hideMapLoading();
            this.isLoading = false;
        }
    }

    showMapLoading() {
        const mapContainer = document.getElementById('map-container');
        const loadingElement = document.getElementById('map-loading');
        
        if (mapContainer) {
            mapContainer.style.opacity = '0.5';
            mapContainer.style.pointerEvents = 'none';
        }
        
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }
    }

    hideMapLoading() {
        const mapContainer = document.getElementById('map-container');
        const loadingElement = document.getElementById('map-loading');
        
        if (mapContainer) {
            mapContainer.style.opacity = '1';
            mapContainer.style.pointerEvents = 'auto';
        }
        
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    updateMapContainer(mapHtml) {
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) {
            mapContainer.innerHTML = mapHtml;
            
            // Перезапускаем Plotly если необходимо
            if (window.Plotly && mapContainer.querySelector('.plotly-graph-div')) {
                window.Plotly.Plots.resize(mapContainer.querySelector('.plotly-graph-div'));
            }
        }
    }

    updateCurrentYearDisplay(year) {
        const yearDisplay = document.getElementById('current-year-display');
        if (yearDisplay) {
            yearDisplay.textContent = year;
        }
    }

    updateRegionsCount(year) {
        // Обновляем счетчик регионов если есть данные
        if (window.dashboardConfig && window.dashboardConfig.regionalDataByYear) {
            const regionsCount = document.getElementById('regions-count');
            if (regionsCount) {
                const yearData = window.dashboardConfig.regionalDataByYear[year];
                const count = yearData ? Object.keys(yearData).length : 0;
                regionsCount.textContent = count;
            }
        }
    }

    async refreshDashboard() {
        if (this.isLoading || !this.currentNodeId) {
            return;
        }

        this.isLoading = true;
        
        try {
            this.showNotification('Обновление дашборда...', 'info');
            
            // Очищаем кеш и перезагружаем страницу
            await fetch('/api/clear-cache');
            window.location.reload();
        } catch (error) {
            console.error('Ошибка при обновлении дашборда:', error);
            this.showNotification('Ошибка при обновлении дашборда', 'error');
            this.isLoading = false;
        }
    }

    showShareModal() {
        const modal = document.getElementById('share-modal');
        if (modal) {
            modal.style.display = 'flex';
            
            // Фокус на первом поле ввода
            const firstInput = modal.querySelector('input');
            if (firstInput) {
                setTimeout(() => firstInput.select(), 100);
            }
        }
    }

    closeShareModal() {
        const modal = document.getElementById('share-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }

    async copyToClipboard(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        try {
            await navigator.clipboard.writeText(input.value);
            this.showNotification('Ссылка скопирована в буфер обмена', 'success');
        } catch (error) {
            // Fallback для старых браузеров
            input.select();
            document.execCommand('copy');
            this.showNotification('Ссылка скопирована в буфер обмена', 'success');
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        if (!notification) return;

        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.style.display = 'block';
        
        // Показываем уведомление
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Скрываем через 3 секунды
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.style.display = 'none';
            }, 300);
        }, 3000);
    }

    // Утилиты для работы с данными
    formatNumber(num) {
        if (typeof num !== 'number') return num;
        return num.toLocaleString('ru-RU', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('ru-RU', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Проверка состояния системы
    async checkSystemHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Ошибка проверки состояния системы:', error);
            return null;
        }
    }
}

// Глобальные функции для использования в HTML
function changeYear(year) {
    if (window.dashboardManager) {
        window.dashboardManager.changeYear(year);
    }
}

function refreshDashboard() {
    if (window.dashboardManager) {
        window.dashboardManager.refreshDashboard();
    }
}

function shareDashboard() {
    if (window.dashboardManager) {
        window.dashboardManager.showShareModal();
    }
}

function closeShareModal() {
    if (window.dashboardManager) {
        window.dashboardManager.closeShareModal();
    }
}

function copyToClipboard(inputId) {
    if (window.dashboardManager) {
        window.dashboardManager.copyToClipboard(inputId);
    }
}

// Функция инициализации дашборда
function initializeDashboard() {
    window.dashboardManager = new DashboardManager();
    
    // Настройка Plotly для лучшей производительности
    if (window.Plotly) {
        window.Plotly.setPlotConfig({
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            displaylogo: false
        });
    }
    
    // Обработка изменения размера окна
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (window.Plotly) {
                const plotlyDivs = document.querySelectorAll('.plotly-graph-div');
                plotlyDivs.forEach(div => {
                    window.Plotly.Plots.resize(div);
                });
            }
        }, 250);
    });
    
    console.log('Dashboard Manager инициализирован');
}

// Утилиты для работы с URL
class URLManager {
    static updateURL(nodeId, year) {
        const newUrl = `/dashboard/${nodeId}?year=${year}`;
        window.history.pushState({nodeId, year}, '', newUrl);
    }
    
    static getURLParams() {
        const urlParams = new URLSearchParams(window.location.search);
        return {
            year: urlParams.get('year') || '2024'
        };
    }
}

// Обработка состояния браузера (назад/вперед)
window.addEventListener('popstate', (event) => {
    if (event.state && window.dashboardManager) {
        const {nodeId, year} = event.state;
        if (year && year !== window.dashboardManager.currentYear) {
            const yearSelector = document.getElementById('year-selector');
            if (yearSelector) {
                yearSelector.value = year;
                window.dashboardManager.changeYear(year);
            }
        }
    }
});

// Обработка ошибок JavaScript
window.addEventListener('error', (event) => {
    console.error('JavaScript ошибка:', event.error);
    if (window.dashboardManager) {
        window.dashboardManager.showNotification('Произошла ошибка в интерфейсе', 'error');
    }
});

// Обработка необработанных промисов
window.addEventListener('unhandledrejection', (event) => {
    console.error('Необработанная ошибка промиса:', event.reason);
    if (window.dashboardManager) {
        window.dashboardManager.showNotification('Произошла ошибка при загрузке данных', 'error');
    }
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DashboardManager,
        URLManager,
        initializeDashboard
    };
}