<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div id="app">
    <nav>
      <RouterLink to="/">Home</RouterLink> |
      <RouterLink to="/add">Add Keyword/Domain</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>

<style scoped>
nav {
  padding: 1rem 0;
}
nav a {
  padding: 0 0.5rem;
}
</style>