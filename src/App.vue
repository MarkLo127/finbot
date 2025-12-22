<script setup lang="ts">
import { ref } from 'vue'
import ChatView from './views/ChatView.vue'
import DashboardView from './views/DashboardView.vue'
import BudgetView from './views/BudgetView.vue'
import HistoryView from './views/HistoryView.vue'

type ViewType = 'chat' | 'dashboard' | 'budget' | 'history'

const currentView = ref<ViewType>('chat')

const navItems: { key: ViewType; icon: string; label: string }[] = [
  { key: 'chat', icon: '💬', label: '記帳' },
  { key: 'dashboard', icon: '📊', label: '分析' },
  { key: 'budget', icon: '🎯', label: '預算' },
  { key: 'history', icon: '📜', label: '紀錄' },
]
</script>

<template>
  <div class="crt-effect">
    <!-- 導航列 -->
    <nav class="navbar">
      <div class="navbar-brand">
        <span style="font-size: 20px;">💰</span>
        <span>FinBot</span>
      </div>
      <div class="navbar-links">
        <a 
          v-for="item in navItems" 
          :key="item.key"
          href="#" 
          @click.prevent="currentView = item.key" 
          :class="{ active: currentView === item.key }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </a>
      </div>
    </nav>

    <!-- 主內容 -->
    <main>
      <KeepAlive>
        <ChatView v-if="currentView === 'chat'" />
        <DashboardView v-else-if="currentView === 'dashboard'" />
        <BudgetView v-else-if="currentView === 'budget'" />
        <HistoryView v-else-if="currentView === 'history'" />
      </KeepAlive>
    </main>
  </div>
</template>

<style scoped>
.nav-icon {
  font-size: 14px;
}

.nav-label {
  margin-left: 4px;
}

@media (max-width: 480px) {
  .nav-label {
    display: none;
  }
  .nav-icon {
    font-size: 18px;
  }
}
</style>
