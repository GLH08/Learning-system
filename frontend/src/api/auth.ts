import api from './index'

export interface InitRequest {
  password: string
}

export interface LoginRequest {
  password: string
}

export interface LoginResponse {
  token: string
  expiresIn: number
}

export interface VerifyResponse {
  valid: boolean
  initialized: boolean
}

export interface ChangePasswordRequest {
  oldPassword: string
  newPassword: string
}

export const authApi = {
  // Initialize admin password
  init(data: InitRequest) {
    return api.post<any, { data: LoginResponse }>('/auth/init', data)
  },
  
  // Login
  login(data: LoginRequest) {
    return api.post<any, { data: LoginResponse }>('/auth/login', data)
  },
  
  // Logout
  logout() {
    return api.post('/auth/logout')
  },
  
  // Verify token
  verify() {
    return api.get<any, { data: VerifyResponse }>('/auth/verify')
  },
  
  // Change password
  changePassword(data: ChangePasswordRequest) {
    return api.put('/auth/password', data)
  }
}
