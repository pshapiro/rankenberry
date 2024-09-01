<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div id="app">
    <nav class="navbar is-light" role="navigation" aria-label="main navigation">
      <div class="container">
        <div class="navbar-brand">
          <a class="navbar-item" href="/">
            <strong>Rankenberry</strong>
          </a>
        </div>
        <div class="navbar-menu is-active">
          <div class="navbar-end">
            <RouterLink to="/" class="navbar-item">Home</RouterLink>
            <RouterLink to="/add" class="navbar-item">Add Keyword/Domain</RouterLink>
          </div>
        </div>
      </div>
    </nav>
    <section class="section">
      <div class="container">
        <RouterView />
      </div>
    </section>
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