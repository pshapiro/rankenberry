<template>
  <div class="add-keyword-domain">
    <h2>Add Project</h2>
    <form @submit.prevent="addProject">
      <input v-model="projectName" placeholder="Project Name" required>
      <input v-model="domain" placeholder="Domain" required>
      <button type="submit">Add Project</button>
    </form>
    <p v-if="message">{{ message }}</p>

    <h2>Projects</h2>
    <ul v-if="projects.length">
      <li v-for="project in projects" :key="project.id">
        {{ project.name }} ({{ project.domain }})
      </li>
    </ul>
    <p v-else>No projects yet.</p>

    <h2>Add Keywords</h2>
    <form @submit.prevent="addKeywords">
      <select v-model="selectedProject" required>
        <option value="">Select a project</option>
        <option v-for="project in projects" :key="project.id" :value="project.id">
          {{ project.name }}
        </option>
      </select>
      <textarea v-model="keywords" placeholder="Enter keywords, one per line" required></textarea>
      <button type="submit">Add Keywords</button>
    </form>
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
    for (const keyword of keywordList) {
      await store.addKeyword(selectedProject.value, keyword)
    }
    message.value = 'Keywords added successfully!'
    keywords.value = ''
  } catch (error) {
    message.value = `Error adding keywords: ${error.message}`
    console.error('Error adding keywords:', error)
  }
}
</script>