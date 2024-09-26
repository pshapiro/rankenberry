<template>
    <div class="gsc-domain-selection">
      <h1 class="title">Select Google Search Console Domain</h1>
      <GSCDomainSelector @domain-added="onDomainAdded" />
    </div>
  </template>
  
  <script setup>
  import { useRouter } from 'vue-router'
  import GSCDomainSelector from './GSCDomainSelector.vue'
  import { useMainStore } from '../stores'
  
  const router = useRouter()
  const store = useMainStore()
  
  const addDomain = async () => {
  try {
    const domainId = await store.addGSCDomain(selectedDomain.value, selectedProject.value)
    // Assuming you have a way to get the current user's ID, replace 1 with the actual user ID
    await store.setGSCDomain(domainId, 1)
    emit('domain-added', domainId)
    selectedDomain.value = ''
    selectedProject.value = ''
  } catch (error) {
    console.error('Error adding GSC domain:', error)
  }
}
</script>