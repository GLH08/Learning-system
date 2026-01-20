import axios, { AxiosError } from 'axios'
import { useUserStore } from '@/stores/user'
import { useMessage } from '@/composables/useMessage'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL,
  timeout: 120000,  // 120秒，适应AI补全等耗时操作
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    const data = response.data

    // Handle standard response format
    if (data.code !== undefined) {
      if (data.code === 0) {
        return data
      } else {
        const message = useMessage()
        message.error(data.message || '请求失败')
        return Promise.reject(new Error(data.message))
      }
    }

    return data
  },
  (error: AxiosError) => {
    const message = useMessage()

    if (error.response) {
      const status = error.response.status
      const data: any = error.response.data

      if (status === 401) {
        // Unauthorized - clear token and redirect to login
        const userStore = useUserStore()
        userStore.logout()
        message.error('登录已过期，请重新登录')
      } else if (status === 403) {
        message.error('没有权限访问')
      } else if (status === 404) {
        message.error('请求的资源不存在')
      } else if (status === 500) {
        message.error(data?.message || '服务器错误')
      } else {
        message.error(data?.message || '请求失败')
      }
    } else if (error.request) {
      message.error('网络错误，请检查网络连接')
    } else {
      message.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default api
