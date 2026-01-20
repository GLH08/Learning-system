import request from './request'

export interface QuickExamRequest {
  count: number
  shuffle_options: boolean
}

export interface TypeCount {
  type: string
  count: number
}

export interface CustomExamRequest {
  title: string
  mode: string
  category_ids?: string[]
  question_types?: string[]
  difficulties?: string[]
  type_counts?: TypeCount[]
  time_limit?: number
  shuffle_options: boolean
  shuffle_questions: boolean
}

export interface Exam {
  id: string
  title: string
  mode: string
  status: string
  total_count: number
  total_score: number
  score: number
  correct_count: number
  wrong_count: number
  time_limit?: number
  start_time?: string
  submit_time?: string
  time_used?: number
  created_at: string
}

export interface ExamDetail extends Exam {
  config?: string
  question_ids: string
  answers?: string
}

export interface QuestionInExam {
  id: string
  type: string
  difficulty: string
  content: string
  options?: string
  answer?: string
  explanation?: string
  user_answer?: string
}

export interface ExamQuestionsResponse {
  exam: Exam
  questions: QuestionInExam[]
}

export interface GradingResult {
  score: number
  total_score: number
  correct_count: number
  wrong_count: number
  results: Record<string, {
    correct: boolean
    user_answer: string
    correct_answer: string
  }>
}

export const examsApi = {
  // 快速组卷
  generateQuickExam(data: QuickExamRequest) {
    return request.post<Exam>('/exams/generate/quick', data)
  },

  // 自定义组卷
  generateCustomExam(data: CustomExamRequest) {
    return request.post<Exam>('/exams/generate/custom', data)
  },

  // 获取考试列表
  listExams(params?: {
    status?: string
    mode?: string
    skip?: number
    limit?: number
  }) {
    return request.get<Exam[]>('/exams', { params })
  },

  // 获取考试详情
  getExam(id: string) {
    return request.get<ExamDetail>(`/exams/${id}`)
  },

  // 获取考试题目
  getExamQuestions(id: string) {
    return request.get<ExamQuestionsResponse>(`/exams/${id}/questions`)
  },

  // 保存答案
  saveAnswer(examId: string, questionId: string, answer: string) {
    return request.put(`/exams/${examId}/answer`, {
      question_id: questionId,
      answer
    })
  },

  // 提交试卷
  submitExam(examId: string, answers: Record<string, string>) {
    return request.post<GradingResult>(`/exams/${examId}/submit`, { answers })
  },

  // 删除考试
  deleteExam(id: string) {
    return request.delete(`/exams/${id}`)
  },

  // 生成错题试卷
  generateWrongQuestionExam(data: {
    title?: string
    mode?: string
    mastered?: number
    limit?: number
  }) {
    return request.post<Exam>('/exams/generate/wrong-questions', data)
  },

  // 手动评分
  manualGrade(examId: string, questionId: string, score: number, feedback?: string) {
    return request.post(`/exams/${examId}/manual-grade`, {
      question_id: questionId,
      score,
      feedback
    })
  }
}
