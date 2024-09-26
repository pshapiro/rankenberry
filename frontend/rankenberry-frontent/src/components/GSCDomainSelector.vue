<template>
  <div class="gsc-domain-selector">
    <h2 class="title is-4">Select Google Search Console Domain</h2>
    <div v-if="loading" class="is-loading">Loading...</div>
    <div v-else>
      <div class="field">
        <label class="label">Project</label>
        <div class="control">
          <div class="select">
            <select v-model="selectedProject">
              <option value="">Select a project</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">
                {{ project.name }} ({{ project.domain }})
              </option>
            </select>
          </div>
        </div>
      </div>
      <div class="field">
        <label class="label">GSC Domain</label>
        <div class="control">
          <div class="select">
            <select v-model="selectedDomain">
              <option value="">Select a GSC domain</option>
              <option v-for="domain in gscDomains" :key="domain" :value="domain">
                {{ domain }}
              </option>
            </select>
          </div>
        </div>
      </div>
      <button @click="addDomain" class="button is-primary" :disabled="!selectedProject || !selectedDomain">
        Add Domain
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMainStore } from '../stores'

const store = useMainStore()
const projects = ref([])
const gscDomains = ref([])
const selectedProject = ref('')
const selectedDomain = ref('')
const loading = ref(true)

const emit = defineEmits(['domain-added'])

onMounted(async () => {
  try {
    await Promise.all([
      fetchProjects(),
      fetchGSCDomains()
    ])
  } catch (error) {
    console.error('Error fetching data:', error)
  } finally {
    loading.value = false
  }
})

const fetchProjects = async () => {
  try {
    projects.value = await store.fetchProjects()
  } catch (error) {
    console.error('Error fetching projects:', error)
  }
}

const fetchGSCDomains = async () => {
  try {
    gscDomains.value = await store.fetchGSCDomains()
  } catch (error) {
    console.error('Error fetching GSC domains:', error)
  }
}

const addDomain = async () => {
  try {
    const domainId = await store.addGSCDomain(selectedDomain.value, selectedProject.value)
    // Use a placeholder user ID (e.g., 1) for now. In a real application, you'd get this from your authentication system.
    await store.setGSCDomain(domainId, 1, selectedProject.value)
    emit('domain-added', domainId)
    selectedDomain.value = ''
    selectedProject.value = ''
  } catch (error) {
    console.error('Error adding GSC domain:', error)
  }
}
</script>

<style scoped>
.is-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
}
</style>