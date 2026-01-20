<template>
  <n-card title="编辑题目">
    <n-spin :show="loadingQuestion">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="top"
      >
        <n-form-item label="分类" path="categoryId">
          <n-select
            v-model:value="formData.categoryId"
            :options="categoryOptions"
            placeholder="请选择分类"
            clearable
          />
        </n-form-item>
        
        <n-form-item label="题型" path="type">
          <n-select
            v-model:value="formData.type"
            :options="typeOptions"
            placeholder="请选择题型"
          />
        </n-form-item>
        
        <n-form-item label="难度" path="difficulty">
          <n-select
            v-model:value="formData.difficulty"
            :options="difficultyOptions"
            placeholder="请选择难度"
          />
        </n-form-item>
        
        <n-form-item label="题目内容" path="content">
          <n-input
            v-model:value="formData.content"
            type="textarea"
            :rows="4"
            placeholder="请输入题目内容"
          />
        </n-form-item>
        
        <n-form-item v-if="showOptions" label="选项">
          <n-space vertical class="w-full">
            <n-input
              v-for="(option, key) in formData.options"
              :key="key"
              v-model:value="formData.options[key]"
              :placeholder="`选项 ${key}`"
            >
              <template #prefix>{{ key }}.</template>
            </n-input>
          </n-space>
        </n-form-item>
        
        <n-form-item label="答案" path="answer">
          <n-input
            v-model:value="formData.answer"
            placeholder="请输入答案"
          />
        </n-form-item>
        
        <n-form-item label="解析">
          <n-input
            v-model:value="formData.explanation"
            type="textarea"
            :rows="4"
            placeholder="请输入解析（可选）"
          />
        </n-form-item>
        
        <n-form-item label="标签">
          <n-dynamic-tags v-model:value="formData.tags" />
        </n-form-item>
        
        <n-form-item label="来源">
          <n-input
            v-model:value="formData.source"
            placeholder="请输入题目来源（可选）"
          />
        </n-form-item>
        
        <n-form-item>
          <n-space>
            <n-button type="primary" :loading="loading" @click="handleSubmit">
              保存
            </n-button>
            <n-button @click="$router.back()">
              取消
            </n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-spin>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  NCard, NForm, NFormItem, NInput, NSelect, NButton, NSpace, NSpin, NDynamicTags,
  FormInst, FormRules 
} from 'naive-ui'
import { useQuestionStore } from '@/stores/question'
import { useCategoryStore } from '@/stores/category'
import { useMessage } from '@/composables/useMessage'

const router = useRouter()
const route = useRoute()
const questionStore = useQuestionStore()
const categoryStore = useCategoryStore()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const loadingQuestion = ref(false)

const formData = reactive({
  categoryId: '',
  type: 'single',
  difficulty: 'medium',
  content: '',
  options: {
    A: '',
    B: '',
    C: '',
    D: ''
  },
  answer: '',
  explanation: '',
  tags: [] as string[],
  source: ''
})

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

const categoryOptions = computed(() => {
  return categoryStore.categories.map(cat => ({
    label: cat.name,
    value: cat.id
  }))
})

const showOptions = computed(() => {
  return formData.type === 'single' || formData.type === 'multiple'
})

const rules: FormRules = {
  type: { required: true, message: '请选择题型', trigger: 'change' },
  difficulty: { required: true, message: '请选择难度', trigger: 'change' },
  content: { required: true, message: '请输入题目内容', trigger: 'blur' }
}

const loadQuestion = async () => {
  const questionId = route.params.id as string
  if (!questionId) {
    message.error('题目ID不存在')
    router.back()
    return
  }
  
  try {
    loadingQuestion.value = true
    const question = await questionStore.getQuestionById(questionId)
    
    // Fill form data
    formData.categoryId = question.categoryId || ''
    formData.type = question.type
    formData.difficulty = question.difficulty
    formData.content = question.content
    formData.options = question.options || { A: '', B: '', C: '', D: '' }
    formData.answer = question.answer || ''
    formData.explanation = question.explanation || ''
    formData.tags = question.tags || []
    formData.source = question.source || ''
  } catch (error) {
    message.error('加载题目失败')
    router.back()
  } finally {
    loadingQuestion.value = false
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    
    const questionId = route.params.id as string
    const data = {
      ...formData,
      options: showOptions.value ? formData.options : null
    }
    
    await questionStore.updateQuestion(questionId, data)
    message.success('更新成功')
    router.push(`/questions/${questionId}`)
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
  await loadQuestion()
})
</script>
