<template>
  <n-card title="导入题目">
    <n-steps :current="currentStep" :status="stepStatus">
      <n-step title="上传文件" />
      <n-step title="预览数据" />
      <n-step title="确认导入" />
    </n-steps>
    
    <n-divider />
    
    <!-- Step 1: Upload File -->
    <div v-if="currentStep === 1">
      <n-space vertical :size="16">
        <n-alert type="info" title="支持的文件格式">
          <ul>
            <li>Word 文档 (.docx)</li>
            <li>Excel 表格 (.xlsx)</li>
            <li>文本文件 (.txt)</li>
            <li>JSON 文件 (.json)</li>
          </ul>
        </n-alert>
        
        <n-upload
          :custom-request="handleUpload"
          :show-file-list="true"
          :max="1"
          accept=".docx,.xlsx,.txt,.json"
          @before-upload="handleBeforeUpload"
        >
          <n-button>选择文件</n-button>
        </n-upload>
        
        <n-space v-if="uploadedFile">
          <n-button type="primary" :loading="parsing" @click="handlePreview">
            解析预览
          </n-button>
          <n-button @click="handleReset">
            重新选择
          </n-button>
        </n-space>
      </n-space>
    </div>
    
    <!-- Step 2: Preview Data -->
    <div v-if="currentStep === 2">
      <n-space vertical :size="16">
        <n-card title="解析统计" size="small">
          <n-descriptions :column="3" bordered size="small">
            <n-descriptions-item label="总数">
              {{ statistics.total }}
            </n-descriptions-item>
            <n-descriptions-item label="成功">
              <n-tag type="success">{{ statistics.success }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="警告">
              <n-tag type="warning">{{ statistics.warning }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="完整题目">
              {{ statistics.complete }}
            </n-descriptions-item>
            <n-descriptions-item label="有答案">
              {{ statistics.hasAnswer }}
            </n-descriptions-item>
            <n-descriptions-item label="仅题干">
              {{ statistics.onlyContent }}
            </n-descriptions-item>
          </n-descriptions>
          
          <n-divider />
          
          <n-space>
            <span>题型分布：</span>
            <n-tag v-for="(count, type) in statistics.byType" :key="type">
              {{ typeMap[type] || type }}: {{ count }}
            </n-tag>
          </n-space>
        </n-card>
        
        <n-form inline>
          <n-form-item label="目标分类">
            <n-select
              v-model:value="importConfig.categoryId"
              :options="categoryOptions"
              placeholder="选择分类（可选）"
              clearable
              style="width: 200px"
            />
          </n-form-item>
          
          <n-form-item label="默认难度">
            <n-select
              v-model:value="importConfig.defaultDifficulty"
              :options="difficultyOptions"
              style="width: 120px"
            />
          </n-form-item>
          
          <n-form-item label="跳过错误">
            <n-switch v-model:value="importConfig.skipErrors" />
          </n-form-item>

          <n-form-item label="跳过重复">
            <n-switch v-model:value="importConfig.skipDuplicates" />
          </n-form-item>
        </n-form>
        
        <n-data-table
          :columns="previewColumns"
          :data="previewQuestions"
          :pagination="{ pageSize: 10 }"
          :max-height="400"
        />
        
        <n-space>
          <n-button @click="currentStep = 1">
            上一步
          </n-button>
          <n-button type="primary" @click="handleImport" :loading="importing">
            确认导入
          </n-button>
        </n-space>
      </n-space>
    </div>
    
    <!-- Step 3: Import Result -->
    <div v-if="currentStep === 3">
      <n-result
        :status="importResult.success > 0 ? 'success' : 'error'"
        :title="importResult.success > 0 ? '导入成功' : '导入失败'"
      >
        <template #description>
          <div style="text-align: center">
             <p>成功导入 {{ importResult.success }} 道题目</p>
             <p v-if="importResult.failed > 0" style="color: #d03050">失败 {{ importResult.failed }} 道</p>
             <p v-if="importResult.skipped > 0" style="color: #f0a020">跳过重复 {{ importResult.skipped }} 道</p>
          </div>
        </template>
        <template #footer>
          <n-space>
            <n-button type="primary" @click="$router.push('/questions')">
              查看题目列表
            </n-button>
            <n-button @click="handleReset">
              继续导入
            </n-button>
          </n-space>
        </template>
      </n-result>
      
      <n-card v-if="importResult.errors && importResult.errors.length > 0" title="错误详情" style="margin-top: 16px">
        <n-list bordered>
          <n-list-item v-for="error in importResult.errors" :key="error.line">
            第 {{ error.line }} 题: {{ error.message }}
          </n-list-item>
        </n-list>
      </n-card>

      <n-card v-if="importResult.skippedDetails && importResult.skippedDetails.length > 0" title="跳过详情" style="margin-top: 16px">
        <n-list bordered>
          <n-list-item v-for="skip in importResult.skippedDetails" :key="skip.line">
            第 {{ skip.line }} 题: {{ skip.message }}
          </n-list-item>
        </n-list>
      </n-card>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NSteps, NStep, NDivider, NSpace, NAlert, NUpload, NButton,
  NDescriptions, NDescriptionsItem, NTag, NForm, NFormItem, NSelect, NSwitch,
  NDataTable, NResult, NList, NListItem, NText,
  UploadCustomRequestOptions
} from 'naive-ui'
import { useCategoryStore } from '@/stores/category'
import { useMessage } from '@/composables/useMessage'
import api from '@/api'
import type { DataTableColumns } from 'naive-ui'

const router = useRouter()
const categoryStore = useCategoryStore()
const message = useMessage()

const currentStep = ref(1)
const stepStatus = ref<'process' | 'finish' | 'error' | 'wait'>('process')
const uploadedFile = ref<File | null>(null)
const parsing = ref(false)
const importing = ref(false)

const previewQuestions = ref<any[]>([])
const statistics = ref({
  total: 0,
  success: 0,
  warning: 0,
  duplicate: 0,
  complete: 0,
  hasAnswer: 0,
  onlyContent: 0,
  byType: {} as Record<string, number>
})

const importConfig = reactive({
  categoryId: undefined as string | undefined,
  defaultDifficulty: 'medium',
  skipErrors: true,
  skipDuplicates: true,
  autoAIComplete: false
})

const importResult = ref({
  success: 0,
  failed: 0,
  skipped: 0,
  errors: [] as any[],
  skippedDetails: [] as any[]
})

const typeMap: Record<string, string> = {
  single: '单选题',
  multiple: '多选题',
  judge: '判断题',
  essay: '简述题',
  unknown: '未知'
}

const categoryOptions = computed(() => {
  return categoryStore.categories.map(cat => ({
    label: cat.name,
    value: cat.id
  }))
})

const difficultyOptions = [
  { label: '简单', value: 'easy' },
  { label: '中等', value: 'medium' },
  { label: '困难', value: 'hard' }
]

const previewColumns: DataTableColumns<any> = [
  {
    title: '序号',
    key: 'index',
    width: 80
  },
  {
    title: '题型',
    key: 'type',
    width: 100,
    render: (row) => typeMap[row.type] || row.type
  },
  {
    title: '题目内容',
    key: 'content',
    ellipsis: true,
    render: (row) => {
        return h('div', [
             h('span', row.content),
             row.isDuplicate ? h(NTag, { type: 'warning', size: 'small', style: 'margin-left: 8px' }, { default: () => '重复' }) : null
        ])
    }
  },
  {
    title: '答案',
    key: 'hasAnswer',
    width: 80,
    render: (row) => h(NTag, { type: row.hasAnswer ? 'success' : 'default' }, 
      { default: () => row.hasAnswer ? '有' : '无' })
  },
  {
    title: '解析',
    key: 'hasExplanation',
    width: 80,
    render: (row) => h(NTag, { type: row.hasExplanation ? 'success' : 'default' }, 
      { default: () => row.hasExplanation ? '有' : '无' })
  },
  {
    title: '状态',
    key: 'parseStatus',
    width: 100,
    render: (row) => {
      const statusMap: Record<string, { label: string; type: any }> = {
        success: { label: '成功', type: 'success' },
        warning: { label: '警告', type: 'warning' },
        error: { label: '错误', type: 'error' }
      }
      const status = statusMap[row.parseStatus] || { label: row.parseStatus, type: 'default' }
      return h(NTag, { type: status.type }, { default: () => status.label })
    }
  }
]

const handleBeforeUpload = (options: { file: File }) => {
  const file = options.file
  const validTypes = [
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'application/json'
  ]
  
  if (!validTypes.includes(file.type) && !file.name.match(/\.(docx|xlsx|txt|json)$/i)) {
    message.error('不支持的文件格式')
    return false
  }
  
  if (file.size > 10 * 1024 * 1024) {
    message.error('文件大小不能超过 10MB')
    return false
  }
  
  return true
}

const handleUpload = (options: UploadCustomRequestOptions) => {
  uploadedFile.value = options.file.file as File
  message.success('文件已选择')
}

const handlePreview = async () => {
  if (!uploadedFile.value) {
    message.error('请先选择文件')
    return
  }
  
  try {
    parsing.value = true
    
    const formData = new FormData()
    formData.append('file', uploadedFile.value)
    
    const response = await api.post('/questions/import/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    previewQuestions.value = response.data.questions
    statistics.value = response.data.statistics
    
    currentStep.value = 2
    message.success('解析成功')
  } catch (error) {
    message.error('解析失败')
  } finally {
    parsing.value = false
  }
}

const handleImport = async () => {
  try {
    importing.value = true
    
    const response = await api.post('/questions/import', previewQuestions.value, {
      params: {
        categoryId: importConfig.categoryId,
        defaultDifficulty: importConfig.defaultDifficulty,
        skipErrors: importConfig.skipErrors,
        skipDuplicates: importConfig.skipDuplicates
      }
    })
    
    importResult.value = {
      success: response.data.success,
      failed: response.data.failed,
      skipped: response.data.skipped,
      errors: response.data.errors || [],
      skippedDetails: response.data.skippedDetails || []
    }
    
    currentStep.value = 3
    stepStatus.value = 'finish'
  } catch (error) {
    message.error('导入失败')
    stepStatus.value = 'error'
  } finally {
    importing.value = false
  }
}

const handleReset = () => {
  currentStep.value = 1
  stepStatus.value = 'process'
  uploadedFile.value = null
  previewQuestions.value = []
  statistics.value = {
    total: 0,
    success: 0,
    warning: 0,
    complete: 0,
    hasAnswer: 0,
    onlyContent: 0,
    byType: {}
  }
  importResult.value = {
    success: 0,
    failed: 0,
    errors: []
  }
}

onMounted(() => {
  categoryStore.fetchCategories()
})
</script>
