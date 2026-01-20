import { defineStore } from 'pinia'
import { ref } from 'vue'
import { wrongQuestionsApi, type WrongQuestion, type WrongQuestionsStats } from '@/api/wrongQuestions'

export const useWrongQuestionStore = defineStore('wrongQuestion', () => {
  const wrongQuestions = ref<WrongQuestion[]>([])
  const stats = ref<WrongQuestionsStats>({ total: 0, mastered: 0, unmastered: 0 })
  const loading = ref(false)

  // 获取错题列表
  async function fetchWrongQuestions(params?: {
    mastered?: number
    skip?: number
    limit?: number
  }) {
    loading.value = true
    try {
      wrongQuestions.value = await wrongQuestionsApi.listWrongQuestions(params)
    } finally {
      loading.value = false
    }
  }

  // 获取错题统计
  async function fetchStats() {
    stats.value = await wrongQuestionsApi.getStats()
  }

  // 标记为已掌握
  async function markAsMastered(id: string) {
    await wrongQuestionsApi.markAsMastered(id)
    const wq = wrongQuestions.value.find(w => w.id === id)
    if (wq) {
      wq.mastered = 1
    }
    await fetchStats()
  }

  // 取消掌握标记
  async function markAsUnmastered(id: string) {
    await wrongQuestionsApi.markAsUnmastered(id)
    const wq = wrongQuestions.value.find(w => w.id === id)
    if (wq) {
      wq.mastered = 0
    }
    await fetchStats()
  }

  // 删除错题
  async function deleteWrongQuestion(id: string) {
    await wrongQuestionsApi.deleteWrongQuestion(id)
    wrongQuestions.value = wrongQuestions.value.filter(w => w.id !== id)
    await fetchStats()
  }

  return {
    wrongQuestions,
    stats,
    loading,
    fetchWrongQuestions,
    fetchStats,
    markAsMastered,
    markAsUnmastered,
    deleteWrongQuestion
  }
})
