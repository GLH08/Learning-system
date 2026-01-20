import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const initialized = ref<boolean>(false)
  
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }
  
  const clearToken = () => {
    token.value = null
    localStorage.removeItem('token')
  }
  
  const login = async (password: string) => {
    const response = await authApi.login({ password })
    setToken(response.data.token)
    return response
  }
  
  const initPassword = async (password: string) => {
    const response = await authApi.init({ password })
    setToken(response.data.token)
    initialized.value = true
    return response
  }
  
  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      // Ignore error
    } finally {
      clearToken()
      router.push('/login')
    }
  }
  
  const checkAuth = async () => {
    if (!token.value) {
      return false
    }
    
    try {
      const response = await authApi.verify()
      initialized.value = response.data.initialized
      return response.data.valid
    } catch (error) {
      clearToken()
      return false
    }
  }
  
  return {
    token,
    initialized,
    setToken,
    clearToken,
    login,
    initPassword,
    logout,
    checkAuth
  }
})
