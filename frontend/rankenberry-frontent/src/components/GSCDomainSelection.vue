<template>
  <div class="gsc-domain-selection container">
    <h1 class="title">Select Google Search Console Domain</h1>

    <!-- Success Notification -->
    <div v-if="successMessage" class="notification is-success">
      {{ successMessage }}
    </div>

    <!-- Error Notification -->
    <div v-if="errorMessage" class="notification is-danger">
      {{ errorMessage }}
    </div>

    <div v-if="loading">
      <p>Loading domains...</p>
    </div>
    <div v-else>
      <div v-if="domains.length === 0">
        <p>No GSC Domains found. Please add a domain.</p>
      </div>
      <div v-else>
        <!-- Project Selection -->
        <div class="field">
          <label class="label">Select Project</label>
          <div class="control">
            <div class="select is-fullwidth">
              <select v-model="selectedProject">
                <option value="">Select a project</option>
                <option v-for="project in projects" :key="project.id" :value="project.id">
                  {{ project.name }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- Domain Selection -->
        <div class="field">
          <label class="label">Select Domain</label>
          <div class="control">
            <div class="select is-fullwidth">
              <select v-model="selectedDomain">
                <option value="">Select a domain</option>
                <option v-for="domain in domains" :key="domain" :value="domain">
                  {{ domain }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- Associate Button -->
        <button
          @click="associateDomain"
          class="button is-primary"
          :disabled="!selectedDomain || !selectedProject || isAssociating"
        >
          <span v-if="isAssociating">Associating...</span>
          <span v-else>Associate Domain with Project</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useMainStore } from '../stores';
import { storeToRefs } from 'pinia';

const route = useRoute();
const router = useRouter();
const store = useMainStore();
const { projects } = storeToRefs(store);

const domains = ref([]);
const selectedDomain = ref('');
const selectedProject = ref('');
const loading = ref(true);
const isAssociating = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

const fetchDomains = async () => {
  const projectId = route.query.project_id;
  if (!projectId) {
    console.error('No project_id provided in the URL.');
    return;
  }

  try {
    domains.value = await store.fetchGSCDomains(projectId);
  } catch (error) {
    console.error('Error fetching GSC domains:', error);
    errorMessage.value = 'Failed to fetch GSC domains. Please try again.';
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  loading.value = true;
  await store.fetchProjects();
  selectedProject.value = route.query.project_id || '';
  await fetchDomains();
});

const associateDomain = async () => {
  if (!selectedProject.value || !selectedDomain.value) {
    errorMessage.value = 'Please select both a project and a domain.';
    return;
  }
  isAssociating.value = true;
  successMessage.value = '';
  errorMessage.value = '';

  try {
    await store.addGSCDomain(selectedDomain.value, selectedProject.value);
    successMessage.value = 'Domain associated with project successfully.';
    // Optionally, redirect the user after a short delay
    setTimeout(() => {
      router.push('/');
    }, 2000);
  } catch (error) {
    console.error('Error associating domain:', error);
    errorMessage.value = 'Failed to associate domain. Please try again.';
  } finally {
    isAssociating.value = false;
  }
};
</script>

<style scoped>
.gsc-domain-selection {
  margin-top: 40px;
}
</style>