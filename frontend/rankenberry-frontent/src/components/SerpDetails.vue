<template>
  <div v-if="serpData" class="serp-details box">
    <h3 class="title is-3">SERP Details for "{{ keyword }}"</h3>
    <p class="subtitle">Date: {{ formatDate(serpData.date) }}</p>
    <h4 class="title is-4">Organic Results:</h4>
    <div v-if="organicResults.length > 0" class="table-container">
      <table class="table is-fullwidth is-striped is-hoverable">
        <thead>
          <tr>
            <th>Position</th>
            <th>Domain</th>
            <th>Title</th>
            <th>Link</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="result in organicResults" :key="result.position">
            <td>{{ result.position }}</td>
            <td>{{ extractDomain(result.link) }}</td>
            <td>{{ result.title }}</td>
            <td><a :href="result.link" target="_blank" rel="noopener noreferrer">{{ result.link }}</a></td>
            <td>{{ result.description }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else>
      <p>No organic results found. The full_data field is empty.</p>
      <p>Rank: {{ serpData.rank }}</p>
      <pre>{{ JSON.stringify(serpData, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { defineProps, watch, computed } from 'vue'

const props = defineProps({
  serpData: Object,
  keyword: String
})

const organicResults = computed(() => {
  console.log('Computing organicResults');
  console.log('serpData:', props.serpData);
  if (props.serpData && props.serpData.full_data) {
    console.log('full_data:', props.serpData.full_data);
    if (props.serpData.full_data.organic_results) {
      console.log('organic_results:', props.serpData.full_data.organic_results);
      return props.serpData.full_data.organic_results;
    }
  }
  return [];
});

watch(() => props.serpData, (newValue) => {
  console.log('SerpDetails received new serpData:', newValue)
  if (newValue && newValue.full_data) {
    console.log('Full data:', newValue.full_data)
    console.log('Organic results:', organicResults.value)
  } else {
    console.log('No full_data found in serpData')
  }
}, { immediate: true })

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
