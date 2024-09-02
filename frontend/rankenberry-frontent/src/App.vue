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
      <div class="navbar-brand">
        <a class="navbar-item" href="/">
          <img src="@/assets/rankenberry-logo.png" alt="Rankenberry Logo" class="logo">
          <span class="has-text-weight-bold is-size-4">Rankenberry</span>
        </a>
      </div>
      <div class="navbar-menu">
        <div class="navbar-start">
          <router-link to="/" class="navbar-item">Home / Rank Table</router-link>
          <router-link to="/add" class="navbar-item">Add Project/Keywords</router-link>
          <router-link to="/keyword-management" class="navbar-item">Keyword Management</router-link>
        </div>
      </div>
    </nav>
    <div class="container">
      <router-view></router-view>
    </div>
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

.container {
  flex-grow: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.navbar-brand {
  display: flex;
  align-items: center;
}

.navbar-brand .logo {
  width: auto;
  height: 42px;
  margin-right: 0; /* Removed margin */
}

.navbar-brand span {
  color: inherit;
}

/* Adjust padding for the navbar-item */
.navbar-brand .navbar-item {
  padding: 5px 10px 5px 10px; /* Reduced right padding */
}
</style>