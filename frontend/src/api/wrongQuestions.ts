import request from './request'

export interface WrongQuestion {
  id: string
  question_id: string
  exam_id: string
  user_answer?: string
  correct_answer?: string
  wrong_count: number
  mastered: number
  last_wrong_time: string
  created_at: string
  question?: {
    id: string
    type: string
    difficulty: string
    content: string
    options?: string
    answer?: string
    explanation?: string
  }
}

export interface WrongQuestionsStats {
  total: number
  mastered: number
  unmastered: number
}

export const wrongQuestionsApi = {
  // 获取错题列表
  listWrongQuestions(params?: {
    mastered?: number
    skip?: number
    limit?: number
  }) {
    return request.get<WrongQuestion[]>('/api/wrong-questions', { params })
  },

  // 获取错题详情
  getWrongQuestion(id: string) {
    return request.get<WrongQuestion>(`/api/wrong-questions/${id}`)
  },

  // 标记为已掌握
  markAsMastered(id: string) {
    return request.put(`/api/wrong-questions/${id}/master`)
  },

  // 取消掌握标记
  markAsUnmastered(id: string) {
    return request.put(`/api/wrong-questions/${id}/unmaster`)
  },

  // 删除错题
  deleteWrongQuestion(id: string) {
    return request.delete(`/api/wrong-questions/${id}`)
  },

  // 获取错题统计
  getStats() {
    return request.get<WrongQuestionsStats>('/api/wrong-questions/stats/overview')
  }
}
