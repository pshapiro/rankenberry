import { createRouter, createWebHistory } from 'vue-router'
import RankTable from '../components/RankTable.vue'
import AddKeywordDomain from '../components/AddKeywordDomain.vue'
import KeywordManagement from '../components/KeywordManagement.vue'
import SchedulePull from '../components/SchedulePull.vue';
import OptionsPage from '../components/OptionsPage.vue'
import GSCDomainSelection from '../components/GSCDomainSelection.vue'
import GSCDomainSelector from '../components/GSCDomainSelector.vue'
import EditProject from '../components/EditProject.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Rank Table',
      component: RankTable,
      meta: { title: 'Rank Table' }
    },
    {
      path: '/add',
      name: 'Add Project/Keywords',
      component: AddKeywordDomain,
      meta: { title: 'Add Project/Keywords' }
    },
    {
      path: '/keyword-management',
      name: 'Keyword Management',
      component: KeywordManagement,
      meta: { title: 'Keyword Management' }
    },
    {
      path: '/schedule-pull',
      name: 'Schedule Pull',
      component: SchedulePull,
      meta: { title: 'Schedule' }
    },
    {
      path: '/options',
      name: 'Options',
      component: OptionsPage,
      meta: { title: 'Options' }
    },
    {
      path: '/api/gsc/oauth2callback',
      name: 'GoogleCallback',
      component: () => import('../components/GoogleCallback.vue')
    },
    {
      path: '/gsc-domain-selection',
      name: 'GSCDomainSelection',
      component: GSCDomainSelection
    },
    {
      path: '/gsc-domain-selector',
      name: 'GSCDomainSelector',
      component: GSCDomainSelector
    },
    {
      path: '/edit-project/:id',
      name: 'Edit Project',
      component: EditProject,
      props: route => ({ projectId: parseInt(route.params.id) }),
      meta: { title: 'Edit Project' }
    }
  ]
})

export default router