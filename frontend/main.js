const { app, BrowserWindow, ipcMain, Menu, Tray, nativeImage } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { spawn } = require('child_process');
let pythonProcess = null;

// 保持对window对象的全局引用，防止JavaScript对象被垃圾回收时窗口被关闭
let mainWindow;
let tray = null;

// 创建浏览器窗口
function createWindow() {
    // 创建主窗口
    mainWindow = new BrowserWindow({
        width: 1024,
        height: 768,
        minWidth: 800,
        minHeight: 600,
        title: 'DailyEnchant - 工作计划记录',
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, 'assets', 'icon.png')
    });

    // 加载应用的index.html
    const startUrl = isDev 
        ? 'file://' + path.join(__dirname, 'index.html') 
        : `file://${path.join(__dirname, 'index.html')}`;
    
    mainWindow.loadURL(startUrl);

    // 在开发模式下打开开发者工具
    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    // 当窗口关闭时触发
    mainWindow.on('closed', function () {
        // 取消引用window对象，如果应用支持多窗口，则通常会将窗口存储在数组中
        mainWindow = null;
    });

    // 创建应用菜单
    createMenu();

    // 创建系统托盘图标
    createTray();
}

// 创建应用菜单
function createMenu() {
    const template = [
        {
            label: '文件',
            submenu: [
                {
                    label: '新建任务',
                    accelerator: 'CmdOrCtrl+N',
                    click: () => {
                        mainWindow.webContents.send('create-new-task');
                    }
                },
                {
                    label: '导入任务',
                    click: () => {
                        mainWindow.webContents.send('import-tasks');
                    }
                },
                {
                    label: '导出任务',
                    click: () => {
                        mainWindow.webContents.send('export-tasks');
                    }
                },
                { type: 'separator' },
                {
                    label: '退出',
                    accelerator: 'CmdOrCtrl+Q',
                    click: () => {
                        app.quit();
                    }
                }
            ]
        },
        {
            label: '编辑',
            submenu: [
                {
                    label: '撤销',
                    accelerator: 'CmdOrCtrl+Z',
                    role: 'undo'
                },
                {
                    label: '重做',
                    accelerator: 'CmdOrCtrl+Y',
                    role: 'redo'
                },
                { type: 'separator' },
                {
                    label: '剪切',
                    accelerator: 'CmdOrCtrl+X',
                    role: 'cut'
                },
                {
                    label: '复制',
                    accelerator: 'CmdOrCtrl+C',
                    role: 'copy'
                },
                {
                    label: '粘贴',
                    accelerator: 'CmdOrCtrl+V',
                    role: 'paste'
                },
                {
                    label: '全选',
                    accelerator: 'CmdOrCtrl+A',
                    role: 'selectall'
                }
            ]
        },
        {
            label: '查看',
            submenu: [
                {
                    label: '切换到任务视图',
                    click: () => {
                        mainWindow.webContents.send('switch-to-task-view');
                    }
                },
                {
                    label: '切换到日历视图',
                    click: () => {
                        mainWindow.webContents.send('switch-to-calendar-view');
                    }
                },
                {
                    label: '切换到统计视图',
                    click: () => {
                        mainWindow.webContents.send('switch-to-stats-view');
                    }
                },
                { type: 'separator' },
                {
                    label: '刷新',
                    accelerator: 'CmdOrCtrl+R',
                    click: () => {
                        mainWindow.webContents.reload();
                    }
                },
                {
                    label: '开发者工具',
                    accelerator: 'CmdOrCtrl+Shift+I',
                    click: () => {
                        mainWindow.webContents.toggleDevTools();
                    }
                }
            ]
        },
        {
            label: '帮助',
            submenu: [
                {
                    label: '关于',
                    click: () => {
                        mainWindow.webContents.send('show-about');
                    }
                },
                {
                    label: '使用指南',
                    click: () => {
                        mainWindow.webContents.send('show-help');
                    }
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

// 创建系统托盘
function createTray() {
    // 尝试创建托盘图标
    try {
        // 在开发环境中，如果没有图标，使用占位符
        let trayIcon;
        try {
            trayIcon = nativeImage.createFromPath(path.join(__dirname, 'assets', 'tray-icon.png'));
        } catch (error) {
            // 如果图标文件不存在，创建一个简单的文本图标
            trayIcon = nativeImage.createEmpty();
        }

        tray = new Tray(trayIcon);
        const contextMenu = Menu.buildFromTemplate([
            {
                label: '显示窗口',
                click: () => {
                    if (mainWindow) {
                        if (mainWindow.isMinimized()) mainWindow.restore();
                        mainWindow.focus();
                    } else {
                        createWindow();
                    }
                }
            },
            {
                label: '新建任务',
                click: () => {
                    if (mainWindow) {
                        mainWindow.webContents.send('create-new-task');
                    }
                }
            },
            {
                label: '退出',
                click: () => {
                    app.quit();
                }
            }
        ]);

        tray.setToolTip('DailyEnchant - 工作计划记录');
        tray.setContextMenu(contextMenu);

        // 点击托盘图标显示/隐藏窗口
        tray.on('click', () => {
            if (mainWindow) {
                if (mainWindow.isVisible()) {
                    mainWindow.hide();
                } else {
                    mainWindow.show();
                }
            }
        });
    } catch (error) {
        console.error('创建托盘图标失败:', error);
        // 如果创建托盘失败，继续执行应用，不影响核心功能
    }
}

// 启动Python后端服务
function startPythonBackend() {
    const backendPath = path.join(__dirname, '..', 'backend', 'main.py');
    
    // 检测操作系统类型，选择合适的Python命令
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
    
    // 启动Python进程
    pythonProcess = spawn(pythonCommand, [backendPath]);
    
    // 捕获Python输出
    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python后端输出: ${data}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python后端错误: ${data}`);
    });
    
    pythonProcess.on('close', (code) => {
        console.log(`Python后端进程退出，退出码: ${code}`);
        pythonProcess = null;
    });
}

// 当Electron完成初始化并准备创建浏览器窗口时触发
app.on('ready', () => {
    // 启动Python后端服务
    startPythonBackend();
    
    // 创建主窗口
    createWindow();
});

// 当所有窗口关闭时触发
app.on('window-all-closed', function () {
    // 在macOS上，应用程序及其菜单栏通常保持活动状态，直到用户使用Cmd+Q明确退出
    if (process.platform !== 'darwin') {
        // 关闭Python后端进程
        if (pythonProcess) {
            pythonProcess.kill();
        }
        app.quit();
    }
});

// 当应用程序被激活时触发（通常在macOS上点击Dock图标时）
app.on('activate', function () {
    // 如果没有打开的窗口，则创建一个新窗口
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// 监听IPC消息
ipcMain.on('minimize-window', () => {
    if (mainWindow) {
        mainWindow.minimize();
    }
});

ipcMain.on('maximize-window', () => {
    if (mainWindow) {
        if (mainWindow.isMaximized()) {
            mainWindow.unmaximize();
        } else {
            mainWindow.maximize();
        }
    }
});

ipcMain.on('close-window', () => {
    if (mainWindow) {
        mainWindow.close();
    }
});

// 监听应用退出事件，确保正确关闭Python后端
app.on('before-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});

// 捕获未处理的异常
process.on('uncaughtException', (error) => {
    console.error('未捕获的异常:', error);
    // 可以在这里添加错误报告或恢复逻辑
});

// 开发模式下启用热重载（如果安装了electron-reloader）
if (isDev) {
    try {
        require('electron-reloader')(module);
    } catch (error) {
        console.error('Electron热重载加载失败:', error);
    }
}