<template>
    <div class="options-page">
      <h2 class="title is-3">Google Search Console Integration</h2>
      
      <div v-if="!isAuthenticated">
        <button @click="initiateGoogleSignIn" class="button is-primary">Sign in with Google</button>
      </div>
      <div v-else>
        <p>You are signed in as {{ userEmail }}</p>
        <button @click="signOut" class="button is-danger">Sign Out</button>
      </div>
      
      <div v-if="message" class="notification is-info">{{ message }}</div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  
  const isAuthenticated = ref(false)
  const userEmail = ref('')
  const message = ref('')
  const googleClientId = ref('YOUR_GOOGLE_CLIENT_ID') // Ensure this is correctly set
  
  const API_URL = 'http://localhost:5001'  // Adjust based on your backend URL
  
  onMounted(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/google-client-id`)
      googleClientId.value = response.data.client_id
      console.log('Received client ID from backend:', googleClientId.value)
    } catch (error) {
      console.error('Error fetching Google Client ID:', error)
      message.value = "Error initializing Google Sign-In. Please try again later."
    }
  })
  
  const initiateGoogleSignIn = () => {
    const redirectUri = `${window.location.origin}/auth-callback`
    const scope = 'email profile https://www.googleapis.com/auth/webmasters.readonly'
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${googleClientId.value}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${encodeURIComponent(scope)}&access_type=offline`
    
    window.location.href = authUrl
  }
  
  const signOut = async () => {
    try {
      const res = await axios.get(`${API_URL}/oauth/logout`)
      if (res.data.message === "Logged out successfully") {
        isAuthenticated.value = false
        userEmail.value = ''
        message.value = "Successfully signed out."
      }
    } catch (error) {
      console.error('Logout error:', error)
      message.value = "Logout failed. Please try again."
    }
  }
  </script>
  
  <style scoped>
  .options-page {
      padding: 20px;
  }
  </style>