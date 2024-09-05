<template>
  <div>
    <h2 class="title is-4">Share of Voice for {{ type === 'tag' ? 'Tag' : 'Project' }}</h2>
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

const calculateShareOfVoice = (rank) => {
  if (rank === null || rank === -1) return 0
  return Math.max(0, (10 - Math.min(rank, 10)) / 10) * 100
}

const createChart = () => {
  const shareOfVoice = props.data.map(keyword => ({
    keyword: keyword.keyword,
    sov: calculateShareOfVoice(keyword.rank)
  }))

  const trace = {
    x: shareOfVoice.map(item => item.keyword),
    y: shareOfVoice.map(item => item.sov),
    type: 'bar',
    name: 'Share of Voice'
  }

  const layout = {
    title: `Share of Voice for ${props.type === 'tag' ? 'Tag' : 'Project'} #${props.id}`,
    xaxis: { title: 'Keyword' },
    yaxis: { title: 'Share of Voice (%)' }
  }

  Plotly.newPlot(chart.value, [trace], layout)
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