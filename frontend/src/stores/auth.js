import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    email: localStorage.getItem('email') || null,
    user: null
  }),
  getters: {
    isAuthenticated: (state) => !!state.token
  },
  actions: {
    async login(email, password) {
      // 后端登录走 OAuth2 password flow（表单编码），字段名为 username
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)
      const { data } = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      this.token = data.access_token
      this.email = email
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('email', email)
    },
    async register(email, password) {
      await api.post('/auth/register', { email, password })
    },
    logout() {
      this.token = null
      this.email = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('email')
    }
  }
})
