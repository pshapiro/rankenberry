import { createRouter, createWebHistory } from 'vue-router'
import RankTable from '../components/RankTable.vue'
import AddKeywordDomain from '../components/AddKeywordDomain.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: RankTable
    },
    {
      path: '/add',
      name: 'add',
      component: AddKeywordDomain
    }
  ]
})

export default router