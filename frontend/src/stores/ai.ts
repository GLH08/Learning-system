import { defineStore } from 'pinia'
import { ref } from 'vue'
import { aiApi, AITask, AICompleteRequest, AIBatchCompleteRequest } from '@/api/ai'

export const useAIStore = defineStore('ai', () => {
  const tasks = ref<AITask[]>([])
  const currentTask = ref<AITask | null>(null)
  const loading = ref(false)
  
  const completeQuestion = async (data: AICompleteRequest) => {
    const response = await aiApi.completeQuestion(data)
    return response.data
  }
  
  const batchCompleteQuestions = async (data: AIBatchCompleteRequest) => {
    const response = await aiApi.batchCompleteQuestions(data)
    return response.data
  }
  
  const fetchTasks = async (status?: string) => {
    loading.value = true
    try {
      const response = await aiApi.getTasks(status)
      tasks.value = response.data.items
      return response.data
    } finally {
      loading.value = false
    }
  }
  
  const fetchTask = async (id: string) => {
    loading.value = true
    try {
      const response = await aiApi.getTask(id)
      currentTask.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }
  
  const pauseTask = async (id: string) => {
    const response = await aiApi.pauseTask(id)
    return response.data
  }
  
  const resumeTask = async (id: string) => {
    const response = await aiApi.resumeTask(id)
    return response.data
  }
  
  const cancelTask = async (id: string) => {
    const response = await aiApi.cancelTask(id)
    return response.data
  }
  
  const generateReport = async (examId: string) => {
    const response = await aiApi.generateReport(examId)
    return response.data
  }
  
  return {
    tasks,
    currentTask,
    loading,
    completeQuestion,
    batchCompleteQuestions,
    fetchTasks,
    fetchTask,
    pauseTask,
    resumeTask,
    cancelTask,
    generateReport
  }
})
