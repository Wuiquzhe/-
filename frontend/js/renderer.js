// renderer.js - DailyEnchant 前端交互逻辑

// API基础URL
const API_BASE_URL = 'http://localhost:5000/api';

// 全局变量
let currentView = 'tasks';
let currentFilter = 'all';
let currentCategory = 'all';
let currentTaskId = null;
let tasks = [];
let categories = [];

// DOM元素引用
const elements = {
    // 视图相关
    tasksView: document.getElementById('tasks-view'),
    calendarView: document.getElementById('calendar-view'),
    statsView: document.getElementById('stats-view'),
    tasksContainer: document.getElementById('tasks-container'),
    
    // 按钮相关
    tasksViewBtn: document.getElementById('tasks-view-btn'),
    calendarViewBtn: document.getElementById('calendar-view-btn'),
    statsViewBtn: document.getElementById('stats-view-btn'),
    createTaskBtn: document.getElementById('create-task-btn'),
    createFirstTaskBtn: document.getElementById('create-first-task-btn'),
    refreshBtn: document.getElementById('refresh-btn'),
    filterTasksBtn: document.getElementById('filter-tasks-btn'),
    
    // 模态框相关
    taskModal: document.getElementById('task-modal'),
    closeModalBtn: document.getElementById('close-modal-btn'),
    cancelModalBtn: document.getElementById('cancel-modal-btn'),
    saveTaskBtn: document.getElementById('save-task-btn'),
    deleteTaskBtn: document.getElementById('delete-task-btn'),
    modalTitle: document.getElementById('modal-title'),
    
    // 表单相关
    taskForm: document.getElementById('task-form'),
    taskTitle: document.getElementById('task-title'),
    taskCategory: document.getElementById('task-category'),
    taskPriority: document.getElementById('task-priority'),
    taskDueDate: document.getElementById('task-due-date'),
    taskStatus: document.getElementById('task-status'),
    taskDescription: document.getElementById('task-description'),
    taskTags: document.getElementById('task-tags'),
    progressRecords: document.getElementById('progress-records'),
    newProgress: document.getElementById('new-progress'),
    addProgressBtn: document.getElementById('add-progress-btn'),
    
    // 筛选和排序相关
    filterList: document.querySelectorAll('.filter-item'),
    categoryList: document.getElementById('category-list'),
    sortSelect: document.getElementById('sort-select'),
    searchInput: document.getElementById('search-input'),
    searchBtn: document.getElementById('search-btn'),
    
    // 统计相关
    totalTasks: document.getElementById('total-tasks'),
    todoTasks: document.getElementById('todo-tasks'),
    inProgressTasks: document.getElementById('in-progress-tasks'),
    completedTasks: document.getElementById('completed-tasks'),
    
    // 加载和通知
    loadingIndicator: document.getElementById('loading-indicator'),
    notification: document.getElementById('notification'),
    notificationIcon: document.getElementById('notification-icon'),
    notificationMessage: document.getElementById('notification-message'),
    
    // 分类管理
    addCategoryBtn: document.getElementById('add-category-btn')
};

// 初始化应用
function initApp() {
    // 绑定事件监听器
    bindEventListeners();
    
    // 加载任务和分类数据
    loadAllData();
}

// 绑定事件监听器
function bindEventListeners() {
    // 视图切换
    elements.tasksViewBtn.addEventListener('click', () => switchView('tasks'));
    elements.calendarViewBtn.addEventListener('click', () => switchView('calendar'));
    elements.statsViewBtn.addEventListener('click', () => switchView('stats'));
    
    // 添加日志查看功能（按F12可在控制台查看更详细日志）
    document.addEventListener('keydown', (e) => {
        // 按Shift+L查看日志
        if (e.shiftKey && e.key.toLowerCase() === 'l') {
            e.preventDefault();
            showLogs();
        }
    });
    
    // 任务操作
    elements.createTaskBtn.addEventListener('click', openCreateTaskModal);
    elements.createFirstTaskBtn.addEventListener('click', openCreateTaskModal);
    elements.refreshBtn.addEventListener('click', loadAllData);
    
    // 模态框操作
    elements.closeModalBtn.addEventListener('click', closeTaskModal);
    elements.cancelModalBtn.addEventListener('click', closeTaskModal);
    elements.saveTaskBtn.addEventListener('click', saveTask);
    elements.deleteTaskBtn.addEventListener('click', deleteTask);
    
    // 表单操作
    elements.addProgressBtn.addEventListener('click', addProgressRecord);
    
    // 筛选和排序
    elements.filterList.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            setFilter(item.dataset.filter);
        });
    });
    
    elements.sortSelect.addEventListener('change', renderTasks);
    
    elements.searchBtn.addEventListener('click', () => {
        renderTasks();
    });
    
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            renderTasks();
        }
    });
    
    // 分类管理
    elements.addCategoryBtn.addEventListener('click', createCategory);
}

// 切换视图
function switchView(view) {
    if (currentView === view) return;
    
    // 更新当前视图
    currentView = view;
    
    // 更新视图按钮状态
    elements.tasksViewBtn.classList.toggle('active', view === 'tasks');
    elements.calendarViewBtn.classList.toggle('active', view === 'calendar');
    elements.statsViewBtn.classList.toggle('active', view === 'stats');
    
    // 显示/隐藏视图内容
    elements.tasksView.classList.toggle('active', view === 'tasks');
    elements.calendarView.classList.toggle('active', view === 'calendar');
    elements.statsView.classList.toggle('active', view === 'stats');
    
    // 如果切换到统计视图，更新统计数据
    if (view === 'stats') {
        updateStats();
    }
}

// 设置筛选条件
function setFilter(filter) {
    if (currentFilter === filter) return;
    
    // 更新当前筛选条件
    currentFilter = filter;
    
    // 更新筛选按钮状态
    elements.filterList.forEach(item => {
        item.classList.toggle('active', item.dataset.filter === filter);
    });
    
    // 重新渲染任务列表
    renderTasks();
}

// 设置分类筛选
function setCategoryFilter(categoryId) {
    if (currentCategory === categoryId) return;
    
    // 更新当前分类筛选
    currentCategory = categoryId;
    
    // 更新分类按钮状态
    document.querySelectorAll('.category-item').forEach(item => {
        item.classList.toggle('active', item.dataset.category === categoryId);
    });
    
    // 重新渲染任务列表
    renderTasks();
}

// 加载所有数据
function loadAllData() {
    showLoading();
    
    // 返回Promise以便调用者可以知道数据加载何时完成
    return Promise.all([
        loadTasks(),
        loadCategories()
    ]).then(() => {
        FrontendLogger.log('info', '数据加载完成，开始渲染界面');
        hideLoading();
        renderTasks();
        renderCategories();
        
        if (currentView === 'stats') {
            updateStats();
        }
        return true;
    }).catch(error => {
        FrontendLogger.log('error', '加载数据失败', error);
        hideLoading();
        showNotification('加载数据失败: ' + error.message, 'error');
        throw error;
    });
}

// 前端日志管理器
const FrontendLogger = {
    // 记录日志到控制台和本地存储
    log: function(level, message, error = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message,
            error: error ? {
                message: error.message,
                stack: error.stack
            } : null
        };
        
        // 打印到控制台
        const consoleMethod = level === 'error' ? console.error : 
                             level === 'warn' ? console.warn : console.log;
        consoleMethod(`[${timestamp}] [${level}] ${message}`, error || '');
        
        // 保存到本地存储
        this.saveToLocalStorage(logEntry);
        
        // 如果是错误级别，也尝试保存到文件（通过后端API）
        if (level === 'error') {
            this.sendToServer(logEntry);
        }
    },
    
    // 保存日志到本地存储
    saveToLocalStorage: function(logEntry) {
        try {
            let logs = JSON.parse(localStorage.getItem('frontendLogs') || '[]');
            logs.push(logEntry);
            
            // 限制日志数量，只保留最近的1000条
            if (logs.length > 1000) {
                logs = logs.slice(-1000);
            }
            
            localStorage.setItem('frontendLogs', JSON.stringify(logs));
        } catch (e) {
            console.error('保存日志到本地存储失败:', e);
        }
    },
    
    // 发送日志到服务器（可选功能）
    sendToServer: function(logEntry) {
        try {
            // 异步发送，不阻塞主线程
            axios.post(`${API_BASE_URL}/logs`, {
                type: 'frontend',
                log: logEntry
            }).catch(err => {
                // 发送失败时不抛出错误，避免影响用户体验
                console.error('发送日志到服务器失败:', err);
            });
        } catch (e) {
            console.error('构建日志请求失败:', e);
        }
    },
    
    // 获取所有日志
    getLogs: function() {
        try {
            return JSON.parse(localStorage.getItem('frontendLogs') || '[]');
        } catch (e) {
            console.error('获取日志失败:', e);
            return [];
        }
    },
    
    // 清除所有日志
    clearLogs: function() {
        try {
            localStorage.removeItem('frontendLogs');
        } catch (e) {
            console.error('清除日志失败:', e);
        }
    }
};

// 显示日志的函数
function showLogs() {
    try {
        const logs = FrontendLogger.getLogs();

        // 创建日志视图元素（如果不存在）
        let logsView = document.getElementById('logs-view');
        if (!logsView) {
            logsView = document.createElement('div');
            logsView.id = 'logs-view';
            logsView.className = 'logs-view';
            document.body.appendChild(logsView);

            // 添加关闭按钮 - 修复问题2：确保关闭按钮正常工作
            const closeBtn = document.createElement('button');
            closeBtn.className = 'logs-close-btn';
            closeBtn.innerText = '关闭';
            closeBtn.addEventListener('click', function() {
                logsView.classList.remove('active');
                // 延迟移除DOM元素，以便动画效果完成
                setTimeout(() => {
                    if (logsView.parentNode) {
                        logsView.parentNode.removeChild(logsView);
                    }
                    // 移除样式元素
                    const styleElement = document.querySelector('style[data-log-styles]');
                    if (styleElement && styleElement.parentNode) {
                        styleElement.parentNode.removeChild(styleElement);
                    }
                }, 300);
            });
            logsView.appendChild(closeBtn);
            
            // 添加日志容器
            const logsContainer = document.createElement('div');
            logsContainer.className = 'logs-container';
            logsView.appendChild(logsContainer);
            
            // 添加清除按钮
            const clearBtn = document.createElement('button');
            clearBtn.className = 'logs-clear-btn';
            clearBtn.innerText = '清除日志';
            clearBtn.addEventListener('click', () => {
                if (confirm('确定要清除所有日志吗？')) {
                    FrontendLogger.clearLogs();
                    showLogs(); // 重新显示日志
                }
            });
            logsView.appendChild(clearBtn);
            
            // 添加日志样式
            const style = document.createElement('style');
            style.setAttribute('data-log-styles', 'true'); // 添加标识符以便后续移除
            style.textContent = `
                .logs-view {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.8);
                    display: none;
                    z-index: 1000;
                    overflow: hidden;
                    flex-direction: column;
                }
                .logs-view.active {
                    display: flex;
                }
                .logs-close-btn {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    padding: 8px 16px;
                    background-color: #ff4444;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    z-index: 1001;
                }
                .logs-clear-btn {
                    position: absolute;
                    top: 10px;
                    right: 80px;
                    padding: 8px 16px;
                    background-color: #ffaa00;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    z-index: 1001;
                }
                .logs-container {
                    flex: 1;
                    margin-top: 50px;
                    padding: 20px;
                    overflow-y: auto;
                    background-color: #2d2d2d;
                    color: #ffffff;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                }
                .log-entry {
                    margin-bottom: 10px;
                    padding: 8px;
                    border-left: 3px solid #444;
                }
                .log-entry.error {
                    border-left-color: #ff4444;
                }
                .log-entry.warn {
                    border-left-color: #ffaa00;
                }
                .log-entry.info {
                    border-left-color: #4444ff;
                }
                .log-timestamp {
                    color: #888;
                    font-size: 10px;
                }
                .log-level {
                    font-weight: bold;
                    margin-left: 10px;
                }
                .log-level.error {
                    color: #ff4444;
                }
                .log-level.warn {
                    color: #ffaa00;
                }
                .log-level.info {
                    color: #4444ff;
                }
                .log-message {
                    margin-top: 5px;
                }
                .log-error-details {
                    margin-top: 5px;
                    padding: 5px;
                    background-color: #3d3d3d;
                    font-size: 10px;
                    color: #ffaaaa;
                }
            `;
            document.head.appendChild(style);
        }
        
        // 获取日志容器
        const logsContainer = logsView.querySelector('.logs-container');
        
        // 清空并重新填充日志
        logsContainer.innerHTML = '';
        
        if (logs.length === 0) {
            logsContainer.innerHTML = '<p style="text-align: center; color: #888;">暂无日志记录</p>';
        } else {
            // 逆序显示（最新的在前面）
            logs.reverse().forEach(log => {
                const logElement = document.createElement('div');
                logElement.className = `log-entry ${log.level}`;
                
                const timestamp = new Date(log.timestamp).toLocaleString();
                
                logElement.innerHTML = `
                    <div>
                        <span class="log-timestamp">${timestamp}</span>
                        <span class="log-level ${log.level}">${log.level.toUpperCase()}</span>
                    </div>
                    <div class="log-message">${escapeHTML(log.message)}</div>
                    ${log.error ? `
                    <div class="log-error-details">
                        <div>Error: ${escapeHTML(log.error.message)}</div>
                        ${log.error.stack ? `<div>Stack: ${escapeHTML(log.error.stack).replace(/\n/g, '<br>')}</div>` : ''}
                    </div>
                    ` : ''}
                `;
                
                logsContainer.appendChild(logElement);
            });
        }
        
        // 显示日志视图
        logsView.classList.add('active');
        
    } catch (error) {
        FrontendLogger.log('error', '显示日志失败', error);
        alert('显示日志失败: ' + error.message);
    }
}

// 加载任务数据
function loadTasks() {
    FrontendLogger.log('info', '开始加载任务数据');
    return axios.get(`${API_BASE_URL}/tasks`)
        .then(response => {
            FrontendLogger.log('info', '任务数据加载响应', { response: response.data });
            // 确保tasks总是一个数组
            if (response && response.data && Array.isArray(response.data.tasks)) {
                FrontendLogger.log('info', `成功加载 ${response.data.tasks.length} 个任务`);
                tasks = response.data.tasks;
            } else {
                // 记录警告日志
                FrontendLogger.log('warn', 'API返回的任务数据格式不符合预期', new Error('tasks数据不是数组'));
                // 重置为安全的空数组
                tasks = [];
            }
        })
        .catch(error => {
            FrontendLogger.log('error', '加载任务失败', error);
            // 确保即使出错，tasks仍然是数组
            tasks = [];
            throw error;
        });
}

// 加载分类数据
function loadCategories() {
    return axios.get(`${API_BASE_URL}/categories`)
        .then(response => {
            FrontendLogger.log('info', '加载分类数据响应', { responseData: response.data });
            
            // 确保categories总是一个数组
            if (response && response.data && Array.isArray(response.data.categories)) {
                categories = response.data.categories;
                FrontendLogger.log('info', `成功加载 ${categories.length} 个分类`);
                console.log('当前可用分类:', categories);
            } else {
                // 记录警告日志
                FrontendLogger.log('warn', 'API返回的分类数据格式不符合预期', new Error('categories数据不是数组'));
                // 重置为安全的空数组
                categories = [];
            }
        })
        .catch(error => {
            FrontendLogger.log('error', '加载分类失败', error);
            // 确保即使出错，categories仍然是数组
            categories = [];
            throw error;
        });
}

// 调试函数: 显示所有可用分类
function showAllCategories() {
    console.log('当前可用的任务分类:');
    if (categories.length === 0) {
        console.log('没有找到任何分类');
        showNotification('当前没有可用的任务分类', 'info');
    } else {
        console.log(categories);
        const categoryNames = categories.map(c => c.name).join('、');
        showNotification(`可用的分类: ${categoryNames}`, 'info');
    }
}

// 添加调试按钮到页面
function addDebugButton() {
    if (!document.getElementById('debug-categories-btn')) {
        const debugBtn = document.createElement('button');
        debugBtn.id = 'debug-categories-btn';
        debugBtn.className = 'btn btn-secondary';
        debugBtn.textContent = '查看所有分类';
        debugBtn.style.position = 'fixed';
        debugBtn.style.top = '20px';
        debugBtn.style.right = '20px';
        debugBtn.style.zIndex = '1000';
        debugBtn.addEventListener('click', showAllCategories);
        document.body.appendChild(debugBtn);
    }
}

// 在应用初始化时添加调试按钮
initApp = new Proxy(initApp, {
    apply: function(target, thisArg, args) {
        const result = target.apply(thisArg, args);
        addDebugButton();
        return result;
    }
});

// 渲染任务列表
function renderTasks() {
    FrontendLogger.log('info', '开始渲染任务列表', { taskCount: tasks.length });
    
    // 确保tasksContainer存在
    if (!elements.tasksContainer) {
        FrontendLogger.log('error', '渲染任务失败: tasksContainer元素未找到');
        return;
    }
    
    const filteredTasks = getFilteredAndSortedTasks();
    FrontendLogger.log('info', '渲染筛选后的任务列表', { filteredTaskCount: filteredTasks.length, currentFilter: currentFilter, currentCategory: currentCategory });
    
    // 清空任务容器
    elements.tasksContainer.innerHTML = '';
    
    // 添加一个小延迟以确保DOM完全准备好（解决某些边缘情况下的渲染问题）
    setTimeout(() => {
    
    // 如果没有任务，显示空状态
    if (filteredTasks.length === 0) {
        elements.tasksContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-tasks"></i>
                <p>暂无任务</p>
                <button id="create-first-task-btn" class="btn btn-primary">
                    <i class="fas fa-plus"></i> 创建第一个任务
                </button>
            </div>
        `;
        
        // 绑定创建第一个任务按钮事件 - 首先检查元素是否存在
        const createBtn = document.getElementById('create-first-task-btn');
        if (createBtn) {
            createBtn.addEventListener('click', openCreateTaskModal);
        }
        return;
    }
    
    // 创建任务卡片
    filteredTasks.forEach(task => {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.dataset.id = task.id;
        
        // 获取分类信息
        const category = categories.find(c => c.id === task.category_id) || { name: '无分类', color: '#999999' };
        
        // 设置任务截止日期状态
        let dueDateClass = '';
        if (task.due_date) {
            const dueDate = new Date(task.due_date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (dueDate < today && task.status !== 'completed') {
                dueDateClass = 'overdue';
            } else if (dueDate.getTime() === today.getTime() && task.status !== 'completed') {
                dueDateClass = 'due-soon';
            }
        }
        
        // 创建任务卡片内容
        taskCard.innerHTML = `
            <div class="task-card-header">
                <div>
                    <h3 class="task-title">${escapeHTML(task.title)}</h3>
                    <div class="task-meta">
                        <div class="task-category">
                            <span class="category-color" style="background-color: ${category.color};"></span>
                            ${category.name}
                        </div>
                        <div class="task-priority">
                            <i class="fas ${getPriorityIcon(task.priority)}"></i>
                            ${getPriorityText(task.priority)}
                        </div>
                        <div class="task-due-date ${dueDateClass}">
                            <i class="fas fa-calendar-alt"></i>
                            ${task.due_date ? formatDate(task.due_date) : '无截止日期'}
                        </div>
                    </div>
                </div>
                <div class="task-status ${task.status}">
                    <i class="fas ${getStatusIcon(task.status)}"></i>
                    ${getStatusText(task.status)}
                </div>
            </div>
            ${task.description ? `<p class="task-description">${escapeHTML(task.description)}</p>` : ''}
            ${task.tags && task.tags.length > 0 ? `
                <div class="task-tags">
                    ${task.tags.map(tag => `<span class="task-tag">${escapeHTML(tag)}</span>`).join('')}
                </div>
            ` : ''}
        `;
        
        // 绑定点击事件
        taskCard.addEventListener('click', () => openTaskDetails(task.id));
        
        // 添加到任务容器
        elements.tasksContainer.appendChild(taskCard);
    });
    
    }, 50); // 50ms的小延迟确保DOM准备就绪
}

// 获取筛选和排序后的任务
function getFilteredAndSortedTasks() {
    let filtered = [...tasks];
    
    // 应用状态筛选
    if (currentFilter !== 'all') {
        if (currentFilter === 'todo') {
            filtered = filtered.filter(task => task.status === 'todo');
        } else if (currentFilter === 'in_progress') {
            filtered = filtered.filter(task => task.status === 'in_progress');
        } else if (currentFilter === 'completed') {
            filtered = filtered.filter(task => task.status === 'completed');
        } else if (currentFilter === 'overdue') {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            filtered = filtered.filter(task => 
                task.due_date && new Date(task.due_date) < today && task.status !== 'completed'
            );
        } else if (currentFilter === 'due_soon') {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            filtered = filtered.filter(task => 
                task.due_date && new Date(task.due_date) >= today && new Date(task.due_date) < tomorrow && task.status !== 'completed'
            );
        }
    }
    
    // 应用分类筛选
    if (currentCategory !== 'all') {
        filtered = filtered.filter(task => task.category_id === currentCategory);
    }
    
    // 应用搜索筛选
    const searchTerm = elements.searchInput.value.toLowerCase().trim();
    if (searchTerm) {
        filtered = filtered.filter(task => 
            task.title.toLowerCase().includes(searchTerm) ||
            (task.description && task.description.toLowerCase().includes(searchTerm)) ||
            (task.tags && task.tags.some(tag => tag.toLowerCase().includes(searchTerm)))
        );
    }
    
    // 应用排序
    const sortBy = elements.sortSelect.value;
    switch (sortBy) {
        case 'updated_at_desc':
            filtered.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
            break;
        case 'updated_at_asc':
            filtered.sort((a, b) => new Date(a.updated_at) - new Date(b.updated_at));
            break;
        case 'due_date_asc':
            filtered.sort((a, b) => {
                if (!a.due_date && !b.due_date) return 0;
                if (!a.due_date) return 1;
                if (!b.due_date) return -1;
                return new Date(a.due_date) - new Date(b.due_date);
            });
            break;
        case 'due_date_desc':
            filtered.sort((a, b) => {
                if (!a.due_date && !b.due_date) return 0;
                if (!a.due_date) return -1;
                if (!b.due_date) return 1;
                return new Date(b.due_date) - new Date(a.due_date);
            });
            break;
        case 'priority':
            const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
            filtered.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
            break;
    }
    
    return filtered;
}

// 渲染分类列表
function renderCategories() {
    FrontendLogger.log('info', '渲染分类列表', { categoryCount: categories.length });
    
    // 清空分类列表（保留"全部分类"）
    const allCategoryItem = document.querySelector('.category-item[data-category="all"]');
    elements.categoryList.innerHTML = '';
    if (allCategoryItem) {
        elements.categoryList.appendChild(allCategoryItem);
    }
    
    // 添加分类项
    categories.forEach(category => {
        const li = document.createElement('li');
        li.innerHTML = `
            <a href="#" class="category-item" data-category="${category.id}">
                <span class="category-color" style="background-color: ${category.color};"></span>
                ${escapeHTML(category.name)}
            </a>
        `;
        
        // 绑定点击事件
        li.querySelector('.category-item').addEventListener('click', (e) => {
            e.preventDefault();
            setCategoryFilter(category.id);
        });
        
        elements.categoryList.appendChild(li);
    });
    
    // 确保任务分类下拉框存在
    if (elements.taskCategory) {
        // 更新任务表单中的分类选项
        const options = [`<option value="">无分类</option>`];
        categories.forEach(category => {
            options.push(`<option value="${category.id}">${escapeHTML(category.name)}</option>`);
        });
        elements.taskCategory.innerHTML = options.join('');
        console.log('已更新任务表单中的分类选项，共', categories.length, '个分类');
    }
}

// 打开创建任务模态框
function openCreateTaskModal() {
    currentTaskId = null;
    elements.modalTitle.textContent = '创建新任务';

    // 重置表单
    elements.taskForm.reset();
    elements.progressRecords.innerHTML = '';
    
    // 修复问题3：确保分类选项是最新的
    renderCategories();

    // 显示模态框
    elements.taskModal.classList.add('active');
}

// 打开任务详情模态框
function openTaskDetails(taskId) {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    currentTaskId = taskId;
    elements.modalTitle.textContent = '任务详情';
    
    // 填充表单数据
    elements.taskTitle.value = task.title || '';
    elements.taskCategory.value = task.category_id || '';
    elements.taskPriority.value = task.priority || 'medium';
    elements.taskDueDate.value = task.due_date ? formatDateForInput(task.due_date) : '';
    elements.taskStatus.value = task.status || 'todo';
    elements.taskDescription.value = task.description || '';
    elements.taskTags.value = task.tags ? task.tags.join(', ') : '';
    
    // 渲染进展记录
    elements.progressRecords.innerHTML = '';
    if (task.progress_records && task.progress_records.length > 0) {
        task.progress_records.forEach(record => {
            addProgressRecordToDOM(record.text, record.created_at);
        });
    }
    
    // 显示模态框
    elements.taskModal.classList.add('active');
}

// 关闭任务模态框
function closeTaskModal() {
    elements.taskModal.classList.remove('active');
    currentTaskId = null;
}

// 保存任务
function saveTask() {
    // 验证表单
    if (!elements.taskTitle.value.trim()) {
        showNotification('请输入任务标题', 'warning');
        return;
    }

    // 获取选中的分类ID
    const selectedCategoryId = elements.taskCategory.value || null;
    const selectedCategory = selectedCategoryId ? categories.find(c => c.id === selectedCategoryId) : null;
    
    FrontendLogger.log('info', '保存任务，选择的分类', { 
        categoryId: selectedCategoryId, 
        categoryName: selectedCategory ? selectedCategory.name : '无分类'
    });

    // 收集表单数据
    const taskData = {
        title: elements.taskTitle.value.trim(),
        category_id: selectedCategoryId,
        category: selectedCategoryId, // 兼容后端期望的category参数
        priority: elements.taskPriority.value,
        due_date: elements.taskDueDate.value || null,
        status: elements.taskStatus.value,
        description: elements.taskDescription.value.trim() || null,
        tags: elements.taskTags.value.trim() ? 
            elements.taskTags.value.split(',').map(tag => tag.trim()).filter(tag => tag) : 
            []
    };

    // 收集进展记录
    const progressRecords = [];
    document.querySelectorAll('.progress-record').forEach(record => {
        const text = record.querySelector('.progress-record-text').textContent;
        const createdAt = record.dataset.createdAt;
        progressRecords.push({ text, created_at: createdAt });
    });
    taskData.progress_records = progressRecords;

    showLoading();

    // 记录保存任务的日志
    FrontendLogger.log('info', '开始保存任务', { taskId: currentTaskId, taskTitle: taskData.title });

    // 发送API请求
    const promise = currentTaskId 
        ? axios.put(`${API_BASE_URL}/tasks/${currentTaskId}`, taskData)
        : axios.post(`${API_BASE_URL}/tasks`, taskData);

    promise.then(response => {
        FrontendLogger.log('info', currentTaskId ? '任务更新成功' : '任务创建成功', { responseData: response.data });
        hideLoading();
        closeTaskModal();
        
        // 确保在数据完全加载后再执行后续操作
            loadAllData().then(() => {
                FrontendLogger.log('info', '数据加载完成，任务列表应该已更新');
                
                // 额外的保障措施：即使数据加载完成，也再次尝试渲染任务列表
                setTimeout(() => {
                    if (currentView === 'tasks') {
                        FrontendLogger.log('info', '执行额外的任务列表渲染保障');
                        renderTasks();
                    }
                }, 200); // 增加延迟时间到200ms以确保DOM完全更新
                
                showNotification(currentTaskId ? '任务更新成功' : '任务创建成功', 'success');
            }).catch(loadError => {
                FrontendLogger.log('error', '加载数据失败，但任务已保存成功', loadError);
                // 即使数据加载失败，也尝试直接渲染任务列表
                setTimeout(() => {
                    if (currentView === 'tasks') {
                        FrontendLogger.log('info', '尝试直接渲染任务列表作为最后的保障');
                        renderTasks();
                    }
                }, 200); // 增加延迟时间到200ms以确保DOM完全更新
                showNotification(currentTaskId ? '任务更新成功，但刷新列表失败' : '任务创建成功，但刷新列表失败', 'warning');
            });
    }).catch(error => {
        FrontendLogger.log('error', '保存任务失败', error);
        hideLoading();
        // 提供更详细的错误信息
        let errorMessage = '保存任务失败';
        if (error.response?.status === 409) {
            errorMessage = '分类已存在，请选择其他分类名称';
        } else if (error.response?.data?.message) {
            errorMessage = '保存任务失败: ' + error.response.data.message;
        } else {
            errorMessage = '保存任务失败: ' + error.message;
        }
        showNotification(errorMessage, 'error');
    });
}

// 删除任务
function deleteTask() {
    if (!currentTaskId) return;
    
    if (confirm('确定要删除这个任务吗？')) {
        showLoading();
        
        axios.delete(`${API_BASE_URL}/tasks/${currentTaskId}`)
            .then(() => {
                hideLoading();
                closeTaskModal();
                loadAllData();
                showNotification('任务删除成功', 'success');
            })
            .catch(error => {
                hideLoading();
                showNotification('删除任务失败: ' + error.message, 'error');
            });
    }
}

// 创建分类
function createCategory() {
    const categoryName = prompt('请输入分类名称:');
    if (!categoryName || !categoryName.trim()) return;

    const trimmedName = categoryName.trim();
    FrontendLogger.log('info', '尝试创建新分类', { categoryName: trimmedName });

    // 随机生成颜色
    const color = getRandomColor();

    showLoading();

    axios.post(`${API_BASE_URL}/categories`, {
        name: trimmedName,
        color: color
    }).then(response => {
        FrontendLogger.log('info', '分类创建成功，服务器响应', { responseData: response.data });
        hideLoading();
        // 确保在创建分类后重新加载所有数据
        loadAllData().then(() => {
            // 额外确保分类列表和任务表单分类选项更新
            renderCategories();
            renderTasks();
            showNotification(`分类"${trimmedName}"创建成功`, 'success');
        });
    }).catch(error => {
        FrontendLogger.log('error', '创建分类失败', error);
        hideLoading();
        // 提供更详细的错误信息
        let errorMessage = '创建分类失败';
        if (error.response?.status === 409) {
            errorMessage = '分类已存在，请选择其他分类名称';
        } else if (error.response?.data?.message) {
            errorMessage = '创建分类失败: ' + error.response.data.message;
        } else {
            errorMessage = '创建分类失败: ' + error.message;
        }
        showNotification(errorMessage, 'error');
    });
}

// 添加进展记录
function addProgressRecord() {
    const text = elements.newProgress.value.trim();
    if (!text) return;
    
    addProgressRecordToDOM(text, new Date().toISOString());
    elements.newProgress.value = '';
}

// 将进展记录添加到DOM
function addProgressRecordToDOM(text, createdAt) {
    const recordElement = document.createElement('div');
    recordElement.className = 'progress-record';
    recordElement.dataset.createdAt = createdAt;
    
    recordElement.innerHTML = `
        <div class="progress-record-icon">
            <i class="fas fa-comment-alt"></i>
        </div>
        <div class="progress-record-content">
            <p class="progress-record-text">${escapeHTML(text)}</p>
            <p class="progress-record-time">${formatDateTime(createdAt)}</p>
        </div>
    `;
    
    elements.progressRecords.appendChild(recordElement);
}

// 更新统计信息
function updateStats() {
    const total = tasks.length;
    const todo = tasks.filter(task => task.status === 'todo').length;
    const inProgress = tasks.filter(task => task.status === 'in_progress').length;
    const completed = tasks.filter(task => task.status === 'completed').length;
    
    elements.totalTasks.textContent = total;
    elements.todoTasks.textContent = todo;
    elements.inProgressTasks.textContent = inProgress;
    elements.completedTasks.textContent = completed;
    
    // 这里可以添加图表绘制逻辑
}

// 显示加载指示器
function showLoading() {
    elements.loadingIndicator.classList.add('active');
}

// 隐藏加载指示器
function hideLoading() {
    elements.loadingIndicator.classList.remove('active');
}

// 显示通知
function showNotification(message, type = 'info') {
    elements.notificationMessage.textContent = message;
    elements.notification.className = 'notification';
    elements.notification.classList.add('active');
    elements.notification.classList.add(type);
    
    // 设置通知图标
    elements.notificationIcon.className = 'fas';
    if (type === 'success') {
        elements.notificationIcon.classList.add('fa-check-circle');
    } else if (type === 'error') {
        elements.notificationIcon.classList.add('fa-exclamation-circle');
    } else if (type === 'warning') {
        elements.notificationIcon.classList.add('fa-exclamation-triangle');
    } else {
        elements.notificationIcon.classList.add('fa-info-circle');
    }
    
    // 3秒后自动隐藏
    setTimeout(() => {
        elements.notification.classList.remove('active');
    }, 3000);
}

// 辅助函数: 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 辅助函数: 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 辅助函数: 格式化日期用于输入框
function formatDateForInput(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 辅助函数: 获取优先级图标
function getPriorityIcon(priority) {
    switch (priority) {
        case 'high': return 'fa-flag text-danger';
        case 'medium': return 'fa-flag text-warning';
        case 'low': return 'fa-flag text-secondary';
        default: return 'fa-flag text-secondary';
    }
}

// 辅助函数: 获取优先级文本
function getPriorityText(priority) {
    switch (priority) {
        case 'high': return '高';
        case 'medium': return '中';
        case 'low': return '低';
        default: return '中';
    }
}

// 辅助函数: 获取状态图标
function getStatusIcon(status) {
    switch (status) {
        case 'todo': return 'fa-circle';
        case 'in_progress': return 'fa-spinner fa-spin';
        case 'completed': return 'fa-check-circle';
        default: return 'fa-circle';
    }
}

// 辅助函数: 获取状态文本
function getStatusText(status) {
    switch (status) {
        case 'todo': return '待办';
        case 'in_progress': return '进行中';
        case 'completed': return '已完成';
        default: return '待办';
    }
}

// 辅助函数: 生成随机颜色
function getRandomColor() {
    const colors = [
        '#4CAF50', '#2196F3', '#F44336', '#FF9800', '#9C27B0',
        '#3F51B5', '#00BCD4', '#FFEB3B', '#795548', '#607D8B'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

// 辅助函数: HTML转义
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 应用初始化
initApp();