<template>
  <div class="rise">
    <div class="page-head">
      <h1 class="page-title">创建短链</h1>
      <p class="page-sub">粘贴一个长链接，立即得到简洁、可追踪的短链。</p>
    </div>

    <div class="grid">
      <!-- 表单 -->
      <div class="card card-pad">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large" @submit.prevent="submit">
          <el-form-item label="目标 URL" prop="target_url">
            <el-input v-model="form.target_url" placeholder="https://example.com/very/long/path" :prefix-icon="LinkIcon" clearable />
          </el-form-item>
          <el-form-item prop="custom_alias">
            <template #label>
              自定义别名 <span class="opt">（可选）</span>
            </template>
            <el-input v-model="form.custom_alias" placeholder="my-link">
              <template #prepend>{{ origin }}/</template>
            </el-input>
            <div class="hint">3–16 位，字母、数字、<code>-</code>、<code>_</code>。留空则自动生成。</div>
          </el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="submit">
            <el-icon><Promotion /></el-icon> 生成短链
          </el-button>
        </el-form>
      </div>

      <!-- 结果 -->
      <transition name="fade">
        <div v-if="result" class="card card-pad result">
          <div class="result-tag">短链已生成</div>
          <div class="result-url">
            <a :href="result.short_url" target="_blank" rel="noopener" class="mono">{{ result.short_url }}</a>
          </div>
          <div class="result-actions">
            <button class="copy-btn" :class="{ 'is-copied': copied }" @click="copy(result.short_url)">
              <el-icon><component :is="copied ? Select : CopyDocument" /></el-icon>
              {{ copied ? '已复制' : '复制' }}
            </button>
            <el-button text :icon="TopRight" @click="open(result.short_url)">打开</el-button>
            <el-button text :icon="DataLine" @click="$router.push(`/analytics/${result.code}`)">查看分析</el-button>
          </div>
          <div class="result-meta">
            目标 · <span :title="result.target_url">{{ result.target_url }}</span>
          </div>
          <el-button class="again" plain @click="reset">
            <el-icon><Plus /></el-icon> 再创建一个
          </el-button>
        </div>
        <div v-else class="card card-pad placeholder">
          <span class="ph-mark">
            <el-icon><MagicStick /></el-icon>
          </span>
          <p>生成的短链会显示在这里，并自动复制到剪贴板。</p>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import {
  Link as LinkIcon, Promotion, CopyDocument, Select,
  TopRight, DataLine, Plus, MagicStick
} from '@element-plus/icons-vue'

const origin = window.location.origin.replace(/^https?:\/\//, '')
const formRef = ref()
const loading = ref(false)
const result = ref(null)
const copied = ref(false)
const form = reactive({ target_url: '', custom_alias: '' })

const rules = {
  target_url: [
    { required: true, message: '请输入目标 URL', trigger: 'blur' },
    {
      validator: (_r, v, cb) =>
        /^https?:\/\/.+\..+/.test(v) ? cb() : cb(new Error('请输入合法的 http(s) 链接')),
      trigger: 'blur'
    }
  ],
  custom_alias: [
    {
      validator: (_r, v, cb) =>
        !v || /^[0-9A-Za-z_-]{3,16}$/.test(v) ? cb() : cb(new Error('别名需为 3–16 位字母数字、- 或 _')),
      trigger: 'blur'
    }
  ]
}

async function copy(text) {
  try { await navigator.clipboard.writeText(text) }
  catch { const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove() }
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}
function open(url) { window.open(url, '_blank', 'noopener') }
function reset() { result.value = null; form.target_url = ''; form.custom_alias = '' }

async function submit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const payload = { target_url: form.target_url }
      if (form.custom_alias) payload.custom_alias = form.custom_alias
      const { data } = await api.post('/links', payload)
      result.value = data
      copy(data.short_url)
      ElMessage.success('创建成功，已复制到剪贴板')
    } catch (e) {
      const status = e.response?.status
      const msg = status === 409 ? '该自定义别名已被占用，换一个试试'
        : status === 422 ? '链接格式不合法'
        : e.response?.data?.detail || '创建失败'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
.opt { color: var(--faint); font-weight: 400; }
.hint { color: var(--muted); font-size: 12.5px; margin-top: 7px; }
.hint code { font-family: var(--mono); background: var(--bg-tint); padding: 0 4px; border-radius: 4px; }
.submit { width: 100%; font-weight: 600; }
.submit .el-icon { margin-right: 4px; }

.placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: var(--muted); min-height: 230px; border-style: dashed; }
.ph-mark { width: 52px; height: 52px; border-radius: 14px; display: grid; place-items: center; background: var(--accent-soft); color: var(--accent); margin-bottom: 14px; }
.ph-mark .el-icon { font-size: 24px; }
.placeholder p { font-size: 14px; max-width: 240px; }

.result-tag { display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: var(--ok); background: var(--ok-soft); padding: 4px 10px; border-radius: 99px; }
.result-url { margin: 16px 0 14px; }
.result-url a { font-size: 19px; font-weight: 500; color: var(--accent-700); word-break: break-all; }
.result-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding-bottom: 14px; border-bottom: 1px solid var(--line); }
.result-meta { color: var(--muted); font-size: 13px; margin: 14px 0 18px; }
.result-meta span { color: var(--ink-soft); word-break: break-all; }
.again { width: 100%; }
.again .el-icon { margin-right: 4px; }

@media (max-width: 820px) { .grid { grid-template-columns: 1fr; } }
</style>
