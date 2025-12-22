<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { API_BASE } from '../config'

const budgets = ref<any[]>([])
const categories = ref<any[]>([])
const isLoading = ref(true)
const showForm = ref(false)

const newBudget = ref({ category_id: null as number | null, limit_amount: 0, period: 'monthly' })

onMounted(() => loadData())

async function loadData() {
  isLoading.value = true
  try {
    const [budgetRes, catRes] = await Promise.all([
      fetch(`${API_BASE}/budgets`),
      fetch(`${API_BASE}/chat/categories`)
    ])
    budgets.value = await budgetRes.json()
    categories.value = (await catRes.json()).filter((c: any) => c.type === 'expense')
  } catch (error) {
    console.error('載入失敗:', error)
  } finally {
    isLoading.value = false
  }
}

async function createBudget() {
  if (!newBudget.value.limit_amount) return
  try {
    await fetch(`${API_BASE}/budgets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newBudget.value)
    })
    showForm.value = false
    newBudget.value = { category_id: null, limit_amount: 0, period: 'monthly' }
    await loadData()
  } catch { alert('建立失敗') }
}

async function deleteBudget(id: number) {
  if (!confirm('確定刪除？')) return
  try {
    await fetch(`${API_BASE}/budgets/${id}`, { method: 'DELETE' })
    await loadData()
  } catch { alert('刪除失敗') }
}

function getStatusClass(rate: number) {
  if (rate <= 80) return 'success'
  if (rate <= 100) return 'warning'
  return 'danger'
}

function formatAmount(amount: number) {
  return new Intl.NumberFormat('zh-TW').format(Math.round(amount))
}
</script>

<template>
  <div class="budget-page">
    <div class="page-header">
      <h1 class="page-title">🎯 預算管理</h1>
      <button @click="showForm = !showForm" class="btn btn-sm">
        {{ showForm ? '取消' : '+ 新增' }}
      </button>
    </div>
    
    <!-- 新增表單 -->
    <div v-if="showForm" class="card">
      <div class="card-header">新增預算</div>
      <div class="form-row">
        <div class="form-group">
          <label>類別</label>
          <select v-model="newBudget.category_id" class="input">
            <option :value="null">總預算</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.icon }} {{ cat.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>金額上限</label>
          <input v-model.number="newBudget.limit_amount" type="number" class="input" placeholder="金額" />
        </div>
        <div class="form-group">
          <label>週期</label>
          <select v-model="newBudget.period" class="input">
            <option value="monthly">每月</option>
            <option value="weekly">每週</option>
          </select>
        </div>
      </div>
      <button @click="createBudget" class="btn btn-accent" style="margin-top: var(--space-sm);">建立</button>
    </div>
    
    <div v-if="isLoading" class="loading-container">
      <span class="loading"></span> 載入中...
    </div>
    
    <div v-else-if="budgets.length === 0" class="empty-state card">
      <p>尚未設定預算</p>
      <p class="text-muted" style="margin-top: var(--space-sm);">點擊「新增」開始</p>
    </div>
    
    <div v-else class="budget-grid">
      <div v-for="budget in budgets" :key="budget.id" class="card budget-card">
        <div class="budget-header">
          <span class="budget-icon">{{ budget.category_icon }}</span>
          <span class="budget-name">{{ budget.category_name }}</span>
          <span class="badge" :class="'badge-' + getStatusClass(budget.rate)">
            {{ budget.period === 'weekly' ? '週' : '月' }}
          </span>
        </div>
        
        <div class="budget-progress">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :class="getStatusClass(budget.rate)"
              :style="{ width: Math.min(budget.rate, 100) + '%' }"
            ></div>
          </div>
          <div class="progress-info">
            <span>${{ formatAmount(budget.used) }} / ${{ formatAmount(budget.limit_amount) }}</span>
            <span :class="'text-' + getStatusClass(budget.rate)">{{ Math.round(budget.rate) }}%</span>
          </div>
        </div>
        
        <div class="budget-footer">
          <span class="text-muted">剩餘 ${{ formatAmount(budget.remaining) }}</span>
          <button @click="deleteBudget(budget.id)" class="btn btn-danger btn-sm">刪除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-md);
}

.budget-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.budget-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.budget-icon {
  font-size: 24px;
}

.budget-name {
  flex: 1;
  font-size: var(--font-sm);
}

.budget-progress {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-xs);
}

.budget-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-sm);
  border-top: 1px dashed var(--color-border);
}

@media (max-width: 480px) {
  .budget-grid {
    grid-template-columns: 1fr;
  }
}
</style>
