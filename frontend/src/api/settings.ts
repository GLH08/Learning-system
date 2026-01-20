import request from './request'

export interface AISettings {
  api_url: string
  api_key: string
  model: string
  temperature: number
  max_tokens: number
}

export interface SettingsResponse {
  ai_api_url?: string
  ai_api_key?: string
  ai_model?: string
  ai_temperature?: number
  ai_max_tokens?: number
}

export interface TestAIResponse {
  success: boolean
  message: string
}

export interface BackupInfo {
  filename: string
  size: number
  created_at: string
}

export const settingsApi = {
  // 获取设置
  getSettings() {
    return request.get<SettingsResponse>('/api/settings')
  },

  // 更新设置
  updateSettings(data: AISettings) {
    return request.put('/api/settings', data)
  },

  // 测试 AI 连接
  testAI(data: AISettings) {
    return request.post<TestAIResponse>('/api/settings/test-ai', data)
  },

  // 创建备份
  createBackup() {
    return request.post<BackupInfo>('/api/settings/backup')
  },

  // 获取备份列表
  listBackups() {
    return request.get<BackupInfo[]>('/api/settings/backups')
  },

  // 下载备份
  downloadBackup(filename: string) {
    return `/api/settings/backups/${filename}`
  },

  // 恢复备份
  restoreBackup(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/api/settings/restore', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除备份
  deleteBackup(filename: string) {
    return request.delete(`/api/settings/backups/${filename}`)
  }
}
