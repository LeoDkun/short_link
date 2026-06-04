import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
  baseURL: '/api/v1'
})

// 请求拦截：自动附带 JWT
api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截：token 失效 / 过期时自动登出并回到登录页
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const auth = useAuthStore()
      if (auth.token) {
        auth.logout()
        // 动态引入 router，避免与 stores 形成静态循环依赖
        if (!window.location.pathname.startsWith('/login')) {
          const { default: router } = await import('../router')
          router.push('/login')
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
