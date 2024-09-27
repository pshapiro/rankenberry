<template>
  <div>
    <button @click="signIn" class="button is-primary is-large">Sign in with Google</button>
    <p v-if="error" class="has-text-danger">{{ error }}</p>
  </div>
</template>
<script setup>
import { ref } from 'vue';
import axios from 'axios';

const error = ref(null);

const signIn = async () => {
  try {
    // Replace with your actual project ID or logic to obtain it
    const projectId = 1; // For example purposes

    // Make a request to your backend to get the authorization URL
    const response = await axios.get(`http://localhost:5001/api/gsc/auth?project_id=${projectId}`);
    const data = response.data;

    if (data.authorization_url) {
      // Redirect the browser to the authorization URL
      window.location.href = data.authorization_url;
    } else {
      console.error('No authorization_url received from the server');
      error.value = 'Failed to initiate Google Sign-In. Please try again.';
    }
  } catch (err) {
    console.error('Error initiating Google Sign-In:', err);
    error.value = 'Failed to initiate Google Sign-In. Please try again.';
  }
};
</script>
<style scoped>
.has-text-danger {
  margin-top: 10px;
}
</style>