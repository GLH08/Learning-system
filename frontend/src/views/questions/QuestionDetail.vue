<template>
  <n-spin :show="questionStore.loading">
    <n-card v-if="question" :title="`题目详情 - ${question.id}`">
      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="题型">
          {{ typeMap[question.type] || question.type }}
        </n-descriptions-item>
        <n-descriptions-item label="难度">
          <n-tag :type="difficultyMap[question.difficulty]?.type">
            {{ difficultyMap[question.difficulty]?.label || question.difficulty }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="题目内容" :span="2">
          {{ question.content }}
        </n-descriptions-item>
        <n-descriptions-item v-if="question.options" label="选项" :span="2">
          <n-space vertical>
            <div v-for="(value, key) in question.options" :key="key">
              <strong>{{ key }}.</strong> {{ value }}
            </div>
          </n-space>
        </n-descriptions-item>
        <n-descriptions-item label="答案">
          {{ question.answer || '未设置' }}
        </n-descriptions-item>
        <n-descriptions-item label="答案状态">
          <n-tag :type="statusMap[question.answerStatus]?.type">
            {{ statusMap[question.answerStatus]?.label }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="解析" :span="2">
          <div style="white-space: pre-wrap; max-height: 300px; overflow-y: auto">
            {{ question.explanation || '未设置' }}
          </div>
        </n-descriptions-item>
        <n-descriptions-item label="解析状态" :span="2">
          <n-tag :type="statusMap[question.explanationStatus]?.type">
            {{ statusMap[question.explanationStatus]?.label }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="创建时间">
          {{ formatDate(question.createdAt) }}
        </n-descriptions-item>
        <n-descriptions-item label="更新时间">
          {{ formatDate(question.updatedAt) }}
        </n-descriptions-item>
      </n-descriptions>
      
      <template #footer>
        <n-space>
          <n-button @click="$router.back()">返回</n-button>
          <n-button type="primary" @click="handleEdit">编辑</n-button>
          <n-button type="info" @click="openAIModal">
            AI 补全/重新生成
          </n-button>
        </n-space>
      </template>
    </n-card>
  </n-spin>
  
  <!-- AI Complete Modal -->
  <n-modal v-model:show="showAICompleteModal" preset="card" title="AI 补全" style="width: 600px">
    <!-- 内容区域 -->
    <div v-if="aiStatus === 'idle'">
      <n-form>
        <n-form-item label="补全类型">
          <n-radio-group v-model:value="aiCompleteType">
            <n-space vertical>
              <n-radio value="answer">
                仅答案{{ question?.answerStatus === 'confirmed' ? '（将覆盖已确认内容）' : '' }}
              </n-radio>
              <n-radio value="explanation">
                仅解析{{ question?.explanationStatus === 'confirmed' ? '（将覆盖已确认内容）' : '' }}
              </n-radio>
              <n-radio value="both">
                答案+解析
              </n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>
      </n-form>
    </div>
    
    <div v-else-if="aiStatus === 'loading'">
      <n-space vertical align="center" style="padding: 40px 0">
        <n-spin size="large" />
        <n-text>正在调用 AI 生成{{ aiCompleteType === 'answer' ? '答案' : aiCompleteType === 'explanation' ? '解析' : '答案和解析' }}...</n-text>
        <n-text depth="3">请稍候，这可能需要几秒钟</n-text>
      </n-space>
    </div>
    
    <div v-else-if="aiStatus === 'success'">
      <n-alert type="success" title="补全成功" style="margin-bottom: 16px">
        AI 已成功生成内容，请查看下方结果
      </n-alert>
      <n-space vertical>
        <n-card v-if="aiResult.answer" title="生成的答案" size="small">
          <n-text>{{ aiResult.answer }}</n-text>
        </n-card>
        <n-card v-if="aiResult.explanation" title="生成的解析" size="small">
          <n-text style="white-space: pre-wrap">{{ aiResult.explanation }}</n-text>
        </n-card>
      </n-space>
    </div>
    
    <div v-else-if="aiStatus === 'error'">
      <n-alert type="error" title="补全失败" style="margin-bottom: 16px">
        {{ aiErrorMessage }}
      </n-alert>
      <n-collapse>
        <n-collapse-item title="错误详情" name="detail">
          <pre style="white-space: pre-wrap; word-break: break-all">{{ aiErrorDetail }}</pre>
        </n-collapse-item>
      </n-collapse>
    </div>
    
    <!-- 底部按钮 -->
    <template #footer>
      <n-space justify="end">
        <template v-if="aiStatus === 'idle'">
          <n-button @click="showAICompleteModal = false">取消</n-button>
          <n-button type="primary" @click="handleAIComplete">开始补全</n-button>
        </template>
        <template v-else-if="aiStatus === 'loading'">
          <n-button disabled>处理中...</n-button>
        </template>
        <template v-else-if="aiStatus === 'success'">
          <n-button @click="closeAndRefresh">关闭</n-button>
        </template>
        <template v-else-if="aiStatus === 'error'">
          <n-button @click="resetAIStatus">重试</n-button>
          <n-button @click="showAICompleteModal = false">关闭</n-button>
        </template>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  NSpin, NCard, NDescriptions, NDescriptionsItem, NTag, NSpace, NButton, 
  NModal, NForm, NFormItem, NRadioGroup, NRadio, NAlert, NText, NCollapse, NCollapseItem
} from 'naive-ui'
import { useQuestionStore } from '@/stores/question'
import { useAIStore } from '@/stores/ai'
import { useMessage } from '@/composables/useMessage'
import type { Question } from '@/api/questions'

const route = useRoute()
const router = useRouter()
const questionStore = useQuestionStore()
const aiStore = useAIStore()
const message = useMessage()

const question = ref<Question | null>(null)
const showAICompleteModal = ref(false)
const aiCompleteType = ref<'answer' | 'explanation' | 'both'>('both')

// AI 补全状态
const aiStatus = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const aiResult = ref<{ answer?: string; explanation?: string }>({})
const aiErrorMessage = ref('')
const aiErrorDetail = ref('')

const typeMap: Record<string, string> = {
  single: '单选题',
  multiple: '多选题',
  judge: '判断题',
  essay: '简述题'
}

const difficultyMap: Record<string, { label: string; type: any }> = {
  easy: { label: '简单', type: 'success' },
  medium: { label: '中等', type: 'warning' },
  hard: { label: '困难', type: 'error' }
}

const statusMap: Record<string, { label: string; type: any }> = {
  none: { label: '未设置', type: 'default' },
  ai_pending: { label: 'AI生成中', type: 'info' },
  ai_generated: { label: 'AI已生成', type: 'warning' },
  confirmed: { label: '已确认', type: 'success' }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const handleEdit = () => {
  router.push(`/questions/${question.value?.id}/edit`)
}

const openAIModal = () => {
  aiStatus.value = 'idle'
  aiResult.value = {}
  aiErrorMessage.value = ''
  aiErrorDetail.value = ''
  showAICompleteModal.value = true
}

const resetAIStatus = () => {
  aiStatus.value = 'idle'
}

const closeAndRefresh = async () => {
  showAICompleteModal.value = false
  if (question.value) {
    question.value = await questionStore.fetchQuestion(question.value.id)
  }
}

const handleAIComplete = async () => {
  if (!question.value) return
  
  aiStatus.value = 'loading'
  
  try {
    const result = await aiStore.completeQuestion({
      questionId: question.value.id,
      type: aiCompleteType.value
    })
    
    aiResult.value = {
      answer: result.answer,
      explanation: result.explanation
    }
    aiStatus.value = 'success'
    message.success('AI 补全成功')
    
  } catch (error: any) {
    aiStatus.value = 'error'
    
    if (error.response?.data?.message) {
      aiErrorMessage.value = error.response.data.message
    } else if (error.message) {
      aiErrorMessage.value = error.message
    } else {
      aiErrorMessage.value = '未知错误'
    }
    
    aiErrorDetail.value = JSON.stringify(error.response?.data || error, null, 2)
    message.error(`AI 补全失败: ${aiErrorMessage.value}`)
  }
}

onMounted(async () => {
  const id = route.params.id as string
  question.value = await questionStore.fetchQuestion(id)
})
</script>
