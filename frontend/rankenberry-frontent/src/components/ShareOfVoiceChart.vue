<template>
  <div class="share-of-voice-chart">
    <h2 class="title is-2">Share of Voice</h2>
    <div class="field is-grouped">
      <div class="control">
        <input
          type="date"
          v-model="startDate"
          class="input"
          @change="updateDateRange"
        />
      </div>
      <div class="control">
        <input
          type="date"
          v-model="endDate"
          class="input"
          @change="updateDateRange"
        />
      </div>
    </div>
    
    <div v-if="isLoading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else-if="lineChartData.length > 0 && donutChartData.length > 0" class="charts">
      <div v-show="showCharts" class="chart-wrapper">
        <div ref="stackedBarChart" class="chart-container"></div>
      </div>
      <div v-show="showCharts" class="chart-wrapper">
        <div ref="donutChart" class="chart-container"></div>
      </div>
      <table class="table is-fullwidth is-striped is-hoverable">
        <thead>
          <tr>
            <th>Domain</th>
            <th>Share of Voice</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in topDonutChartData" :key="item.name">
            <td>{{ item.name }}</td>
            <td>{{ item.share.toFixed(2) }}%</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else>No data available for the selected date range.</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue';
import { useMainStore } from '../stores';
import Plotly from 'plotly.js-dist-min';

const props = defineProps({
  projectId: {
    type: Number,
    required: false
  },
  tagId: {
    type: [String, Number],
    default: ''
  }
});

const store = useMainStore();
const startDate = ref(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
const endDate = ref(new Date().toISOString().split('T')[0]);
const lineChartData = ref([]);
const donutChartData = ref([]);
const stackedBarChart = ref(null);
const donutChart = ref(null);
const isLoading = ref(false);
const error = ref(null);
const showCharts = ref(false);

const topDonutChartData = computed(() => {
  return [...donutChartData.value]
    .sort((a, b) => b.share - a.share)
    .slice(0, 10); // Show only top 10 domains
});

const updateDateRange = () => {
  fetchShareOfVoiceData();
};

const fetchShareOfVoiceData = async () => {
  if (props.projectId && startDate.value && endDate.value) {
    isLoading.value = true;
    error.value = null;
    showCharts.value = false;
    try {
      const response = await store.fetchShareOfVoiceData(props.projectId, {
        date_range: {
          start: startDate.value,
          end: endDate.value
        },
        tag_id: props.tagId
      });
      console.log('Full response:', response);

      lineChartData.value = response.lineChartData;
      donutChartData.value = response.donutChartData;
      showCharts.value = true;
      await nextTick();
      setTimeout(createCharts, 100); // Add a small delay before creating charts
    } catch (err) {
      console.error('Error fetching Share of Voice data:', err);
      error.value = 'Failed to fetch Share of Voice data. Please try again.';
    } finally {
      isLoading.value = false;
    }
  }
};

const createCharts = () => {
  console.log('Creating charts...');
  console.log('Stacked bar chart container:', stackedBarChart.value);
  console.log('Donut chart container:', donutChart.value);

  if (lineChartData.value.length === 0 || donutChartData.value.length === 0) {
    console.warn('Insufficient data to render charts.');
    return;
  }

  if (!stackedBarChart.value || !donutChart.value) {
    console.warn('Chart containers not ready.');
    return;
  }

  // Create Stacked Bar Chart
  const dates = lineChartData.value[0].dates;
  const topDomains = new Set(topDonutChartData.value.map(d => d.name));
  const filteredData = lineChartData.value.filter(domain => topDomains.has(domain.name));

  // Sort domains by their average share
  filteredData.sort((a, b) => {
    const avgA = a.shares.reduce((sum, share) => sum + share, 0) / a.shares.length;
    const avgB = b.shares.reduce((sum, share) => sum + share, 0) / b.shares.length;
    return avgB - avgA;
  });

  const traces = filteredData.map(domain => ({
    x: dates,
    y: domain.shares,
    type: 'bar',
    name: domain.name,
  }));

  const layout = {
    title: 'Share of Voice Over Time',
    barmode: 'stack',
    xaxis: { title: 'Date' },
    yaxis: { title: 'Share of Voice (%)', range: [0, 100] },
    autosize: true,
    margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 }
  };

  const config = {
    responsive: true,
    useResizeHandler: true,
  };

  Plotly.newPlot(stackedBarChart.value, traces, layout, config);

  // Create Donut Chart
  const donutData = [{
    values: topDonutChartData.value.map(domain => domain.share),
    labels: topDonutChartData.value.map(domain => domain.name),
    type: 'pie',
    hole: 0.4,
    textinfo: 'label+percent',
  }];

  const donutLayout = {
    title: 'Current Share of Voice',
    autosize: true,
    margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 }
  };

  Plotly.newPlot(donutChart.value, donutData, donutLayout, config);

  console.log('Charts created successfully.');
};

watch(() => props.projectId, fetchShareOfVoiceData);

onMounted(() => {
  if (props.projectId) {
    fetchShareOfVoiceData();
  }
  window.addEventListener('resize', () => {
    if (stackedBarChart.value && donutChart.value) {
      Plotly.Plots.resize(stackedBarChart.value);
      Plotly.Plots.resize(donutChart.value);
    }
  });
});

console.log('Plotly object:', Plotly);
</script>

<style scoped>
.share-of-voice-chart {
  width: 100%;
}

.charts {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.chart-wrapper {
  width: 100%;
  height: 400px;
}

.chart-container {
  width: 100%;
  height: 100%;
}
</style>