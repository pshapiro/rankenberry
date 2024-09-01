<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

watch(() => route.meta.title, (newTitle) => {
  document.title = `Rankenberry - ${newTitle || 'Home'}`
})
</script>

<template>
  <div id="app">
    <nav class="navbar is-light" role="navigation" aria-label="main navigation">
      <div class="navbar-menu">
        <div class="navbar-start">
          <router-link to="/" class="navbar-item">Home</router-link>
          <router-link to="/add" class="navbar-item">Add Project/Keywords</router-link>
          <router-link to="/keyword-management" class="navbar-item">Keyword Management</router-link>
        </div>
      </div>
    </nav>
    <router-view></router-view>
  </div>
</template>

<style>
#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.navbar {
  width: 100%;
}

.section {
  flex-grow: 1;
}
</style>