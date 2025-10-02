import { createApp } from 'vue'
import App from './App.vue'
import PrimeVue from 'primevue/config'
import 'primeicons/primeicons.css'
// Стили удалены
import { createPinia } from 'pinia'
import { useConfigStore } from './stores/config.store'
import ToastService from 'primevue/toastservice';
import Select from 'primevue/select'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Lara from '@primeuix/themes/lara'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import Dialog from 'primevue/dialog';
import Toast from 'primevue/toast';
import DatePicker from 'primevue/datepicker';
import { ProgressBar } from 'primevue'

const app = createApp(App)

app.use(createPinia())
    .use(PrimeVue, {
        theme: {
            preset: Lara
        }
    })
    .use(ToastService)
    .component('Toast', Toast)
    .component('Select', Select)
    .component('Card', Card)
    .component('InputText', InputText)
    .component('Button', Button)
    .component('DataTable', DataTable)
    .component('Column', Column)
    .component('Tag', Tag)
    .component('Message', Message)
    .component('Dialog', Dialog)
    .component('DatePicker', DatePicker)
    .component('ProgressBar', ProgressBar)

// Безопасная проверка NW.js
if (typeof window.nw !== 'undefined' || typeof nw !== 'undefined') {
    const nwObj = window.nw || nw
    try {
        nwObj.Window.get().showDevTools()
    } catch (error) {
        console.error('Ошибка при открытии DevTools:', error)
    }
} else {
    console.warn('NW.js API недоступен')
}

// Автозагрузка настроек
const configStore = useConfigStore()
try {
    configStore.loadSettings()
} catch (error) {
    console.error('Ошибка при загрузке настроек:', error)
}

app.mount('#app')