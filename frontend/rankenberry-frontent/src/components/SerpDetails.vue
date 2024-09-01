<template>
  <div v-if="serpData" class="serp-details">
    <h3>SERP Details for "{{ keyword }}"</h3>
    <p>Date: {{ formatDate(serpData.date) }}</p>
    <h4>Organic Results:</h4>
    <table>
      <thead>
        <tr>
          <th>Position</th>
          <th>Page</th>
          <th>Domain</th>
          <th>Link</th>
          <th>Title</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="result in serpData.full_data" :key="result.position">
          <td>{{ result.position }}</td>
          <td>{{ Math.ceil(result.position / 10) }}</td>
          <td>{{ extractDomain(result.link) }}</td>
          <td><a :href="result.link" target="_blank">{{ result.link }}</a></td>
          <td>{{ result.title }}</td>
          <td>{{ result.snippet }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  serpData: Object,
  keyword: String
})

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString()
}

const extractDomain = (url) => {
  try {
    return new URL(url).hostname
  } catch {
    return url
  }
}
</script>

<style scoped>
.serp-details {
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}
</style>
