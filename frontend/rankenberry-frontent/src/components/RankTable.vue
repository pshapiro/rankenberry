<template>
  <div class="rank-table">
    <h2 class="title is-2">Rank Table</h2>
    <div class="field is-grouped">
      <!-- Project Selector -->
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

      <!-- Tag Selector -->
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

      <!-- Date Range Picker -->
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

      <!-- Fetch SERP Data Button -->
      <div class="control">
        <button @click="fetchSerpData" :disabled="!selectedProject && !selectedTag" class="button is-primary">
          Fetch Latest SERP Data
        </button>
      </div>

      <!-- Share of Voice Button -->
      <div class="control">
        <button @click="showShareOfVoice" class="button is-info" :disabled="!selectedProject">
          Share of Voice
        </button>
      </div>
    </div>

    <!-- View Details Section -->
    <div class="box mt-4 mb-4">
      <h3 class="title is-4">Summary</h3>
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
          <p><strong>Total Search Volume:</strong> {{ formatNumber(totalSearchVolume) }}</p>
        </div>
      </div>
    </div>

    <!-- Rank Data Table -->
    <table v-if="dataLoaded" class="table is-fullwidth is-striped is-hoverable">
      <thead>
        <tr>
          <th>Date</th>
          <th>Keyword</th>
          <th>Domain</th>
          <th>Rank</th>
          <th>Estimated Business Impact</th>
          <th>Search Volume</th>
          <th>Rank Change</th>
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
          <td>{{ formatRank(item.rank) }}</td>

          <!-- Estimated Business Impact Column -->
          <td>
            {{ formatCurrency(item.estimated_business_impact) }}
            <span v-if="typeof item.estimated_business_impact_change === 'number' && !isNaN(item.estimated_business_impact_change)">
              (<span :class="{
                'has-text-success': item.estimated_business_impact_change > 0,
                'has-text-danger': item.estimated_business_impact_change < 0,
                'has-text-grey': item.estimated_business_impact_change === 0
              }">
                {{ formatChange(item.estimated_business_impact_change) }}
              </span>)
            </span>
          </td>

          <!-- Search Volume -->
          <td>{{ item.search_volume === null ? '-' : formatNumber(item.search_volume) }}</td>
          <!-- Rank Change Column -->
          <td>
            <span v-if="typeof item.rankChange === 'number' && !isNaN(item.rankChange)">
              <span :class="{
                'has-text-success': item.rankChange > 0,
                'has-text-danger': item.rankChange < 0,
                'has-text-grey': item.rankChange === 0
              }">
                <span v-if="item.rankChange > 0">▲ {{ Math.abs(item.rankChange) }}</span>
                <span v-else-if="item.rankChange < 0">▼ {{ Math.abs(item.rankChange) }}</span>
                <span v-else>-</span>
              </span>
            </span>
            <span v-else>-</span>
          </td>

          <!-- GSC Avg Position Column -->
          <td>
            <span v-if="item.gscDataForDate && typeof item.gscDataForDate.position === 'number'">
              {{ item.gscDataForDate.position.toFixed(2) }}
              <span v-if="item.dataSourceDate && item.dataSourceDate !== formatDate(item.date)">
                <em>(Derived from {{ formatDate(item.dataSourceDate) }})</em>
              </span>
            </span>
            <span v-else>
              -
              <em>(keyword_id: {{ item.keyword_id }}, date: {{ formatDate(item.date) }})</em>
            </span>
          </td>

          <!-- GSC Clicks -->
          <td>
            <span v-if="item.gscDataForDate">
              {{ formatNumber(item.gscDataForDate.clicks) }}
            </span>
            <span v-else>-</span>
          </td>

          <!-- GSC Impressions -->
          <td>
            <span v-if="item.gscDataForDate">
              {{ formatNumber(item.gscDataForDate.impressions) }}
            </span>
            <span v-else>-</span>
          </td>

          <!-- GSC CTR -->
          <td>
            <span v-if="item.gscDataForDate && typeof item.gscDataForDate.ctr === 'number'">
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

    <!-- Loading Indicator -->
    <div v-else class="has-text-centered">
      <p>Loading data...</p>
    </div>

  <!-- Pagination Controls -->
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

    <!-- Keyword History Modal -->
    <KeywordHistoryModal
      :is-open="isKeywordHistoryModalOpen"
      :keyword="selectedKeyword"
      :keyword-id="selectedKeywordId"
      :history="keywordHistory"
      @close="closeKeywordHistoryModal"
      @export="exportKeywordHistory"
    />

    <!-- Loading Overlay -->
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

// Initialize the main store
const store = useMainStore()
const { rankData, projects, tags } = storeToRefs(store)

// Reactive variables
const selectedProject = ref('')
const selectedTag = ref('')
const selectedSerpData = ref(null)
const selectedKeyword = ref('')
const isLoading = ref(false)
const currentPage = ref(1)
const itemsPerPage = 10
const isKeywordHistoryModalOpen = ref(false)
const selectedKeywordId = ref(null)
const keywordHistory = ref([])

// Date Range with default to last 7 days
const dateRange = ref({
  start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  end: new Date().toISOString().split('T')[0],
})
// const dateRange = ref({
//   start: '2020-01-01', // or any date that includes all your data
//   end: new Date().toISOString().split('T')[0],
// });

// Additional reactive variables
const isShareOfVoiceModalOpen = ref(false)
const dataLoaded = ref(false)
const gscDataMap = ref({})

// Load tags for each keyword
const loadKeywordTags = async () => {
  for (const item of rankData.value) {
    item.tags = await store.getKeywordTags(item.keyword_id)
  }
}

// Computed property to filter and sort rank data based on selected filters
const filteredRankData = computed(() => {
  let filtered = rankData.value

  // Apply Project Filter
  if (selectedProject.value) {
    filtered = filtered.filter(item => item.project_id === Number(selectedProject.value))
  }

  // Apply Tag Filter
  if (selectedTag.value) {
    filtered = filtered.filter(item =>
      item.tags && item.tags.some(tag => tag.id === Number(selectedTag.value))
    )
  }

  // Apply Date Range Filter
  if (dateRange.value.start && dateRange.value.end) {
    const start = new Date(dateRange.value.start)
    const end = new Date(dateRange.value.end)
    end.setHours(23, 59, 59, 999) // Include the entire end date
    console.log('Date Range Start:', start)
    console.log('Date Range End:', end)
    filtered = filtered.filter(item => {
      const itemDate = new Date(item.date)
      const isInRange = itemDate >= start && itemDate <= end
      console.log(`Item Date ${itemDate} is in range:`, isInRange)
      return isInRange
    })
  }

  // Sort descending by date
  filtered = filtered.sort((a, b) => new Date(b.date) - new Date(a.date))
  console.log('filteredRankData length:', filtered.length);

  return filtered
})

// Computed property to get the latest rank data per keyword
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

  console.log('latestRankData length:', Array.from(keywordMap.values()).length);
  return Array.from(keywordMap.values())
})

// Rank Changes for indicators
const rankChanges = computed(() => {
  const changes = {};
  filteredRankData.value.forEach(item => {
    if (!changes[item.keyword_id]) {
      changes[item.keyword_id] = [item];
    } else {
      changes[item.keyword_id].push(item);
    }
  });
  // Ensure the changes are sorted by date in descending order
  Object.keys(changes).forEach(keywordId => {
    changes[keywordId].sort((a, b) => new Date(b.date) - new Date(a.date));
  });
  return changes;
});

// Computed statistics
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
  const project = projects.value.find(p => p.id === Number(selectedProject.value))
  return project ? project.name : 'Unknown Project'
})

const selectedTagName = computed(() => {
  if (!selectedTag.value) return 'All Tags'
  const tag = tags.value.find(t => t.id === Number(selectedTag.value))
  return tag ? tag.name : 'Unknown Tag'
})

const totalSearchVolume = computed(() => {
  const uniqueKeywords = new Set(latestRankData.value.map(item => item.keyword_id))
  return Array.from(uniqueKeywords).reduce((sum, keywordId) => {
    const keyword = latestRankData.value.find(item => item.keyword_id === keywordId)
    return sum + (keyword && keyword.search_volume !== null ? keyword.search_volume : 0)
  }, 0)
})

// Pagination Controls
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

// Watchers to refetch data on filter changes
watch([selectedProject, selectedTag, dateRange], () => {
  console.log('Filters changed. Current Page reset to 1.')
  currentPage.value = 1
})

// Fetch SERP Data
const fetchSerpData = async () => {
  isLoading.value = true
  try {
    if (selectedProject.value) {
      await store.fetchSerpData(selectedProject.value, selectedTag.value)
    } else if (selectedTag.value) {
      await store.fetchSerpDataByTag(selectedTag.value)
    }
    await store.fetchRankData()
    console.log("Fetched rank data:", store.rankData)
    await fetchGscData()
    await loadKeywordTags()
  } catch (error) {
    console.error('Error fetching SERP data:', error)
    alert('Failed to fetch SERP data. Please try again later.')
  } finally {
    isLoading.value = false
  }
}

// View SERP Details Modal
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

// Fetch Data for a Single Keyword
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

// Utility Functions
const formatCurrency = (value) => {
  if (typeof value !== 'number' || isNaN(value)) return '-';
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return formatter.format(value);
};

const formatNumber = (value) => {
  if (typeof value !== 'number') return '-'
  return new Intl.NumberFormat('en-US').format(value)
}

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const formatChange = (value) => {
  if (typeof value !== 'number' || isNaN(value)) {
    return '-';
  }
  const formatted = `${value > 0 ? '+' : ''}${formatCurrency(value)}`;
  return formatted;
};

const formatRank = (rank) => {
  return rank === null || rank === -1 ? '-' : rank
}

// Close SERP Details Modal
const closeSerpDetails = () => {
  selectedSerpData.value = null
  selectedKeyword.value = ''
}

// Delete Rank Data Entry
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

// View Keyword History Modal
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
    // Optionally, display an error message to the user
  }
}

// Close Keyword History Modal
const closeKeywordHistoryModal = () => {
  isKeywordHistoryModalOpen.value = false
  selectedKeyword.value = ''
  selectedKeywordId.value = null
  keywordHistory.value = []
}

// Export Keyword History to CSV
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
    // Optionally, display an error message to the user
  }
}

// Helper to format DateTime String
const formatDateTime = (dateTimeString) => {
  const date = new Date(dateTimeString)
  return [
    date.toLocaleDateString(),
    date.toLocaleTimeString()
  ]
}

// Show Share of Voice Modal
const showShareOfVoice = () => {
  if (!selectedProject.value) {
    alert('Please select a project before viewing Share of Voice.')
    return
  }
  isShareOfVoiceModalOpen.value = true
}

// Close Share of Voice Modal
const closeShareOfVoiceModal = () => {
  isShareOfVoiceModalOpen.value = false
}

// Fetch GSC Data
const fetchGscData = async () => {
  if (dateRange.value.start && dateRange.value.end && selectedProject.value) {
    try {
      const filters = {
        project_id: parseInt(selectedProject.value),
        start_date: dateRange.value.start,
        end_date: dateRange.value.end,
      };
      const gscData = await store.fetchGscData(filters);
      console.log('Fetched GSC data:', gscData);

      // Create a map of GSC data by keyword_id and date
      const gscDataMap = {};
      gscData.forEach(item => {
        if (!gscDataMap[item.keyword_id]) {
          gscDataMap[item.keyword_id] = {};
        }
        gscDataMap[item.keyword_id][item.date] = item;
      });
      console.log('GSC data map:', gscDataMap);

      // Associate GSC data with rank data
      rankData.value = rankData.value.map(item => {
        const itemDate = new Date(item.date).toISOString().split('T')[0];
        const gscDataForDate = gscDataMap[item.keyword_id] && gscDataMap[item.keyword_id][itemDate];
        console.log(`Associating GSC data for keyword_id ${item.keyword_id} on ${itemDate}:`, gscDataForDate);
        return {
          ...item,
          gscDataForDate: gscDataForDate || null
        };
      });

      console.log('Updated rank data with GSC:', rankData.value);
    } catch (error) {
      console.error('Error fetching GSC data:', error);
    }
  } else {
    console.warn('No project selected. Skipping GSC data fetch.');
  }
};

const latestRankDataWithChange = computed(() => {
  const keywordMap = new Map();

  filteredRankData.value.forEach(item => {
    const keywordId = item.keyword_id;
    if (!keywordMap.has(keywordId) || new Date(item.date) > new Date(keywordMap.get(keywordId).date)) {
      keywordMap.set(keywordId, item);
    }
  });

  const result = Array.from(keywordMap.values()).map(item => {
    const keywordId = item.keyword_id;
    const changes = rankChanges.value[keywordId];
    let estimated_business_impact_change = null;
    let rankChange = null;

    if (changes && changes.length > 1) {
      const previousItem = changes[1];
      const currentImpact = item.estimated_business_impact;
      const previousImpact = previousItem.estimated_business_impact;

      if (
        typeof currentImpact === 'number' &&
        typeof previousImpact === 'number'
      ) {
        // Always calculate absolute change
        estimated_business_impact_change = currentImpact - previousImpact;
      }

      // Calculate rank change (as before)
      const currentRank = item.rank;
      const previousRank = previousItem.rank;

      if (
        currentRank !== null && currentRank !== -1 &&
        previousRank !== null && previousRank !== -1
      ) {
        rankChange = previousRank - currentRank;
      } else if (
        (currentRank === null || currentRank === -1) &&
        previousRank !== null && previousRank !== -1
      ) {
        rankChange = -previousRank;
      } else if (
        currentRank !== null && currentRank !== -1 &&
        (previousRank === null || previousRank === -1)
      ) {
        rankChange = currentRank;
      } else {
        rankChange = null;
      }
    }

    return {
      ...item,
      estimated_business_impact_change,
      rankChange,
    };
  });

  return result;
});

// Pagination
const paginatedRankData = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  return filteredRankDataWithChange.value.slice(startIndex, endIndex);
});

const totalPages = computed(() => {
  const totalItems = filteredRankDataWithChange.value.length;
  const pages = Math.ceil(totalItems / itemsPerPage);
  console.log('Total Items:', totalItems, 'Total Pages:', pages);
  return pages;
});

const filteredRankDataWithChange = computed(() => {
  const changes = {};

  // Group entries by keyword and sort them by date ascending
  filteredRankData.value.forEach(item => {
    const keywordId = item.keyword_id;
    if (!changes[keywordId]) {
      changes[keywordId] = [];
    }
    changes[keywordId].push(item);
  });

  Object.keys(changes).forEach(keywordId => {
    changes[keywordId].sort((a, b) => new Date(a.date) - new Date(b.date));
  });

  // Calculate rankChange and estimated_business_impact_change for each entry
  const result = [];
  Object.values(changes).forEach(entries => {
    for (let i = 0; i < entries.length; i++) {
      const currentItem = entries[i];
      const previousItem = entries[i - 1];
      let rankChange = null;
      let estimated_business_impact_change = null;

      if (previousItem) {
        // Rank change calculation
        const currentRank = currentItem.rank;
        const previousRank = previousItem.rank;

        if (
          currentRank !== null && currentRank !== -1 &&
          previousRank !== null && previousRank !== -1
        ) {
          rankChange = previousRank - currentRank;
        } else if (
          (currentRank === null || currentRank === -1) &&
          previousRank !== null && previousRank !== -1
        ) {
          rankChange = -previousRank;
        } else if (
          currentRank !== null && currentRank !== -1 &&
          (previousRank === null || previousRank === -1)
        ) {
          rankChange = currentRank;
        }

        // Estimated business impact change calculation
        const currentImpact = currentItem.estimated_business_impact;
        const previousImpact = previousItem.estimated_business_impact;

        if (
          typeof currentImpact === 'number' &&
          typeof previousImpact === 'number'
        ) {
          estimated_business_impact_change = currentImpact - previousImpact;
        }
      }

      result.push({
        ...currentItem,
        rankChange,
        estimated_business_impact_change,
      });
    }
  });

  // **Sort the result by date descending**
  result.sort((a, b) => new Date(b.date) - new Date(a.date));

  return result;
});

// Displayed Pages for Pagination Controls
const displayedPages = computed(() => {
  const range = 2;
  let start = Math.max(1, currentPage.value - range);
  let end = Math.min(totalPages.value, currentPage.value + range);

  if (end - start < range * 2) {
    start = Math.max(1, end - range * 2);
  }
  if (end - start < range * 2) {
    end = Math.min(totalPages.value, start + range * 2);
  }

  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
});

const paginatedRankDataWithChange = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  return latestRankDataWithChange.value.slice(startIndex, endIndex);
});

console.log('Total rankData entries:', rankData.value.length);
console.log('Filtered entries:', filteredRankData.value.length);
console.log('Unique keywords:', new Set(filteredRankData.value.map(item => item.keyword_id)).size);
console.log('latestRankDataWithChange length:', latestRankDataWithChange.value.length);
console.log('Filtered Rank Data with Changes:', filteredRankDataWithChange.value);

onMounted(async () => {
  await store.fetchProjects();
  await store.fetchRankData();
  await store.fetchTags();
  await loadKeywordTags();

  if (selectedProject.value) {
    await fetchGscData();
  }

  dataLoaded.value = true;
});

watch([dateRange, selectedProject], async () => {
  if (selectedProject.value) {
    await fetchGscData();
  }
});
</script>

<style scoped>
.rank-table {
  padding: 20px;
}

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

.field.has-addons {
  flex-wrap: nowrap;
}
</style>