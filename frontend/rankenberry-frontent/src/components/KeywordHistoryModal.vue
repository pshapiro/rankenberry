<template>
    <div class="modal" :class="{ 'is-active': isOpen }">
      <div class="modal-background" @click="close"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <p class="modal-card-title">Rank History for "{{ keyword }}"</p>
          <button class="delete" aria-label="close" @click="close"></button>
        </header>
        <section class="modal-card-body">
          <div ref="chart" class="chart-container"></div>
          <div class="table-container mt-4">
            <table class="table is-fullwidth is-striped is-hoverable">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Rank</th>
                  <th>Change</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(entry, index) in history" :key="index">
                  <td>{{ formatDate(entry.date) }}</td>
                  <td>{{ formatTime(entry.date) }}</td>
                  <td>{{ entry.rank === null || entry.rank === -1 ? 'Not Ranked' : entry.rank }}</td>
                  <td>
                    <span v-if="index < history.length - 1" :class="getChangeClass(entry.rank, history[index + 1].rank)">
                      {{ getChangeText(entry.rank, history[index + 1].rank) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <button @click="exportHistory" class="button is-success mt-4">Export History</button>
        </section>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
  import Plotly from 'plotly.js-dist-min'

  const props = defineProps({
    isOpen: Boolean,
    keyword: String,
    keywordId: Number,
    history: Array
  })

  const emit = defineEmits(['close', 'export'])

  const chart = ref(null)

  const close = () => {
    emit('close')
  }

  const exportHistory = () => {
    emit('export')
  }

  const createChart = () => {
    if (!props.history || props.history.length === 0) return

    const dailyData = props.history.reduce((acc, entry) => {
      const date = new Date(entry.date).toISOString().split('T')[0]
      if (!acc[date] || new Date(entry.date) > new Date(acc[date].date)) {
        acc[date] = entry
      }
      return acc
    }, {})

    const sortedDailyData = Object.entries(dailyData)
      .sort(([dateA], [dateB]) => new Date(dateA) - new Date(dateB))
      .map(([date, entry]) => ({ date, rank: entry.rank }))

    const dates = sortedDailyData.map(entry => entry.date)
    const ranks = sortedDailyData.map(entry => entry.rank === null || entry.rank === -1 ? null : entry.rank)

    const trace = {
      x: dates,
      y: ranks,
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Rank',
      line: { color: '#3273dc' }
    }

    const layout = {
      title: `Rank History for "${props.keyword}"`,
      xaxis: { 
        title: 'Date',
        type: 'date',
        tickformat: '%Y-%m-%d'
      },
      yaxis: { 
        title: 'Rank',
        autorange: 'reversed',
        rangemode: 'tozero'
      },
      autosize: true,
      margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 }
    }

    const config = {
      responsive: true,
      displayModeBar: false // Hide the mode bar for a cleaner look
    }

    nextTick(() => {
      Plotly.newPlot(chart.value, [trace], layout, config)
      window.addEventListener('resize', resizeChart)
    })
  }

  const resizeChart = () => {
    Plotly.Plots.resize(chart.value)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString()
  }

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString()
  }

  const getChangeClass = (currentRank, previousRank) => {
    if (currentRank === null || currentRank === -1 || previousRank === null || previousRank === -1) return ''
    return currentRank < previousRank ? 'has-text-success' : currentRank > previousRank ? 'has-text-danger' : ''
  }

  const getChangeText = (currentRank, previousRank) => {
    if (currentRank === null || currentRank === -1 || previousRank === null || previousRank === -1) return '-'
    const change = previousRank - currentRank
    return change > 0 ? `▲${change}` : change < 0 ? `▼${Math.abs(change)}` : '-'
  }

  watch(() => props.history, createChart, { deep: true })

  onMounted(() => {
    createChart()
  })

  // Cleanup event listener on component unmount
  onUnmounted(() => {
    window.removeEventListener('resize', resizeChart)
  })
  </script>
  
  <style scoped>
  .modal-card {
    width: 90%;
    max-width: 1200px;
  }
  
  .chart-container {
    width: 100%;
    height: 400px; /* You can adjust this value as needed */
  }
  
  .table-container {
    max-height: 300px;
    overflow-y: auto;
    margin-top: 1rem;
  }
  </style>