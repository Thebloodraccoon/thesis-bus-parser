import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import BlockViewer from '@/components/BlockViewer.vue'
import Aura from '@primevue/themes/aura'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'

import '@/assets/styles.scss'
import '@/assets/tailwind.css'

// 👇 кастомная локаль для календаря
const ruLocale = {
  firstDayOfWeek: 1,
  dayNames: ['Воскресенье','Понедельник','Вторник','Среда','Четверг','Пятница','Суббота'],
  dayNamesShort: ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'],
  dayNamesMin: ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'],
  monthNames: ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'],
  monthNamesShort: ['Янв','Фев','Мар','Апр','Май','Июн','Июл','Авг','Сен','Окт','Ноя','Дек'],
  today: 'Сегодня',
  clear: 'Очистить'
}

const app = createApp(App)

app.use(router)
app.use(PrimeVue, {
  locale: ruLocale, // 👈 добавляем локаль здесь
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: '.app-dark'
    }
  }
})
app.use(ToastService)
app.use(ConfirmationService)

app.directive('tooltip', Tooltip)

app.component('BlockViewer', BlockViewer)

app.mount('#app')
