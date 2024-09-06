<template>
    <div class="api-source-selector">
      <h3 class="title is-4">Search Volume API Source</h3>
      <div class="field">
        <div class="control">
          <div class="select">
            <select v-model="selectedApiSource" @change="updateApiSource">
              <option value="grepwords">Grepwords</option>
              <option value="dataforseo">DataForSEO</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useMainStore } from '../stores'
  
  const store = useMainStore()
  const selectedApiSource = ref('')
  
  onMounted(async () => {
    try {
      selectedApiSource.value = await store.getSearchVolumeApiSource()
    } catch (error) {
      console.error('Error fetching API source:', error)
    }
  })
  
  const updateApiSource = async () => {
    try {
      await store.updateSearchVolumeApiSource(selectedApiSource.value)
    } catch (error) {
      console.error('Error updating API source:', error)
    }
  }
  </script>