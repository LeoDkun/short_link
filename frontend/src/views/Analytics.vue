<template>
  <div class="rise" v-loading="loading">
    <!-- header -->
    <div class="ana-head">
      <el-button text :icon="ArrowLeft" class="back" @click="$router.push('/dashboard')">返回</el-button>
      <div class="ana-title">
        <h1 class="page-title">链接分析</h1>
        <div class="ana-link">
          <span class="code-tag">{{ code }}</span>
          <a :href="shortUrl" target="_blank" rel="noopener" class="mono short">{{ shortPath }}</a>
          <button class="copy-btn mini" :class="{ 'is-copied': copied }" @click="copy(shortUrl)">
            <el-icon><component :is="copied ? Select : CopyDocument" /></el-icon>
          </button>
        </div>
      </div>
    </div>

    <!-- stats -->
    <div class="stat-strip ana-stats">
      <div class="stat accent">
        <div class="k">总点击</div>
        <div class="v">{{ analytics.total_clicks.toLocaleString() }}</div>
      </div>
      <div class="stat">
        <div class="k">有记录天数</div>
        <div class="v">{{ analytics.daily.length }}</div>
      </div>
      <div class="stat">
        <div class="k">单日峰值</div>
        <div class="v">{{ peak.toLocaleString() }}</div>
      </div>
    </div>

    <!-- daily chart -->
    <div class="card card-pad section">
      <h3 class="sec-title">每日点击</h3>
      <div v-if="analytics.daily.length" class="chart">
        <div v-for="d in analytics.daily" :key="d.day" class="bar-col" :title="`${d.day} · ${d.count} 次`">
          <span class="bar-val">{{ d.count }}</span>
          <div class="bar-track">
            <div class="bar-fill" :style="{ height: barHeight(d.count) }"></div>
          </div>
          <span class="bar-x">{{ shortDay(d.day) }}</span>
        </div>
      </div>
      <p v-else class="nodata">还没有点击数据，分享链接后这里会出现每日趋势。</p>
    </div>

    <!-- referrers -->
    <div class="card card-pad section">
      <h3 class="sec-title">Top 来源</h3>
      <div v-if="analytics.top_referrers.length" class="refs">
        <div v-for="r in analytics.top_referrers" :key="r.referrer || 'direct'" class="ref-row">
          <span class="ref-name" :title="r.referrer || '直接访问'">{{ r.referrer || '直接访问 / 无来源' }}</span>
          <div class="ref-bar"><div class="ref-fill" :style="{ width: refWidth(r.count) }"></div></div>
          <span class="ref-count mono">{{ r.count }}</span>
        </div>
      </div>
      <p v-else class="nodata">暂无来源数据。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { ElMessage } from 'element-plus'
import { ArrowLeft, CopyDocument, Select } from '@element-plus/icons-vue'

const route = useRoute()
const code = route.params.code
const loading = ref(false)
const copied = ref(false)
const analytics = ref({ code: '', total_clicks: 0, daily: [], top_referrers: [] })

const shortUrl = computed(() => `${window.location.origin}/${code}`)
const shortPath = computed(() => `${window.location.host}/${code}`)
const peak = computed(() => analytics.value.daily.reduce((m, d) => Math.max(m, d.count), 0))
const maxRef = computed(() => analytics.value.top_referrers.reduce((m, r) => Math.max(m, r.count), 0))

function barHeight(c) { const m = peak.value; if (!m) return '0%'; return `${Math.max((c / m) * 100, c > 0 ? 4 : 0)}%` }
function refWidth(c) { const m = maxRef.value; return m ? `${Math.max((c / m) * 100, 6)}%` : '0%' }
function shortDay(s) { const p = String(s).split('-'); return p.length === 3 ? `${+p[1]}/${+p[2]}` : s }

async function copy(text) {
  try { await navigator.clipboard.writeText(text) }
  catch { const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove() }
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/links/${code}/analytics`)
    analytics.value = data
  } catch (e) {
    ElMessage.error(e.response?.status === 404 ? '短链不存在或无权访问' : '加载分析数据失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.ana-head { margin-bottom: 24px; }
.back { margin-bottom: 8px; color: var(--muted); }
.ana-link { display: flex; align-items: center; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
.ana-link .short { font-size: 14px; color: var(--accent-700); }
.copy-btn.mini { padding: 4px 7px; }

.ana-stats .stat.accent { background: linear-gradient(135deg, #fff6f2, #fff); border-color: #ffd8cd; }
.ana-stats .stat.accent .v { color: var(--accent-700); }

.section { margin-top: 18px; }
.sec-title { font-family: var(--display); font-weight: 700; font-size: 16px; color: var(--ink); margin: 0 0 20px; }
.nodata { color: var(--muted); font-size: 14px; margin: 0; }

/* bar chart */
.chart {
  display: flex; align-items: flex-end; gap: 8px;
  height: 220px; padding-top: 18px; overflow-x: auto;
}
.bar-col { flex: 1 1 0; min-width: 22px; display: flex; flex-direction: column; align-items: center; height: 100%; }
.bar-val { font-family: var(--mono); font-size: 11px; color: var(--muted); margin-bottom: 6px; }
.bar-track { flex: 1; width: 100%; max-width: 38px; display: flex; align-items: flex-end; }
.bar-fill {
  width: 100%; border-radius: 6px 6px 0 0;
  background: linear-gradient(180deg, #ff7a5c, #ff5d3b);
  transition: height .5s cubic-bezier(.2,.8,.2,1), filter .15s;
  min-height: 0;
}
.bar-col:hover .bar-fill { filter: brightness(1.08); }
.bar-x { font-size: 10.5px; color: var(--faint); margin-top: 8px; white-space: nowrap; }

/* referrers */
.refs { display: flex; flex-direction: column; gap: 14px; }
.ref-row { display: grid; grid-template-columns: minmax(120px, 240px) 1fr auto; align-items: center; gap: 14px; }
.ref-name { font-size: 13.5px; color: var(--ink-soft); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ref-bar { height: 10px; background: var(--bg-tint); border-radius: 99px; overflow: hidden; }
.ref-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #ffb09c, #ff5d3b); transition: width .5s cubic-bezier(.2,.8,.2,1); }
.ref-count { font-size: 13px; font-weight: 600; color: var(--ink); min-width: 36px; text-align: right; }

@media (max-width: 560px) {
  .ref-row { grid-template-columns: 1fr auto; }
  .ref-bar { grid-column: 1 / -1; order: 3; }
}
</style>
