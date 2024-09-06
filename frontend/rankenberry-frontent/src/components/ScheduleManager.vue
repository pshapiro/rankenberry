<template>
  <div class="schedule-manager">
    <h2 class="title is-4">Manage Schedules</h2>
    <form @submit.prevent="createSchedule">
      <div class="field">
        <label class="label">Name</label>
        <div class="control">
          <input v-model="newSchedule.name" class="input" type="text" required>
        </div>
      </div>
      <div class="field">
        <label class="label">Project</label>
        <div class="control">
          <div class="select">
            <select v-model="newSchedule.project_id">
              <option :value="null">Select a project</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
          </div>
        </div>
      </div>
      <div class="field">
        <label class="label">Tag</label>
        <div class="control">
          <div class="select">
            <select v-model="newSchedule.tag_id">
              <option :value="null">Select a tag</option>
              <option v-for="tag in tags" :key="tag.id" :value="tag.id">
                {{ tag.name }}
              </option>
            </select>
          </div>
        </div>
      </div>
      <div class="field">
        <label class="label">Frequency</label>
        <div class="control">
          <div class="select">
            <select v-model="newSchedule.frequency" required>
              <option value="">Select frequency</option>
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
        </div>
      </div>
      <div class="field">
        <div class="control">
          <button type="submit" class="button is-primary">Create Schedule</button>
        </div>
      </div>
    </form>

    <table class="table is-fullwidth">
      <thead>
        <tr>
          <th>Name</th>
          <th>Project/Tag</th>
          <th>Frequency</th>
          <th>Last Run</th>
          <th>Next Run</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="schedule in schedules" :key="schedule.id">
          <td>{{ schedule.name }}</td>
          <td>
            {{ schedule.project_id ? getProjectName(schedule.project_id) : getTagName(schedule.tag_id) }}
          </td>
          <td>{{ schedule.frequency }}</td>
          <td>{{ formatDateTime(schedule.last_run) || 'N/A' }}</td>
          <td>{{ formatDateTime(schedule.next_run) }}</td>
          <td>
            <button @click="runSchedule(schedule.id)" class="button is-primary is-small" :class="{ 'is-loading': isLoading[schedule.id] }">
              Run Now
            </button>
            <button @click="runScheduleIn1Minute(schedule.id)" class="button is-info is-small" :class="{ 'is-loading': isLoadingIn1Min[schedule.id] }">
              Run in 1 Min
            </button>
            <button @click="deleteSchedule(schedule.id)" class="button is-danger is-small">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="message" :class="['notification', messageType]">
      {{ message }}
    </div>
    <p v-if="error" class="has-text-danger">{{ error }}</p>
    <p v-if="projects.length === 0">No projects available. Please add projects first.</p>
    <p v-if="tags.length === 0">No tags available. Please add tags first.</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useMainStore } from '../stores'
import { storeToRefs } from 'pinia'

const store = useMainStore()
const { projects, tags, schedules } = storeToRefs(store)
const newSchedule = ref({
  name: '',
  project_id: null,
  tag_id: null,
  frequency: ''
})
const error = ref('')
const isLoading = ref({})
const isLoadingIn1Min = ref({})
const message = ref('')
const messageType = ref('is-info')

const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return 'N/A';
  const date = new Date(dateTimeString);
  return date.toLocaleString();
}

onMounted(async () => {
  await store.fetchSchedules()
  await store.fetchProjects()
  await store.fetchTags()
})

const createSchedule = async () => {
  try {
    console.log("Sending schedule data:", newSchedule.value)
    await store.createSchedule(newSchedule.value)
    await store.fetchSchedules()  // Fetch updated schedules
    newSchedule.value = { name: '', project_id: null, tag_id: null, frequency: '' }
    error.value = ''
  } catch (error) {
    console.error('Error creating schedule:', error)
    error.value = 'Failed to create schedule. Please try again.'
  }
}

const deleteSchedule = async (id) => {
  try {
    await store.deleteSchedule(id)
    await store.fetchSchedules()  // Fetch updated schedules
  } catch (error) {
    console.error('Error deleting schedule:', error)
  }
}

const runSchedule = async (id) => {
  isLoading.value[id] = true
  message.value = ''
  try {
    await store.runSchedule(id)
    await store.fetchSchedules()  // Fetch updated schedules
    message.value = 'Schedule run successfully'
    messageType.value = 'is-success'
  } catch (error) {
    console.error('Error running schedule:', error)
    message.value = 'Error running schedule'
    messageType.value = 'is-danger'
  } finally {
    isLoading.value[id] = false
    setTimeout(() => {
      message.value = ''
    }, 3000)
  }
}

const runScheduleIn1Minute = async (id) => {
  isLoadingIn1Min.value[id] = true
  message.value = ''
  try {
    await store.runScheduleIn1Minute(id)
    message.value = 'Schedule set to run in 1 minute'
    messageType.value = 'is-success'
    
    // Set a timeout to fetch updated data after 2 minutes
    setTimeout(async () => {
      try {
        await store.fetchSchedules()
        await store.fetchRankData()
        message.value = 'Schedule executed and data updated'
        messageType.value = 'is-success'
      } catch (error) {
        console.error('Error fetching updated data:', error)
        message.value = 'Error fetching updated data'
        messageType.value = 'is-danger'
      }
    }, 120000)  // 2 minutes
  } catch (error) {
    console.error('Error scheduling run in 1 minute:', error)
    message.value = 'Error scheduling run'
    messageType.value = 'is-danger'
  } finally {
    isLoadingIn1Min.value[id] = false
  }
}

const getProjectName = (id) => {
  const project = projects.value.find(p => p.id === id)
  return project ? project.name : 'Unknown Project'
}

const getTagName = (id) => {
  const tag = tags.value.find(t => t.id === id)
  return tag ? tag.name : 'Unknown Tag'
}
</script>