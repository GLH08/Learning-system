<template>
  <div class="stats-page">
    <n-spin :show="loading">
      <n-space vertical :size="20">
        <!-- 概览统计 -->
        <n-card title="学习概览">
          <n-grid :cols="4" :x-gap="16" :y-gap="16">
            <n-gi>
              <n-statistic label="总题目数" :value="overview.total_questions">
                <template #prefix>
                  <n-icon :component="DocumentTextOutline" />
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="总考试数" :value="overview.total_exams">
                <template #prefix>
                  <n-icon :component="ClipboardOutline" />
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="总练习时长" :value="formatTime(overview.total_practice_time)">
                <template #prefix>
                  <n-icon :component="TimeOutline" />
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="平均分数" :value="overview.average_score" suffix="%">
                <template #prefix>
                  <n-icon :component="TrophyOutline" />
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="总体正确率" :value="overview.overall_accuracy" suffix="%">
                <template #prefix>
                  <n-icon :component="CheckmarkCircleOutline" />
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="总错题数" :value="overview.total_wrong_questions">
                <template #prefix>
                  <n-icon :component="CloseCircleOutline" />
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="已掌握错题" :value="overview.mastered_wrong_questions">
                <template #prefix>
                  <n-icon :component="CheckmarkDoneOutline" />
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="未掌握错题" :value="overview.total_wrong_questions - overview.mastered_wrong_questions">
                <template #prefix>
                  <n-icon :component="AlertCircleOutline" />
                </template>
              </n-statistic>
            </n-gi>
          </n-grid>
        </n-card>

        <!-- 每日学习曲线 -->
        <n-card title="每日学习曲线">
          <template #header-extra>
            <n-select
              v-model:value="daysRange"
              :options="daysOptions"
              style="width: 120px"
              @update:value="fetchDailyStats"
            />
          </template>
          <div ref="dailyChartRef" style="height: 400px"></div>
        </n-card>

        <!-- 分类正确率 -->
        <n-card title="分类正确率">
          <div ref="categoryChartRef" style="height: 400px"></div>
        </n-card>

        <!-- 薄弱知识点 -->
        <n-card title="薄弱知识点">
          <n-empty v-if="weakPoints.length === 0" description="暂无薄弱知识点" />
          <n-list v-else>
            <n-list-item v-for="point in weakPoints" :key="point.category_id">
              <n-thing>
                <template #header>
                  {{ point.category_name }}
                </template>
                <template #description>
                  <n-space>
                    <n-tag type="error">正确率: {{ point.accuracy }}%</n-tag>
                    <n-tag>错误次数: {{ point.wrong_count }}</n-tag>
                  </n-space>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-card>
      </n-space>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import {
  useMessage,
  NSpin,
  NSpace,
  NCard,
  NGrid,
  NGi,
  NStatistic,
  NIcon,
  NSelect,
  NEmpty,
  NList,
  NListItem,
  NThing,
  NTag
} from 'naive-ui'
import * as echarts from 'echarts'
import {
  DocumentTextOutline,
  ClipboardOutline,
  TimeOutline,
  TrophyOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  CheckmarkDoneOutline,
  AlertCircleOutline
} from '@vicons/ionicons5'
import { statsApi, type OverviewStats, type DailyStats, type CategoryStats, type WeakPoint } from '@/api/stats'

const message = useMessage()
const loading = ref(false)

const overview = ref<OverviewStats>({
  total_questions: 0,
  total_exams: 0,
  total_practice_time: 0,
  average_score: 0,
  overall_accuracy: 0,
  total_wrong_questions: 0,
  mastered_wrong_questions: 0
})

const dailyStats = ref<DailyStats[]>([])
const categoryStats = ref<CategoryStats[]>([])
const weakPoints = ref<WeakPoint[]>([])

const daysRange = ref(30)
const daysOptions = [
  { label: '最近7天', value: 7 },
  { label: '最近30天', value: 30 },
  { label: '最近90天', value: 90 }
]

const dailyChartRef = ref<HTMLElement>()
const categoryChartRef = ref<HTMLElement>()

let dailyChart: echarts.ECharts | null = null
let categoryChart: echarts.ECharts | null = null

// 格式化时间
function formatTime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) {
    return `${h}小时${m}分`
  }
  if (m > 0) {
    return `${m}分钟`
  }
  return `${seconds}秒`
}

// 获取概览统计
async function fetchOverview() {
  try {
    overview.value = await statsApi.getOverview()
  } catch (error: any) {
    message.error('获取概览统计失败')
  }
}

// 获取每日统计
async function fetchDailyStats() {
  try {
    dailyStats.value = await statsApi.getDailyStats(daysRange.value)
    await nextTick()
    renderDailyChart()
  } catch (error: any) {
    message.error('获取每日统计失败')
  }
}

// 获取分类统计
async function fetchCategoryStats() {
  try {
    categoryStats.value = await statsApi.getCategoryStats()
    await nextTick()
    renderCategoryChart()
  } catch (error: any) {
    message.error('获取分类统计失败')
  }
}

// 获取薄弱知识点
async function fetchWeakPoints() {
  try {
    weakPoints.value = await statsApi.getWeakPoints()
  } catch (error: any) {
    message.error('获取薄弱知识点失败')
  }
}

// 渲染每日学习曲线
function renderDailyChart() {
  if (!dailyChartRef.value) return
  
  if (!dailyChart) {
    dailyChart = echarts.init(dailyChartRef.value)
  }
  
  const dates = dailyStats.value.map(d => d.date)
  const examCounts = dailyStats.value.map(d => d.exam_count)
  const accuracies = dailyStats.value.map(d => d.accuracy)
  const avgScores = dailyStats.value.map(d => d.average_score)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['考试次数', '正确率', '平均分']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: [
      {
        type: 'value',
        name: '次数',
        position: 'left'
      },
      {
        type: 'value',
        name: '百分比',
        position: 'right',
        max: 100
      }
    ],
    series: [
      {
        name: '考试次数',
        type: 'bar',
        data: examCounts,
        yAxisIndex: 0
      },
      {
        name: '正确率',
        type: 'line',
        data: accuracies,
        yAxisIndex: 1,
        smooth: true
      },
      {
        name: '平均分',
        type: 'line',
        data: avgScores,
        yAxisIndex: 1,
        smooth: true
      }
    ]
  }
  
  dailyChart.setOption(option)
}

// 渲染分类正确率图表
function renderCategoryChart() {
  if (!categoryChartRef.value) return
  
  if (!categoryChart) {
    categoryChart = echarts.init(categoryChartRef.value)
  }
  
  const categories = categoryStats.value.map(c => c.category_name)
  const accuracies = categoryStats.value.map(c => c.accuracy)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'value',
      max: 100
    },
    yAxis: {
      type: 'category',
      data: categories
    },
    series: [
      {
        name: '正确率',
        type: 'bar',
        data: accuracies,
        itemStyle: {
          color: (params: any) => {
            const value = params.value
            if (value >= 80) return '#52c41a'
            if (value >= 60) return '#faad14'
            return '#f5222d'
          }
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%'
        }
      }
    ]
  }
  
  categoryChart.setOption(option)
}

// 窗口大小变化时重新渲染图表
function handleResize() {
  dailyChart?.resize()
  categoryChart?.resize()
}

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchOverview(),
      fetchDailyStats(),
      fetchCategoryStats(),
      fetchWeakPoints()
    ])
  } finally {
    loading.value = false
  }
  
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.stats-page {
  padding: 20px;
}
</style>
