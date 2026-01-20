<template>
  <n-layout has-sider class="min-h-screen">
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="240"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
    >
      <div class="p-4 text-center font-bold text-lg">
        {{ collapsed ? '答题' : '智能答题学习系统' }}
      </div>
      
      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuSelect"
      />
    </n-layout-sider>
    
    <n-layout>
      <n-layout-header bordered class="p-4 flex justify-between items-center">
        <div class="text-lg font-semibold">{{ pageTitle }}</div>
        <n-dropdown :options="userMenuOptions" @select="handleUserMenuSelect">
          <n-button text>
            <template #icon>
              <n-icon><UserOutlined /></n-icon>
            </template>
            管理员
          </n-button>
        </n-dropdown>
      </n-layout-header>
      
      <n-layout-content class="p-6">
        <router-view />
      </n-layout-content>
    </n-layout>
    
    <AIQueueMonitor />
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout, NLayoutSider, NLayoutHeader, NLayoutContent,
  NMenu, NButton, NDropdown, NIcon
} from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import AIQueueMonitor from '@/components/AIQueueMonitor.vue'

// Icons (you can use any icon library)
const DashboardOutlined = () => h('span', '📊')
const BookOutlined = () => h('span', '📚')
const EditOutlined = () => h('span', '📝')
const LearningOutlined = () => h('span', '📈')
const SettingsOutlined = () => h('span', '⚙️')
const UserOutlined = () => h('span', '👤')

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const collapsed = ref(false)

const menuOptions = [
  {
    label: '仪表盘',
    key: 'dashboard',
    icon: () => h(NIcon, null, { default: () => h(DashboardOutlined) })
  },
  {
    label: '题库管理',
    key: 'questions-group',
    icon: () => h(NIcon, null, { default: () => h(BookOutlined) }),
    children: [
      {
        label: '题目列表',
        key: 'questions'
      },
      {
        label: '分类管理',
        key: 'categories'
      },
      {
        label: '导入题目',
        key: 'questions-import'
      }
    ]
  },
  {
    label: '答题中心',
    key: 'exams-group',
    icon: () => h(NIcon, null, { default: () => h(EditOutlined) }),
    children: [
      {
        label: '开始答题',
        key: 'exams-config'
      },
      {
        label: '答题历史',
        key: 'exams'
      }
    ]
  },
  {
    label: '学习追踪',
    key: 'learning-group',
    icon: () => h(NIcon, null, { default: () => h(LearningOutlined) }),
    children: [
      {
        label: '错题本',
        key: 'wrong-questions'
      },
      {
        label: '学习统计',
        key: 'stats'
      }
    ]
  },
  {
    label: '系统设置',
    key: 'settings',
    icon: () => h(NIcon, null, { default: () => h(SettingsOutlined) })
  }
]

const userMenuOptions = [
  {
    label: '修改密码',
    key: 'change-password'
  },
  {
    label: '退出登录',
    key: 'logout'
  }
]

const activeKey = computed(() => {
  const path = route.path
  if (path === '/') return 'dashboard'
  if (path.startsWith('/questions/import')) return 'questions-import'
  if (path.startsWith('/questions')) return 'questions'
  if (path.startsWith('/categories')) return 'categories'
  if (path.startsWith('/exams/config')) return 'exams-config'
  if (path.startsWith('/exams')) return 'exams'
  if (path.startsWith('/wrong-questions')) return 'wrong-questions'
  if (path.startsWith('/stats')) return 'stats'
  if (path.startsWith('/settings')) return 'settings'
  return 'dashboard'
})

const pageTitle = computed(() => {
  const name = route.name as string
  const titles: Record<string, string> = {
    'Dashboard': '仪表盘',
    'QuestionList': '题目列表',
    'QuestionCreate': '创建题目',
    'QuestionDetail': '题目详情',
    'QuestionEdit': '编辑题目',
    'QuestionImport': '导入题目',
    'CategoryManage': '分类管理',
    'ExamConfig': '开始答题',
    'ExamList': '答题历史',
    'ExamAnswer': '答题中',
    'ExamResult': '答题结果',
    'WrongQuestionList': '错题本',
    'StatsOverview': '学习统计',
    'SystemSettings': '系统设置'
  }
  return titles[name] || '智能答题学习系统'
})

const handleMenuSelect = (key: string) => {
  const routeMap: Record<string, string> = {
    'dashboard': '/',
    'questions': '/questions',
    'categories': '/categories',
    'questions-import': '/questions/import',
    'exams-config': '/exams/config',
    'exams': '/exams',
    'wrong-questions': '/wrong-questions',
    'stats': '/stats',
    'settings': '/settings'
  }
  const path = routeMap[key] || '/'
  router.push(path)
}

const handleUserMenuSelect = (key: string) => {
  if (key === 'logout') {
    userStore.logout()
  } else if (key === 'change-password') {
    // TODO: Open change password modal
  }
}
</script>
