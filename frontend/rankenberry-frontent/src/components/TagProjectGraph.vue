<template>
  <div>
    <h2 class="title is-4">SERP Data for {{ type === 'tag' ? 'Tag' : 'Project' }}</h2>
    <div ref="chart" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ['tag', 'project'].includes(value)
  },
  id: {
    type: Number,
    required: true
  },
  data: {
    type: Array,
    required: true
  }
})

const chart = ref(null)

const createChart = () => {
  const traces = props.data.map(keyword => ({
    x: keyword.dates,
    y: keyword.ranks,
    type: 'scatter',
    mode: 'lines+markers',
    name: keyword.keyword
  }))

  const layout = {
    title: `SERP Data for ${props.type === 'tag' ? 'Tag' : 'Project'} #${props.id}`,
    xaxis: { title: 'Date' },
    yaxis: { title: 'Rank', autorange: 'reversed' }
  }

  Plotly.newPlot(chart.value, traces, layout)
}

onMounted(() => {
  createChart()
})

watch(() => props.data, () => {
  createChart()
})
</script>

<style scoped>
.chart-container {
  height: 500px;
}
</style>