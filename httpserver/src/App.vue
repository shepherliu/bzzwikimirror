<template>
  <el-container>
    <el-header><NavBar /></el-header>
    <el-container>
      <el-main><HomePage /></el-main>   
    </el-container>
    <el-footer>
      <FootPage />
    </el-footer>
  </el-container>  
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';

import NavBar from './components/NavBar.vue';
import HomePage from './pages/HomePage.vue';
import FootPage from './pages/FootPage.vue';

@Options({
  components: {
    NavBar,
    HomePage,
    FootPage,
  },
})
export default class App extends Vue {}
</script>