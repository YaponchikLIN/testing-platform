import { defineStore } from 'pinia';

const useConfigStore = defineStore('config', {
    state: () => ({
        theme: 'light',
        devicePaths: {},
        lastUsedOrderId: null,
        lastUsedDeviceType: null
    }),

    actions: {
        toggleTheme() {
            this.theme = this.theme === 'light' ? 'dark' : 'light';
            this.saveSettings();
        },

        loadSettings() {
            try {
                // Проверяем доступность NW.js API
                if (typeof window.nw === 'undefined' || typeof window.nw.require !== 'function') {
                    console.warn('NW.js API недоступен. Используются настройки по умолчанию.');
                    return;
                }

                const nwStore = window.nw.require('nw.gui').App.data;
                if (nwStore && nwStore.settings) {
                    const { theme, devicePaths, lastUsedOrderId, lastUsedDeviceType } = nwStore.settings;
                    if (theme) this.theme = theme;
                    if (devicePaths) this.devicePaths = devicePaths;
                    if (lastUsedOrderId) this.lastUsedOrderId = lastUsedOrderId;
                    if (lastUsedDeviceType) this.lastUsedDeviceType = lastUsedDeviceType;
                }
            } catch (error) {
                console.error('Ошибка при загрузке настроек:', error);
                // При ошибке используем настройки по умолчанию
            }
        },

        saveSettings() {
            try {
                // Проверяем доступность NW.js API
                if (typeof window.nw === 'undefined') {
                    console.warn('NW.js API недоступен. Настройки не сохранены.');
                    return;
                }

                const settings = {
                    theme: this.theme,
                    devicePaths: this.devicePaths,
                    lastUsedOrderId: this.lastUsedOrderId,
                    lastUsedDeviceType: this.lastUsedDeviceType
                };
                window.nw.require('nw.gui').App.data.settings = settings;
            } catch (error) {
                console.error('Ошибка при сохранении настроек:', error);
            }
        },

        setDevicePath(deviceType, path) {
            this.devicePaths[deviceType] = path;
            this.saveSettings();
        },

        setLastUsedOrder(orderId) {
            this.lastUsedOrderId = orderId;
            this.saveSettings();
        },

        setLastUsedDevice(deviceType) {
            this.lastUsedDeviceType = deviceType;
            this.saveSettings();
        }
    }
});

export { useConfigStore };