<template>
  <div class="settings-page">
    <n-space vertical :size="20">
      <!-- AI 配置 -->
      <n-card title="AI 配置">
        <n-form
          ref="aiFormRef"
          :model="aiForm"
          :rules="aiRules"
          label-placement="left"
          label-width="120"
        >
          <n-form-item label="API 地址" path="api_url">
            <n-input v-model:value="aiForm.api_url" placeholder="https://api.openai.com/v1" />
          </n-form-item>
          
          <n-form-item label="API 密钥" path="api_key">
            <n-input
              v-model:value="aiForm.api_key"
              type="password"
              show-password-on="click"
              placeholder="sk-..."
            />
          </n-form-item>
          
          <n-form-item label="模型" path="model">
            <n-input v-model:value="aiForm.model" placeholder="gpt-3.5-turbo" />
          </n-form-item>
          
          <n-form-item label="温度">
            <n-slider v-model:value="aiForm.temperature" :min="0" :max="2" :step="0.1" />
            <span style="margin-left: 12px">{{ aiForm.temperature }}</span>
          </n-form-item>
          
          <n-form-item label="最大 Token">
            <n-input-number v-model:value="aiForm.max_tokens" :min="100" :max="65536" style="width: 200px" />
            <span style="margin-left: 8px; color: #999; font-size: 12px;">单次输出限制</span>
          </n-form-item>
          
          <n-form-item>
            <n-space>
              <n-button type="primary" :loading="saving" @click="handleSave">
                保存配置
              </n-button>
              <n-button :loading="testing" @click="handleTest">
                测试连接
              </n-button>
            </n-space>
          </n-form-item>
        </n-form>
      </n-card>

      <!-- 数据备份 -->
      <n-card title="数据备份">
        <n-space vertical :size="16">
          <n-space>
            <n-button type="primary" :loading="creating" @click="handleCreateBackup">
              创建备份
            </n-button>
            <n-upload
              :custom-request="handleRestore"
              :show-file-list="false"
              accept=".db"
            >
              <n-button>恢复备份</n-button>
            </n-upload>
          </n-space>
          
          <n-data-table
            :columns="backupColumns"
            :data="backups"
            :loading="loadingBackups"
            :pagination="{ pageSize: 10 }"
          />
        </n-space>
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="tsx">
import { ref, h, onMounted } from 'vue'
import {
  useMessage,
  useDialog,
  NButton,
  NSpace,
  NCard,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSlider,
  NUpload,
  NDataTable,
  type FormInst,
  type FormRules,
  type UploadCustomRequestOptions
} from 'naive-ui'
import { settingsApi, type AISettings, type BackupInfo } from '@/api/settings'
import type { DataTableColumns } from 'naive-ui'

const message = useMessage()
const dialog = useDialog()

const aiFormRef = ref<FormInst | null>(null)
const aiForm = ref<AISettings>({
  api_url: '',
  api_key: '',
  model: 'gpt-3.5-turbo',
  temperature: 0.7,
  max_tokens: 2000
})

const aiRules: FormRules = {
  api_url: [
    { required: true, message: '请输入 API 地址', trigger: 'blur' }
  ],
  api_key: [
    { required: true, message: '请输入 API 密钥', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ]
}

const saving = ref(false)
const testing = ref(false)
const creating = ref(false)
const loadingBackups = ref(false)
const backups = ref<BackupInfo[]>([])

const backupColumns: DataTableColumns<BackupInfo> = [
  {
    title: '文件名',
    key: 'filename'
  },
  {
    title: '大小',
    key: 'size',
    render: (row) => formatSize(row.size)
  },
  {
    title: '创建时间',
    key: 'created_at',
    render: (row) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      return h(NSpace, {}, () => [
        h(
          NButton,
          {
            size: 'small',
            onClick: () => handleDownload(row.filename)
          },
          () => '下载'
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            onClick: () => handleDeleteBackup(row.filename)
          },
          () => '删除'
        )
      ])
    }
  }
]

// 格式化文件大小
function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 加载设置
async function loadSettings() {
  try {
    const settings = await settingsApi.getSettings()
    if (settings.ai_api_url) {
      aiForm.value = {
        api_url: settings.ai_api_url,
        api_key: settings.ai_api_key || '',
        model: settings.ai_model || 'gpt-3.5-turbo',
        temperature: settings.ai_temperature || 0.7,
        max_tokens: settings.ai_max_tokens || 2000
      }
    }
  } catch (error: any) {
    message.error('加载设置失败')
  }
}

// 保存配置
async function handleSave() {
  try {
    await aiFormRef.value?.validate()
    saving.value = true
    await settingsApi.updateSettings(aiForm.value)
    message.success('保存成功')
  } catch (error: any) {
    if (error.message) {
      message.error(error.message)
    }
  } finally {
    saving.value = false
  }
}

// 测试连接
async function handleTest() {
  try {
    await aiFormRef.value?.validate()
    testing.value = true
    const result = await settingsApi.testAI(aiForm.value)
    if (result.success) {
      message.success(result.message)
    } else {
      message.error(result.message)
    }
  } catch (error: any) {
    message.error('测试失败')
  } finally {
    testing.value = false
  }
}

// 加载备份列表
async function loadBackups() {
  loadingBackups.value = true
  try {
    backups.value = await settingsApi.listBackups()
  } catch (error: any) {
    message.error('加载备份列表失败')
  } finally {
    loadingBackups.value = false
  }
}

// 创建备份
async function handleCreateBackup() {
  creating.value = true
  try {
    const backup = await settingsApi.createBackup()
    message.success('备份创建成功')
    await loadBackups()
  } catch (error: any) {
    message.error('创建备份失败')
  } finally {
    creating.value = false
  }
}

// 下载备份
function handleDownload(filename: string) {
  const url = settingsApi.downloadBackup(filename)
  window.open(url, '_blank')
}

// 恢复备份
async function handleRestore(options: UploadCustomRequestOptions) {
  const file = options.file.file as File
  
  dialog.warning({
    title: '确认恢复',
    content: '恢复备份将覆盖当前数据，确定要继续吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await settingsApi.restoreBackup(file)
        message.success('恢复成功，请重启应用')
      } catch (error: any) {
        message.error('恢复失败')
      }
    }
  })
}

// 删除备份
function handleDeleteBackup(filename: string) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个备份吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await settingsApi.deleteBackup(filename)
        message.success('删除成功')
        await loadBackups()
      } catch (error: any) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadSettings()
  loadBackups()
})
</script>

<style scoped>
.settings-page {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}
</style>
