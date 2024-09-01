<template>
  <div class="rank-table">
    <h2 class="title is-2">Rank Table</h2>
    <div class="field is-grouped">
      <div class="control is-expanded">
        <div class="select is-fullwidth">
          <select v-model="selectedProject">
            <option value="">All Projects</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>
      </div>
      <div class="control">
        <button @click="fetchSerpData" :disabled="!selectedProject" class="button is-primary">Fetch Latest SERP Data</button>
      </div>
    </div>
    <table class="table is-fullwidth is-striped is-hoverable">
      <thead>
        <tr>
          <th>Date</th>
          <th>Keyword</th>
          <th>Domain</th>
          <th>Rank</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in filteredRankData" :key="item.id">
          <td>{{ formatDate(item.date) }}</td>
          <td>{{ item.keyword }}</td>
          <td>{{ item.domain }}</td>
          <td>{{ item.rank }}</td>
          <td>
            <div class="buttons">
              <button @click="viewDetails(item)" class="button is-small is-info">
                {{ selectedSerpData && selectedSerpData.id === item.id ? 'Hide Details' : 'View Details' }}
              </button>
              <button @click="fetchSingleSerpData(item)" :disabled="!item.keyword_id" class="button is-small is-primary">Fetch New Data</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <SerpDetails v-if="selectedSerpData" :serpData="selectedSerpData" :keyword="selectedKeyword" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useMainStore } from '../stores'
import { storeToRefs } from 'pinia'
import SerpDetails from './SerpDetails.vue'

const store = useMainStore()
const { rankData, projects } = storeToRefs(store)
const selectedProject = ref('')
const selectedSerpData = ref(null)
const selectedKeyword = ref('')

onMounted(() => {
  store.fetchProjects()
  store.fetchRankData()
})

const filteredRankData = computed(() => {
  if (selectedProject.value) {
    return rankData.value.filter(item => item.project_id === selectedProject.value)
  }
  return rankData.value
})

const fetchSerpData = async () => {
  if (selectedProject.value) {
    try {
      await store.fetchSerpData(selectedProject.value)
    } catch (error) {
      console.error('Error fetching SERP data:', error)
    }
  }
}

const viewDetails = async (item) => {
  if (item && item.id) {
    if (selectedSerpData.value && selectedSerpData.value.id === item.id) {
      selectedSerpData.value = null
      selectedKeyword.value = ''
    } else {
      try {
        const fullSerpData = await store.fetchFullSerpData(item.id)
        console.log('Full SERP data fetched:', fullSerpData) // Add this line
        selectedSerpData.value = fullSerpData
        console.log('Fetched SERP data:', selectedSerpData.value)
        selectedKeyword.value = item.keyword
      } catch (error) {
        console.error('Error fetching full SERP data:', error)
      }
    }
  } else {
    console.error('Invalid item or missing ID:', item)
  }
}

const fetchSingleSerpData = async (item) => {
  if (item && item.keyword_id) {
    try {
      await store.fetchSingleSerpData(item.keyword_id)
      await store.fetchRankData()
    } catch (error) {
      console.error('Error fetching single SERP data:', error)
    }
  } else {
    console.error('Invalid item or missing keyword_id:', item)
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString()
}
</script>