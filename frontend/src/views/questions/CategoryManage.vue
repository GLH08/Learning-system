<template>
  <n-card title="分类管理">
    <template #header-extra>
      <n-button type="primary" @click="showCreateModal = true">
        创建分类
      </n-button>
    </template>
    
    <n-tree
      block-line
      :data="categories"
      :node-props="nodeProps"
      :render-suffix="renderSuffix"
    />
    
    <n-modal v-model:show="showCreateModal" preset="dialog" title="创建分类">
      <n-form ref="formRef" :model="formData" :rules="rules">
        <n-form-item label="分类名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入分类名称" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入描述（可选）"
          />
        </n-form-item>
      </n-form>
      
      <template #action>
        <n-space>
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" :loading="loading" @click="handleCreate">
            创建
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { useRouter } from 'vue-router' // Add useRouter here
import {
  NCard, NButton, NTree, NModal, NForm, NFormItem, NInput, NSpace,
  NPopconfirm, FormInst, FormRules
} from 'naive-ui'
import { categoriesApi, type Category } from '@/api/categories'
import { useMessage } from '@/composables/useMessage'

const message = useMessage()
const router = useRouter()

const categories = ref<Category[]>([])
const showCreateModal = ref(false)
const loading = ref(false)
const formRef = ref<FormInst | null>(null)

const formData = reactive({
  name: '',
  description: ''
})

const rules: FormRules = {
  name: { required: true, message: '请输入分类名称', trigger: 'blur' }
}

const nodeProps = ({ option }: any) => {
  return {
    onClick() {
      // Navigate to question list with filter
      router.push({
          path: '/questions',
          query: { categoryId: option.id }
      })
    }
  }
}

const renderSuffix = ({ option }: any) => {
  if (option.id === 'default') {
    return null
  }
  
  return h(NSpace, { size: 'small' }, {
    default: () => [
      h(
        NPopconfirm,
        {
          onPositiveClick: () => handleDelete(option.id)
        },
        {
          trigger: () => h(NButton, { size: 'tiny', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除这个分类吗？'
        }
      )
    ]
  })
}

const fetchCategories = async () => {
  try {
    const response = await categoriesApi.getCategories()
    categories.value = response.data.map((cat: Category) => ({
      ...cat,
      key: cat.id,
      label: `${cat.name} (${cat.questionCount})`,
      isLeaf: !cat.children || cat.children.length === 0
    }))
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleCreate = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    
    await categoriesApi.createCategory(formData)
    message.success('创建成功')
    showCreateModal.value = false
    formData.name = ''
    formData.description = ''
    fetchCategories()
  } catch (error: any) {
    if (error.errors) {
      return
    }
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await categoriesApi.deleteCategory(id)
    message.success('删除成功')
    fetchCategories()
  } catch (error) {
    // Error handled by interceptor
  }
}

onMounted(() => {
  fetchCategories()
})
</script>
