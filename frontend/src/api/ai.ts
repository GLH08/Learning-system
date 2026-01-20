import api from './index'

export interface AITask {
  id: string
  type: 'answer' | 'explanation' | 'both' | 'report'
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  totalCount: number
  completedCount: number
  failedCount: number
  progress: number
  currentQuestionId: string | null
  questionIds?: string[]
  errorMessage: string | null
  createdAt: string
  startedAt: string | null
  updatedAt: string
  completedAt: string | null
}

export interface AICompleteRequest {
  questionId: string
  type: 'answer' | 'explanation' | 'both'
}

export interface AICompleteResponse {
  questionId: string
  answer?: string
  explanation?: string
  answerStatus: string
  explanationStatus: string
}

export interface AIBatchCompleteRequest {
  questionIds?: string[]
  type: 'answer' | 'explanation' | 'both'
  filter?: {
    categoryId?: string
    answerStatus?: string
    explanationStatus?: string
  }
}

export const aiApi = {
  // Complete single question
  completeQuestion(data: AICompleteRequest) {
    return api.post<any, { data: AICompleteResponse }>('/ai/complete', data)
  },
  
  // Batch complete questions
  batchCompleteQuestions(data: AIBatchCompleteRequest) {
    return api.post<any, { data: AITask }>('/ai/batch-complete', data)
  },
  
  // Get tasks list
  getTasks(status?: string) {
    return api.get<any, { data: { items: AITask[]; total: number } }>('/ai/tasks', {
      params: { status }
    })
  },
  
  // Get task details
  getTask(id: string) {
    return api.get<any, { data: AITask }>(`/ai/tasks/${id}`)
  },
  
  // Pause task
  pauseTask(id: string) {
    return api.put<any, { data: AITask }>(`/ai/tasks/${id}/pause`)
  },
  
  // Resume task
  resumeTask(id: string) {
    return api.put<any, { data: AITask }>(`/ai/tasks/${id}/resume`)
  },
  
  // Cancel task
  cancelTask(id: string) {
    return api.put<any, { data: AITask }>(`/ai/tasks/${id}/cancel`)
  },
  
  // Generate report
  generateReport(examId: string) {
    return api.post<any, { data: { report: string } }>('/ai/generate-report', { examId })
  }
}
