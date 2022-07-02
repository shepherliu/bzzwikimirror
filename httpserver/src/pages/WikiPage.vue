<template>
  <div class="file-arae">
    <el-container>
      <el-header style="background-color: #ffffff;">
        <el-tabs v-model="activeName" class="file-tabs" @tab-click="handleClick">
          <el-tab-pane label="Wiki" name="wiki"></el-tab-pane>
        </el-tabs>
      </el-header>
      <el-main
        style="height: 450px;" 
        v-loading="loadStatus"
        element-loading-text="Loading..."
        :element-loading-spinner="svg"
        element-loading-svg-view-box="-10, -10, 50, 50"
        element-loading-background="#ffffff"
      >
        <el-row :gutter="20">
          <el-col :span="8">
            <el-input size="large" v-model="titleSearch" placeholder="" style="margin-top: 10px;">
              <template #prepend>Title</template>
            </el-input>
          </el-col>          
          <el-col :span="8">
            <el-input size="large" v-model="contentSearch" placeholder="" style="margin-top: 10px;">
              <template #prepend>Content</template>
            </el-input>
          </el-col>                                                             
          <el-col :span="1">
            <el-button circle type="primary" size="large" style="margin-top: 10px;" @click="handleClick">
              <el-icon :size="20"><search /></el-icon>
            </el-button>
          </el-col>            
        </el-row>  
        <el-row :gutter="40">
          <template v-for="item in tokenList" :key="item.link">
            <el-link :href="item.link" type="primary" target="_blank">{{item.name}}</el-link>
          </template>
        </el-row>
      </el-main>
      <el-footer>
        <div>
          <el-button type="primary" style="margin-top: 10px;" @click="onHandlePrev">Prev
          </el-button>
          <el-button type="primary" style="margin-top: 10px;" @click="onHandleNext" :disabled="hasMore">Next
          </el-button>          
      </div>
      </el-footer>
    </el-container>
  </div> 

</template>

<script lang="ts">
export default {
  name: 'WikiPage',
  props: {
  }
}
</script>

<script setup lang="ts">
import { ref } from "vue"

import * as bzzwikimirror from "../libs/bzzwikimirror"
import { connectState } from "../libs/connect"
import * as tools from "../libs/tools"

const titleSearch = ref('');
const contentSearch = ref('');

const activeName = connectState.activeName;
const loadStatus = ref(false);
const pageSize = ref(100);
const currentPage = ref(0);
const tokenList = ref(new Array());
const hasMore = ref(false);

const svg = `
        <path class="path" d="
          M 30 15
          L 28 17
          M 25.61 25.61
          A 15 15, 0, 0, 1, 15 30
          A 15 15, 0, 1, 1, 27.99 7.5
          L 15 15
        " style="stroke-width: 4px; fill: rgba(0, 0, 0, 0)"/>
      `;

//get total tokens count and pull tokens info
const getTokenCount = async () => {
  
  let res = [];

  if (contentSearch.value != ''){
    res = await bzzwikimirror.getContentSearch(contentSearch.value, pageSize.value, currentPage.value);
  }else if(titleSearch.value != ''){
    res = await bzzwikimirror.getFileSearch(titleSearch.value, pageSize.value, currentPage.value);
  }else{
    res = await bzzwikimirror.getFileList(pageSize.value, currentPage.value);
  }

  if (res.length < pageSize.value){
    hasMore.value = false;
  }else{
    hasMore.value = true;
  }

  const newTokenList = new Array();

  for(const i in res){
    newTokenList.push(res[i]);
  }

  tokenList.value = newTokenList;
}

//on click for prev page
const onHandlePrev = async () => {
  if(currentPage.value > 0){
    currentPage.value--;
  }

  handleClick();
}

//on click for next page
const onHandleNext = async () => {
  if(hasMore.value){
    currentPage.value++;
  }
  handleClick();
}

//click to change active item and refresh page
const handleClick = async () => {

  connectState.activeName.value = activeName.value;
  tools.setUrlParamter('activeName', activeName.value);

  try{

    loadStatus.value = true;

    await getTokenCount();

  }catch(e){
     tokenList.value = new Array();
  }finally{
    loadStatus.value = false;
  }

}

connectState.searchCallback = handleClick;

//try get activeName from the url paramter
try{
  activeName.value = tools.getUrlParamter('activeName');

  if(activeName.value != 'wiki'){

    activeName.value = 'wiki';
  }
}catch(e){
  activeName.value = 'wiki';
}

//update page
handleClick();
</script>