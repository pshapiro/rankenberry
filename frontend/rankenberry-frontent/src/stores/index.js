import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = 'http://localhost:5001/api'

export const useMainStore = defineStore('main', {
  state: () => ({
    projects: [],
    keywords: [],
    rankData: [],
    tags: [],
    schedules: [],
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
    async fetchSerpData(projectId, tagId = null) {
      try {
        console.log(`Fetching SERP data for project ${projectId} and tag ${tagId}`);
        const payload = { tag_id: tagId };
        const response = await axios.post(`${API_URL}/fetch-serp-data/${projectId}`, payload);
        console.log('SERP data fetched successfully:', response.data);
        await this.fetchRankData();
        return response.data;
      } catch (error) {
        console.error('Error fetching SERP data:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
        }
        throw error;
      }
    },
    async fetchSerpDataByTag(tagId) {
      try {
        console.log(`Fetching SERP data for tag ${tagId}`)
        const response = await axios.post(`${API_URL}/fetch-serp-data-by-tag/${tagId}`)
        console.log('SERP data fetched successfully:', response.data)
        await this.fetchRankData()
        return response.data
      } catch (error) {
        console.error('Error fetching SERP data by tag:', error)
        if (error.response) {
          console.error('Response data:', error.response.data)
          console.error('Response status:', error.response.status)
        }
        throw error
      }
    },
    async fetchFullSerpData(keywordId) {
      try {
        const response = await axios.get(`${API_URL}/serp-data/keyword/${keywordId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching full SERP data:', error);
        throw error;
      }
    },
    async fetchSingleSerpData(keywordId) {
      try {
        console.log(`Fetching SERP data for keyword ID ${keywordId}`);
        const response = await axios.post(`${API_URL}/fetch-serp-data-single/${keywordId}`);
        console.log("SERP data response:", response.data);
        
        // Update the rankData state
        const index = this.rankData.findIndex(item => item.keyword_id === keywordId);
        if (index !== -1) {
          this.rankData[index] = response.data;
        } else {
          this.rankData.push(response.data);
        }
        
        // Force reactivity
        this.rankData = [...this.rankData];
        
        return response.data;
      } catch (error) {
        console.error('Error fetching single SERP data:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
          console.error('Response headers:', error.response.headers);
        }
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
        this.rankData = this.rankData.filter(item => item.keyword_id !== keywordId)
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
    async deleteRankData(serpDataId) {
      try {
        if (serpDataId === null || serpDataId === undefined) {
          throw new Error('Invalid SERP data ID');
        }
        await axios.delete(`${API_URL}/serp_data/${serpDataId}`);
        console.log(`SERP data with ID ${serpDataId} deleted successfully`);
        // Remove the deleted item from the local state
        this.rankData = this.rankData.filter(item => item.serp_data_id !== serpDataId);
      } catch (error) {
        console.error('Error deleting rank data:', error);
        throw error;
      }
    },
    async toggleProjectStatus(projectId) {
      try {
        const response = await axios.put(`${API_URL}/projects/${projectId}/toggle-status`)
        const updatedProject = response.data
        const index = this.projects.findIndex(p => p.id === projectId)
        if (index !== -1) {
          this.projects[index] = updatedProject
        }
      } catch (error) {
        console.error('Error toggling project status:', error)
        throw error
      }
    },
    async deleteProject(projectId) {
      try {
        await axios.delete(`${API_URL}/projects/${projectId}`)
        this.projects = this.projects.filter(p => p.id !== projectId)
        this.keywords = this.keywords.filter(k => k.project_id !== projectId)
      } catch (error) {
        console.error('Error deleting project:', error)
        throw error
      }
    },
    async fetchTags() {
      try {
        const response = await axios.get(`${API_URL}/tags`)
        this.tags = response.data
      } catch (error) {
        console.error('Error fetching tags:', error)
        throw error
      }
    },
    async createTag(name) {
      try {
        const response = await axios.post(`${API_URL}/tags`, { name })
        this.tags.push(response.data)
        return response.data
      } catch (error) {
        console.error('Error creating tag:', error)
        throw error
      }
    },
    async addTagToKeyword(keywordId, tagId) {
      try {
        await axios.post(`${API_URL}/keywords/${keywordId}/tags/${tagId}`)
      } catch (error) {
        console.error('Error adding tag to keyword:', error)
        throw error
      }
    },
    async removeTagFromKeyword(keywordId, tagId) {
      try {
        await axios.delete(`${API_URL}/keywords/${keywordId}/tags/${tagId}`)
      } catch (error) {
        console.error('Error removing tag from keyword:', error)
        throw error
      }
    },
    async deleteTag(tagId) {
      try {
        await axios.delete(`${API_URL}/tags/${tagId}`)
        this.tags = this.tags.filter(tag => tag.id !== tagId)
      } catch (error) {
        console.error('Error deleting tag:', error)
        throw error
      }
    },
    async bulkTagKeywords(keywordIds, tagId) {
      try {
        await axios.post(`${API_URL}/keywords/bulk-tag`, { keyword_ids: keywordIds, tag_id: tagId })
      } catch (error) {
        console.error('Error bulk tagging keywords:', error)
        throw error
      }
    },
    async getKeywordTags(keywordId) {
      try {
        const response = await axios.get(`${API_URL}/keywords/${keywordId}/tags`)
        return response.data
      } catch (error) {
        console.error('Error fetching keyword tags:', error)
        throw error
      }
    },
    async fetchKeywordHistory(keywordId) {
      try {
        const response = await axios.get(`${API_URL}/keyword-history/${keywordId}`)
        return response.data
      } catch (error) {
        console.error('Error fetching keyword history:', error)
        throw error
      }
    },
    async getSearchVolumeApiSource() {
      try {
        const response = await axios.get(`${API_URL}/search-volume-api-source`);
        console.log("Current API source:", response.data.api_source);
        return response.data.api_source;
      } catch (error) {
        console.error('Error fetching search volume API source:', error);
        throw error;
      }
    },
    async updateSearchVolumeApiSource(apiSource) {
      try {
        console.log("Sending data:", { api_source: apiSource });
        const response = await axios.post(`${API_URL}/search-volume-api-source`, { api_source: apiSource });
        console.log("Response:", response.data);
        return response.data;
      } catch (error) {
        console.error('Error updating search volume API source:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
          console.error('Response headers:', error.response.headers);
        }
        throw error;
      }
    },
    async fetchSchedules() {
      try {
        const response = await axios.get(`${API_URL}/schedules`)
        this.schedules = response.data
      } catch (error) {
        console.error('Error fetching schedules:', error)
        throw error
      }
    },
    async createSchedule(schedule) {
      try {
        const response = await axios.post(`${API_URL}/schedules`, schedule)
        this.schedules.push(response.data)
        return response.data
      } catch (error) {
        console.error('Error creating schedule:', error)
        throw error
      }
    },
    async deleteSchedule(id) {
      try {
        await axios.delete(`${API_URL}/schedules/${id}`)
        this.schedules = this.schedules.filter(s => s.id !== id)
      } catch (error) {
        console.error('Error deleting schedule:', error)
        throw error
      }
    },
    async runSchedule(id) {
      try {
        await axios.post(`${API_URL}/schedules/${id}/run`)
        // After running the schedule, fetch the updated schedules
        await this.fetchSchedules()
      } catch (error) {
        console.error('Error running schedule:', error)
        throw error
      }
    },
    async runScheduleIn1Minute(id) {
      try {
        await axios.post(`${API_URL}/schedules/${id}/run-in-1-minute`)
      } catch (error) {
        console.error('Error scheduling run in 1 minute:', error)
        throw error
      }
    }
  }
})