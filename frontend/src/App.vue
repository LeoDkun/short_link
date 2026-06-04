<template>
  <div class="app-shell">
    <Navbar />
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <footer class="app-foot">
      ShortLink · 由 <code>FastAPI</code> + <code>Redis</code> + <code>Vue</code> 驱动
    </footer>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>
