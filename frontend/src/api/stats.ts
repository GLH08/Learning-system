import request from './request'

export interface OverviewStats {
  total_questions: number
  total_exams: number
  total_practice_time: number
  average_score: number
  overall_accuracy: number
  total_wrong_questions: number
  mastered_wrong_questions: number
}

export interface DailyStats {
  date: string
  exam_count: number
  question_count: number
  correct_count: number
  wrong_count: number
  accuracy: number
  average_score: number
}

export interface CategoryStats {
  category_id: string
  category_name: string
  total_count: number
  correct_count: number
  wrong_count: number
  accuracy: number
}

export interface WeakPoint {
  category_id: string
  category_name: string
  accuracy: number
  wrong_count: number
}

export const statsApi = {
  // 获取学习概览
  getOverview() {
    return request.get<OverviewStats>('/api/stats/overview')
  },

  // 获取每日统计
  getDailyStats(days: number = 30) {
    return request.get<DailyStats[]>('/api/stats/daily', { params: { days } })
  },

  // 获取分类统计
  getCategoryStats() {
    return request.get<CategoryStats[]>('/api/stats/category')
  },

  // 获取薄弱知识点
  getWeakPoints(limit: number = 5) {
    return request.get<WeakPoint[]>('/api/stats/weak-points', { params: { limit } })
  }
}
