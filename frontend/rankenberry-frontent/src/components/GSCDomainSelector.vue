<template>
    <div class="gsc-domain-selector">
      <h3 class="title is-4">Select GSC Domain</h3>
      <div class="field">
        <div class="control">
          <div class="select">
            <select v-model="selectedDomain" @change="updateDomain">
              <option value="">Select a domain</option>
              <option v-for="domain in gscDomains" :key="domain" :value="domain">
                {{ domain }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useMainStore } from '../stores';
  
  const props = defineProps({
    projectId: {
      type: Number,
      required: true
    }
  });
  
  const store = useMainStore();
  const gscDomains = ref([]);
  const selectedDomain = ref('');
  
  onMounted(async () => {
    try {
      gscDomains.value = await store.fetchGSCDomains();
      // Fetch the current GSC domain for the project and set it as selectedDomain
      // You might need to add this to your API and store
    } catch (error) {
      console.error('Error fetching GSC domains:', error);
    }
  });
  
  const updateDomain = async () => {
    try {
      await store.updateProjectGSCDomain(props.projectId, selectedDomain.value);
    } catch (error) {
      console.error('Error updating GSC domain:', error);
    }
  };
  </script>