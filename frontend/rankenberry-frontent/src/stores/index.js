import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = 'http://localhost:5001/api'

export const useMainStore = defineStore('main', {
  state: () => ({
    projects: [],
    keywords: [],
    rankData: []
  }),
  actions: {
    async fetchProjects() {
      try {
        const response = await axios.get(`${API_URL}/projects`)
        this.projects = response.data
      } catch (error) {
        console.error('Error fetching projects:', error)
        throw error
      }
    },
    async addProject(name, domain) {
      try {
        const response = await axios.post(`${API_URL}/projects`, { name, domain })
        this.projects.push(response.data)
        return response.data
      } catch (error) {
        console.error('Error adding project:', error)
        if (error.response && error.response.data) {
          throw new Error(error.response.data.detail || 'An error occurred')
        } else {
          throw error
        }
      }
    },
    async fetchKeywords(projectId) {
      try {
        const response = await axios.get(`${API_URL}/projects/${projectId}/keywords`)
        this.keywords = response.data
      } catch (error) {
        console.error('Error fetching keywords:', error)
        throw error
      }
    },
    async addKeyword(projectId, keyword) {
      try {
        const response = await axios.post(`${API_URL}/projects/${projectId}/keywords`, { keyword })
        this.keywords.push(response.data)
        return response.data
      } catch (error) {
        console.error('Error adding keyword:', error)
        throw error
      }
    },
    async fetchRankData() {
      try {
        const response = await axios.get(`${API_URL}/rankData`)
        this.rankData = response.data
      } catch (error) {
        console.error('Error fetching rank data:', error)
        throw error
      }
    },
    async fetchSerpData(projectId) {
      try {
        const response = await axios.post(`${API_URL}/fetch-serp-data/${projectId}`)
        await this.fetchRankData()
        return response.data
      } catch (error) {
        console.error('Error fetching SERP data:', error)
        throw error
      }
    },
    async fetchFullSerpData(serpDataId) {
      try {
        const response = await axios.get(`${API_URL}/serp-data/${serpDataId}`)
        const data = response.data
        if (typeof data.full_data === 'string') {
          try {
            data.full_data = JSON.parse(data.full_data)
          } catch (parseError) {
            console.error('Error parsing full_data:', parseError)
            data.full_data = {}
          }
        }
        console.log('Full SERP data response:', JSON.stringify(data, null, 2))
        return data
      } catch (error) {
        console.error('Error fetching full SERP data:', error)
        throw error
      }
    },
    async fetchSingleSerpData(keywordId) {
      try {
        const response = await axios.post(`${API_URL}/fetch-serp-data-single/${keywordId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching single SERP data:', error);
        throw error;
      }
    },
    async addKeywords(projectId, keywords) {
      try {
        const response = await axios.post(`${API_URL}/keywords`, { project_id: projectId, keywords })
        this.keywords = [...this.keywords, ...response.data]
        return response.data
      } catch (error) {
        console.error('Error adding keywords:', error)
        throw error
      }
    },
    async fetchSerpDataForKeywords(keywords) {
      for (const keyword of keywords) {
        await this.fetchSingleSerpData(keyword.id)
      }
      await this.fetchRankData()
    },
    async fetchKeywords() {
      try {
        const response = await axios.get(`${API_URL}/keywords`)
        this.keywords = response.data
      } catch (error) {
        console.error('Error fetching keywords:', error)
        throw error
      }
    },
    async deleteKeyword(keywordId) {
      try {
        await axios.delete(`${API_URL}/keywords/${keywordId}`)
        this.keywords = this.keywords.filter(kw => kw.id !== keywordId)
      } catch (error) {
        console.error('Error deleting keyword:', error)
        throw error
      }
    },
    async deactivateKeyword(keywordId) {
      try {
        await axios.put(`${API_URL}/keywords/${keywordId}/deactivate`)
        const index = this.keywords.findIndex(kw => kw.id === keywordId)
        if (index !== -1) {
          this.keywords[index].active = false
        }
      } catch (error) {
        console.error('Error deactivating keyword:', error)
        throw error
      }
    },
    async activateKeyword(keywordId) {
      try {
        await axios.put(`${API_URL}/keywords/${keywordId}/activate`)
        const index = this.keywords.findIndex(kw => kw.id === keywordId)
        if (index !== -1) {
          this.keywords[index].active = true
        }
      } catch (error) {
        console.error('Error activating keyword:', error)
        throw error
      }
    },
    async deleteAllKeywords(projectId) {
      try {
        await axios.delete(`${API_URL}/projects/${projectId}/keywords`)
        this.keywords = this.keywords.filter(kw => kw.project_id !== projectId)
      } catch (error) {
        console.error('Error deleting all keywords:', error)
        throw error
      }
    },
    async deleteRankData(id) {
      try {
        await axios.delete(`${API_URL}/serp_data/${id}`)
        this.rankData = this.rankData.filter(item => item.id !== id)
      } catch (error) {
        console.error('Error deleting rank data:', error)
        throw error
      }
    }
  }
})