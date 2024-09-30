import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = 'http://localhost:5001/api'

export const useMainStore = defineStore('main', {
  state: () => ({
    projects: [],
    keywords: [],
    rankData: [],
    tags: [],
    gscDomains: [],
    gscDomain: null,
  }),
  actions: {
    async fetchProjects() {
      try {
        const response = await axios.get(`${API_URL}/projects`);
        this.projects = response.data; // Update the state variable
        return response.data;
      } catch (error) {
        console.error('Error fetching projects:', error);
        throw error;
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

    async addGSCDomain(domain, projectId) {
      try {
        const response = await axios.post(`${API_URL}/gsc/domains`, { domain, project_id: projectId });
        this.gscDomain = response.data.domain_id;
        return response.data.domain_id;
      } catch (error) {
        console.error('Error adding GSC domain:', error);
        throw error;
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
        console.log('Received rank data:', response.data)
        this.rankData = response.data.map(item => ({
          ...item,
          date: item.date ? new Date(item.date).toISOString() : null
        }))
      } catch (error) {
        console.error('Error fetching rank data:', error)
        throw error
      }
    },
    async fetchSerpData(projectId, tagId = null) {
      try {
        const payload = tagId ? { tag_id: tagId } : {};
        const response = await axios.post(`${API_URL}/fetch-serp-data/${projectId}`, payload);
        await this.fetchRankData();
        return response.data;
      } catch (error) {
        console.error('Error fetching SERP data:', error);
        throw error;
      }
    },
    
    async fetchSerpDataByTag(tagId) {
      try {
        const response = await axios.post(`${API_URL}/fetch-serp-data-by-tag/${tagId}`)
        await this.fetchRankData()
        return response.data
      } catch (error) {
        console.error('Error fetching SERP data by tag:', error)
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
        // After fetching, update the rankData state
        await this.fetchRankData();
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
    async fetchAllKeywords() {
      try {
        const response = await axios.get(`${API_URL}/keywords`);
        this.keywords = response.data; // Update the state
      } catch (error) {
        console.error('Error fetching all keywords:', error);
        throw error;
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
    },
    async toggleProjectStatus(projectId) {
      try {
        await axios.put(`${API_URL}/projects/${projectId}/toggle-status`)
        await this.fetchProjects() // Re-fetch to ensure state consistency
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
        return response.data || []
      } catch (error) {
        console.error(`Error fetching tags for keyword ID ${keywordId}:`, error)
        return []
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
    async fetchShareOfVoiceData(projectId, payload) {
      try {
        console.log('Sending request with data:', payload);
        const response = await axios.post(`${API_URL}/share-of-voice/${projectId}`, payload);
        console.log('Received response:', response.data);
        return response.data;
      } catch (error) {
        console.error('Error fetching share of voice data:', error);
        if (error.response) {
          console.log('Response status:', error.response.status);
          console.log('Response data:', error.response.data);
        }
        throw error;
      }
    },
    
  async fetchGSCDomains(projectId) {
    try {
      const response = await axios.get(`${API_URL}/gsc/domains`, {
        params: { project_id: projectId }
      });
      return response.data.domains;
    } catch (error) {
      console.error('Error fetching GSC domains:', error);
      throw error;
        }
    },

    async addGSCDomain(domain, projectId) {
      try {
        const response = await axios.post(`${API_URL}/gsc/domains`, { domain, project_id: projectId });
        return response.data.domain_id;
      } catch (error) {
        console.error('Error adding GSC domain:', error);
        throw error;
      }
    },

    async setGSCDomain(domainId, userId, projectId = null) {
      try {
          const payload = {
              user_id: userId,
              project_id: projectId
          };
          console.log('Sending payload:', payload);
          const response = await axios.put(`${API_URL}/gsc/domains/${domainId}`, payload);
          this.gscDomain = response.data.domain_id;
          return response.data;
      } catch (error) {
          console.error('Error setting GSC domain:', error);
          if (error.response) {
              console.error('Response data:', error.response.data);
          }
          throw error;
      }
    },

    async getGSCDomain(domainId) {
      try {
        const response = await axios.get(`${API_URL}/gsc/domains/${domainId}`);
        return response.data;
      } catch (error) {
        console.error('Error getting GSC domain:', error);
        throw error;
      }
    },

  fetchGscData: async (projectId, startDate, endDate) => {
    try {
      const params = { start_date: startDate, end_date: endDate };
      if (projectId) {
        params.project_id = projectId;
      }
      const response = await axios.get(`${API_URL}/gsc-data`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching GSC data:', error);
      throw error;
    }
  },

    async fetchCombinedData(projectId, startDate, endDate) {
      try {
        const response = await axios.post(`${API_URL}/fetch-serp-data/${projectId}`, {
          start_date: startDate,
          end_date: endDate
        })
        return response.data
      } catch (error) {
        console.error('Error fetching combined data:', error)
        throw error
      }
    },
    async setAuthenticated(value) {
      this.isAuthenticated = value
    },
    async getProject(projectId) {
      try {
        const response = await axios.get(`${API_URL}/projects/${projectId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching project:', error);
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          console.error('Error response:', error.response.data);
          console.error('Error status:', error.response.status);
        } else if (error.request) {
          // The request was made but no response was received
          console.error('Error request:', error.request);
        } else {
          // Something happened in setting up the request that triggered an Error
          console.error('Error message:', error.message);
        }
        throw error;
      }
    },

    async updateProject(projectId, projectData) {
      try {
        const response = await axios.put(`${API_URL}/projects/${projectId}`, projectData)
        const updatedProject = response.data
        const index = this.projects.findIndex(p => p.id === updatedProject.id)
        if (index !== -1) {
          this.projects[index] = updatedProject
        }
        return updatedProject
      } catch (error) {
        console.error('Error updating project:', error)
        throw error
      }
    }
  }
})