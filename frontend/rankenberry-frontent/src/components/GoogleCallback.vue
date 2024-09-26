<template>
  <div>Processing Google Sign-In...</div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useMainStore } from '../stores'

const router = useRouter()
const store = useMainStore()

onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search)
  const code = urlParams.get('code')
  
  if (code) {
    try {
      await axios.get(`http://localhost:5001/api/gsc/oauth2callback?code=${code}`)
      await store.setAuthenticated(true)
      router.push('/gsc-domain-selection')
    } catch (error) {
      console.error('Error completing Google Sign-In:', error)
      router.push('/error')
    }
  } else {
    router.push('/')
  }
})
</script>