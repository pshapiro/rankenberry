<template>
  <div>
    <div v-if="!selectedProject">
      <p>Please select a project:</p>
      <select v-model="selectedProject">
        <option v-for="project in projects" :key="project.id" :value="project.id">
          {{ project.name }}
        </option>
      </select>
    </div>
    <button @click="addDomain" :disabled="!selectedProject">Add GSC Domain</button>
    <!-- Add other UI elements as needed -->
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useMainStore } from '@/stores';

const mainStore = useMainStore();
const projects = ref([]);
const selectedProject = ref(null);

onMounted(async () => {
  projects.value = await mainStore.fetchProjects();
});

const addDomain = async () => {
  try {
    if (!selectedProject.value) {
      console.error('No project selected');
      return;
    }
    const response = await fetch(`http://localhost:5001/api/gsc/auth?project_id=${selectedProject.value}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (data.authorization_url) {
      window.location.href = data.authorization_url;
    } else {
      console.error('No authorization_url received from the server');
    }
  } catch (error) {
    console.error('Error initiating GSC auth:', error);
  }
};
</script>