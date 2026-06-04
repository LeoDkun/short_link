<template>
  <div class="rise">
    <div class="head">
      <div>
        <h1 class="page-title">我的短链</h1>
        <p class="page-sub">管理你创建的所有短链接，查看点击表现。</p>
      </div>
      <el-button type="primary" size="large" @click="$router.push('/create')">
        <el-icon><Plus /></el-icon> 创建短链
      </el-button>
    </div>

    <div class="stat-strip">
      <div class="stat"><div class="k">短链总数</div><div class="v">{{ links.length }}</div></div>
      <div class="stat"><div class="k">总点击</div><div class="v">{{ totalClicks.toLocaleString() }}</div></div>
      <div class="stat"><div class="k">启用中</div><div class="v">{{ activeCount }} <small>/ {{ links.length }}</small></div></div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && links.length === 0" class="empty">
      <div class="ring"><el-icon><Link /></el-icon></div>
      <h3>还没有短链接</h3>
      <p>创建你的第一条短链，开始追踪点击数据。</p>
      <el-button type="primary" @click="$router.push('/create')">
        <el-icon><Plus /></el-icon> 创建短链
      </el-button>
    </div>

    <!-- 列表 -->
    <div v-else class="card table-wrap">
      <el-table :data="links" v-loading="loading" style="width: 100%">
        <el-table-column prop="code" label="短码" width="120">
          <template #default="{ row }"><span class="code-tag">{{ row.code }}</span></template>
        </el-table-column>
        <el-table-column label="短链接" min-width="220">
          <template #default="{ row }">
            <div class="urlcell">
              <a :href="row.short_url" target="_blank" rel="noopener" class="mono shorturl">{{ shortPath(row.short_url) }}</a>
              <button class="copy-btn mini" :class="{ 'is-copied': copiedCode === row.code }" @click="copy(row.short_url, row.code)">
                <el-icon><component :is="copiedCode === row.code ? Select : CopyDocument" /></el-icon>
              </button>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="target_url" label="目标 URL" min-width="240" show-overflow-tooltip>
          <template #default="{ row }"><span class="target">{{ row.target_url }}</span></template>
        </el-table-column>
        <el-table-column prop="click_count" label="点击" width="92" align="right">
          <template #default="{ row }"><span class="clicks">{{ row.click_count.toLocaleString() }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="92" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" size="small" @change="toggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="right">
          <template #default="{ row }">
            <el-button text :icon="DataLine" @click="$router.push(`/analytics/${row.code}`)">分析</el-button>
            <el-button text type="danger" :icon="Delete" @click="remove(row.code)" />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Link, CopyDocument, Select, DataLine, Delete } from '@element-plus/icons-vue'

const links = ref([])
const loading = ref(false)
const copiedCode = ref(null)

const totalClicks = computed(() => links.value.reduce((s, l) => s + (l.click_count || 0), 0))
const activeCount = computed(() => links.value.filter((l) => l.is_active).length)

function shortPath(url) { try { const u = new URL(url); return u.host + u.pathname } catch { return url } }

async function fetchLinks() {
  loading.value = true
  try {
    const { data } = await api.get('/links')
    links.value = data
  } catch {
    ElMessage.error('加载短链列表失败')
  } finally {
    loading.value = false
  }
}

async function copy(text, code) {
  try { await navigator.clipboard.writeText(text) }
  catch { const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove() }
  copiedCode.value = code
  setTimeout(() => (copiedCode.value = null), 1500)
}

async function toggle(row) {
  const next = row.is_active
  try {
    await api.patch(`/links/${row.code}`, { is_active: next })
    ElMessage.success(next ? '已启用' : '已停用')
  } catch {
    row.is_active = !next // 失败回滚
    ElMessage.error('更新状态失败')
  }
}

async function remove(code) {
  try {
    await ElMessageBox.confirm('删除后该短链将立即失效，确定删除？', '删除短链', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger'
    })
  } catch { return }
  try {
    await api.delete(`/links/${code}`)
    links.value = links.value.filter((l) => l.code !== code)
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(fetchLinks)
</script>

<style scoped>
.head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 26px; }
.head .el-button .el-icon { margin-right: 4px; }
.table-wrap { padding: 6px; overflow: hidden; }
.urlcell { display: flex; align-items: center; gap: 8px; }
.shorturl { font-size: 13.5px; color: var(--accent-700); }
.copy-btn.mini { padding: 4px 6px; }
.target { color: var(--ink-soft); font-size: 13.5px; }
.clicks { font-family: var(--mono); font-weight: 600; color: var(--ink); }
@media (max-width: 720px) {
  .head { flex-direction: column; align-items: stretch; }
}
</style>
