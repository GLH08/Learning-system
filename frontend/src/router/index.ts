import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue')
        },
        {
          path: 'questions',
          name: 'QuestionList',
          component: () => import('@/views/questions/QuestionList.vue')
        },
        {
          path: 'questions/create',
          name: 'QuestionCreate',
          component: () => import('@/views/questions/QuestionCreate.vue')
        },
        {
          path: 'questions/:id',
          name: 'QuestionDetail',
          component: () => import('@/views/questions/QuestionDetail.vue')
        },
        {
          path: 'questions/:id/edit',
          name: 'QuestionEdit',
          component: () => import('@/views/questions/QuestionEdit.vue')
        },
        {
          path: 'questions/import',
          name: 'QuestionImport',
          component: () => import('@/views/questions/QuestionImport.vue')
        },
        {
          path: 'categories',
          name: 'CategoryManage',
          component: () => import('@/views/questions/CategoryManage.vue')
        },
        {
          path: 'ai/tasks',
          name: 'AITaskList',
          component: () => import('@/views/ai/AITaskList.vue')
        },
        {
          path: 'ai/batch-complete',
          name: 'AIBatchComplete',
          component: () => import('@/views/ai/AIBatchComplete.vue')
        },
        {
          path: 'exams',
          name: 'ExamList',
          component: () => import('@/views/exams/ExamList.vue')
        },
        {
          path: 'exams/config',
          name: 'ExamConfig',
          component: () => import('@/views/exams/ExamConfig.vue')
        },
        {
          path: 'exams/:id/answer',
          name: 'ExamAnswer',
          component: () => import('@/views/exams/ExamAnswer.vue')
        },
        {
          path: 'exams/:id/result',
          name: 'ExamResult',
          component: () => import('@/views/exams/ExamResult.vue')
        },
        {
          path: 'wrong-questions',
          name: 'WrongQuestionList',
          component: () => import('@/views/wrong-questions/WrongQuestionList.vue')
        },
        {
          path: 'stats',
          name: 'StatsOverview',
          component: () => import('@/views/stats/StatsOverview.vue')
        },
        {
          path: 'settings',
          name: 'SystemSettings',
          component: () => import('@/views/settings/SystemSettings.vue')
        }
      ]
    }
  ]
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth !== false) {
    // Check if user is authenticated
    if (!userStore.token) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    
    // Verify token
    const isValid = await userStore.checkAuth()
    if (!isValid) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }
  
  next()
})

export default router
