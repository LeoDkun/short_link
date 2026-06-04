<template>
  <header class="nav">
    <div class="nav-inner">
      <router-link :to="auth.isAuthenticated ? '/dashboard' : '/'" class="brand">
        <span class="brand-mark">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.5 1.5" />
            <path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.5-1.5" />
          </svg>
        </span>
        <span class="brand-name">shortlink</span>
      </router-link>

      <nav class="links">
        <template v-if="auth.isAuthenticated">
          <router-link to="/dashboard" class="navlink">我的短链</router-link>
          <router-link to="/create" class="cta">
            <el-icon><Plus /></el-icon><span>创建短链</span>
          </router-link>
          <el-dropdown trigger="click" @command="onCommand">
            <span class="avatar" :title="auth.email || ''">{{ initial }}</span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>{{ auth.email }}</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <router-link to="/login" class="navlink">登录</router-link>
          <router-link to="/register" class="cta cta--ghost">注册</router-link>
        </template>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const initial = computed(() => (auth.email ? auth.email[0].toUpperCase() : '·'))

function onCommand(cmd) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.nav {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250, 249, 246, .82);
  backdrop-filter: saturate(140%) blur(10px);
  border-bottom: 1px solid var(--line);
}
.nav-inner {
  max-width: 1080px; margin: 0 auto; height: 62px; padding: 0 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.brand { display: inline-flex; align-items: center; gap: 10px; text-decoration: none; }
.brand:hover { text-decoration: none; }
.brand-mark {
  width: 32px; height: 32px; border-radius: 9px;
  display: grid; place-items: center; color: #fff;
  background: linear-gradient(135deg, #ff6f4d, #e8482a);
  box-shadow: 0 4px 12px -4px var(--accent-ring);
}
.brand-mark svg { width: 18px; height: 18px; }
.brand-name {
  font-family: var(--display); font-weight: 800; font-size: 20px;
  letter-spacing: -.03em; color: var(--ink);
}
.links { display: flex; align-items: center; gap: 6px; }
.navlink {
  color: var(--muted); font-weight: 500; font-size: 14.5px;
  padding: 8px 12px; border-radius: 9px; text-decoration: none; transition: all .15s;
}
.navlink:hover { color: var(--ink); background: rgba(0,0,0,.035); text-decoration: none; }
.router-link-active.navlink { color: var(--ink); background: rgba(0,0,0,.05); }
.cta {
  display: inline-flex; align-items: center; gap: 6px;
  margin-left: 6px; padding: 8px 14px; border-radius: 10px;
  background: var(--accent); color: #fff; font-weight: 600; font-size: 14px;
  text-decoration: none; box-shadow: 0 6px 16px -8px var(--accent); transition: all .15s;
}
.cta:hover { background: var(--accent-600); text-decoration: none; transform: translateY(-1px); }
.cta .el-icon { font-size: 15px; }
.cta--ghost {
  background: transparent; color: var(--ink); box-shadow: none;
  border: 1px solid var(--line-strong);
}
.cta--ghost:hover { background: #fff; border-color: var(--faint); }
.avatar {
  width: 34px; height: 34px; margin-left: 8px; border-radius: 50%;
  display: grid; place-items: center; cursor: pointer;
  background: var(--bg-tint); color: var(--ink-soft);
  font-weight: 700; font-size: 14px; outline: none; transition: all .15s;
}
.avatar:hover { background: var(--accent-soft); color: var(--accent-700); }
@media (max-width: 560px) {
  .navlink { padding: 8px 8px; }
  .brand-name { font-size: 18px; }
  .cta span { display: none; }
  .cta { padding: 8px 11px; }
}
</style>
