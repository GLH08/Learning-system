<template>
  <div class="exam-config-page">
    <n-card title="组卷配置">
      <n-tabs v-model:value="tabValue" type="segment">
        <!-- 快速组卷 -->
        <n-tab-pane name="quick" tab="快速组卷">
          <n-form ref="quickFormRef" :model="quickForm" :rules="quickRules" label-placement="left" label-width="120">
            <n-form-item label="题目数量" path="count">
              <n-input-number v-model:value="quickForm.count" :min="1" :max="100" style="width: 200px" />
            </n-form-item>
            
            <n-form-item label="打乱选项">
              <n-switch v-model:value="quickForm.shuffle_options" />
            </n-form-item>
            
            <n-form-item>
              <n-space>
                <n-button type="primary" :loading="examStore.loading" @click="handleQuickGenerate">
                  生成试卷
                </n-button>
              </n-space>
            </n-form-item>
          </n-form>
        </n-tab-pane>

        <!-- 自定义组卷 -->
        <n-tab-pane name="custom" tab="自定义组卷">
          <n-form ref="customFormRef" :model="customForm" :rules="customRules" label-placement="left" label-width="120">
            <n-form-item label="试卷标题" path="title">
              <n-input v-model:value="customForm.title" placeholder="请输入试卷标题" />
            </n-form-item>
            
            <n-form-item label="答题模式" path="mode">
              <n-radio-group v-model:value="customForm.mode">
                <n-radio value="exam">考试模式</n-radio>
                <n-radio value="practice">练习模式</n-radio>
                <n-radio value="review">背题模式</n-radio>
              </n-radio-group>
            </n-form-item>
            
            <n-form-item label="选择分类">
              <n-tree-select
                v-model:value="customForm.category_ids"
                :options="categoryOptions"
                multiple
                checkable
                cascade
                check-strategy="child"
                placeholder="不选择则包含所有分类"
              />
            </n-form-item>
            
            <n-form-item label="题型">
              <n-checkbox-group v-model:value="customForm.question_types">
                <n-space>
                  <n-checkbox value="single">单选题</n-checkbox>
                  <n-checkbox value="multiple">多选题</n-checkbox>
                  <n-checkbox value="judge">判断题</n-checkbox>
                  <n-checkbox value="essay">简述题</n-checkbox>
                </n-space>
              </n-checkbox-group>
            </n-form-item>
            
            <n-form-item label="难度">
              <n-checkbox-group v-model:value="customForm.difficulties">
                <n-space>
                  <n-checkbox value="easy">简单</n-checkbox>
                  <n-checkbox value="medium">中等</n-checkbox>
                  <n-checkbox value="hard">困难</n-checkbox>
                </n-space>
              </n-checkbox-group>
            </n-form-item>
            
            <n-form-item label="题型数量">
              <n-space vertical style="width: 100%">
                <n-space v-for="(tc, index) in customForm.type_counts" :key="index" align="center">
                  <n-select
                    v-model:value="tc.type"
                    :options="typeOptions"
                    style="width: 120px"
                    placeholder="题型"
                  />
                  <n-input-number v-model:value="tc.count" :min="1" style="width: 120px" placeholder="数量" />
                  <n-button text @click="removeTypeCount(index)">
                    <template #icon><n-icon :component="TrashOutline" /></template>
                  </n-button>
                </n-space>
                <n-button dashed @click="addTypeCount">+ 添加题型</n-button>
              </n-space>
            </n-form-item>
            
            <n-form-item label="考试时长">
              <n-input-number v-model:value="customForm.time_limit" :min="0" placeholder="分钟，0表示不限时" style="width: 200px" />
              <span style="margin-left: 8px">分钟（0表示不限时）</span>
            </n-form-item>
            
            <n-form-item label="打乱选项">
              <n-switch v-model:value="customForm.shuffle_options" />
            </n-form-item>
            
            <n-form-item label="打乱题目">
              <n-switch v-model:value="customForm.shuffle_questions" />
            </n-form-item>
            
            <n-form-item>
              <n-space>
                <n-button type="primary" :loading="examStore.loading" @click="handleCustomGenerate">
                  生成试卷
                </n-button>
              </n-space>
            </n-form-item>
          </n-form>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  useMessage,
  NCard,
  NTabs,
  NTabPane,
  NForm,
  NFormItem,
  NInputNumber,
  NSwitch,
  NSpace,
  NButton,
  NInput,
  NRadioGroup,
  NRadio,
  NTreeSelect,
  NCheckboxGroup,
  NCheckbox,
  NSelect,
  NIcon,
  type FormInst,
  type FormRules
} from 'naive-ui'
import { TrashOutline } from '@vicons/ionicons5'
import { useExamStore } from '@/stores/exam'
import { useCategoryStore } from '@/stores/category'
import type { CustomExamRequest } from '@/api/exams'

const router = useRouter()
const message = useMessage()
const examStore = useExamStore()
const categoryStore = useCategoryStore()

const tabValue = ref('quick')

// 快速组卷表单
const quickFormRef = ref<FormInst | null>(null)
const quickForm = ref({
  count: 20,
  shuffle_options: true
})

const quickRules: FormRules = {
  count: [
    { required: true, type: 'number', message: '请输入题目数量', trigger: 'blur' }
  ]
}

// 自定义组卷表单
const customFormRef = ref<FormInst | null>(null)
const customForm = ref<CustomExamRequest>({
  title: '自定义测试',
  mode: 'exam',
  category_ids: [],
  question_types: [],
  difficulties: [],
  type_counts: [],
  time_limit: 0,
  shuffle_options: true,
  shuffle_questions: true
})

const customRules: FormRules = {
  title: [
    { required: true, message: '请输入试卷标题', trigger: 'blur' }
  ],
  mode: [
    { required: true, message: '请选择答题模式', trigger: 'change' }
  ]
}

const typeOptions = [
  { label: '单选题', value: 'single' },
  { label: '多选题', value: 'multiple' },
  { label: '判断题', value: 'judge' },
  { label: '简述题', value: 'essay' }
]

// 分类树选项
const categoryOptions = computed(() => {
  const buildTree = (categories: any[], parentId: string | null = null): any[] => {
    return categories
      .filter(c => c.parent_id === parentId)
      .map(c => ({
        label: c.name,
        key: c.id,
        value: c.id,
        children: buildTree(categories, c.id)
      }))
  }
  return buildTree(categoryStore.categories)
})

// 添加题型数量
function addTypeCount() {
  customForm.value.type_counts!.push({ type: 'single', count: 5 })
}

// 删除题型数量
function removeTypeCount(index: number) {
  customForm.value.type_counts!.splice(index, 1)
}

// 快速组卷
async function handleQuickGenerate() {
  try {
    await quickFormRef.value?.validate()
    const exam = await examStore.generateQuickExam(quickForm.value)
    message.success('试卷生成成功')
    router.push(`/exams/${exam.id}/answer`)
  } catch (error: any) {
    message.error(error.message || '生成试卷失败')
  }
}

// 自定义组卷
async function handleCustomGenerate() {
  try {
    await customFormRef.value?.validate()
    
    // 转换时间限制（分钟转秒）
    const data = {
      ...customForm.value,
      time_limit: customForm.value.time_limit! > 0 ? customForm.value.time_limit! * 60 : undefined
    }
    
    const exam = await examStore.generateCustomExam(data)
    message.success('试卷生成成功')
    router.push(`/exams/${exam.id}/answer`)
  } catch (error: any) {
    message.error(error.message || '生成试卷失败')
  }
}

onMounted(() => {
  categoryStore.fetchCategories()
})
</script>

<style scoped>
.exam-config-page {
  padding: 20px;
}
</style>
