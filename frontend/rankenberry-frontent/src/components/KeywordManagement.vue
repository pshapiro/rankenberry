<template>
  <div class="keyword-management">
    <h2 class="title is-2">Keyword Management</h2>
    <div v-if="isLoading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <div v-for="project in projects" :key="project.id" class="box">
        <h3 class="title is-3">{{ project.name }}</h3>
        <table class="table is-fullwidth">
          <thead>
            <tr>
              <th>Keyword</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="keyword in projectKeywords[project.id]" :key="keyword.id" :class="{ 'has-background-grey-lighter': !keyword.active }">
              <td>{{ keyword.keyword }}</td>
              <td>
                <div class="buttons">
                  <button v-if="keyword.active" @click="deactivateKeyword(keyword.id)" class="button is-warning is-small">Deactivate</button>
                  <button v-else @click="activateKeyword(keyword.id)" class="button is-success is-small">Activate</button>
                  <button @click="deleteKeyword(keyword.id)" class="button is-danger is-small">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <button @click="deleteAllKeywords(project.id)" class="button is-danger">Delete All Keywords</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useMainStore } from '../stores'
import { storeToRefs } from 'pinia'

const store = useMainStore()
const { projects, keywords } = storeToRefs(store)

const isLoading = ref(false)
const error = ref(null)

const projectKeywords = computed(() => {
  const keywordsByProject = {}
  projects.value.forEach(project => {
    keywordsByProject[project.id] = keywords.value.filter(kw => kw.project_id === project.id)
  })
  return keywordsByProject
})

onMounted(async () => {
  isLoading.value = true
  try {
    await store.fetchProjects()
    await store.fetchKeywords()
  } catch (err) {
    error.value = 'Error loading data. Please try again.'
    console.error('Error:', err)
  } finally {
    isLoading.value = false
  }
})

const deactivateKeyword = async (keywordId) => {
  try {
    await store.deactivateKeyword(keywordId)
  } catch (error) {
    console.error('Error deactivating keyword:', error)
  }
}

const deleteKeyword = async (keywordId) => {
  try {
    await store.deleteKeyword(keywordId)
  } catch (error) {
    console.error('Error deleting keyword:', error)
  }
}

const deleteAllKeywords = async (projectId) => {
  try {
    await store.deleteAllKeywords(projectId)
  } catch (error) {
    console.error('Error deleting all keywords:', error)
  }
}

const activateKeyword = async (keywordId) => {
  try {
    await store.activateKeyword(keywordId)
  } catch (error) {
    console.error('Error activating keyword:', error)
  }
}
</script>
