// Основной JavaScript для обработки интерактивности

document.addEventListener('DOMContentLoaded', function() {
    const yearSlider = document.getElementById('year-slider');
    const yearDisplay = document.getElementById('year-display');
    const mapContainer = document.getElementById('map-container');
    
    if (yearSlider && yearDisplay && mapContainer && window.currentNodeId) {
        // Обновление отображения года при движении слайдера
        yearSlider.addEventListener('input', function() {
            yearDisplay.textContent = this.value;
        });
        
        // Обновление карты при изменении года через AJAX (без перезагрузки страницы)
        yearSlider.addEventListener('change', function() {
            updateMap(window.currentNodeId, this.value);
        });
        
        // Настраиваем обработчики кликов для изначально загруженной карты
        setupMapClickHandlers();
    }
});

// Переменная для предотвращения дублированных запросов
let isUpdatingMap = false;

/**
 * Обновляет карту для выбранного года через AJAX
 * @param {string} nodeId - ID узла Neo4j
 * @param {string} year - Выбранный год
 */
function updateMap(nodeId, year) {
    const mapContainer = document.getElementById('map-container');
    
    if (!mapContainer) {
        console.error('Контейнер карты не найден');
        return;
    }
    
    // Предотвращаем дублированные запросы
    if (isUpdatingMap) {
        console.log('Обновление карты уже в процессе, пропускаем запрос');
        return;
    }
    
    isUpdatingMap = true;
    
    // Показываем индикатор загрузки
    mapContainer.classList.add('updating');
    
    // Отправляем AJAX-запрос
    fetch('/update_map', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            node_id: nodeId,
            year: year
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            showError('Ошибка при обновлении карты: ' + data.error);
        } else if (data.map_html) {
            // Очищаем старый Plotly график
            const existingPlotlyDiv = mapContainer.querySelector('.plotly-graph-div');
            if (existingPlotlyDiv && window.Plotly) {
                window.Plotly.purge(existingPlotlyDiv);
            }
            
            // Обновляем содержимое карты
            mapContainer.innerHTML = data.map_html;
            console.log(`Карта обновлена для ${year} года`);
            
            // Инициализируем Plotly для нового div - выполняем скрипты из HTML
            const newPlotlyDiv = mapContainer.querySelector('.plotly-graph-div');
            if (newPlotlyDiv && window.Plotly) {
                console.log('Выполняем Plotly скрипты из обновленного HTML...');
                
                // Ищем и выполняем все скрипты в HTML
                const scriptMatches = data.map_html.match(/<script[^>]*>([\s\S]*?)<\/script>/gi);
                
                if (scriptMatches) {
                    scriptMatches.forEach((scriptMatch, index) => {
                        try {
                            // Извлекаем содержимое скрипта
                            const contentMatch = scriptMatch.match(/<script[^>]*>([\s\S]*?)<\/script>/i);
                            if (contentMatch) {
                                const scriptContent = contentMatch[1];
                                console.log(`Выполняем скрипт ${index + 1}/${scriptMatches.length}`);
                                
                                // Выполняем скрипт в глобальном контексте
                                eval(scriptContent);
                            }
                        } catch (error) {
                            console.error(`Ошибка выполнения скрипта ${index + 1}:`, error);
                        }
                    });
                    
                    // Настраиваем обработчики кликов после небольшой задержки
                    setTimeout(() => {
                        setupMapClickHandlers();
                    }, 300);
                } else {
                    console.warn('Скрипты Plotly не найдены в HTML');
                }
            }
        }
    })
    .catch(error => {
        console.error('Ошибка при обновлении карты:', error);
        showError('Не удалось обновить карту. Проверьте подключение к интернету.');
    })
    .finally(() => {
        // Убираем индикатор загрузки
        mapContainer.classList.remove('updating');
        // Сбрасываем флаг обновления
        isUpdatingMap = false;
    });
}

/**
 * Ждет полной готовности Plotly графика перед выполнением callback
 * @param {HTMLElement} plotlyDiv - Plotly div элемент
 * @param {Function} callback - Функция для выполнения после готовности
 */
function waitForPlotlyReady(plotlyDiv, callback) {
    let attempts = 0;
    const maxAttempts = 20; // Увеличиваем количество попыток
    
    function checkReady() {
        attempts++;
        
        // Проверяем различные признаки готовности Plotly
        const isReady = plotlyDiv._fullLayout ||
                       (plotlyDiv.data && plotlyDiv.layout) ||
                       plotlyDiv.querySelector('svg') ||
                       (window.Plotly && plotlyDiv.id && window.Plotly.d3 && window.Plotly.d3.select('#' + plotlyDiv.id).select('svg').node());
        
        if (isReady) {
            console.log(`Plotly готов после ${attempts} попыток`);
            
            // Дополнительная проверка - пытаемся изменить размер графика
            setTimeout(() => {
                try {
                    if (plotlyDiv._fullLayout && window.Plotly.Plots) {
                        window.Plotly.Plots.resize(plotlyDiv);
                    }
                } catch (resizeError) {
                    console.warn('Не удалось изменить размер графика:', resizeError);
                }
                
                callback();
            }, 200);
            
        } else if (attempts < maxAttempts) {
            console.log(`Ожидание готовности Plotly, попытка ${attempts}/${maxAttempts}`);
            setTimeout(checkReady, 250);
        } else {
            console.error(`Plotly не готов после ${maxAttempts} попыток`);
            // Все равно пытаемся выполнить callback
            callback();
        }
    }
    
    // Начинаем проверку с небольшой задержкой
    setTimeout(checkReady, 300);
}

/**
 * Показывает сообщение об ошибке
 * @param {string} message - Текст ошибки
 */
function showError(message) {
    // Ищем существующий контейнер для ошибок
    let errorSection = document.querySelector('.error-section');
    
    if (!errorSection) {
        // Создаем новый контейнер для ошибок
        errorSection = document.createElement('div');
        errorSection.className = 'error-section';
        
        // Вставляем после формы
        const formSection = document.querySelector('.form-section');
        if (formSection) {
            formSection.insertAdjacentElement('afterend', errorSection);
        } else {
            // Если формы нет, вставляем в начало main
            const main = document.querySelector('main');
            if (main) {
                main.insertBefore(errorSection, main.firstChild);
            }
        }
    }
    
    // Обновляем содержимое ошибки
    errorSection.innerHTML = `
        <div class="error-message">
            <strong>Ошибка:</strong> ${message}
        </div>
    `;
    
    // Автоматически скрываем ошибку через 5 секунд
    setTimeout(() => {
        if (errorSection && errorSection.parentNode) {
            errorSection.remove();
        }
    }, 5000);
}

/**
 * Утилита для дебаггинга - выводит информацию о текущем состоянии
 */
function debugInfo() {
    console.log('=== Debug Info ===');
    console.log('Current Node ID:', window.currentNodeId || 'Not set');
    console.log('Year Slider:', document.getElementById('year-slider'));
    console.log('Year Display:', document.getElementById('year-display'));
    console.log('Map Container:', document.getElementById('map-container'));
    console.log('==================');
}

/**
 * Настраивает обработчики кликов по регионам карты
 */
function setupMapClickHandlers() {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) {
        console.error('Контейнер карты не найден');
        return;
    }
    
    const plotlyDiv = mapContainer.querySelector('.plotly-graph-div');
    if (!plotlyDiv) {
        console.error('Plotly div не найден');
        return;
    }
    
    // Простая проверка готовности и настройка обработчиков
    function trySetupHandlers() {
        try {
            if (window.Plotly && plotlyDiv && typeof plotlyDiv.on === 'function') {
                // Настраиваем обработчик кликов
                plotlyDiv.on('plotly_click', function(data) {
                    if (data.points && data.points.length > 0) {
                        const point = data.points[0];
                        const regionName = point.data.name;
                        const hoverText = point.text;
                        
                        console.log('Клик по region:', regionName);
                        console.log('Hover text:', hoverText);
                        
                        // Показываем информацию о регионе
                        showRegionInfo(regionName, hoverText);
                    }
                });
                
                console.log('Обработчики кликов по карте настроены успешно');
                return true;
            }
        } catch (error) {
            console.error('Ошибка при настройке обработчиков Plotly:', error);
        }
        return false;
    }
    
    // Пробуем настроить с несколькими попытками
    let attempts = 0;
    const maxAttempts = 5;
    
    function attemptSetup() {
        attempts++;
        
        if (trySetupHandlers()) {
            return; // Успешно настроили
        }
        
        if (attempts < maxAttempts) {
            console.log(`Попытка настройки обработчиков ${attempts}/${maxAttempts}`);
            setTimeout(attemptSetup, 200);
        } else {
            console.warn('Не удалось настроить обработчики Plotly, используем альтернативный подход');
            setupAlternativeClickHandlers(plotlyDiv);
        }
    }
    
    // Начинаем попытки
    attemptSetup();
}

/**
 * Альтернативный способ настройки обработчиков кликов
 */
function setupAlternativeClickHandlers(plotlyDiv) {
    try {
        // Используем стандартный DOM API как fallback
        plotlyDiv.addEventListener('click', function(event) {
            console.log('Клик по карте (альтернативный обработчик)');
            // Можно добавить дополнительную логику обработки кликов
        });
        console.log('Альтернативные обработчики кликов настроены');
    } catch (error) {
        console.error('Ошибка при настройке альтернативных обработчиков:', error);
    }
}

/**
 * Показывает информацию о выбранном регионе
 * @param {string} regionName - Название региона
 * @param {string} hoverText - Текст с подробной информацией
 */
function showRegionInfo(regionName, hoverText) {
    // Создаем или обновляем панель с информацией о регионе
    let infoPanel = document.getElementById('region-info-panel');
    
    if (!infoPanel) {
        infoPanel = document.createElement('div');
        infoPanel.id = 'region-info-panel';
        infoPanel.className = 'region-info-panel';
        
        // Вставляем панель после контейнера карты
        const mapContainer = document.getElementById('map-container');
        if (mapContainer && mapContainer.parentNode) {
            mapContainer.parentNode.insertBefore(infoPanel, mapContainer.nextSibling);
        }
    }
    
    // Парсим информацию из hover text
    let regionTitle = regionName;
    let indicator = '';
    let year = '';
    let value = '';
    
    if (hoverText && typeof hoverText === 'string') {
        const lines = hoverText.split('<br>');
        
        lines.forEach(line => {
            if (line.includes('<b>') && !line.includes('Значение:')) {
                if (line !== `<b>${regionName}</b>`) {
                    indicator = line.replace(/<\/?b>/g, '');
                }
            } else if (line.startsWith('Год:')) {
                year = line.replace('Год: ', '');
            } else if (line.includes('Значение:')) {
                value = line.replace('Значение: ', '').replace(/<\/?b>/g, '');
            }
        });
    }
    
    infoPanel.innerHTML = `
        <div class="region-info-content">
            <h4>Информация о регионе</h4>
            <p><strong>Регион:</strong> ${regionTitle}</p>
            ${indicator ? `<p><strong>Показатель:</strong> ${indicator}</p>` : ''}
            ${year ? `<p><strong>Год:</strong> ${year}</p>` : ''}
            ${value ? `<p><strong>Значение:</strong> ${value}</p>` : ''}
            <button onclick="closeRegionInfo()" class="close-btn">Закрыть</button>
        </div>
    `;
    
    // Показываем панель с анимацией
    infoPanel.style.display = 'block';
    setTimeout(() => {
        infoPanel.classList.add('show');
    }, 10);
}

/**
 * Закрывает панель с информацией о регионе
 */
function closeRegionInfo() {
    const infoPanel = document.getElementById('region-info-panel');
    if (infoPanel) {
        infoPanel.classList.remove('show');
        setTimeout(() => {
            infoPanel.style.display = 'none';
        }, 300);
    }
}


// Экспортируем функции для возможного использования в консоли
window.updateMap = updateMap;
window.showError = showError;
window.waitForPlotlyReady = waitForPlotlyReady;
window.debugInfo = debugInfo;
window.setupMapClickHandlers = setupMapClickHandlers;
window.showRegionInfo = showRegionInfo;
window.closeRegionInfo = closeRegionInfo;

// === Функции для работы с графом Neo4j ===

let network = null;
let nodes = null;
let edges = null;

/**
 * Инициализация графа Neo4j
 */
function initializeGraph() {
    const container = document.getElementById('graph-container');
    if (!container) {
        console.error('Контейнер для графа не найден');
        return;
    }

    // Показываем индикатор загрузки
    container.innerHTML = '<div class="graph-loading">Загрузка графа...</div>';

    // Загружаем данные графа с сервера
    fetch('/graph_data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            console.log('Получены данные графа:', data);
            
            // Устанавливаем цветовую схему, если она есть в данных
            if (data.color_mapping) {
                setGraphColorMapping(data.color_mapping);
            }
            
            renderGraph(data.nodes, data.edges);
        })
        .catch(error => {
            console.error('Ошибка при загрузке данных графа:', error);
            container.innerHTML = `
                <div class="graph-loading" style="color: #c33;">
                    Ошибка загрузки графа: ${error.message}
                </div>
            `;
        });
}

/**
 * Отрисовка графа с помощью vis.js
 */
function renderGraph(nodesData, edgesData) {
    const container = document.getElementById('graph-container');
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Модифицируем edges для установки разной длины связей
    const modifiedEdgesData = edgesData.map(edge => {
        // Находим узлы источника и назначения
        const sourceNode = nodesData.find(n => n.id === edge.from);
        const targetNode = nodesData.find(n => n.id === edge.to);
        
        if (sourceNode && targetNode) {
            const sourceGroup = sourceNode.group;
            const targetGroup = targetNode.group;
            
            // Если связь между "Счетное" и "Расчетные" - делаем короткой
            if ((sourceGroup === 'Счетное' && targetGroup === 'Расчетные') ||
                (sourceGroup === 'Расчетные' && targetGroup === 'Счетное')) {
                return { ...edge, length: 50 };
            }
        }
        
        // Для всех остальных связей - длинные
        return { ...edge, length: 200 };
    });
    
    // Создаем DataSets для vis.js
    nodes = new vis.DataSet(nodesData);
    edges = new vis.DataSet(modifiedEdgesData);
    
    // Данные для графа
    const data = {
        nodes: nodes,
        edges: edges
    };
    
    // Применяем динамическую цветовую схему к узлам
    // Получаем цветовую схему из данных или используем генерацию по умолчанию
    let colors = {};
    
    // Проверяем, есть ли цветовая схема в данных графа
    if (window.graphColorMapping && typeof window.graphColorMapping === 'object') {
        colors = window.graphColorMapping;
    } else {
        // Генерируем цвета динамически для всех найденных групп
        const allGroups = [...new Set(nodesData.map(node => node.group))];
        colors = generateDynamicColors(allGroups);
    }
    
    // Подсчитываем количество узлов для равномерного распределения
    const calculatedNodes = nodesData.filter(node => node.group === 'Расчетные');
    const calculatedCount = calculatedNodes.length;
    const schetnyeNodes = nodesData.filter(node => node.group === 'Счетное');
    const schetnyeCount = schetnyeNodes.length;
    
    let calculatedIndex = 0;
    let schetnyeIndex = 0;
    
    const updatedNodesData = nodesData.map(node => {
        const baseNode = {
            ...node,
            color: colors[node.group] || generateColorFromLabel(node.group),
            size: (node.group === 'Счетное' ? 12 : 15)  // Узлы "Счетное" меньшего размера
        };
        
        // Задаем начальные позиции для узлов "Расчетные" в центре графа
        if (node.group === 'Расчетные') {
            const radius = 80; // Радиус круга для размещения узлов "Расчетные"
            const angle = (calculatedIndex * 2 * Math.PI) / calculatedCount;
            
            baseNode.x = radius * Math.cos(angle);
            baseNode.y = radius * Math.sin(angle);
            // Убираем фиксацию - узлы могут двигаться по физике
            
            calculatedIndex++;
        }
        
        // Задаем начальные позиции для узлов "Счетное" вокруг "Расчетных"
        if (node.group === 'Счетное') {
            const radius = 180; // Больший радиус для узлов "Счетное"
            const angle = (schetnyeIndex * 2 * Math.PI) / schetnyeCount;
            
            baseNode.x = radius * Math.cos(angle);
            baseNode.y = radius * Math.sin(angle);
            // Узлы также могут двигаться по физике
            
            schetnyeIndex++;
        }
        
        return baseNode;
    });
    
    // Обновляем DataSet с новыми цветами и размерами
    nodes.update(updatedNodesData);
    
    // Опции для графа с использованием глобальных настроек
    const options = {
        nodes: {
            shape: 'dot',
            font: {
                size: 14,
                color: '#333'
            },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            width: 2,
            color: {
                color: '#848484',
                highlight: '#667eea'
            },
            smooth: {
                type: 'continuous'
            },
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 1
                }
            },
            font: {
                size: 12,
                color: '#666'
            }
        },
        physics: {
            stabilization: {
                enabled: true,
                iterations: 100
            },
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 95,
                springConstant: 0.04,
                damping: 0.09
            },
            // Включаем использование индивидуальной длины ребер
            solver: 'barnesHut'
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            hideEdgesOnDrag: false,
            hideNodesOnDrag: false
        },
        layout: {
            improvedLayout: true
        }
    };
    
    // Создаем граф
    network = new vis.Network(container, data, options);
    
    // Обработчик клика по узлу
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            
            // Автозаполнение формы для узлов типа "Счетное" и "Расчетные"
            if (node && (node.group === 'Счетное' || node.group === 'Расчетные')) {
                const nodeIdInput = document.getElementById('node_id');
                if (nodeIdInput) {
                    nodeIdInput.value = node.id;
                }
            }
            
            showNodeDetails(node);
        } else {
            hideNodeDetails();
        }
    });
    
    // Обработчик наведения для tooltip
    network.on('hoverNode', function(params) {
        const nodeId = params.node;
        const node = nodes.get(nodeId);
        
        // vis.js автоматически показывает tooltip на основе title
        console.log('Наведение на узел:', node.label);
    });
    
    console.log('Граф успешно отрисован');
}

/**
 * Показывает детальную информацию об узле
 */
function showNodeDetails(node) {
    const detailsContainer = document.getElementById('node-details');
    const contentContainer = document.getElementById('node-details-content');
    
    if (!detailsContainer || !contentContainer) {
        console.error('Контейнеры для деталей узла не найдены');
        return;
    }
    
    // Парсим HTML из title для извлечения информации
    const parser = new DOMParser();
    const doc = parser.parseFromString(node.title, 'text/html');
    const textContent = doc.body.textContent || doc.body.innerText || '';
    
    // Разбиваем на строки и форматируем
    const lines = textContent.split('\n').filter(line => line.trim());
    let formattedContent = '';
    
    lines.forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine) {
            formattedContent += `<p>${trimmedLine}</p>`;
        }
    });
    
    contentContainer.innerHTML = formattedContent || `<p>Информация об узле "${node.label}" недоступна</p>`;
    detailsContainer.style.display = 'block';
    
    console.log('Показаны детали узла:', node.label);
}

/**
 * Скрывает детальную информацию об узле
 */
function hideNodeDetails() {
    const detailsContainer = document.getElementById('node-details');
    if (detailsContainer) {
        detailsContainer.style.display = 'none';
    }
}

/**
 * Закрывает панель с деталями узла (вызывается из HTML)
 */
function closeNodeDetails() {
    hideNodeDetails();
}

/**
 * Обновляет граф (перезагружает данные)
 */
function refreshGraph() {
    initializeGraph();
}

// Экспортируем основные функции для использования в консоли
window.initializeGraph = initializeGraph;
window.renderGraph = renderGraph;
window.showNodeDetails = showNodeDetails;
window.hideNodeDetails = hideNodeDetails;
window.closeNodeDetails = closeNodeDetails;
window.refreshGraph = refreshGraph;
window.generateColorFromLabel = generateColorFromLabel;
window.generateDynamicColors = generateDynamicColors;
window.setGraphColorMapping = setGraphColorMapping;

/**
 * Генерирует цвет для метки на основе хеша (аналогично Python версии)
 * @param {string} label - Метка узла
 * @returns {string} HEX цвет
 */
function generateColorFromLabel(label) {
    if (!label) return '#a8a8a8';
    
    // Создаем простой хеш от строки
    let hash = 0;
    for (let i = 0; i < label.length; i++) {
        const char = label.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Преобразуем в 32-битное число
    }
    
    // Преобразуем хеш в цвет
    const r = (hash & 0xFF0000) >> 16;
    const g = (hash & 0x00FF00) >> 8;
    const b = hash & 0x0000FF;
    
    // Убеждаемся, что цвет достаточно яркий
    const brightness = r + g + b;
    let finalR = r, finalG = g, finalB = b;
    
    if (brightness < 200) {
        finalR = Math.min(255, r + 100);
        finalG = Math.min(255, g + 100);
        finalB = Math.min(255, b + 100);
    }
    
    // Преобразуем в HEX
    const toHex = (num) => {
        const hex = Math.abs(num).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    
    return `#${toHex(finalR)}${toHex(finalG)}${toHex(finalB)}`;
}

/**
 * Генерирует динамическую цветовую схему для массива групп
 * @param {Array<string>} groups - Массив названий групп
 * @returns {Object} Объект с маппингом группа -> цвет
 */
function generateDynamicColors(groups) {
    const colors = {};
    
    // Фиксированный цвет для счетных узлов
    if (groups.includes('Счетное')) {
        colors['Счетное'] = '#808080';
    }
    
    // Генерируем цвета для остальных групп
    groups.forEach(group => {
        if (group !== 'Счетное' && !colors[group]) {
            colors[group] = generateColorFromLabel(group);
        }
    });
    
    return colors;
}

/**
 * Устанавливает глобальную цветовую схему для использования в графе
 * @param {Object} colorMapping - Маппинг метка -> цвет
 */
function setGraphColorMapping(colorMapping) {
    window.graphColorMapping = colorMapping;
    console.log('Установлена цветовая схема:', colorMapping);
}
