<template>
  <div class="auth rise">
    <div class="auth-card card">
      <div class="auth-head">
        <span class="auth-mark">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.5 1.5" />
            <path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.5-1.5" />
          </svg>
        </span>
        <h1 class="auth-title display">创建账号</h1>
        <p class="auth-sub">几秒钟即可开始缩短你的链接</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large" @submit.prevent="submit">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" type="email" placeholder="user@example.com" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="8–128 位" :prefix-icon="Lock" @keyup.enter="submit" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="auth-btn">注册</el-button>
      </el-form>

      <p class="auth-foot">已有账号？<router-link to="/login">去登录</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ email: '', password: '' })
const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度需为 8–128 位', trigger: 'blur' }
  ]
}

async function submit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await auth.register(form.email, form.password)
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '注册失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.auth { display: flex; justify-content: center; padding-top: 4vh; }
.auth-card { width: 100%; max-width: 420px; padding: 36px 34px; }
.auth-head { text-align: center; margin-bottom: 26px; }
.auth-mark {
  width: 48px; height: 48px; border-radius: 13px; margin: 0 auto 16px;
  display: grid; place-items: center; color: #fff;
  background: linear-gradient(135deg, #ff6f4d, #e8482a);
  box-shadow: 0 10px 24px -10px var(--accent-ring);
}
.auth-mark svg { width: 26px; height: 26px; }
.auth-title { font-size: 26px; font-weight: 800; margin: 0; color: var(--ink); }
.auth-sub { color: var(--muted); font-size: 14px; margin: 8px 0 0; }
.auth-btn { width: 100%; margin-top: 4px; font-weight: 600; }
.auth-foot { text-align: center; color: var(--muted); font-size: 14px; margin: 20px 0 0; }
</style>
