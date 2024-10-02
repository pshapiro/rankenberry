<template>
  <div class="rank-table">
    <h2 class="title is-2">Rank Table</h2>
    <div class="field is-grouped">
      <div class="control is-expanded">
        <div class="select is-fullwidth">
          <select v-model="selectedProject">
            <option value="">All Projects</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>
      </div>
      <div class="control is-expanded">
        <div class="select is-fullwidth">
          <select v-model="selectedTag">
            <option value="">All Tags</option>
            <option v-for="tag in tags" :key="tag.id" :value="tag.id">
              {{ tag.name }}
            </option>
          </select>
        </div>
      </div>
      <div class="control is-expanded">
        <div class="field is-grouped">
          <div class="control">
            <input
              type="date"
              v-model="dateRange.start"
              class="input"
            />
          </div>
          <div class="control">
            <input
              type="date"
              v-model="dateRange.end"
              class="input"
            />
          </div>
        </div>
      </div>
      <div class="control">
        <button @click="fetchSerpData" :disabled="!selectedProject && !selectedTag" class="button is-primary">
          Fetch Latest SERP Data
        </button>
      </div>
      <div class="control">
        <button @click="showShareOfVoice" class="button is-info" :disabled="!selectedProject">
          Share of Voice
        </button>
      </div>
    </div>

    <!-- New View Details Section -->
    <div class="box mt-4 mb-4">
      <h3 class="title is-4">View Details</h3>
      <div class="columns">
        <div class="column">
          <p><strong>Total Keywords:</strong> {{ latestRankData.length }}</p>
          <p><strong>Average Rank:</strong> {{ averageRank }}</p>
        </div>
        <div class="column">
          <p><strong>Keywords in Top 10:</strong> {{ keywordsInTop10 }}</p>
          <p><strong>Keywords Not Ranked:</strong> {{ keywordsNotRanked }}</p>
        </div>
        <div class="column">
          <p><strong>Selected Project:</strong> {{ selectedProjectName }}</p>
          <p><strong>Selected Tag:</strong> {{ selectedTagName }}</p>
        </div>
        <div class="column">
          <p><strong>Total Search Volume:</strong> {{ totalSearchVolume }}</p>
        </div>
      </div>
    </div>


    <table v-if="dataLoaded" class="table is-fullwidth is-striped is-hoverable">
      <thead>
        <tr>
          <th>Date</th>
          <th>Keyword</th>
          <th>Domain</th>
          <th>Rank</th>
          <th>Search Volume</th>
          <th>Change</th>
          <th>GSC Avg Position</th>
          <th>GSC Clicks</th>
          <th>GSC Impressions</th>
          <th>GSC CTR</th>
          <th>Actions</th>
          <th>Tags</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in paginatedRankData" :key="item.id">
          <!-- Date -->
          <td>{{ formatDate(item.date) }}</td>
          
          <!-- Keyword -->
          <td>{{ item.keyword }}</td>
          
          <!-- Domain -->
          <td>{{ item.domain }}</td>
          
          <!-- Rank -->
          <td>{{ item.rank === null || item.rank === -1 ? '-' : item.rank }}</td>
          
          <!-- Search Volume -->
          <td>{{ item.search_volume === null ? '-' : item.search_volume }}</td>
          
          <!-- Change (Rank Change with Arrows) -->
          <td>
            <span v-if="rankChanges[item.keyword_id] && rankChanges[item.keyword_id].length > 1">
              <span
                v-if="(item.rank === null || item.rank === -1) && rankChanges[item.keyword_id][1].rank !== null && rankChanges[item.keyword_id][1].rank !== -1"
                class="has-text-danger"
              >
                ▼ {{ rankChanges[item.keyword_id][1].rank }}
              </span>
              <span
                v-else-if="(item.rank !== null && item.rank !== -1) && (rankChanges[item.keyword_id][1].rank === null || rankChanges[item.keyword_id][1].rank === -1)"
                class="has-text-success"
              >
                ▲ {{ item.rank }}
              </span>
              <span
                v-else-if="item.rank !== null && item.rank !== -1 && rankChanges[item.keyword_id][1].rank !== null && rankChanges[item.keyword_id][1].rank !== -1"
              >
                <span v-if="item.rank < rankChanges[item.keyword_id][1].rank" class="has-text-success">
                  ▲ {{ rankChanges[item.keyword_id][1].rank - item.rank }}
                </span>
                <span v-else-if="item.rank > rankChanges[item.keyword_id][1].rank" class="has-text-danger">
                  ▼ {{ item.rank - rankChanges[item.keyword_id][1].rank }}
                </span>
                <span v-else>-</span>
              </span>
              <span v-else>-</span>
            </span>
            <span v-else>-</span>
          </td>

         <!-- GSC Avg Position -->
        <td>
          <span v-if="item.gscDataForDate">
            {{ item.gscDataForDate.position.toFixed(2) }}
            <span v-if="item.gscDataForDate.date !== item.date.split('T')[0]" class="has-text-grey">
              ({{ formatDate(item.gscDataForDate.date) }})
            </span>
          </span>
          <span v-else>-</span>
        </td>

          <!-- GSC Clicks -->
          <td>
            <span v-if="item.gscDataForDate">
              {{ item.gscDataForDate.clicks }}
            </span>
            <span v-else>-</span>
          </td>

          <!-- GSC Impressions -->
          <td>
            <span v-if="item.gscDataForDate">
              {{ item.gscDataForDate.impressions }}
            </span>
            <span v-else>-</span>
          </td>

          <!-- GSC CTR -->
          <td>
            <span v-if="item.gscDataForDate">
              {{ (item.gscDataForDate.ctr * 100).toFixed(2) }}%
            </span>
            <span v-else>-</span>
          </td>

          <!-- Actions -->
          <td>
            <div class="buttons">
              <button @click="viewDetails(item)" class="button is-small is-info">
                {{ selectedSerpData && selectedSerpData.id === item.id ? 'Hide Details' : 'View Details' }}
              </button>
              <button
                @click="fetchSingleSerpData(item)"
                :disabled="!item.keyword_id"
                class="button is-small is-primary"
              >
                Fetch New Data
              </button>
              <button @click="viewKeywordHistory(item)" class="button is-small is-warning">View History</button>
              <button @click="deleteRankData(item.id)" class="button is-small is-danger">Delete</button>
            </div>
          </td>
          
          <!-- Tags -->
          <td>
            <div class="tags">
              <span v-for="tag in item.tags" :key="tag.id" class="tag is-info is-small">
                {{ tag.name }}
              </span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="has-text-centered">
      <p>Loading data...</p>
    </div>
    <!-- Pagination -->
    <nav class="pagination is-centered" role="navigation" aria-label="pagination">
      <a class="pagination-previous" @click="previousPage" :disabled="currentPage === 1">Previous</a>
      <a class="pagination-next" @click="nextPage" :disabled="currentPage === totalPages">Next page</a>
      <ul class="pagination-list">
        <li v-for="page in displayedPages" :key="page">
          <a class="pagination-link" :class="{ 'is-current': page === currentPage }" @click="goToPage(page)">
            {{ page }}
          </a>
        </li>
      </ul>
    </nav>

    <!-- SERP Details Modal -->
    <div class="modal" :class="{ 'is-active': selectedSerpData }">
      <div class="modal-background" @click="closeSerpDetails"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <p class="modal-card-title">SERP Details for "{{ selectedKeyword }}"</p>
          <button class="delete" aria-label="close" @click="closeSerpDetails"></button>
        </header>
        <section class="modal-card-body">
          <SerpDetails v-if="selectedSerpData" :serpData="selectedSerpData" :keyword="selectedKeyword" />
        </section>
      </div>
    </div>

    <KeywordHistoryModal
      :is-open="isKeywordHistoryModalOpen"
      :keyword="selectedKeyword"
      :keyword-id="selectedKeywordId"
      :history="keywordHistory"
      @close="closeKeywordHistoryModal"
      @export="exportKeywordHistory"
    />

    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>

    <!-- Share of Voice Modal -->
    <div class="modal" :class="{ 'is-active': isShareOfVoiceModalOpen }">
      <div class="modal-background" @click="closeShareOfVoiceModal"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <p class="modal-card-title">Share of Voice</p>
          <button class="delete" aria-label="close" @click="closeShareOfVoiceModal"></button>
        </header>
        <section class="modal-card-body">
          <ShareOfVoiceChart
            :projectId="selectedProject ? parseInt(selectedProject) : null"
            :tagId="selectedTag"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useMainStore } from '../stores'
import { storeToRefs } from 'pinia'
import SerpDetails from './SerpDetails.vue'
import KeywordHistoryModal from './KeywordHistoryModal.vue'
import ShareOfVoiceChart from './ShareOfVoiceChart.vue'

const store = useMainStore()
const { rankData, projects, tags } = storeToRefs(store)
const selectedProject = ref(null)
const selectedTag = ref(null)
const selectedSerpData = ref(null)
const selectedKeyword = ref('')
const isLoading = ref(false)
const currentPage = ref(1)
const itemsPerPage = 10
const isKeywordHistoryModalOpen = ref(false)
const selectedKeywordId = ref(null)
const keywordHistory = ref([])
// const dateRange = ref({
//   start: '',
//   end: ''
// })

const dateRange = ref({
  start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  end: new Date().toISOString().split('T')[0],
});

console.log('Date Range:', dateRange.value);
const isShareOfVoiceModalOpen = ref(false)
const dataLoaded = ref(false) // New flag to indicate data loading status
const gscDataMap = ref({})


onMounted(async () => {
  await store.fetchProjects()
  await store.fetchRankData()
  await store.fetchTags()
  await loadKeywordTags()
  await fetchGscData()
  dataLoaded.value = true
})

const loadKeywordTags = async () => {
  for (const item of rankData.value) {
    item.tags = await store.getKeywordTags(item.keyword_id)
  }
}

const filteredRankData = computed(() => {
  let filtered = rankData.value;

  // Apply filters for selected project and tag
  if (selectedProject.value !== null) {
    filtered = filtered.filter(item => item.project_id === Number(selectedProject.value));
  }
  if (selectedTag.value !== null) {
    filtered = filtered.filter(item =>
      item.tags && item.tags.some(tag => tag.id === Number(selectedTag.value))
    );
  }

  // Apply date range filter
  if (dateRange.value.start && dateRange.value.end) {
    const startDate = new Date(dateRange.value.start);
    const endDate = new Date(dateRange.value.end);
    endDate.setHours(23, 59, 59, 999); // Include the entire end date

    filtered = filtered.filter(item => {
      const itemDate = new Date(item.date);
      return itemDate >= startDate && itemDate <= endDate;
    });
  }

  // Map to include GSC data
  return filtered.map(item => {
    const gscDataArray = gscDataMap.value[item.keyword_id] || [];
    const itemDateStr = item.date.split('T')[0]; // 'YYYY-MM-DD'
    const itemDate = new Date(itemDateStr);

    // Find GSC data for the same date
    let gscDataForDate = gscDataArray.find(gscEntry => gscEntry.date === itemDateStr);

    if (!gscDataForDate) {
      // Find the most recent GSC data prior to or on the rank date
      gscDataForDate = gscDataArray
        .filter(gscEntry => new Date(gscEntry.date) <= itemDate)
        .sort((a, b) => new Date(b.date) - new Date(a.date))[0];
    }

    return {
      ...item,
      gscDataForDate: gscDataForDate || null,
    };
  });
});

const latestRankData = computed(() => {
  const keywordMap = new Map()
  
  filteredRankData.value.forEach(item => {
    if (
      !keywordMap.has(item.keyword_id) ||
      new Date(item.date) > new Date(keywordMap.get(item.keyword_id).date)
    ) {
      keywordMap.set(item.keyword_id, item)
    }
  })
  
  return Array.from(keywordMap.values())
})

const paginatedRankData = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  return filteredRankData.value.slice(startIndex, endIndex)
})

const totalPages = computed(() => Math.ceil(filteredRankData.value.length / itemsPerPage))

const displayedPages = computed(() => {
  const range = 2
  let start = Math.max(1, currentPage.value - range)
  let end = Math.min(totalPages.value, currentPage.value + range)

  if (start > 1) {
    start = Math.max(1, end - range * 2)
  }
  if (end < totalPages.value) {
    end = Math.min(totalPages.value, start + range * 2)
  }

  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
})

const rankChanges = computed(() => {
  const changes = {}
  const sortedData = [...filteredRankData.value].sort((a, b) => new Date(b.date) - new Date(a.date))
  sortedData.forEach(item => {
    if (!changes[item.keyword_id]) {
      changes[item.keyword_id] = [item]
    } else if (changes[item.keyword_id].length < 2) {
      changes[item.keyword_id].push(item)
    }
  })
  return changes
})

const averageRank = computed(() => {
  if (latestRankData.value.length === 0) return 'N/A'
  const sum = latestRankData.value.reduce((acc, item) => {
    return acc + (item.rank !== null && item.rank !== -1 ? item.rank : 0)
  }, 0)
  return (sum / latestRankData.value.length).toFixed(2)
})

const keywordsInTop10 = computed(() => {
  return latestRankData.value.filter(item => {
    return item.rank !== null && item.rank !== -1 && item.rank <= 10
  }).length
})

const keywordsNotRanked = computed(() => {
  return latestRankData.value.filter(item => item.rank === null || item.rank === -1).length
})

const selectedProjectName = computed(() => {
  if (!selectedProject.value) return 'All Projects'
  const project = projects.value.find(p => p.id === selectedProject.value)
  return project ? project.name : 'Unknown Project'
})

const selectedTagName = computed(() => {
  if (!selectedTag.value) return 'All Tags'
  const tag = tags.value.find(t => t.id === selectedTag.value)
  return tag ? tag.name : 'Unknown Tag'
})

const totalSearchVolume = computed(() => {
  const uniqueKeywords = new Set(latestRankData.value.map(item => item.keyword_id))
  return Array.from(uniqueKeywords).reduce((sum, keywordId) => {
    const keyword = latestRankData.value.find(item => item.keyword_id === keywordId)
    return sum + (keyword && keyword.search_volume !== null ? keyword.search_volume : 0)
  }, 0)
})

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const goToPage = (page) => {
  currentPage.value = page
}

watch([selectedProject, selectedTag, dateRange], async () => {
  console.log('Date range changed:', dateRange.value);
  currentPage.value = 1;
  await loadKeywordTags();
  await fetchGscData();
});

const fetchSerpData = async () => {
  isLoading.value = true
  try {
    if (selectedProject.value) {
      await store.fetchSerpData(selectedProject.value, selectedTag.value)
    } else if (selectedTag.value) {
      await store.fetchSerpDataByTag(selectedTag.value)
    }
    await store.fetchRankData()
    console.log("Fetched rank data:", store.rankData)  // Add this line
    await fetchGscData() // Add this line
    await loadKeywordTags()
  } catch (error) {
    console.error('Error fetching SERP data:', error)
  } finally {
    isLoading.value = false
  }
}

const viewDetails = async (item) => {
  if (item && item.id) {
    if (selectedSerpData.value && selectedSerpData.value.id === item.id) {
      selectedSerpData.value = null
      selectedKeyword.value = ''
    } else {
      try {
        const fullSerpData = await store.fetchFullSerpData(item.id)
        console.log('Full SERP data fetched:', fullSerpData)
        selectedSerpData.value = fullSerpData
        console.log('Fetched SERP data:', selectedSerpData.value)
        selectedKeyword.value = item.keyword
      } catch (error) {
        console.error('Error fetching full SERP data:', error)
      }
    }
  } else {
    console.error('Invalid item or missing ID:', item)
  }
}

const fetchSingleSerpData = async (item) => {
  if (item && item.keyword_id) {
    isLoading.value = true
    try {
      await store.fetchSingleSerpData(item.keyword_id)
      await store.fetchRankData()
    } catch (error) {
      console.error('Error fetching single SERP data:', error)
    } finally {
      isLoading.value = false
    }
  } else {
    console.error('Invalid item or missing keyword_id:', item)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
};

const closeSerpDetails = () => {
  selectedSerpData.value = null
  selectedKeyword.value = ''
}

const deleteRankData = async (id) => {
  if (confirm('Are you sure you want to delete this rank data?')) {
    try {
      await store.deleteRankData(id)
      await store.fetchRankData()
    } catch (error) {
      console.error('Error deleting rank data:', error)
    }
  }
}

const viewKeywordHistory = async (item) => {
  selectedKeyword.value = item.keyword
  selectedKeywordId.value = item.keyword_id
  try {
    const history = await store.fetchKeywordHistory(item.keyword_id)
    console.log('Fetched history:', history)
    keywordHistory.value = history.sort((a, b) => new Date(b.date) - new Date(a.date)) // Sort by date, most recent first
    console.log('Sorted history:', keywordHistory.value)
    isKeywordHistoryModalOpen.value = true
  } catch (error) {
    console.error('Error fetching keyword history:', error)
    // You might want to show an error message to the user here
  }
}

const closeKeywordHistoryModal = () => {
  isKeywordHistoryModalOpen.value = false
  selectedKeyword.value = ''
  selectedKeywordId.value = null
  keywordHistory.value = []
}

const exportKeywordHistory = async () => {
  try {
    const csvContent = [
      ['Date', 'Time', 'Rank'].join(','),
      ...keywordHistory.value.map(entry => {
        const [date, time] = formatDateTime(entry.date)
        return [date, time, entry.rank === null || entry.rank === -1 ? 'Not Ranked' : entry.rank].join(',')
      })
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `keyword_history_${selectedKeyword.value}_${formatDate(new Date())}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  } catch (error) {
    console.error('Error exporting keyword history:', error)
  }
}

const formatDateTime = (dateTimeString) => {
  const date = new Date(dateTimeString)
  return [
    date.toLocaleDateString(),
    date.toLocaleTimeString()
  ]
}

const showShareOfVoice = () => {
  if (!selectedProject.value) {
    alert('Please select a project before viewing Share of Voice.');
    return;
  }
  isShareOfVoiceModalOpen.value = true;
};

const closeShareOfVoiceModal = () => {
  isShareOfVoiceModalOpen.value = false;
};

const fetchGscData = async () => {
  if (dateRange.value.start && dateRange.value.end) {
    try {
      const projectId = selectedProject.value ? parseInt(selectedProject.value) : null;
      const gscDataResponse = await store.fetchGscData(
        projectId,
        dateRange.value.start,
        dateRange.value.end
      );

      gscDataMap.value = {};
      gscDataResponse.forEach(item => {
        if (!gscDataMap.value[item.keyword_id]) {
          gscDataMap.value[item.keyword_id] = [];
        }
        gscDataMap.value[item.keyword_id].push(item);
      });
      console.log('GSC Data Map:', gscDataMap.value);
    } catch (error) {
      console.error('Error fetching GSC data:', error);
    }
  } else {
    console.warn('Date range is invalid.');
  }
};

// watch(filteredRankData, (newData) => {
//   console.log('Filtered Rank Data:', newData)
// })

watch(dateRange, (newRange) => {
  console.log('Date range changed:', newRange)
})
</script>

<style scoped>
@import 'v-calendar/dist/style.css';

.modal-card {
  width: 95%;
  max-width: 1200px;
}

.modal-card-body {
  padding: 20px;
  width: 100%;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.pagination-link.is-current {
  background-color: #3273dc;
  border-color: #3273dc;
  color: #fff;
}

/* Add some basic styling for the date picker */
.v-date-picker input {
  width: 120px;
}

.field.has-addons {
  flex-wrap: nowrap;
}
</style>