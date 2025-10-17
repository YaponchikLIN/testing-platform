const { contextBridge, ipcRenderer } = require('electron');

// Предоставляем безопасный API для рендер процесса
contextBridge.exposeInMainWorld('electronAPI', {
  // Методы для работы с приложением
  getVersion: () => process.versions.electron,
  getPlatform: () => process.platform,
  
  // Методы для работы с файлами (если понадобятся)
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, data) => ipcRenderer.invoke('write-file', filePath, data),
  
  // Методы для работы с окном
  minimize: () => ipcRenderer.invoke('window-minimize'),
  maximize: () => ipcRenderer.invoke('window-maximize'),
  close: () => ipcRenderer.invoke('window-close'),
  
  // Методы для уведомлений
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', title, body)
});

// Логирование для отладки
console.log('Preload script loaded successfully');