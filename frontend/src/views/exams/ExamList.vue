<template>
  <div class="exam-list-page">
    <n-card title="考试记录">
      <template #header-extra>
        <n-button type="primary" @click="router.push('/exams/config')">
          开始答题
        </n-button>
      </template>
      
      <n-space vertical :size="16">
        <!-- 筛选 -->
        <n-space>
          <n-select
            v-model:value="filters.status"
            :options="statusOptions"
            placeholder="状态"
            clearable
            style="width: 150px"
            @update:value="fetchData"
          />
          <n-select
            v-model:value="filters.mode"
            :options="modeOptions"
            placeholder="模式"
            clearable
            style="width: 150px"
            @update:value="fetchData"
          />
        </n-space>
        
        <!-- 列表 -->
        <n-data-table
          :columns="columns"
          :data="examStore.exams"
          :loading="examStore.loading"
          :pagination="pagination"
        />
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="tsx">
import { ref, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NSpace,
  NTag,
  NCard,
  NSelect,
  NDataTable,
  useMessage,
  useDialog
} from 'naive-ui'
import { useExamStore } from '@/stores/exam'
import type { DataTableColumns } from 'naive-ui'
import type { Exam } from '@/api/exams'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const examStore = useExamStore()

const filters = ref({
  status: null as string | null,
  mode: null as string | null
})

const pagination = {
  pageSize: 20
}

const statusOptions = [
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' }
]

const modeOptions = [
  { label: '考试模式', value: 'exam' },
  { label: '练习模式', value: 'practice' },
  { label: '背题模式', value: 'review' }
]

const columns: DataTableColumns<Exam> = [
  {
    title: '标题',
    key: 'title',
    width: 200
  },
  {
    title: '模式',
    key: 'mode',
    width: 100,
    render: (row) => {
      const map: Record<string, { label: string; type: any }> = {
        exam: { label: '考试', type: 'error' },
        practice: { label: '练习', type: 'success' },
        review: { label: '背题', type: 'info' }
      }
      const info = map[row.mode] || { label: row.mode, type: 'default' }
      return h(NTag, { type: info.type }, () => info.label)
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => {
      const map: Record<string, { label: string; type: any }> = {
        in_progress: { label: '进行中', type: 'warning' },
        completed: { label: '已完成', type: 'success' }
      }
      const info = map[row.status] || { label: row.status, type: 'default' }
      return h(NTag, { type: info.type }, () => info.label)
    }
  },
  {
    title: '题目数',
    key: 'total_count',
    width: 80
  },
  {
    title: '得分',
    key: 'score',
    width: 100,
    render: (row) => {
      if (row.status === 'completed') {
        return `${row.score} / ${row.total_score}`
      }
      return '-'
    }
  },
  {
    title: '正确率',
    key: 'correct_rate',
    width: 100,
    render: (row) => {
      if (row.status === 'completed' && row.total_score > 0) {
        const rate = Math.round((row.score / row.total_score) * 100)
        return `${rate}%`
      }
      return '-'
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) => {
      return h(NSpace, {}, () => [
        row.status === 'in_progress'
          ? h(
              NButton,
              {
                size: 'small',
                type: 'primary',
                onClick: () => router.push(`/exams/${row.id}/answer`)
              },
              () => '继续答题'
            )
          : h(
              NButton,
              {
                size: 'small',
                onClick: () => router.push(`/exams/${row.id}/result`)
              },
              () => '查看结果'
            ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            onClick: () => handleDelete(row.id)
          },
          () => '删除'
        )
      ])
    }
  }
]

async function fetchData() {
  await examStore.fetchExams({
    status: filters.value.status || undefined,
    mode: filters.value.mode || undefined
  })
}

function handleDelete(id: string) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这条考试记录吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await examStore.deleteExam(id)
        message.success('删除成功')
      } catch (error: any) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.exam-list-page {
  padding: 20px;
}
</style>
