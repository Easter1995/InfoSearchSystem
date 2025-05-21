<script setup lang="ts">
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const locale = zhCn

</script>

<template>
  <el-config-provider :locale="locale">
    <router-view />
  </el-config-provider>
</template>

<style lang="scss" scoped>
html,
body {
    overscroll-behavior: none;
    overflow-y: overlay;
    overflow-x: hidden;
}
</style>
