import { defineStore } from 'pinia'
import { ref } from 'vue'
import { examsApi, type Exam, type ExamQuestionsResponse, type QuickExamRequest, type CustomExamRequest, type GradingResult } from '@/api/exams'

export const useExamStore = defineStore('exam', () => {
  const exams = ref<Exam[]>([])
  const currentExam = ref<ExamQuestionsResponse | null>(null)
  const loading = ref(false)

  // 快速组卷
  async function generateQuickExam(data: QuickExamRequest) {
    loading.value = true
    try {
      const exam = await examsApi.generateQuickExam(data)
      return exam
    } finally {
      loading.value = false
    }
  }

  // 自定义组卷
  async function generateCustomExam(data: CustomExamRequest) {
    loading.value = true
    try {
      const exam = await examsApi.generateCustomExam(data)
      return exam
    } finally {
      loading.value = false
    }
  }

  // 获取考试列表
  async function fetchExams(params?: {
    status?: string
    mode?: string
    skip?: number
    limit?: number
  }) {
    loading.value = true
    try {
      exams.value = await examsApi.listExams(params)
    } finally {
      loading.value = false
    }
  }

  // 获取考试题目
  async function fetchExamQuestions(id: string) {
    loading.value = true
    try {
      currentExam.value = await examsApi.getExamQuestions(id)
    } finally {
      loading.value = false
    }
  }

  // 保存答案
  async function saveAnswer(examId: string, questionId: string, answer: string) {
    await examsApi.saveAnswer(examId, questionId, answer)
    
    // 更新本地状态
    if (currentExam.value) {
      const question = currentExam.value.questions.find(q => q.id === questionId)
      if (question) {
        question.user_answer = answer
      }
    }
  }

  // 提交试卷
  async function submitExam(examId: string, answers: Record<string, string>) {
    loading.value = true
    try {
      const result = await examsApi.submitExam(examId, answers)
      return result
    } finally {
      loading.value = false
    }
  }

  // 删除考试
  async function deleteExam(id: string) {
    await examsApi.deleteExam(id)
    exams.value = exams.value.filter(e => e.id !== id)
  }

  return {
    exams,
    currentExam,
    loading,
    generateQuickExam,
    generateCustomExam,
    fetchExams,
    fetchExamQuestions,
    saveAnswer,
    submitExam,
    deleteExam
  }
})
