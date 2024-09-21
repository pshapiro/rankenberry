<template>
    <div class="schedule-pull">
        <h2 class="title">Schedule Ranking Pulls</h2>
        <form @submit.prevent="schedulePull" class="schedule-form">
            <div class="field">
                <label class="label" for="frequency">Frequency:</label>
                <div class="control">
                    <div class="select is-fullwidth">
                        <select v-model="frequency" id="frequency">
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                            <option value="test">Test (1 from now)</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="field">
                <label class="label" for="project">Select Project:</label>
                <div class="control">
                    <div class="select is-fullwidth">
                        <select v-model="selectedProject" id="project">
                            <option value="">Select a project</option>
                            <option v-for="project in projects" :key="project.id" :value="project.id">
                                {{ project.name }}
                            </option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="field">
                <label class="label" for="tag">Select Tag:</label>
                <div class="control">
                    <div class="select is-fullwidth">
                        <select v-model="selectedTag" id="tag">
                            <option value="">Select a tag</option>
                            <option v-for="tag in tags" :key="tag.id" :value="tag.id">
                                {{ tag.name }}
                            </option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="field">
                <div class="control">
                    <button type="submit" class="button is-primary">Schedule Pull</button>
                </div>
            </div>
        </form>

        <h3 class="title is-4 mt-6">Scheduled Pulls</h3>
        <table class="table is-fullwidth">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Project</th>
                    <th>Tag</th>
                    <th>Frequency</th>
                    <th>Last Run</th>
                    <th>Next Pull</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="pull in scheduledPulls" :key="pull.id">
                    <td>{{ pull.id }}</td>
                    <td>{{ pull.project_name }}</td>
                    <td>{{ pull.tag_name || 'No Tag' }}</td>
                    <td>{{ pull.frequency }}</td>
                    <td>{{ formatDate(pull.last_run) }}</td>
                    <td>{{ formatDate(pull.next_pull) }}</td>
                    <td>
                        <button @click="editPull(pull)" class="button is-small is-info mr-2">Edit</button>
                        <button @click="deletePull(pull.id)" class="button is-small is-danger">Delete</button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useMainStore } from '../stores';
import { storeToRefs } from 'pinia';
import axios from 'axios';

const store = useMainStore();
const { projects, tags } = storeToRefs(store);

const frequency = ref('daily');
const selectedProject = ref('');
const selectedTag = ref('');
const scheduledPulls = ref([]);

const API_BASE_URL = 'http://localhost:5001/api'; // Adjust this to match your backend URL

const schedulePull = async () => {
    try {
        const newPull = {
            project_id: parseInt(selectedProject.value),
            tag_id: selectedTag.value ? parseInt(selectedTag.value) : null,
            frequency: frequency.value,
        };
        console.log('Sending request with data:', newPull);
        const response = await axios.post(`${API_BASE_URL}/schedule-rank-pull`, newPull);
        console.log('Received response:', response.data);
        scheduledPulls.value.push(response.data);
        alert('Pull scheduled successfully!');
        resetForm();
        fetchScheduledPulls();
    } catch (error) {
        console.error('Error scheduling pull:', error);
        if (error.response) {
            console.log('Response status:', error.response.status);
            console.log('Response data:', error.response.data);
        }
        alert('Failed to schedule pull. Please try again.');
    }
};

const fetchScheduledPulls = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/scheduled-pulls`);
        scheduledPulls.value = response.data;
        console.log('Fetched scheduled pulls:', scheduledPulls.value);
    } catch (error) {
        console.error('Error fetching scheduled pulls:', error);
    }
};

const deletePull = async (id) => {
    if (!id) {
        console.error('Attempted to delete pull with undefined id');
        return;
    }
    try {
        await axios.delete(`${API_BASE_URL}/scheduled-pulls/${id}`);
        await fetchScheduledPulls();
    } catch (error) {
        console.error('Error deleting pull:', error);
    }
};

const resetForm = () => {
    frequency.value = 'daily';
    selectedProject.value = '';
    selectedTag.value = '';
};

const getProjectName = (projectId) => {
    const project = projects.value.find(p => p.id === projectId);
    return project ? project.name : 'Unknown Project';
};

const getTagName = (tagId) => {
    if (!tagId) return 'No Tag';
    const tag = tags.value.find(t => t.id === tagId);
    return tag ? tag.name : 'Unknown Tag';
};

const formatNextPull = (date) => {
    const parsedDate = new Date(date);
    return isNaN(parsedDate.getTime()) ? 'Invalid Date' : parsedDate.toLocaleString();
};

const formatDate = (date) => {
    if (!date) return 'N/A';
    const parsedDate = new Date(date);
    return isNaN(parsedDate.getTime()) ? 'Invalid Date' : parsedDate.toLocaleString();
};

const editPull = (pull) => {
    frequency.value = pull.frequency;
    selectedProject.value = pull.project_id;
    selectedTag.value = pull.tag_id;
    deletePull(pull.id);
};

onMounted(async () => {
    try {
        await store.fetchProjects();
        await store.fetchTags();
        await fetchScheduledPulls();
    } catch (error) {
        console.error('Error fetching data:', error);
    }
});
</script>

<style scoped>
.schedule-pull {
    max-width: 800px;
    margin: 20px auto;
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 8px;
    background-color: #f9f9f9;
}

.field {
    margin-bottom: 20px;
}

.button {
    width: 100%;
}
</style>