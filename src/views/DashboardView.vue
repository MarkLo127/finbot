<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { API_BASE } from '../config'

const summary = ref<any>(null)
const categoryData = ref<any[]>([])
const trendData = ref<any[]>([])
const insights = ref<string>('')
const isLoading = ref(true)

onMounted(() => loadData())

async function loadData() {
  isLoading.value = true
  try {
    const [summaryRes, categoryRes, trendRes, insightsRes] = await Promise.all([
      fetch(`${API_BASE}/analytics/summary?period=month`),
      fetch(`${API_BASE}/analytics/category-breakdown`),
      fetch(`${API_BASE}/analytics/trend?months=6`),
      fetch(`${API_BASE}/analytics/insights`)
    ])
    
    summary.value = await summaryRes.json()
    const catData = await categoryRes.json()
    categoryData.value = catData.categories || []
    const tData = await trendRes.json()
    trendData.value = tData.data || []
    const iData = await insightsRes.json()
    insights.value = iData.summary || ''
  } catch (error) {
    console.error('載入失敗:', error)
  } finally {
    isLoading.value = false
  }
}

function formatAmount(amount: number) {
  return new Intl.NumberFormat('zh-TW').format(Math.round(amount))
}

function getMaxTrend() {
  return Math.max(...trendData.value.map(d => d.amount || 1), 1)
}
</script>

<template>
  <div class="dashboard">
    <h1 class="page-title">📊 財務分析</h1>
    
    <div v-if="isLoading" class="loading-container">
      <span class="loading"></span> 載入中...
    </div>
    
    <div v-else>
      <!-- 摘要統計 -->
      <div class="grid grid-4">
        <div class="card stat-card">
          <div class="stat-icon">💸</div>
          <div class="stat-value">${{ formatAmount(summary?.total_expense || 0) }}</div>
          <div class="stat-label">本月支出</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-value">${{ formatAmount(summary?.total_income || 0) }}</div>
          <div class="stat-label">本月收入</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">📈</div>
          <div class="stat-value" :class="(summary?.net || 0) >= 0 ? 'text-success' : 'text-danger'">
            ${{ formatAmount(summary?.net || 0) }}
          </div>
          <div class="stat-label">淨額</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">📝</div>
          <div class="stat-value">{{ summary?.transaction_count || 0 }}</div>
          <div class="stat-label">交易筆數</div>
        </div>
      </div>
      
      <div class="grid grid-2">
        <!-- 類別分佈 -->
        <div class="card">
          <div class="card-header">🥧 支出類別</div>
          <div v-if="categoryData.length === 0" class="empty-state">暫無數據</div>
          <div v-else class="category-list">
            <div v-for="cat in categoryData.slice(0, 6)" :key="cat.name" class="category-item">
              <div class="category-info">
                <span>{{ cat.icon }} {{ cat.name }}</span>
                <span class="text-muted">${{ formatAmount(cat.amount) }}</span>
              </div>
              <div class="category-bar-container">
                <div class="category-bar" :style="{ width: cat.percentage + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 趨勢圖 -->
        <div class="card">
          <div class="card-header">📈 近 6 個月</div>
          <div v-if="trendData.length === 0" class="empty-state">暫無數據</div>
          <div v-else class="trend-chart">
            <div v-for="item in trendData" :key="item.month" class="chart-bar-wrapper">
              <div class="chart-bar" :style="{ height: (item.amount / getMaxTrend() * 100) + '%' }"></div>
              <div class="chart-label">{{ item.label }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 智慧摘要 -->
      <div class="card">
        <div class="card-header">🤖 智慧摘要</div>
        <pre class="insights-text">{{ insights || '暫無摘要' }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.category-info {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-xs);
}

.category-bar-container {
  height: 12px;
  background: var(--color-bg);
  box-shadow: var(--pixel-shadow);
}

.category-bar {
  height: 100%;
  background: var(--color-primary);
  min-width: 4px;
}

.trend-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 150px;
  gap: var(--space-xs);
  padding-top: var(--space-md);
}

.chart-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
}

.chart-bar {
  width: 100%;
  max-width: 40px;
  background: var(--color-secondary);
  min-height: 4px;
  margin-top: auto;
  box-shadow: var(--pixel-shadow);
}

.chart-label {
  font-size: var(--font-xs);
  margin-top: var(--space-sm);
  color: var(--color-text-muted);
}

.insights-text {
  white-space: pre-wrap;
  font-family: inherit;
  font-size: var(--font-xs);
  line-height: 2;
  margin: 0;
}

@media (max-width: 480px) {
  .trend-chart {
    height: 120px;
  }
}
</style>
