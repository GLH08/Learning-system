<template>
  <div>
    <n-space vertical :size="16">
      <n-card>
        <n-space justify="space-between">
          <n-space>
            <n-select
              v-model:value="statusFilter"
              placeholder="任务状态"
              :options="statusOptions"
              style="width: 150px"
              @update:value="handleFilterChange"
            />
            <n-button @click="handleRefresh">
              刷新
            </n-button>
          </n-space>
          
          <n-button type="primary" @click="$router.push('/ai/batch-complete')">
            创建批量任务
          </n-button>
        </n-space>
      </n-card>
      
      <n-card title="AI 任务列表">
        <n-data-table
          :columns="columns"
          :data="aiStore.tasks"
          :loading="aiStore.loading"
        />
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import {
  NSpace, NCard, NSelect, NButton, NDataTable, NTag, NProgress, NPopconfirm
} from 'naive-ui'
import { useAIStore } from '@/stores/ai'
import { useMessage } from '@/composables/useMessage'
import type { DataTableColumns } from 'naive-ui'
import type { AITask } from '@/api/ai'

const router = useRouter()
const aiStore = useAIStore()
const message = useMessage()

const statusFilter = ref('all')

const statusOptions = [
  { label: '全部', value: 'all' },
  { label: '等待中', value: 'pending' },
  { label: '运行中', value: 'running' },
  { label: '已暂停', value: 'paused' },
  { label: '已完成', value: 'completed' },
  { label: '已失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' }
]

const typeMap: Record<string, string> = {
  answer: '答案',
  explanation: '解析',
  both: '答案+解析',
  report: '报告'
}

const statusMap: Record<string, { label: string; type: any }> = {
  pending: { label: '等待中', type: 'default' },
  running: { label: '运行中', type: 'info' },
  paused: { label: '已暂停', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '已失败', type: 'error' },
  cancelled: { label: '已取消', type: 'default' }
}

const columns: DataTableColumns<AITask> = [
  {
    title: 'ID',
    key: 'id',
    width: 100,
    ellipsis: true
  },
  {
    title: '类型',
    key: 'type',
    width: 120,
    render: (row) => typeMap[row.type] || row.type
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => {
      const status = statusMap[row.status] || { label: row.status, type: 'default' }
      return h(NTag, { type: status.type }, { default: () => status.label })
    }
  },
  {
    title: '进度',
    key: 'progress',
    width: 200,
    render: (row) => {
      return h(NProgress, {
        type: 'line',
        percentage: row.progress * 100,
        indicatorPlacement: 'inside',
        processing: row.status === 'running'
      })
    }
  },
  {
    title: '完成/总数',
    key: 'count',
    width: 120,
    render: (row) => `${row.completedCount}/${row.totalCount}`
  },
  {
    title: '失败数',
    key: 'failedCount',
    width: 80
  },
  {
    title: '创建时间',
    key: 'createdAt',
    width: 180,
    render: (row) => new Date(row.createdAt).toLocaleString('zh-CN')
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) => {
      return h(NSpace, null, {
        default: () => {
          const actions = []
          
          // View details
          actions.push(
            h(
              NButton,
              {
                size: 'small',
                onClick: () => router.push(`/ai/tasks/${row.id}`)
              },
              { default: () => '详情' }
            )
          )
          
          // Pause
          if (row.status === 'running') {
            actions.push(
              h(
                NButton,
                {
                  size: 'small',
                  type: 'warning',
                  onClick: () => handlePause(row.id)
                },
                { default: () => '暂停' }
              )
            )
          }
          
          // Resume
          if (row.status === 'paused') {
            actions.push(
              h(
                NButton,
                {
                  size: 'small',
                  type: 'info',
                  onClick: () => handleResume(row.id)
                },
                { default: () => '恢复' }
              )
            )
          }
          
          // Cancel
          if (row.status === 'pending' || row.status === 'running' || row.status === 'paused') {
            actions.push(
              h(
                NPopconfirm,
                {
                  onPositiveClick: () => handleCancel(row.id)
                },
                {
                  trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '取消' }),
                  default: () => '确定取消这个任务吗？'
                }
              )
            )
          }
          
          return actions
        }
      })
    }
  }
]

const handleFilterChange = () => {
  aiStore.fetchTasks(statusFilter.value === 'all' ? undefined : statusFilter.value)
}

const handleRefresh = () => {
  aiStore.fetchTasks(statusFilter.value === 'all' ? undefined : statusFilter.value)
}

const handlePause = async (id: string) => {
  try {
    await aiStore.pauseTask(id)
    message.success('任务已暂停')
    handleRefresh()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleResume = async (id: string) => {
  try {
    await aiStore.resumeTask(id)
    message.success('任务已恢复')
    handleRefresh()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleCancel = async (id: string) => {
  try {
    await aiStore.cancelTask(id)
    message.success('任务已取消')
    handleRefresh()
  } catch (error) {
    // Error handled by interceptor
  }
}

onMounted(() => {
  aiStore.fetchTasks()
  
  // Auto refresh every 5 seconds for running tasks
  const interval = setInterval(() => {
    const hasRunningTasks = aiStore.tasks.some(t => t.status === 'running')
    if (hasRunningTasks) {
      aiStore.fetchTasks(statusFilter.value === 'all' ? undefined : statusFilter.value)
    }
  }, 5000)
  
  // Cleanup on unmount
  return () => clearInterval(interval)
})
</script>
