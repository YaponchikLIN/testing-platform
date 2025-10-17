const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const isDev = process.argv.includes('--dev');

let mainWindow;

function createWindow() {
  // Создаем окно браузера
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, '../public/favicon.ico'),
    show: false
  });

  // Загружаем приложение
  if (isDev) {
    // В режиме разработки подключаемся к dev серверу
    mainWindow.loadURL('http://localhost:8081');
    // Открываем DevTools
    mainWindow.webContents.openDevTools();
  } else {
    // В продакшене загружаем собранные файлы
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // Показываем окно когда оно готово
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Обработчик закрытия окна
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Этот метод будет вызван когда Electron завершит инициализацию
app.whenReady().then(createWindow);

// Выходим когда все окна закрыты
app.on('window-all-closed', () => {
  // На macOS приложения обычно остаются активными пока пользователь не выйдет явно
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // На macOS обычно пересоздают окно когда кликают на иконку в доке
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Убираем меню в продакшене
if (!isDev) {
  Menu.setApplicationMenu(null);
}