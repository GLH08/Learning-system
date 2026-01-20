<template>
  <div>
    <n-space vertical :size="16">
      <n-card>
        <n-space justify="space-between">
          <n-space>
            <n-input
              v-model:value="filters.keyword"
              placeholder="搜索题目"
              clearable
              @update:value="handleSearch"
            >
              <template #prefix>🔍</template>
            </n-input>
            
            <n-select
              v-model:value="filters.categoryId"
              placeholder="分类"
              clearable
              filterable
              :options="categoryOptions"
              style="width: 140px"
              @update:value="handleSearch"
            />
            
            <n-select
              v-model:value="filters.type"
              placeholder="题型"
              clearable
              :options="typeOptions"
              style="width: 120px"
              @update:value="handleSearch"
            />
            
            <n-select
              v-model:value="filters.difficulty"
              placeholder="难度"
              clearable
              :options="difficultyOptions"
              style="width: 120px"
              @update:value="handleSearch"
            />
            
            <n-select
              v-model:value="filters.status"
              placeholder="状态"
              clearable
              :options="statusOptions"
              style="width: 120px"
              @update:value="handleSearch"
            />
          </n-space>
          
          <n-space>
            <n-button
              v-if="selectedIds.length > 0"
              type="primary"
              secondary
              @click="handleBatchAI"
            >
              批量 AI 补全 ({{ selectedIds.length }})
            </n-button>
            <n-button
              v-if="selectedIds.length > 0"
              type="error"
              @click="showBatchDeleteModal = true"
            >
              批量删除 ({{ selectedIds.length }})
            </n-button>
            <n-button @click="$router.push('/questions/import')">
              导入题目
            </n-button>
            <n-button @click="handleExport">
              导出题目
            </n-button>
            <n-button type="primary" @click="$router.push('/questions/create')">
              创建题目
            </n-button>
          </n-space>
        </n-space>
      </n-card>
      
      <n-card>
        <n-data-table
          :columns="columns"
          :data="questionStore.questions"
          :loading="questionStore.loading"
          :pagination="pagination"
          :row-key="(row: Question) => row.id"
          v-model:checked-row-keys="selectedIds"
          @update:page="handlePageChange"
        />
      </n-card>
    </n-space>
    
    <!-- Batch Delete Modal -->
    <n-modal
      v-model:show="showBatchDeleteModal"
      preset="dialog"
      title="批量删除确认"
      content="确定要删除选中的题目吗？此操作不可恢复。"
      positive-text="确定"
      negative-text="取消"
      :loading="batchDeleting"
      @positive-click="handleBatchDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NSpace, NCard, NInput, NSelect, NButton, NDataTable, NTag, NPopconfirm, NModal
} from 'naive-ui'
import { useQuestionStore } from '@/stores/question'
import { useAIQueueStore } from '@/stores/aiQueue'
import { categoriesApi, type Category } from '@/api/categories'
import { useMessage } from '@/composables/useMessage'
import type { DataTableColumns } from 'naive-ui'
import type { Question } from '@/api/questions'

const router = useRouter()
const route = useRoute()
const questionStore = useQuestionStore()
const aiQueueStore = useAIQueueStore()
const message = useMessage()

const categories = ref<Category[]>([])

const filters = reactive({
  keyword: '',
  categoryId: null,
  type: null,
  difficulty: null,
  status: null
})

const selectedIds = ref<string[]>([])
const showBatchDeleteModal = ref(false)
const batchDeleting = ref(false)

const categoryOptions = computed(() => {
  return categories.value.map(c => ({
    label: c.name,
    value: c.id
  }))
})

const fetchCategories = async () => {
    try {
        const res = await categoriesApi.getCategories()
        categories.value = res.data
    } catch(e) {
        console.error(e)
    }
}

const typeOptions = [
  { label: '单选题', value: 'single' },
  { label: '多选题', value: 'multiple' },
  { label: '判断题', value: 'judge' },
  { label: '简述题', value: 'essay' }
]

const difficultyOptions = [
  { label: '简单', value: 'easy' },
  { label: '中等', value: 'medium' },
  { label: '困难', value: 'hard' }
]

const statusOptions = [
  { label: '全部', value: 'all' },
  { label: '已完成', value: 'complete' },
  { label: '待补全', value: 'incomplete' }
]

const columns: DataTableColumns<Question> = [
  {
    type: 'selection'
  },
  {
    title: 'ID',
    key: 'id',
    width: 100,
    ellipsis: true
  },
  {
    title: '题目内容',
    key: 'content',
    ellipsis: true
  },
  {
    title: '题型',
    key: 'type',
    width: 100,
    render: (row) => {
      const typeMap: Record<string, string> = {
        single: '单选',
        multiple: '多选',
        judge: '判断',
        essay: '简述'
      }
      return typeMap[row.type] || row.type
    }
  },
  {
    title: '难度',
    key: 'difficulty',
    width: 100,
    render: (row) => {
      const diffMap: Record<string, { label: string; type: any }> = {
        easy: { label: '简单', type: 'success' },
        medium: { label: '中等', type: 'warning' },
        hard: { label: '困难', type: 'error' }
      }
      const diff = diffMap[row.difficulty] || { label: row.difficulty, type: 'default' }
      return h(NTag, { type: diff.type }, { default: () => diff.label })
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => {
      // 只有 none 状态才算待补全，ai_generated 和 confirmed 都算已有内容
      const answerOk = row.answerStatus !== 'none'
      const explanationOk = row.explanationStatus !== 'none'
      const isComplete = answerOk && explanationOk
      return h(
        NTag,
        { type: isComplete ? 'success' : 'warning' },
        { default: () => isComplete ? '已完成' : '待补全' }
      )
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) => {
      return h(NSpace, null, {
        default: () => [
          h(
            NButton,
            {
              size: 'small',
              onClick: () => router.push(`/questions/${row.id}`)
            },
            { default: () => '查看' }
          ),
          h(
            NPopconfirm,
            {
              onPositiveClick: () => handleDelete(row.id)
            },
            {
              trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
              default: () => '确定删除这道题目吗？'
            }
          )
        ]
      })
    }
  }
]

const pagination = computed(() => ({
  page: questionStore.page,
  pageSize: questionStore.pageSize,
  itemCount: questionStore.total,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100]
}))

const handleSearch = () => {
  questionStore.fetchQuestions({
    page: 1,
    pageSize: questionStore.pageSize,
    ...filters
  })
}

const handlePageChange = (page: number) => {
  questionStore.fetchQuestions({
    page,
    pageSize: questionStore.pageSize,
    ...filters
  })
}

const handleDelete = async (id: string) => {
  try {
    await questionStore.deleteQuestion(id)
    message.success('删除成功')
    handleSearch()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleBatchAI = () => {
  if (selectedIds.value.length === 0) return
  
  // Find full question objects for selected IDs
  // Since we only select from current page, this is safe
  const selectedQuestions = questionStore.questions.filter(q => selectedIds.value.includes(q.id))
  
  if (selectedQuestions.length === 0) {
     message.warning('未能找到选中的题目信息')
     return
  }
  
  aiQueueStore.addToQueue(selectedQuestions)
  selectedIds.value = [] // Clear selection
}

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) {
    message.warning('请选择要删除的题目')
    return false
  }
  
  try {
    batchDeleting.value = true
    const result = await questionStore.batchDeleteQuestions(selectedIds.value)
    message.success(`成功删除 ${result.deleted} 道题目`)
    selectedIds.value = []
    showBatchDeleteModal.value = false
    handleSearch()
    return true
  } catch (error) {
    return false
  } finally {
    batchDeleting.value = false
  }
}

const handleExport = async () => {
  try {
    const response = await questionStore.exportQuestionsJSON({
      ...filters,
      includeIncomplete: true
    })
    
    // Create download link
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `questions_${new Date().getTime()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('导出成功')
  } catch (error) {
    message.error('导出失败')
  }
}

onMounted(() => {
  fetchCategories()
  
  // Init filters from query
  if (route.query.status) {
    filters.status = route.query.status as any
  }
  if (route.query.categoryId) {
      filters.categoryId = route.query.categoryId as any
  }
  
  questionStore.fetchQuestions({
     page: 1,
     pageSize: questionStore.pageSize,
     ...filters
  })
})
</script>
