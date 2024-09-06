<template>
    <div class="configure-options">
      <h2 class="title is-2">Configure Options</h2>
      <div class="box">
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
        <p v-if="message" :class="['notification', messageType]">{{ message }}</p>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useMainStore } from '../stores'
  
  const store = useMainStore()
  const selectedApiSource = ref('')
  const message = ref('')
  const messageType = ref('')
  
  onMounted(async () => {
    try {
      selectedApiSource.value = await store.getSearchVolumeApiSource()
    } catch (error) {
      console.error('Error fetching API source:', error)
      showMessage('Error fetching API source', 'is-danger')
    }
  })
  
  const updateApiSource = async () => {
    try {
      console.log("Updating API source to:", selectedApiSource.value);
      await store.updateSearchVolumeApiSource(selectedApiSource.value);
      showMessage('API source updated successfully', 'is-success');
    } catch (error) {
      console.error('Error updating API source:', error);
      showMessage('Error updating API source', 'is-danger');
    }
  }
  
  const showMessage = (msg, type) => {
    message.value = msg
    messageType.value = type
    setTimeout(() => {
      message.value = ''
      messageType.value = ''
    }, 3000)
  }
  </script>