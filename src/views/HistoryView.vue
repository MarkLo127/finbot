<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { API_BASE } from '../config'

const transactions = ref<any[]>([])
const total = ref(0)
const isLoading = ref(true)
const skip = ref(0)
const limit = 20

const filters = ref({ type: '', start_date: '', end_date: '' })

onMounted(() => loadTransactions())

async function loadTransactions(reset = true) {
  if (reset) skip.value = 0
  isLoading.value = true
  
  try {
    const params = new URLSearchParams({ skip: skip.value.toString(), limit: limit.toString() })
    if (filters.value.type) params.append('type', filters.value.type)
    if (filters.value.start_date) params.append('start_date', filters.value.start_date)
    if (filters.value.end_date) params.append('end_date', filters.value.end_date)
    
    const res = await fetch(`${API_BASE}/transactions?${params}`)
    const data = await res.json()
    
    transactions.value = reset ? data.items : [...transactions.value, ...data.items]
    total.value = data.total
  } catch (error) {
    console.error('載入失敗:', error)
  } finally {
    isLoading.value = false
  }
}

async function deleteTransaction(id: number) {
  if (!confirm('確定刪除？')) return
  try {
    await fetch(`${API_BASE}/transactions/${id}`, { method: 'DELETE' })
    await loadTransactions()
  } catch { alert('刪除失敗') }
}

function loadMore() {
  skip.value += limit
  loadTransactions(false)
}

function clearFilters() {
  filters.value = { type: '', start_date: '', end_date: '' }
  loadTransactions()
}

function formatAmount(amount: number, type: string) {
  const formatted = new Intl.NumberFormat('zh-TW').format(Math.round(amount))
  return type === 'income' ? `+$${formatted}` : `-$${formatted}`
}
</script>

<template>
  <div class="history-page">
    <h1 class="page-title">📜 交易紀錄</h1>
    
    <!-- 篩選器 -->
    <div class="card filters">
      <div class="filter-row">
        <select v-model="filters.type" class="input" @change="loadTransactions()">
          <option value="">全部類型</option>
          <option value="expense">支出</option>
          <option value="income">收入</option>
        </select>
        <input v-model="filters.start_date" type="date" class="input" @change="loadTransactions()" />
        <input v-model="filters.end_date" type="date" class="input" @change="loadTransactions()" />
        <button @click="clearFilters" class="btn btn-secondary btn-sm">清除</button>
      </div>
    </div>
    
    <div v-if="isLoading && transactions.length === 0" class="loading-container">
      <span class="loading"></span> 載入中...
    </div>
    
    <div v-else-if="transactions.length === 0" class="empty-state card">
      <p>暫無交易紀錄</p>
    </div>
    
    <div v-else>
      <!-- 手機版：卡片列表 -->
      <div class="transaction-list mobile-only">
        <div v-for="t in transactions" :key="t.id" class="card transaction-card">
          <div class="transaction-header">
            <span class="transaction-icon">{{ t.category_icon }}</span>
            <div class="transaction-info">
              <div class="transaction-category">{{ t.category_name }}</div>
              <div class="transaction-desc text-muted">{{ t.description || t.date }}</div>
            </div>
            <div class="transaction-amount" :class="t.type === 'income' ? 'text-success' : 'text-danger'">
              {{ formatAmount(t.amount, t.type) }}
            </div>
          </div>
          <div class="transaction-footer">
            <span class="text-muted">{{ t.date }}</span>
            <button @click="deleteTransaction(t.id)" class="btn btn-danger btn-sm">刪除</button>
          </div>
        </div>
      </div>
      
      <!-- 電腦版：表格 -->
      <div class="card table-container desktop-only">
        <table class="table">
          <thead>
            <tr>
              <th>日期</th>
              <th>類別</th>
              <th>描述</th>
              <th>金額</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in transactions" :key="t.id">
              <td>{{ t.date }}</td>
              <td>{{ t.category_icon }} {{ t.category_name }}</td>
              <td>{{ t.description || '-' }}</td>
              <td :class="t.type === 'income' ? 'text-success' : 'text-danger'">
                {{ formatAmount(t.amount, t.type) }}
              </td>
              <td>
                <button @click="deleteTransaction(t.id)" class="btn btn-danger btn-sm">刪除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-if="transactions.length < total" class="load-more">
        <button @click="loadMore" class="btn" :disabled="isLoading">
          {{ isLoading ? '載入中...' : `載入更多 (${transactions.length}/${total})` }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.transaction-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.transaction-card {
  padding: var(--space-sm);
}

.transaction-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.transaction-icon {
  font-size: 24px;
}

.transaction-info {
  flex: 1;
  min-width: 0;
}

.transaction-category {
  font-size: var(--font-sm);
}

.transaction-desc {
  font-size: var(--font-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.transaction-amount {
  font-size: var(--font-sm);
  white-space: nowrap;
}

.transaction-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px dashed var(--color-border);
  font-size: var(--font-xs);
}

.load-more {
  text-align: center;
  padding: var(--space-md);
}

/* 響應式顯示切換 */
.mobile-only {
  display: none;
}

.desktop-only {
  display: block;
}

@media (max-width: 768px) {
  .mobile-only {
    display: flex;
  }
  .desktop-only {
    display: none;
  }
}
</style>
