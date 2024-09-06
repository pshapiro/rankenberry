import { createRouter, createWebHistory } from 'vue-router'
import RankTable from '../components/RankTable.vue'
import AddKeywordDomain from '../components/AddKeywordDomain.vue'
import KeywordManagement from '../components/KeywordManagement.vue'
import ConfigureOptions from '../components/ConfigureOptions.vue'
import ScheduleManager from '../components/ScheduleManager.vue'

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
      path: '/configure',
      name: 'Configure Options',
      component: ConfigureOptions,
      meta: { title: 'Configure Options' }
    },
    {
      path: '/schedules',
      name: 'Schedules',
      component: ScheduleManager,
      meta: { title: 'Manage Schedules' }
    }
  ]
})

export default router