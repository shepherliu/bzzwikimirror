import { createApp } from 'vue'

import App from './App.vue'

//import element plus ui 
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

//import vuex
import Vuex from 'vuex'

//import icons
import * as ElIcons from '@element-plus/icons-vue'

//import css style
import './styles/base.css'

const app = createApp(App)
for (const name in ElIcons){
	app.component(name, (ElIcons as any)[name])
}

app.use(ElementPlus).mount('#app')