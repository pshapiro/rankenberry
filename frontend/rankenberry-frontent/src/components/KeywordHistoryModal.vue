<template>
  <div class="modal" :class="{ 'is-active': isOpen }">
    <div class="modal-background" @click="close"></div>
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Rank History for "{{ keyword }}"</p>
        <button class="delete" aria-label="close" @click="close"></button>
      </header>
      <section class="modal-card-body">
        <div class="field">
          <div class="control is-expanded">
            <div class="field is-grouped">
              <div class="control">
                <input
                  type="date"
                  v-model="dateRange.start"
                  class="input"
                  placeholder="Start Date"
                />
              </div>
              <div class="control">
                <input
                  type="date"
                  v-model="dateRange.end"
                  class="input"
                  placeholder="End Date"
                />
              </div>
            </div>
          </div>
        </div>
        <div ref="chart" class="chart-container"></div>
        <div class="table-container mt-4">
          <table class="table is-fullwidth is-striped is-hoverable">
            <thead>
              <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Rank</th>
                <th>Search Volume</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in sortedHistory" :key="index">
                <td>{{ formatDate(entry.date) }}</td>
                <td>{{ formatTime(entry.date) }}</td>
                <td>{{ entry.rank === -1 ? 'Not Ranked' : entry.rank }}</td>
                <td>{{ entry.search_volume === null ? '-' : entry.search_volume }}</td>
                <td>
                  <span v-if="index < sortedHistory.length - 1" :class="getChangeClass(entry.rank, sortedHistory[index + 1].rank)">
                    {{ getChangeText(entry.rank, sortedHistory[index + 1].rank) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="scroll-indicator">
            <span class="icon">
              <i class="fas fa-chevron-down"></i>
            </span>
            Scroll for more
          </div>
        </div>
        <button @click="exportHistory" class="button is-success mt-4">Export History</button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick, computed } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  isOpen: Boolean,
  keyword: String,
  keywordId: Number,
  history: Array
})

const emit = defineEmits(['close', 'export'])

const chart = ref(null)
const dateRange = ref({ start: null, end: null })

const close = () => {
  emit('close')
}

const exportHistory = () => {
  emit('export')
}

const filteredHistory = computed(() => {
  if (!dateRange.value.start || !dateRange.value.end) return props.history

  return props.history.filter(entry => {
    const entryDate = new Date(entry.date)
    entryDate.setHours(0, 0, 0, 0)

    const startDate = new Date(dateRange.value.start)
    startDate.setHours(0, 0, 0, 0)

    const endDate = new Date(dateRange.value.end)
    endDate.setHours(23, 59, 59, 999)

    return entryDate >= startDate && entryDate <= endDate
  })
})

const sortedHistory = computed(() => {
  return [...props.history].sort((a, b) => new Date(b.date) - new Date(a.date))
})

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

const createChart = () => {
  if (!filteredHistory.value || filteredHistory.value.length === 0) {
    console.log('No history data available')
    return
  }

  console.log('Original history:', filteredHistory.value)

  // Group data by date and find the best rank for each day
  const dailyBestRanks = filteredHistory.value.reduce((acc, entry) => {
    let date
    try {
      // Try to create a valid Date object
      date = new Date(entry.date)
      if (isNaN(date.getTime())) {
        console.warn(`Invalid date: ${entry.date}`)
        return acc
      }
      date = date.toISOString().split('T')[0]
    } catch (error) {
      console.warn(`Error processing date: ${entry.date}`, error)
      return acc
    }

    if (!acc[date] || (entry.rank !== -1 && (acc[date].rank === -1 || entry.rank < acc[date].rank))) {
      acc[date] = { date, rank: entry.rank, search_volume: entry.search_volume }
    }
    return acc
  }, {})

  console.log('Daily best ranks:', dailyBestRanks)

  // Ensure we have all dates from the first to the last
  const dates = Object.keys(dailyBestRanks).sort()
  console.log('Sorted dates:', dates)

  if (dates.length < 2) {
    console.log('Not enough valid data points for a line chart')
    return
  }

  const firstDate = new Date(dates[0])
  const lastDate = new Date(dates[dates.length - 1])

  const chartData = []
  for (let d = new Date(firstDate); d <= lastDate; d.setUTCDate(d.getUTCDate() + 1)) {
    const dateString = d.toISOString().split('T')[0]
    chartData.push({
      date: dateString,
      rank: dailyBestRanks[dateString] ? dailyBestRanks[dateString].rank : null,
      search_volume: dailyBestRanks[dateString] ? dailyBestRanks[dateString].search_volume : null
    })
  }

  console.log('Chart data:', chartData)

  const chartDates = chartData.map(entry => entry.date)
  const ranks = chartData.map(entry => entry.rank === -1 ? null : entry.rank)

  console.log('Dates for chart:', chartDates)
  console.log('Ranks for chart:', ranks)

  if (chartDates.length < 2) {
    console.log('Not enough data points for a line chart')
    return
  }

  const rankTrace = {
    x: chartDates,
    y: ranks,
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Rank',
    line: { color: '#3273dc' },
    yaxis: 'y1',
    connectgaps: false
  }

  const layout = {
    title: `Rank History for "${props.keyword}"`,
    xaxis: { 
      title: 'Date',
      type: 'date',
      tickformat: '%Y-%m-%d',
      range: [chartDates[0], chartDates[chartDates.length - 1]]
    },
    yaxis: { 
      title: 'Rank',
      autorange: 'reversed',
      rangemode: 'tozero',
    },
    autosize: true,
    margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 }
  }

  const config = {
    responsive: true,
    displayModeBar: false
  }

  nextTick(() => {
    Plotly.newPlot(chart.value, [rankTrace], layout, config)
  })
}

watch(dateRange, () => {
  createChart()
})

onMounted(() => {
  createChart()
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
})

const resizeChart = () => {
  Plotly.Plots.resize(chart.value)
}

watch(() => props.isOpen, (newValue) => {
  if (newValue) {
    nextTick(() => {
      createChart()
      window.addEventListener('resize', resizeChart)
    })
  } else {
    window.removeEventListener('resize', resizeChart)
  }
})
</script>

<style scoped>
.modal-card {
  width: 90%;
  max-width: 1200px;
}

.chart-container {
  height: 400px;
}

.table-container {
  position: relative;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #dbdbdb;
  border-radius: 4px;
}

/* Styles for WebKit browsers (Chrome, Safari, etc.) */
.table-container::-webkit-scrollbar {
  width: 12px;
  background-color: #F5F5F5;
}

.table-container::-webkit-scrollbar-thumb {
  border-radius: 10px;
  -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,.3);
  background-color: #555;
}

.table-container::-webkit-scrollbar-track {
  -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3);
  border-radius: 10px;
  background-color: #F5F5F5;
}

/* Styles for Firefox */
.table-container {
  scrollbar-width: thin;
  scrollbar-color: #555 #F5F5F5;
}

.table {
  width: 100%;
}

.table th {
  position: sticky;
  top: 0;
  background-color: white;
  z-index: 1;
}

.scroll-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  padding: 10px;
  background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,1));
  color: #888;
  font-size: 0.9em;
}

/* Ensure the scrollbar is visible on hover for macOS users */
.table-container:hover {
  overflow-y: scroll;
}

/* Ensure the modal body allows scrolling if needed */
.modal-card-body {
  max-height: 80vh;
  overflow-y: auto;
}
</style>