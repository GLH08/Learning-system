import api from './index'

export interface Question {
  id: string
  categoryId: string | null
  type: 'single' | 'multiple' | 'judge' | 'essay'
  difficulty: 'easy' | 'medium' | 'hard'
  content: string
  options: Record<string, string> | null
  answer: string | null
  answerStatus: 'none' | 'ai_pending' | 'ai_generated' | 'confirmed'
  explanation: string | null
  explanationStatus: 'none' | 'ai_pending' | 'ai_generated' | 'confirmed'
  tags: string[]
  source: string | null
  createdAt: string
  updatedAt: string
}

export interface QuestionCreate {
  categoryId?: string | null
  type: string
  difficulty?: string
  content: string
  options?: Record<string, string> | null
  answer?: string | null
  explanation?: string | null
  tags?: string[]
  source?: string | null
}

export interface QuestionUpdate {
  categoryId?: string | null
  type?: string
  difficulty?: string
  content?: string
  options?: Record<string, string> | null
  answer?: string | null
  explanation?: string | null
  tags?: string[]
  source?: string | null
}

export interface QuestionListQuery {
  page?: number
  pageSize?: number
  keyword?: string
  categoryId?: string
  type?: string
  difficulty?: string
  status?: string
  answerStatus?: string
  explanationStatus?: string
  sortBy?: string
  sortOrder?: string
}

export interface QuestionStats {
  total: number
  byType: Record<string, number>
  byDifficulty: Record<string, number>
  byStatus: Record<string, number>
  incomplete: number
}

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export const questionsApi = {
  // Get question list
  getQuestions(params: QuestionListQuery) {
    return api.get<any, { data: PageResponse<Question> }>('/questions', { params })
  },
  
  // Get question stats
  getQuestionStats() {
    return api.get<any, { data: QuestionStats }>('/questions/stats')
  },
  
  // Get question details
  getQuestion(id: string) {
    return api.get<any, { data: Question }>(`/questions/${id}`)
  },
  
  // Create question
  createQuestion(data: QuestionCreate) {
    return api.post<any, { data: Question }>('/questions', data)
  },
  
  // Update question
  updateQuestion(id: string, data: QuestionUpdate) {
    return api.put<any, { data: Question }>(`/questions/${id}`, data)
  },
  
  // Delete question
  deleteQuestion(id: string) {
    return api.delete(`/questions/${id}`)
  },
  
  // Batch delete questions
  batchDeleteQuestions(ids: string[]) {
    return api.post<any, { data: { deleted: number } }>('/questions/batch-delete', ids)
  },

  // Batch update category
  batchUpdateCategory(ids: string[], categoryId: string) {
    return api.post<any, { data: { updated: number } }>('/questions/batch-update-category', { question_ids: ids, category_id: categoryId })
  },

  // Confirm answer
  confirmAnswer(id: string) {
    return api.put<any, { data: Question }>(`/questions/${id}/confirm-answer`)
  },
  
  // Confirm explanation
  confirmExplanation(id: string) {
    return api.put<any, { data: Question }>(`/questions/${id}/confirm-explanation`)
  },
  
  // Export questions as JSON
  exportQuestionsJSON(params: {
    categoryId?: string
    type?: string
    difficulty?: string
    includeIncomplete?: boolean
  }) {
    return api.get('/questions/export/json', {
      params,
      responseType: 'blob'
    })
  }
}
