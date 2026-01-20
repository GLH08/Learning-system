<template>
  <n-card title="创建题目">
    <n-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-placement="top"
    >
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
          <n-space v-for="key in optionKeys" :key="key" align="center">
            <n-input
              v-model:value="formData.options[key]"
              :placeholder="`选项 ${key}`"
              style="width: 400px"
            >
              <template #prefix>{{ key }}.</template>
            </n-input>
            <n-button 
              v-if="optionKeys.length > 2" 
              text 
              type="error"
              @click="removeOption(key)"
            >
              删除
            </n-button>
          </n-space>
          <n-button 
            v-if="optionKeys.length < 8" 
            dashed 
            @click="addOption"
          >
            + 添加选项
          </n-button>
        </n-space>
      </n-form-item>
      
      <n-form-item label="答案">
        <n-input
          v-model:value="formData.answer"
          placeholder="请输入答案（可选）"
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
      
      <n-form-item>
        <n-space>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            创建
          </n-button>
          <n-button @click="$router.back()">
            取消
          </n-button>
        </n-space>
      </n-form-item>
    </n-form>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NSelect, NButton, NSpace, FormInst, FormRules } from 'naive-ui'
import { useQuestionStore } from '@/stores/question'
import { useMessage } from '@/composables/useMessage'

const router = useRouter()
const questionStore = useQuestionStore()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

// 可用选项字母 A-H
const allOptionLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
const optionKeys = ref(['A', 'B', 'C', 'D'])

const formData = reactive({
  type: 'single',
  difficulty: 'medium',
  content: '',
  options: {
    A: '',
    B: '',
    C: '',
    D: ''
  } as Record<string, string>,
  answer: '',
  explanation: ''
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

const showOptions = computed(() => {
  return formData.type === 'single' || formData.type === 'multiple'
})

// 添加选项
function addOption() {
  const nextLetter = allOptionLetters.find(l => !optionKeys.value.includes(l))
  if (nextLetter) {
    optionKeys.value.push(nextLetter)
    formData.options[nextLetter] = ''
  }
}

// 删除选项
function removeOption(key: string) {
  const index = optionKeys.value.indexOf(key)
  if (index > -1) {
    optionKeys.value.splice(index, 1)
    delete formData.options[key]
  }
}

const rules: FormRules = {
  type: { required: true, message: '请选择题型', trigger: 'change' },
  difficulty: { required: true, message: '请选择难度', trigger: 'change' },
  content: { required: true, message: '请输入题目内容', trigger: 'blur' }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    
    // 只保留有内容的选项
    const filteredOptions: Record<string, string> = {}
    for (const key of optionKeys.value) {
      if (formData.options[key]?.trim()) {
        filteredOptions[key] = formData.options[key]
      }
    }
    
    const data = {
      ...formData,
      options: showOptions.value && Object.keys(filteredOptions).length > 0 ? filteredOptions : null
    }
    
    await questionStore.createQuestion(data)
    message.success('创建成功')
    router.push('/questions')
  } catch (error: any) {
    if (error.errors) {
      // Validation error
      return
    }
  } finally {
    loading.value = false
  }
}
</script>
