<template>
    <div class="modal" :class="{ 'is-active': isActive }">
      <div class="modal-background" @click="close"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <p class="modal-card-title">SERP Details for "{{ keyword }}"</p>
          <button class="delete" aria-label="close" @click="close"></button>
        </header>
        <section class="modal-card-body">
          <div v-if="serpData">
            <p class="subtitle">Date: {{ formatDate(serpData.date) }}</p>
            <h4 class="title is-4">Organic Results:</h4>
            <div v-if="organicResults.length > 0" class="table-container">
              <table class="table is-fullwidth is-striped is-hoverable">
                <thead>
                  <tr>
                    <th>Position</th>
                    <th>Domain</th>
                    <th>Title</th>
                    <th>Link</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="result in organicResults" :key="result.position">
                    <td>{{ result.position }}</td>
                    <td>{{ extractDomain(result.link) }}</td>
                    <td>{{ result.title }}</td>
                    <td><a :href="result.link" target="_blank" rel="noopener noreferrer">{{ result.link }}</a></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else>
              <p>No organic results found.</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  </template>
  
  <script setup>
  import { defineProps, computed } from 'vue'
  
  const props = defineProps({
    isActive: Boolean,
    serpData: Object,
    keyword: String
  })
  
  const emit = defineEmits(['close'])
  
  const close = () => {
    emit('close')
  }
  
  const organicResults = computed(() => {
    if (props.serpData && props.serpData.full_data) {
      return props.serpData.full_data.organic_results || []
    }
    return []
  })
  
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }
  
  const extractDomain = (url) => {
    try {
      return new URL(url).hostname
    } catch {
      return url
    }
  }
  </script>
  
  <style scoped>
  .modal-card {
    width: 80%;
    max-width: 960px;
  }
  </style>