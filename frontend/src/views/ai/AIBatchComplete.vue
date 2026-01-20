<template>
  <n-card title="批量 AI 补全">
    <n-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-placement="top"
    >
      <n-form-item label="补全类型" path="type">
        <n-radio-group v-model:value="formData.type">
          <n-space>
            <n-radio value="answer">仅答案</n-radio>
            <n-radio value="explanation">仅解析</n-radio>
            <n-radio value="both">答案+解析</n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>
      
      <n-form-item label="选择方式">
        <n-radio-group v-model:value="selectionMode">
          <n-space vertical>
            <n-radio value="filter">按条件筛选</n-radio>
            <n-radio value="manual">手动选择题目</n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>
      
      <template v-if="selectionMode === 'filter'">
        <n-form-item label="分类">
          <n-select
            v-model:value="formData.filter.categoryId"
            :options="categoryOptions"
            placeholder="选择分类（可选）"
            clearable
          />
        </n-form-item>
        
        <n-form-item label="答案状态">
          <n-select
            v-model:value="formData.filter.answerStatus"
            :options="answerStatusOptions"
            placeholder="选择答案状态（可选）"
            clearable
          />
        </n-form-item>
        
        <n-form-item label="解析状态">
          <n-select
            v-model:value="formData.filter.explanationStatus"
            :options="explanationStatusOptions"
            placeholder="选择解析状态（可选）"
            clearable
          />
        </n-form-item>
      </template>
      
      <template v-else>
        <n-form-item label="选择题目">
          <n-button @click="showQuestionSelector = true">
            选择题目 (已选 {{ selectedQuestions.length }} 道)
          </n-button>
        </n-form-item>
      </template>
      
      <n-form-item>
        <n-space>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            创建任务
          </n-button>
          <n-button @click="$router.back()">
            取消
          </n-button>
        </n-space>
      </n-form-item>
    </n-form>
    
    <!-- Question Selector Modal -->
    <n-modal
      v-model:show="showQuestionSelector"
      preset="card"
      title="选择题目"
      style="width: 80%; max-width: 1200px"
    >
      <n-data-table
        :columns="questionColumns"
        :data="questions"
        :row-key="(row: any) => row.id"
        v-model:checked-row-keys="selectedQuestions"
        :pagination="{ pageSize: 10 }"
      />
      <template #footer>
        <n-space justify="end">
          <n-button @click="showQuestionSelector = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NForm, NFormItem, NRadioGroup, NRadio, NSelect, NButton, NSpace,
  NModal, NDataTable, NTag,
  FormInst, FormRules
} from 'naive-ui'
import { useAIStore } from '@/stores/ai'
import { useCategoryStore } from '@/stores/category'
import { useQuestionStore } from '@/stores/question'
import { useMessage } from '@/composables/useMessage'
import type { DataTableColumns } from 'naive-ui'

const router = useRouter()
const aiStore = useAIStore()
const categoryStore = useCategoryStore()
const questionStore = useQuestionStore()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const selectionMode = ref<'filter' | 'manual'>('filter')
const showQuestionSelector = ref(false)
const selectedQuestions = ref<string[]>([])
const questions = ref<any[]>([])

const formData = reactive({
  type: 'both' as 'answer' | 'explanation' | 'both',
  filter: {
    categoryId: undefined as string | undefined,
    answerStatus: undefined as string | undefined,
    explanationStatus: undefined as string | undefined
  }
})

const categoryOptions = computed(() => {
  return categoryStore.categories.map(cat => ({
    label: cat.name,
    value: cat.id
  }))
})

const answerStatusOptions = [
  { label: '未设置', value: 'none' },
  { label: 'AI已生成', value: 'ai_generated' }
]

const explanationStatusOptions = [
  { label: '未设置', value: 'none' },
  { label: 'AI已生成', value: 'ai_generated' }
]

const questionColumns: DataTableColumns<any> = [
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
    width: 100
  },
  {
    title: '答案状态',
    key: 'answerStatus',
    width: 120,
    render: (row) => {
      const statusMap: Record<string, { label: string; type: any }> = {
        none: { label: '未设置', type: 'default' },
        ai_generated: { label: 'AI已生成', type: 'warning' },
        confirmed: { label: '已确认', type: 'success' }
      }
      const status = statusMap[row.answerStatus] || { label: row.answerStatus, type: 'default' }
      return h(NTag, { type: status.type }, { default: () => status.label })
    }
  },
  {
    title: '解析状态',
    key: 'explanationStatus',
    width: 120,
    render: (row) => {
      const statusMap: Record<string, { label: string; type: any }> = {
        none: { label: '未设置', type: 'default' },
        ai_generated: { label: 'AI已生成', type: 'warning' },
        confirmed: { label: '已确认', type: 'success' }
      }
      const status = statusMap[row.explanationStatus] || { label: row.explanationStatus, type: 'default' }
      return h(NTag, { type: status.type }, { default: () => status.label })
    }
  }
]

const rules: FormRules = {
  type: { required: true, message: '请选择补全类型', trigger: 'change' }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    
    const data: any = {
      type: formData.type
    }
    
    if (selectionMode.value === 'filter') {
      data.filter = formData.filter
    } else {
      if (selectedQuestions.value.length === 0) {
        message.warning('请选择要补全的题目')
        return
      }
      data.questionIds = selectedQuestions.value
    }
    
    const task = await aiStore.batchCompleteQuestions(data)
    message.success('任务已创建')
    router.push('/ai/tasks')
  } catch (error: any) {
    if (error.errors) {
      // Validation error
      return
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await categoryStore.fetchCategories()
  
  // Load questions for manual selection
  const result = await questionStore.fetchQuestions({ pageSize: 100 })
  questions.value = questionStore.questions
})
</script>
