<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { API_BASE } from '../config'

interface Message {
  id: number
  text: string
  type: 'user' | 'bot'
  timestamp: Date
  data?: any
}
const messages = ref<Message[]>([])
const inputText = ref('')
const isLoading = ref(false)
const isRecording = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

let recognition: any = null

onMounted(() => {
  addBotMessage('👋 歡迎使用 FinBot！\n\n試試看：\n• 「午餐 120 元」\n• 「昨天搭捷運 35」\n• 「這個月花了多少？」')
  
  if ('webkitSpeechRecognition' in window) {
    recognition = new (window as any).webkitSpeechRecognition()
    recognition.lang = 'zh-TW'
    recognition.continuous = false
    recognition.interimResults = false
    
    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript
      inputText.value = text
      sendMessage()
    }
    
    recognition.onend = () => { isRecording.value = false }
    recognition.onerror = () => {
      isRecording.value = false
      addBotMessage('❌ 語音識別失敗，請重試')
    }
  }
})

function addBotMessage(text: string, data?: any) {
  messages.value.push({
    id: Date.now(),
    text,
    type: 'bot',
    timestamp: new Date(),
    data
  })
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return
  
  messages.value.push({
    id: Date.now(),
    text,
    type: 'user',
    timestamp: new Date()
  })
  
  inputText.value = ''
  isLoading.value = true
  scrollToBottom()
  
  try {
    const response = await fetch(`${API_BASE}/chat/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, source: 'text' })
    })
    
    const data = await response.json()
    addBotMessage(data.message, data.data)
    
    if (data.type === 'confirmation' && 'speechSynthesis' in window) {
      const shortMsg = `已記錄 ${data.data?.amount || ''} 元`
      const utterance = new SpeechSynthesisUtterance(shortMsg)
      utterance.lang = 'zh-TW'
      speechSynthesis.speak(utterance)
    }
  } catch {
    addBotMessage('❌ 連接失敗，請確認後端是否運行')
  } finally {
    isLoading.value = false
  }
}

function toggleVoice() {
  if (!recognition) {
    addBotMessage('⚠️ 請使用 Chrome 或 Edge 瀏覽器')
    return
  }
  
  if (isRecording.value) {
    recognition.stop()
  } else {
    isRecording.value = true
    recognition.start()
  }
}

function formatTime(date: Date) {
  return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="chat-container">
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.type">
        <div class="message-bubble">
          <pre class="message-text">{{ msg.text }}</pre>
        </div>
        <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
      </div>
      
      <div v-if="isLoading" class="message bot">
        <div class="message-bubble">
          <span class="loading"></span> 處理中...
        </div>
      </div>
    </div>
    
    <div class="chat-input-container">
      <input 
        v-model="inputText"
        @keyup.enter="sendMessage"
        class="input chat-input"
        placeholder="輸入記帳內容..."
        :disabled="isLoading"
      />
      <button 
        @click="toggleVoice" 
        class="btn voice-btn"
        :class="{ recording: isRecording }"
        :title="isRecording ? '停止錄音' : '語音輸入'"
      >
        {{ isRecording ? '⏹️' : '🎤' }}
      </button>
      <button @click="sendMessage" class="btn" :disabled="isLoading || !inputText.trim()">
        送出
      </button>
    </div>
  </div>
</template>

<style scoped>
.message-text {
  white-space: pre-wrap;
  font-family: inherit;
  font-size: inherit;
  margin: 0;
}
</style>
