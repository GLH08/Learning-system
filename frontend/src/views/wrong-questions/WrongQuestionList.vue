<template>
  <div class="wrong-question-page">
    <n-card title="错题本">
      <n-space vertical :size="16">
        <!-- 统计卡片 -->
        <n-grid :cols="3" :x-gap="16">
          <n-gi>
            <n-statistic label="总错题数" :value="wrongQuestionStore.stats.total" />
          </n-gi>
          <n-gi>
            <n-statistic label="已掌握" :value="wrongQuestionStore.stats.mastered" />
          </n-gi>
          <n-gi>
            <n-statistic label="未掌握" :value="wrongQuestionStore.stats.unmastered" />
          </n-gi>
        </n-grid>
        
        <!-- 筛选和操作 -->
        <n-space justify="space-between">
          <n-select
            v-model:value="filters.mastered"
            :options="masteredOptions"
            placeholder="掌握状态"
            clearable
            style="width: 150px"
            @update:value="fetchData"
          />
          
          <n-space>
            <n-button type="primary" @click="handleGenerateExam">
              生成错题试卷
            </n-button>
          </n-space>
        </n-space>
        
        <!-- 错题列表 -->
        <div v-for="wq in wrongQuestionStore.wrongQuestions" :key="wq.id" class="wrong-question-item">
          <n-card>
            <template #header>
              <n-space align="center">
                <n-tag :type="wq.question?.difficulty === 'easy' ? 'success' : wq.question?.difficulty === 'hard' ? 'error' : 'warning'">
                  {{ getDifficultyLabel(wq.question?.difficulty) }}
                </n-tag>
                <n-tag>{{ getTypeLabel(wq.question?.type) }}</n-tag>
                <n-tag type="error">错误 {{ wq.wrong_count }} 次</n-tag>
                <n-tag v-if="wq.mastered" type="success">已掌握</n-tag>
              </n-space>
            </template>
            
            <template #header-extra>
              <n-space>
                <n-button
                  v-if="!wq.mastered"
                  size="small"
                  type="success"
                  @click="handleMaster(wq.id)"
                >
                  标记掌握
                </n-button>
                <n-button
                  v-else
                  size="small"
                  @click="handleUnmaster(wq.id)"
                >
                  取消掌握
                </n-button>
                <n-button
                  size="small"
                  type="error"
                  @click="handleDelete(wq.id)"
                >
                  删除
                </n-button>
              </n-space>
            </template>
            
            <n-space vertical>
              <div class="question-content">
                {{ wq.question?.content }}
              </div>
              
              <div v-if="wq.question?.options" class="question-options">
                <div v-for="(value, key) in parseOptions(wq.question.options)" :key="key">
                  {{ key }}. {{ value }}
                </div>
              </div>
              
              <n-space>
                <div>
                  <strong>你的答案：</strong>
                  <n-tag type="error">{{ wq.user_answer || '未作答' }}</n-tag>
                </div>
                <div>
                  <strong>正确答案：</strong>
                  <n-tag type="success">{{ wq.correct_answer }}</n-tag>
                </div>
              </n-space>
              
              <div v-if="wq.question?.explanation" class="explanation">
                <strong>解析：</strong>
                <div style="margin-top: 8px; padding: 12px; background-color: #f5f5f5; border-radius: 4px;">
                  {{ wq.question.explanation }}
                </div>
              </div>
              
              <n-space>
                <span style="color: #999; font-size: 12px;">
                  最后错误时间：{{ new Date(wq.last_wrong_time).toLocaleString() }}
                </span>
              </n-space>
            </n-space>
          </n-card>
        </div>
        
        <n-empty v-if="!wrongQuestionStore.loading && wrongQuestionStore.wrongQuestions.length === 0" description="暂无错题" />
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  useMessage,
  useDialog,
  NCard,
  NSpace,
  NGrid,
  NGi,
  NStatistic,
  NSelect,
  NButton,
  NTag,
  NEmpty
} from 'naive-ui'
import { useWrongQuestionStore } from '@/stores/wrongQuestion'
import { examsApi } from '@/api/exams'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const wrongQuestionStore = useWrongQuestionStore()

const filters = ref({
  mastered: null as number | null
})

const masteredOptions = [
  { label: '未掌握', value: 0 },
  { label: '已掌握', value: 1 }
]

async function fetchData() {
  await wrongQuestionStore.fetchWrongQuestions({
    mastered: filters.value.mastered !== null ? filters.value.mastered : undefined
  })
  await wrongQuestionStore.fetchStats()
}

function parseOptions(options?: string) {
  if (!options) return {}
  try {
    return JSON.parse(options)
  } catch {
    return {}
  }
}

function getDifficultyLabel(difficulty?: string) {
  const map: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return map[difficulty || ''] || difficulty || ''
}

function getTypeLabel(type?: string) {
  const map: Record<string, string> = {
    single: '单选',
    multiple: '多选',
    judge: '判断',
    essay: '简述'
  }
  return map[type || ''] || type || ''
}

async function handleMaster(id: string) {
  try {
    await wrongQuestionStore.markAsMastered(id)
    message.success('已标记为掌握')
  } catch (error: any) {
    message.error('操作失败')
  }
}

async function handleUnmaster(id: string) {
  try {
    await wrongQuestionStore.markAsUnmastered(id)
    message.success('已取消掌握标记')
  } catch (error: any) {
    message.error('操作失败')
  }
}

function handleDelete(id: string) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这道错题吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await wrongQuestionStore.deleteWrongQuestion(id)
        message.success('删除成功')
      } catch (error: any) {
        message.error('删除失败')
      }
    }
  })
}

// 生成错题试卷
async function handleGenerateExam() {
  dialog.info({
    title: '生成错题试卷',
    content: '将使用当前筛选的错题生成试卷，确定继续吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const exam = await examsApi.generateWrongQuestionExam({
          title: '错题专项练习',
          mode: 'practice',
          mastered: filters.value.mastered !== null ? filters.value.mastered : undefined
        })
        message.success('试卷生成成功')
        router.push(`/exams/${exam.id}/answer`)
      } catch (error: any) {
        message.error('生成试卷失败')
      }
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.wrong-question-page {
  padding: 20px;
}

.wrong-question-item {
  margin-bottom: 16px;
}

.question-content {
  font-size: 16px;
  line-height: 1.8;
}

.question-options {
  margin-left: 20px;
  margin-top: 12px;
}

.explanation {
  margin-top: 12px;
}
</style>
