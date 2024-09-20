<template>
    <div class="api-options">
      <h2 class="title is-2">API Options</h2>
      
      <div class="box">
        <!-- SERP Data API Selection -->
        <div class="field">
          <label class="label">SERP Data API</label>
          <div class="control">
            <div class="select">
              <select v-model="selectedSerpAPI" @change="updateSerpAPI">
                <option value="SpaceSERP">SpaceSERP</option>
                <option value="AnotherSERPAPI">Another SERP API</option>
                <!-- Add more SERP API options as needed -->
              </select>
            </div>
          </div>
        </div>
        
        <!-- Search Volume API Selection -->
        <div class="field">
          <label class="label">Search Volume API</label>
          <div class="control">
            <div class="select">
              <select v-model="selectedSearchVolumeAPI" @change="updateSearchVolumeAPI">
                <option value="Grepwords">Grepwords</option>
                <option value="DataForSEO">DataForSEO</option>
                <!-- Add more Search Volume API options as needed -->
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { computed } from 'vue'
  import { useMainStore } from '../stores'
  
  const store = useMainStore()
  
  // Computed properties for two-way binding
  const selectedSerpAPI = computed({
    get: () => store.selectedSerpAPI,
    set: (value) => store.setSelectedSerpAPI(value)
  })
  
  const selectedSearchVolumeAPI = computed({
    get: () => store.selectedSearchVolumeAPI,
    set: (value) => store.setSelectedSearchVolumeAPI(value)
  })
  
  // Methods to handle API selection changes
  const updateSerpAPI = () => {
    // Future Enhancement: Implement logic to handle SERP API changes
    console.log(`Selected SERP API: ${selectedSerpAPI.value}`)
  }
  
  const updateSearchVolumeAPI = () => {
    // Future Enhancement: Implement logic to handle Search Volume API changes
    console.log(`Selected Search Volume API: ${selectedSearchVolumeAPI.value}`)
  }
  </script>
  
  <style scoped>
  .api-options {
    max-width: 600px;
    margin: auto;
    padding: 20px;
  }
  </style>