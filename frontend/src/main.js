import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import { installI18n } from './i18n'

import { useSessionStore } from './stores/session'

const app = createApp(App).use(createPinia()).use(router)
installI18n(app)
useSessionStore().applyTheme() // tema claro/oscuro antes del primer pintado
app.mount('#app')
