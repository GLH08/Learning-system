<template>
  <div>
    <n-space vertical :size="24">
      <!-- 欢迎卡片 -->
      <n-card title="欢迎使用智能答题学习系统">
        <p class="text-gray-600">通过答题系统学习、巩固知识，支持AI自动补全答案与解析</p>
      </n-card>
      
      <!-- 统计卡片 -->
      <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <n-gi :span="24 / 4">
          <n-card>
            <n-statistic label="题目总数" :value="stats?.total || 0">
              <template #prefix>📝</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi :span="24 / 4">
          <n-card>
            <n-statistic label="待补全" :value="stats?.incomplete || 0">
              <template #prefix>⏳</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi :span="24 / 4">
          <n-card>
            <n-statistic label="已完成" :value="(stats?.total || 0) - (stats?.incomplete || 0)">
              <template #prefix>✅</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi :span="24 / 4">
          <n-card>
            <n-statistic label="完成率" :value="completionRate">
              <template #suffix>%</template>
              <template #prefix>📊</template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 快速开始和待处理任务 -->
      <n-grid :cols="2" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <n-gi :span="24 / 2">
          <n-card title="🚀 快速开始">
            <n-space vertical :size="12">
              <n-button type="primary" size="large" block @click="$router.push('/exams/config')">
                📝 开始随机答题
              </n-button>
              <n-button size="large" block @click="$router.push('/exams/config')">
                ⚙️ 自定义组卷
              </n-button>
              <n-button size="large" block @click="$router.push('/wrong-questions')">
                ❌ 错题重做
              </n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi :span="24 / 2">
          <n-card title="📋 待处理任务">
            <n-space vertical :size="12">
              <div class="flex justify-between items-center p-3 bg-yellow-50 rounded-lg" v-if="(stats?.incomplete || 0) > 0">
                <span>⚠️ {{ stats?.incomplete || 0 }} 道题目待补全答案/解析</span>
                <n-button size="small" type="warning" @click="$router.push({ path: '/questions', query: { status: 'incomplete' } })">
                  批量AI补全
                </n-button>
              </div>
              <div class="flex justify-between items-center p-3 bg-green-50 rounded-lg" v-else>
                <span>✅ 所有题目已完善</span>
              </div>
              <div class="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                <span>❌ 错题待复习</span>
                <n-button size="small" type="error" @click="$router.push('/wrong-questions')">
                  进入错题本
                </n-button>
              </div>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 题库操作 -->
      <n-card title="题库操作">
        <n-space>
          <n-button type="primary" @click="$router.push('/questions/create')">
            ➕ 创建题目
          </n-button>
          <n-button @click="$router.push('/questions')">
            📚 题目列表
          </n-button>
          <n-button @click="$router.push('/categories')">
            📁 分类管理
          </n-button>
          <n-button @click="$router.push('/questions/import')">
            📥 导入题目
          </n-button>
        </n-space>
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { NSpace, NCard, NGrid, NGi, NStatistic, NButton } from 'naive-ui'
import { useQuestionStore } from '@/stores/question'

const questionStore = useQuestionStore()

const stats = computed(() => questionStore.stats)

const completionRate = computed(() => {
  if (!stats.value || stats.value.total === 0) return 0
  const complete = stats.value.total - stats.value.incomplete
  return Math.round((complete / stats.value.total) * 100)
})

onMounted(() => {
  questionStore.fetchQuestionStats()
})
</script>

<style scoped>
.flex {
  display: flex;
}
.justify-between {
  justify-content: space-between;
}
.items-center {
  align-items: center;
}
.p-3 {
  padding: 0.75rem;
}
.rounded-lg {
  border-radius: 0.5rem;
}
.bg-yellow-50 {
  background-color: #fefce8;
}
.bg-green-50 {
  background-color: #f0fdf4;
}
.bg-red-50 {
  background-color: #fef2f2;
}
</style>

