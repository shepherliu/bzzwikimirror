<template>
  <div class="file-arae">
    <el-container>
      <el-header style="background-color: #ffffff;">
        <el-tabs v-model="activeName" class="file-tabs" @tab-click="handleClick">
          <el-tab-pane label="Status" name="status"></el-tab-pane>
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
        <el-row>
          <table>
            <thead>
              <th width="350px">Name</th>
              <th width="150px">Size</th>
              <th width="150px">Status</th>
              <th width="150px">Timestamp</th>
            </thead>
            <tbody>
              <template v-for="item in tokenList" :key="item.name">
                <tr>
                  <td>
                    <el-link :href="zimExplorerUrl(item.name)" type="primary" target="_blank">{{item.name}}</el-link>
                  </td>
                  <td>{{item.size}}</td>
                  <td>{{item.status}}</td>
                  <td>{{item.timestamp}}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </el-row>
      </el-main>
      <el-footer>
        <div>
          <el-pagination
            background
            layout="total, prev, pager, next"
            v-model:currentPage="currentPage"
            :total="tokenTotal"
            :page-size="pageSize"
            style="float: right;"
             @current-change="handleClick"
          />
      </div>
      </el-footer>
    </el-container>
  </div> 

</template>

<script lang="ts">
export default {
  name: 'ZimPage',
  props: {
  }
}
</script>

<script setup lang="ts">
import { ref } from "vue"

import * as bzzwikimirror from "../libs/bzzwikimirror"
import * as tools from "../libs/tools"
import * as constant from "../constant"

import { connectState } from "../libs/connect"

const activeName = connectState.activeName;
const loadStatus = ref(false);
const pageSize = ref(10);
const currentPage = ref(0);
const tokenTotal = ref(0);
const tokenList = ref(new Array());

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

//address explore url
const zimExplorerUrl = (zimname:string) => {
  return `${constant.WIKIPEDIA_HOST}/${zimname}`
}

//get total tokens count and pull tokens info
const getTokenCount = async () => {

  const res = await bzzwikimirror.getZimList();

  tokenList.value = res;

  tokenTotal.value = tokenList.value.length;
}

//click to change active item and refresh page
const handleClick = async () => {

  connectState.activeName.value = activeName.value;
  tools.setUrlParamter('activeName', activeName.value);

  try{

    loadStatus.value = true;

    await getTokenCount();
  
    if(currentPage.value < 1){
      currentPage.value = 1;
    }

    let totalPage = Math.floor(tokenTotal.value/pageSize.value);

    if((tokenTotal.value%pageSize.value)!=0){
      totalPage += 1;
    }

    if(currentPage.value > totalPage){
      currentPage.value = totalPage;
    }

    let start = (currentPage.value-1) * pageSize.value;
    let end = currentPage.value * pageSize.value;

    if(start < 0){
      start = 0;
    }

    if(end > tokenTotal.value){
      end = tokenTotal.value;
    }

    tokenList.value = tokenList.value.slice(start, end);

    for (const i in tokenList.value){
      tokenList.value[i].status = await bzzwikimirror.getZimStatus(tokenList.value[i].name);
    }

  }catch(e){
     tokenList.value = new Array();
  }finally{
    loadStatus.value = false;
  }

}

//try get activeName from the url paramter
try{
  activeName.value = tools.getUrlParamter('activeName');

  if(activeName.value != 'status'){

    activeName.value = 'status';
  }
}catch(e){
  activeName.value = 'status';
}

//update page
handleClick();
</script>