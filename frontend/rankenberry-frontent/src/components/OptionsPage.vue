<template>
  <div class="options-page container">
    <h1 class="title">Options</h1>
    <GoogleSignIn @signed-in="onSignedIn" v-if="!isSignedIn" />
    <GSCDomainSelector v-if="isSignedIn" @domain-added="onDomainAdded" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import GoogleSignIn from './GoogleSignIn.vue'
import GSCDomainSelector from './GSCDomainSelector.vue'
import { useMainStore } from '../stores'

const router = useRouter()
const store = useMainStore()
const isSignedIn = ref(false)

const onSignedIn = () => {
  isSignedIn.value = true
}

const onDomainAdded = async (domainId) => {
  try {
    await store.setGSCDomain(domainId)
    router.push('/dashboard')
  } catch (error) {
    console.error('Error setting GSC domain:', error)
  }
}
</script>

<style scoped>
.options-page {
  margin-top: 40px;
}
</style>