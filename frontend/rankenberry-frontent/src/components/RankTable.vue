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
      <div class="control is-expanded">
        <div class="select is-fullwidth">
          <select v-model="selectedTag">
            <option value="">All Tags</option>
            <option v-for="tag in tags" :key="tag.id" :value="tag.id">
              {{ tag.name }}
            </option>
          </select>
        </div>
      </div>
      <div class="control">
        <button @click="fetchSerpData" :disabled="!selectedProject && !selectedTag" class="button is-primary">
          Fetch Latest SERP Data
        </button>
      </div>
    </div>
    <table class="table is-fullwidth is-striped is-hoverable">
      <thead>
        <tr>
          <th>Date</th>
          <th>Keyword</th>
          <th>Domain</th>
          <th>Rank</th>
          <th>Change</th>
          <th>Actions</th>
          <th>Tags</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in filteredRankData" :key="item.id">
          <td>{{ formatDate(item.date) }}</td>
          <td>{{ item.keyword }}</td>
          <td>{{ item.domain }}</td>
          <td>{{ item.rank === null || item.rank === -1 ? '-' : item.rank }}</td>
          <td>
            <span v-if="rankChanges[item.keyword_id] && rankChanges[item.keyword_id].length > 1">
              <span v-if="(item.rank === null || item.rank === -1) && rankChanges[item.keyword_id][1].rank !== null && rankChanges[item.keyword_id][1].rank !== -1" class="has-text-danger">
                ▼ {{ rankChanges[item.keyword_id][1].rank }}
              </span>
              <span v-else-if="(item.rank !== null && item.rank !== -1) && (rankChanges[item.keyword_id][1].rank === null || rankChanges[item.keyword_id][1].rank === -1)" class="has-text-success">
                ▲ {{ item.rank }}
              </span>
              <span v-else-if="item.rank !== null && item.rank !== -1 && rankChanges[item.keyword_id][1].rank !== null && rankChanges[item.keyword_id][1].rank !== -1">
                <span v-if="item.rank < rankChanges[item.keyword_id][1].rank" class="has-text-success">
                  ▲ {{ rankChanges[item.keyword_id][1].rank - item.rank }}
                </span>
                <span v-else-if="item.rank > rankChanges[item.keyword_id][1].rank" class="has-text-danger">
                  ▼ {{ item.rank - rankChanges[item.keyword_id][1].rank }}
                </span>
                <span v-else>-</span>
              </span>
              <span v-else>-</span>
            </span>
            <span v-else>-</span>
          </td>
          <td>
            <div class="buttons">
              <button @click="viewDetails(item)" class="button is-small is-info">
                {{ selectedSerpData && selectedSerpData.id === item.id ? 'Hide Details' : 'View Details' }}
              </button>
              <button @click="fetchSingleSerpData(item)" :disabled="!item.keyword_id" class="button is-small is-primary">Fetch New Data</button>
              <button @click="deleteRankData(item.id)" class="button is-small is-danger">Delete</button>
            </div>
          </td>
          <td>
            <div class="tags">
              <span v-for="tag in item.tags" :key="tag.id" class="tag is-info is-small">
                {{ tag.name }}
              </span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="selectedSerpData" class="box mt-4 serp-details-container">
      <div class="serp-details-header">
        <h3 class="title is-4">SERP Details for "{{ selectedKeyword }}"</h3>
        <button @click="closeSerpDetails" class="delete"></button>
      </div>
      <SerpDetails :serpData="selectedSerpData" :keyword="selectedKeyword" />
    </div>
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useMainStore } from '../stores'
import { storeToRefs } from 'pinia'
import SerpDetails from './SerpDetails.vue'

const store = useMainStore()
const { rankData, projects, tags } = storeToRefs(store)
const selectedProject = ref('')
const selectedTag = ref('')
const selectedSerpData = ref(null)
const selectedKeyword = ref('')
const isLoading = ref(false)

onMounted(async () => {
  store.fetchProjects()
  store.fetchRankData()
  store.fetchTags()
  await loadKeywordTags()
})

const loadKeywordTags = async () => {
  for (const item of rankData.value) {
    item.tags = await store.getKeywordTags(item.keyword_id)
  }
}

const filteredRankData = computed(() => {
  let filtered = rankData.value

  if (selectedProject.value) {
    filtered = filtered.filter(item => item.project_id === selectedProject.value)
  }

  if (selectedTag.value) {
    filtered = filtered.filter(item => 
      item.tags && item.tags.some(tag => tag.id === selectedTag.value)
    )
  }

  return filtered
})

const rankChanges = computed(() => {
  const changes = {}
  const sortedData = [...filteredRankData.value].sort((a, b) => new Date(b.date) - new Date(a.date))
  sortedData.forEach(item => {
    if (!changes[item.keyword_id]) {
      changes[item.keyword_id] = [item]
    } else if (changes[item.keyword_id].length < 2) {
      changes[item.keyword_id].push(item)
    }
  })
  return changes
})

const fetchSerpData = async () => {
  isLoading.value = true
  try {
    if (selectedProject.value) {
      await store.fetchSerpData(selectedProject.value, selectedTag.value)
    } else if (selectedTag.value) {
      await store.fetchSerpDataByTag(selectedTag.value)
    }
    await store.fetchRankData()
    await loadKeywordTags()
  } catch (error) {
    console.error('Error fetching SERP data:', error)
  } finally {
    isLoading.value = false
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
    isLoading.value = true
    try {
      await store.fetchSingleSerpData(item.keyword_id)
      await store.fetchRankData()
    } catch (error) {
      console.error('Error fetching single SERP data:', error)
    } finally {
      isLoading.value = false
    }
  } else {
    console.error('Invalid item or missing keyword_id:', item)
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString()
}

const closeSerpDetails = () => {
  selectedSerpData.value = null
  selectedKeyword.value = ''
}

const deleteRankData = async (id) => {
  if (confirm('Are you sure you want to delete this rank data?')) {
    try {
      await store.deleteRankData(id)
      await store.fetchRankData()
    } catch (error) {
      console.error('Error deleting rank data:', error)
    }
  }
}

watch([selectedProject, selectedTag], async () => {
  await loadKeywordTags()
})
</script>

<style scoped>
.serp-details-container {
  position: relative;
}

.serp-details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.serp-details-header .delete {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>