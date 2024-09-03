<template>
  <div class="keyword-management">
    <h2 class="title is-2">Keyword Management</h2>
    <div v-if="isLoading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <div class="box">
        <h3 class="title is-4">Tag Management</h3>
        <div class="field has-addons">
          <div class="control is-expanded">
            <input v-model="newTagName" class="input" type="text" placeholder="New tag name">
          </div>
          <div class="control">
            <button @click="createTag" class="button is-primary">Add Tag</button>
          </div>
        </div>
        <div class="tags">
          <span v-for="tag in tags" :key="tag.id" class="tag is-info is-medium">
            {{ tag.name }}
            <button @click="deleteTag(tag.id)" class="delete"></button>
          </span>
        </div>
      </div>

      <div v-for="project in projects" :key="project.id" class="box">
        <div class="level">
          <div class="level-left">
            <h3 class="title is-3">{{ project.name }}</h3>
          </div>
          <div class="level-right">
            <div class="buttons">
              <button @click="toggleProjectStatus(project.id)" class="button is-warning is-small">
                {{ project.active ? 'Disable' : 'Enable' }}
              </button>
              <button @click="deleteProject(project.id)" class="button is-danger is-small">Delete</button>
            </div>
          </div>
        </div>
        <div class="field">
          <label class="checkbox">
            <input type="checkbox" v-model="selectAll[project.id]" @change="toggleAllKeywords(project.id)">
            Select All
          </label>
        </div>
        <div class="field has-addons">
          <div class="control">
            <div class="select">
              <select v-model="selectedBulkTag[project.id]">
                <option value="">Select tag to apply</option>
                <option v-for="tag in tags" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
              </select>
            </div>
          </div>
          <div class="control">
            <button @click="applyBulkTag(project.id)" class="button is-primary" :disabled="!selectedBulkTag[project.id]">Apply Tag</button>
          </div>
          <div class="control">
            <button @click="removeBulkTag(project.id)" class="button is-danger" :disabled="!selectedBulkTag[project.id]">Remove Tag</button>
          </div>
        </div>
        <table class="table is-fullwidth">
          <thead>
            <tr>
              <th></th>
              <th>Keyword</th>
              <th>Tags</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="keyword in projectKeywords[project.id]" :key="keyword.id" :class="{ 'has-background-grey-lighter': !keyword.active }">
              <td>
                <label class="checkbox">
                  <input type="checkbox" v-model="keyword.selected">
                </label>
              </td>
              <td>{{ keyword.keyword }}</td>
              <td>
                <div class="tags">
                  <span v-for="tag in keyword.tags" :key="tag.id" class="tag is-info">
                    {{ tag.name }}
                    <button @click="removeTagFromKeyword(keyword.id, tag.id)" class="delete is-small"></button>
                  </span>
                </div>
                <div class="field has-addons">
                  <div class="control">
                    <div class="select is-small">
                      <select v-model="keyword.selectedTag">
                        <option value="">Select tag</option>
                        <option v-for="tag in availableTags(keyword)" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
                      </select>
                    </div>
                  </div>
                  <div class="control">
                    <button @click="addTagToKeyword(keyword.id, keyword.selectedTag)" class="button is-primary is-small">Add Tag</button>
                  </div>
                </div>
              </td>
              <td>
                <div class="buttons">
                  <button v-if="keyword.active" @click="deactivateKeyword(keyword.id)" class="button is-warning is-small">Deactivate</button>
                  <button v-else @click="activateKeyword(keyword.id)" class="button is-success is-small">Activate</button>
                  <button @click="deleteKeyword(keyword.id)" class="button is-danger is-small">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <button @click="deleteAllKeywords(project.id)" class="button is-danger">Delete All Keywords</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useMainStore } from '../stores'
import { storeToRefs } from 'pinia'

const store = useMainStore()
const { projects, keywords, tags } = storeToRefs(store)

const isLoading = ref(false)
const error = ref(null)
const newTagName = ref('')
const selectAll = ref({})
const selectedBulkTag = ref({})

const projectKeywords = computed(() => {
  const keywordsByProject = {}
  projects.value.forEach(project => {
    keywordsByProject[project.id] = keywords.value
      .filter(kw => kw.project_id === project.id)
      .map(kw => ({ ...kw, selected: false }))
  })
  return keywordsByProject
})

onMounted(async () => {
  isLoading.value = true
  try {
    await store.fetchProjects()
    await store.fetchKeywords()
    await store.fetchTags()
    await loadKeywordTags()
    initializeSelectAll()
  } catch (err) {
    error.value = 'Error loading data. Please try again.'
    console.error('Error:', err)
  } finally {
    isLoading.value = false
  }
})

const loadKeywordTags = async () => {
  for (const keyword of keywords.value) {
    keyword.tags = await store.getKeywordTags(keyword.id)
    keyword.selectedTag = ''
  }
}

const initializeSelectAll = () => {
  projects.value.forEach(project => {
    selectAll.value[project.id] = false
    selectedBulkTag.value[project.id] = ''
  })
}

const availableTags = (keyword) => {
  return tags.value.filter(tag => !keyword.tags.some(kwTag => kwTag.id === tag.id))
}

const createTag = async () => {
  if (newTagName.value.trim()) {
    try {
      await store.createTag(newTagName.value.trim())
      newTagName.value = ''
    } catch (error) {
      console.error('Error creating tag:', error)
    }
  }
}

const deleteTag = async (tagId) => {
  if (confirm('Are you sure you want to delete this tag? It will be removed from all keywords.')) {
    try {
      await store.deleteTag(tagId)
      await loadKeywordTags()
    } catch (error) {
      console.error('Error deleting tag:', error)
    }
  }
}

const addTagToKeyword = async (keywordId, tagId) => {
  if (tagId) {
    try {
      await store.addTagToKeyword(keywordId, tagId)
      await loadKeywordTags()
    } catch (error) {
      console.error('Error adding tag to keyword:', error)
    }
  }
}

const removeTagFromKeyword = async (keywordId, tagId) => {
  try {
    await store.removeTagFromKeyword(keywordId, tagId)
    await loadKeywordTags()
  } catch (error) {
    console.error('Error removing tag from keyword:', error)
  }
}

const toggleAllKeywords = (projectId) => {
  projectKeywords.value[projectId].forEach(keyword => {
    keyword.selected = selectAll.value[projectId]
  })
}

const applyBulkTag = async (projectId) => {
  const selectedKeywordIds = projectKeywords.value[projectId]
    .filter(keyword => keyword.selected)
    .map(keyword => keyword.id)
  
  if (selectedKeywordIds.length > 0 && selectedBulkTag.value[projectId]) {
    try {
      await store.bulkTagKeywords(selectedKeywordIds, selectedBulkTag.value[projectId])
      await loadKeywordTags()
    } catch (error) {
      console.error('Error applying bulk tag:', error)
    }
  }
}

const removeBulkTag = async (projectId) => {
  const selectedKeywords = projectKeywords.value[projectId].filter(keyword => keyword.selected)
  
  if (selectedKeywords.length > 0 && selectedBulkTag.value[projectId]) {
    try {
      for (const keyword of selectedKeywords) {
        await store.removeTagFromKeyword(keyword.id, selectedBulkTag.value[projectId])
      }
      await loadKeywordTags()
    } catch (error) {
      console.error('Error removing bulk tag:', error)
    }
  }
}

// ... (existing methods for deactivateKeyword, activateKeyword, deleteKeyword, deleteAllKeywords, toggleProjectStatus, deleteProject)
</script>
