<template>
    <div class="edit-project">
      <h2 class="title is-2">Edit Project</h2>
      <form @submit.prevent="updateProject" class="box">
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
          <label class="label">Branded Terms</label>
          <div class="control">
            <textarea v-model="brandedTerms" class="textarea" placeholder="Enter branded terms, one per line"></textarea>
          </div>
        </div>
        <div class="field">
          <label class="label">Conversion Rate (%)</label>
          <div class="control">
            <input v-model="conversionRate" class="input" type="number" min="0" max="100" step="0.01" placeholder="Enter conversion rate">
          </div>
        </div>
        <div class="field">
          <label class="label">Conversion Value</label>
          <div class="control">
            <input v-model="conversionValue" class="input" type="number" min="0" step="0.01" placeholder="Enter conversion value">
          </div>
        </div>
        <div class="field">
          <div class="control">
            <button type="submit" class="button is-primary">Update Project</button>
          </div>
        </div>
      </form>
      <p v-if="message" class="notification" :class="{'is-success': !message.includes('Error'), 'is-danger': message.includes('Error')}">{{ message }}</p>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useMainStore } from '../stores'
  
  const store = useMainStore()
  
  const props = defineProps({
    projectId: {
      type: Number,
      required: true
    }
  })
  
  const projectName = ref('')
  const domain = ref('')
  const brandedTerms = ref('')
  const conversionRate = ref('')
  const conversionValue = ref('')
  const message = ref('')
  
  onMounted(async () => {
    try {
      const project = await store.getProject(props.projectId)
      projectName.value = project.name
      domain.value = project.domain
      brandedTerms.value = project.branded_terms || ''
      conversionRate.value = project.conversion_rate || ''
      conversionValue.value = project.conversion_value || ''
    } catch (error) {
      console.error('Error fetching project:', error)
      message.value = 'Error loading project details.'
    }
  })
  
  const updateProject = async () => {
    try {
      const updatedProject = await store.updateProject(props.projectId, {
        name: projectName.value,
        domain: domain.value,
        branded_terms: brandedTerms.value,
        conversion_rate: parseFloat(conversionRate.value),
        conversion_value: parseFloat(conversionValue.value)
      })
      console.log('Updated project:', updatedProject)
      message.value = 'Project updated successfully!'
    } catch (error) {
      console.error('Error updating project:', error)
      message.value = `Error updating project: ${error.message}`
    }
  }
  </script>