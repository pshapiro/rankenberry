<template>
  <div class="google-sign-in">
    <button @click="signIn" class="button is-primary">
      Sign in with Google
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits(['signed-in'])

const signIn = async () => {
  try {
    const response = await axios.get('http://localhost:5001/api/gsc/auth')
    window.location.href = response.data.authorization_url
  } catch (error) {
    console.error('Error initiating Google Sign-In:', error)
  }
}

onMounted(async () => {
  // Handle the OAuth callback
  if (window.location.pathname === '/api/gsc/oauth2callback') {
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    
    if (code) {
      try {
        await axios.get(`http://localhost:5001/api/gsc/oauth2callback?code=${code}`)
        emit('signed-in')
      } catch (error) {
        console.error('Error completing Google Sign-In:', error)
      }
    }
  }
})
</script>