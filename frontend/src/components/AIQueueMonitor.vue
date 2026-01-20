<template>
  <transition name="slide-up">
    <div v-if="aiQueueStore.hasPending || aiQueueStore.totalCount > 0" class="ai-queue-monitor">
      <n-card size="small" :bordered="false" class="monitor-card">
        <template #header>
          <div class="header-content">
            <n-space align="center">
              <span class="title">AI 补全队列</span>
              <n-tag :type="statusType" size="small" round>
                {{ statusText }}
              </n-tag>
            </n-space>
            <n-space size="small">
               <n-button text size="tiny" @click="toggleExpand">
                 <template #icon>
                   <span>{{ isExpanded ? '🔽' : '🔼' }}</span>
                 </template>
               </n-button>
               <n-button text size="tiny" @click="handleClose">✖</n-button>
            </n-space>
          </div>
        </template>
        
        <div v-if="isExpanded" class="queue-stats">
          <n-grid :cols="4" class="stats-grid">
            <n-gi><div class="stat-item processing"><span class="label">进行中</span><span class="value">{{ aiQueueStore.processingCount }}</span></div></n-gi>
            <n-gi><div class="stat-item pending"><span class="label">等待</span><span class="value">{{ aiQueueStore.pendingCount }}</span></div></n-gi>
            <n-gi><div class="stat-item success"><span class="label">成功</span><span class="value">{{ aiQueueStore.completedCount }}</span></div></n-gi>
            <n-gi><div class="stat-item failed"><span class="label">失败</span><span class="value">{{ aiQueueStore.failedCount }}</span></div></n-gi>
          </n-grid>
          
          <n-progress
            type="line"
            :percentage="percentage"
            :indicator-placement="'inside'"
            :processing="aiQueueStore.isProcessing"
            class="progress-bar"
          />
          
          <n-space justify="center" size="small" class="actions">
             <n-button 
               size="small" 
               :type="aiQueueStore.isPaused ? 'success' : 'warning'"
               @click="togglePause"
             >
               {{ aiQueueStore.isPaused ? '继续' : '暂停' }}
             </n-button>
             
             <n-button 
               v-if="aiQueueStore.failedCount > 0"
               size="small" 
               type="error"
               @click="aiQueueStore.retryFailed"
             >
               重试失败
             </n-button>
             
             <n-button size="small" @click="aiQueueStore.clearCompleted">
               清除已完成
             </n-button>
          </n-space>
        </div>
        
        <div v-else class="mini-status">
           <span>进度: {{ aiQueueStore.completedCount }}/{{ aiQueueStore.totalCount }}</span>
           <n-progress 
             type="line" 
             :percentage="percentage" 
             :show-indicator="false" 
             style="width: 100px; display: inline-block; margin-left: 10px" 
           />
        </div>
      </n-card>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NCard, NSpace, NTag, NButton, NProgress, NGrid, NGi } from 'naive-ui'
import { useAIQueueStore } from '@/stores/aiQueue'

const aiQueueStore = useAIQueueStore()
const isExpanded = ref(true)

const percentage = computed(() => {
  if (aiQueueStore.totalCount === 0) return 0
  return Math.round(((aiQueueStore.completedCount + aiQueueStore.failedCount) / aiQueueStore.totalCount) * 100)
})

const statusType = computed(() => {
  if (aiQueueStore.isPaused) return 'warning'
  if (aiQueueStore.processingCount > 0) return 'success'
  return 'default'
})

const statusText = computed(() => {
  if (aiQueueStore.isPaused) return '已暂停'
  if (aiQueueStore.processingCount > 0) return '处理中...'
  if (aiQueueStore.pendingCount > 0) return '等待中'
  return '空闲'
})

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const togglePause = () => {
  if (aiQueueStore.isPaused) {
    aiQueueStore.resume()
  } else {
    aiQueueStore.pause()
  }
}

const handleClose = () => {
    aiQueueStore.clearAll()
}
</script>

<style scoped>
.ai-queue-monitor {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 320px;
  z-index: 2000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
}

.monitor-card {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-weight: bold;
  font-size: 14px;
}

.stats-grid {
  margin: 12px 0;
  text-align: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-item .label {
  font-size: 12px;
  color: #666;
}

.stat-item .value {
  font-weight: bold;
  font-size: 16px;
}

.stat-item.processing .value { color: #18a058; }
.stat-item.pending .value { color: #f0a020; }
.stat-item.success .value { color: #18a058; }
.stat-item.failed .value { color: #d03050; }

.progress-bar {
  margin-bottom: 12px;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease-out;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
</style>
