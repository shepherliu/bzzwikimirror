<template>
  <el-row>
    <!-- project logo -->
    <el-col :span="2">
      <div style="float: right;">
        <el-image style="width: 35px;height: 33px; float: right;margin-right: 10px;margin-top: 10px;" :src="logo"/>
      </div>        
    </el-col> 

    <!-- project menus -->
    <el-col :span="10">
      <el-menu
        :default-active="activeIndex"
        class="el-menu-demo"
        mode="horizontal"
        :ellipsis="false"
        :unique-opened="true"
        background-color="#606266"
        style="float: left;width: 100%;"
        text-color="#fff"
        active-text-color="#ffd04b"
        @select="handleSelect"
      >
        <el-menu-item index="1">Wiki</el-menu-item>
        <el-menu-item index="2">Status</el-menu-item>
      </el-menu>
    </el-col>
  </el-row>  
</template>

<script lang="ts">  
export default {
  name: 'NavBar',
  props: {
  },
}
</script>

<script setup lang="ts">

import * as tools from "../libs/tools"
import { connectState } from "../libs/connect"

const logo = require('@/assets/logo.png');
const activeIndex = connectState.activeIndex;
//on menus selected
const handleSelect = (key: string, keyPath: string[]) => {
  activeIndex.value = key;

  tools.setUrlParamter('activeIndex', activeIndex.value);
};    

//login to wallet and switch to the target chain.
const login = async () => {
  connectState.searchCallback();
};

//try get activeIndex from the url paramter
try{
  activeIndex.value = String(tools.getUrlParamter('activeIndex'));
  if(activeIndex.value != '1' && 
    activeIndex.value != '2'){
    activeIndex.value = '1';
  }
}catch(e){
  activeIndex.value = '1';
}

//set activeIndex to connectState and location.href
connectState.activeIndex.value = activeIndex.value;
tools.setUrlParamter('activeIndex', activeIndex.value);

//try connect to metamask
login();
</script>
