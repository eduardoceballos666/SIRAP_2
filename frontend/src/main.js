import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

import { useSessionStore } from './stores/session'

const app = createApp(App).use(createPinia()).use(router)
useSessionStore().applyTheme() // tema claro/oscuro antes del primer pintado
app.mount('#app')
