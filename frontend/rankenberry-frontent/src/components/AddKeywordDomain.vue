<template>
  <div class="add-keyword-domain">
    <h2 class="title is-2">Add Project</h2>
    <form @submit.prevent="addProject" class="box">
      <div class="field">
        <label class="label">Project Name</label>
        <div class="control">
          <input v-model="projectName" class="input" type="text" placeholder="Project Name" required>
        </div>
      </div>
      <div class="field">
        <label class="label">Domain</label>
        <div class="control">
          <input v-model="domain" class="input" type="text" placeholder="Domain" required>
        </div>
      </div>
      <div class="field">
        <div class="control">
          <button type="submit" class="button is-primary">Add Project</button>
        </div>
      </div>
    </form>
    <p v-if="message" class="notification" :class="{'is-success': !message.includes('Error'), 'is-danger': message.includes('Error')}">{{ message }}</p>

    <h2 class="title is-2">Projects</h2>
    <div class="box">
      <ul v-if="projects.length">
        <li v-for="project in projects" :key="project.id">
          {{ project.name }} ({{ project.domain }})
        </li>
      </ul>
      <p v-else>No projects yet.</p>
    </div>

    <h2 class="title is-2">Add Keywords</h2>
    <form @submit.prevent="addKeywords" class="box">
      <div class="field">
        <label class="label">Select Project</label>
        <div class="control">
          <div class="select is-fullwidth">
            <select v-model="selectedProject" required>
              <option value="">Select a project</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
          </div>
        </div>
      </div>
      <div class="field">
        <label class="label">Keywords</label>
        <div class="control">
          <textarea v-model="keywords" class="textarea" placeholder="Enter keywords, one per line" required></textarea>
        </div>
      </div>
      <div class="field">
        <div class="control">
          <button type="submit" class="button is-primary">Add Keywords</button>
        </div>
      </div>
    </form>
    <div v-if="isLoading" class="loading-overlay">Loading...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMainStore } from '../stores'
import { storeToRefs } from 'pinia'

const store = useMainStore()
const { projects } = storeToRefs(store)

const projectName = ref('')
const domain = ref('')
const selectedProject = ref('')
const keywords = ref('')
const message = ref('')
const isLoading = ref(false)

onMounted(async () => {
  try {
    await store.fetchProjects()
  } catch (error) {
    console.error('Error fetching projects:', error)
    message.value = 'Error loading projects. Please refresh the page.'
  }
})

const addProject = async () => {
  try {
    const newProject = await store.addProject(projectName.value, domain.value)
    message.value = `Project "${newProject.name}" added successfully!`
    projectName.value = ''
    domain.value = ''
  } catch (error) {
    message.value = `Error adding project: ${error.message}`
    console.error('Error adding project:', error)
  }
}

const addKeywords = async () => {
  if (!selectedProject.value) {
    message.value = 'Please select a project first.'
    return
  }
  const keywordList = keywords.value.split('\n').map(kw => kw.trim()).filter(kw => kw)
  try {
    isLoading.value = true
    const addedKeywords = await store.addKeywords(selectedProject.value, keywordList)
    message.value = 'Keywords added successfully!'
    keywords.value = ''
    
    // Fetch SERP data for newly added keywords
    await store.fetchSerpDataForKeywords(addedKeywords)
    message.value += ' SERP data fetched for new keywords.'
  } catch (error) {
    message.value = `Error adding keywords: ${error.message}`
    console.error('Error adding keywords:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  font-size: 24px;
  z-index: 9999;
}
</style>