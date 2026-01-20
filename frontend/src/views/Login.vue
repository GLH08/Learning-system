<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <n-card class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">智能答题学习系统</h1>
        <p class="text-gray-600 mt-2">{{ isInit ? '首次使用，请设置管理员密码' : '请登录' }}</p>
      </div>
      
      <n-form ref="formRef" :model="formData" :rules="rules">
        <n-form-item path="password" label="密码">
          <n-input
            v-model:value="formData.password"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="handleSubmit"
          />
        </n-form-item>
        
        <n-form-item v-if="isInit" path="confirmPassword" label="确认密码">
          <n-input
            v-model:value="formData.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            @keyup.enter="handleSubmit"
          />
        </n-form-item>
        
        <n-button
          type="primary"
          block
          size="large"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ isInit ? '初始化' : '登录' }}
        </n-button>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, FormInst, FormRules } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { useMessage } from '@/composables/useMessage'
import { authApi } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const isInit = ref(false)

const formData = reactive({
  password: '',
  confirmPassword: ''
})

const rules: FormRules = {
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    {
      required: true,
      message: '请确认密码',
      trigger: 'blur',
      validator: (rule: any, value: string) => {
        if (isInit.value && value !== formData.password) {
          return new Error('两次密码不一致')
        }
        return true
      }
    }
  ]
}

const checkInitStatus = async () => {
  try {
    const response = await authApi.verify()
    isInit.value = !response.data.initialized
  } catch (error) {
    // If error, assume not initialized
    isInit.value = true
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    
    if (isInit.value) {
      await userStore.initPassword(formData.password)
      message.success('初始化成功')
    } else {
      await userStore.login(formData.password)
      message.success('登录成功')
    }
    
    const redirect = route.query.redirect as string || '/'
    router.push(redirect)
  } catch (error: any) {
    if (error.errors) {
      // Validation error
      return
    }
    // API error will be handled by interceptor
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkInitStatus()
})
</script>
