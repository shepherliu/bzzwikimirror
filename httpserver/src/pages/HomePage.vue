<template>
  <WikiPage v-if="activeIndex==='1'" />
  <ZimPage v-if="activeIndex==='2'"/>
</template>

<script lang="ts">
import WikiPage from './WikiPage.vue';
import ZimPage from './ZimPage.vue';

export default {
  name: 'HomePage',
  props: {
    msg: String
  }
}
</script>

<script setup lang="ts">
import { connectState } from "../libs/connect"

const activeIndex = connectState.activeIndex;
</script>