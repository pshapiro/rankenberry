<template>
    <div>Processing authentication...</div>
  </template>
  
  <script setup>
  import { onMounted } from 'vue'
  import axios from 'axios'
  import { useRouter } from 'vue-router'
  
  const router = useRouter()
  const API_URL = 'http://localhost:5001'
  
  onMounted(async () => {
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
  
    if (code) {
      try {
        const response = await axios.post(`${API_URL}/oauth/callback`, { code })
        if (response.data.message === "Authentication successful") {
          // Optionally, store user info or tokens as needed
          // Example: localStorage.setItem('user', JSON.stringify(response.data.user))
          router.push('/') // Redirect to home or dashboard
        } else {
          console.error('Unexpected response:', response.data)
          // Handle unexpected responses
        }
      } catch (error) {
        console.error('Authentication error:', error.response ? error.response.data : error.message)
        // Optionally, display an error message to the user
      }
    } else {
      console.error('No authorization code found in the URL')
      // Optionally, redirect or inform the user
    }
  })
  </script>