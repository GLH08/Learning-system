import { defineStore } from 'pinia'
import { ref } from 'vue'
import { questionsApi, Question, QuestionListQuery, QuestionStats } from '@/api/questions'

export const useQuestionStore = defineStore('question', () => {
  const questions = ref<Question[]>([])
  const currentQuestion = ref<Question | null>(null)
  const stats = ref<QuestionStats | null>(null)
  const loading = ref(false)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  
  const fetchQuestions = async (params: QuestionListQuery = {}) => {
    loading.value = true
    try {
      const response = await questionsApi.getQuestions(params)
      questions.value = response.data.items
      total.value = response.data.total
      page.value = response.data.page
      pageSize.value = response.data.pageSize
    } finally {
      loading.value = false
    }
  }
  
  const fetchQuestionStats = async () => {
    const response = await questionsApi.getQuestionStats()
    stats.value = response.data
  }
  
  const fetchQuestion = async (id: string) => {
    loading.value = true
    try {
      const response = await questionsApi.getQuestion(id)
      currentQuestion.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }
  
  const getQuestionById = async (id: string) => {
    return await fetchQuestion(id)
  }
  
  const createQuestion = async (data: any) => {
    const response = await questionsApi.createQuestion(data)
    return response.data
  }
  
  const updateQuestion = async (id: string, data: any) => {
    const response = await questionsApi.updateQuestion(id, data)
    return response.data
  }
  
  const deleteQuestion = async (id: string) => {
    await questionsApi.deleteQuestion(id)
  }
  
  const batchDeleteQuestions = async (ids: string[]) => {
    const response = await questionsApi.batchDeleteQuestions(ids)
    return response.data
  }

  const batchUpdateCategory = async (ids: string[], categoryId: string) => {
    const response = await questionsApi.batchUpdateCategory(ids, categoryId)
    return response.data
  }

  const exportQuestionsJSON = async (params: any) => {
    return await questionsApi.exportQuestionsJSON(params)
  }

  return {
    questions,
    currentQuestion,
    stats,
    loading,
    total,
    page,
    pageSize,
    fetchQuestions,
    fetchQuestionStats,
    fetchQuestion,
    getQuestionById,
    createQuestion,
    updateQuestion,
    deleteQuestion,
    batchDeleteQuestions,
    batchUpdateCategory,
    exportQuestionsJSON
  }
})
