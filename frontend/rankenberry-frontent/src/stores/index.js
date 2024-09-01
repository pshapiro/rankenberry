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
        return response.data
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
    }
  }
})