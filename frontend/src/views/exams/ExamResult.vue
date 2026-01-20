<template>
  <div class="exam-result-page">
    <n-spin :show="loading">
      <div v-if="exam && result" class="result-container">
        <!-- 成绩卡片 -->
        <n-card class="score-card">
          <n-result
            :status="getResultStatus()"
            :title="getResultTitle()"
          >
            <template #footer>
              <n-space vertical align="center">
                <n-statistic label="得分">
                  <n-number-animation
                    :from="0"
                    :to="result.score"
                    :duration="1000"
                  />
                  <template #suffix>/ {{ result.total_score }}</template>
                </n-statistic>
                
                <n-space>
                  <n-statistic label="正确" :value="result.correct_count" />
                  <n-statistic label="错误" :value="result.wrong_count" />
                  <n-statistic label="正确率" :value="`${correctRate}%`" />
                </n-space>
                
                <n-space v-if="exam.time_used">
                  <n-statistic label="用时" :value="formatTime(exam.time_used)" />
                </n-space>
              </n-space>
            </template>
          </n-result>
          
          <n-space justify="center" style="margin-top: 24px">
            <n-button @click="router.push('/exams')">返回列表</n-button>
            <n-button type="primary" @click="viewDetails">查看详情</n-button>
            <n-button @click="router.push('/exams/config')">再来一次</n-button>
            <n-button type="info" :loading="generatingReport" @click="handleGenerateReport">
              生成AI报告
            </n-button>
          </n-space>
        </n-card>

        <!-- 答题详情 -->
        <n-card v-if="showDetails" title="答题详情" style="margin-top: 20px">
          <div v-for="(question, index) in questions" :key="question.id" class="question-detail">
            <n-divider v-if="index > 0" />
            
            <div class="question-header">
              <n-space align="center">
                <n-tag>{{ index + 1 }}</n-tag>
                <n-tag :type="result.results[question.id]?.correct ? 'success' : 'error'">
                  {{ result.results[question.id]?.correct ? '正确' : '错误' }}
                </n-tag>
                <n-tag>{{ getTypeLabel(question.type) }}</n-tag>
              </n-space>
            </div>
            
            <div class="question-content">
              {{ question.content }}
            </div>
            
            <div v-if="question.options" class="question-options">
              <div v-for="(value, key) in parseOptions(question.options)" :key="key">
                {{ key }}. {{ value }}
              </div>
            </div>
            
            <n-space vertical style="margin-top: 12px">
              <div>
                <strong>你的答案：</strong>
                <n-tag :type="result.results[question.id]?.correct ? 'success' : 'error'">
                  {{ result.results[question.id]?.user_answer || '未作答' }}
                </n-tag>
              </div>
              
              <div>
                <strong>正确答案：</strong>
                <n-tag type="success">
                  {{ result.results[question.id]?.correct_answer }}
                </n-tag>
              </div>
              
              <div v-if="question.explanation">
                <strong>解析：</strong>
                <div style="margin-top: 8px; padding: 12px; background-color: #f5f5f5; border-radius: 4px;">
                  {{ question.explanation }}
                </div>
              </div>
              
              <!-- 简述题手动评分 -->
              <div v-if="question.type === 'essay' && !isManualGraded(question.id)">
                <n-space style="margin-top: 12px">
                  <n-input-number
                    v-model:value="manualScores[question.id]"
                    :min="0"
                    :max="10"
                    placeholder="分数"
                    style="width: 120px"
                  />
                  <n-input
                    v-model:value="manualFeedbacks[question.id]"
                    placeholder="评语（可选）"
                    style="width: 300px"
                  />
                  <n-button
                    type="primary"
                    size="small"
                    @click="handleManualGrade(question.id)"
                  >
                    评分
                  </n-button>
                </n-space>
              </div>
              
              <div v-else-if="question.type === 'essay' && isManualGraded(question.id)">
                <n-alert type="success" style="margin-top: 12px">
                  已评分：{{ getManualGrade(question.id).score }} 分
                  <div v-if="getManualGrade(question.id).feedback">
                    评语：{{ getManualGrade(question.id).feedback }}
                  </div>
                </n-alert>
              </div>
            </n-space>
          </div>
        </n-card>
      </div>
    </n-spin>

    <!-- AI 报告对话框 -->
    <n-modal v-model:show="showReportModal" preset="card" title="AI 学习报告" style="width: 800px">
      <n-spin :show="generatingReport">
        <div v-if="aiReport" v-html="renderMarkdown(aiReport)" class="markdown-body"></div>
      </n-spin>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  useMessage,
  NSpin,
  NCard,
  NResult,
  NSpace,
  NStatistic,
  NNumberAnimation,
  NButton,
  NDivider,
  NTag,
  NInputNumber,
  NInput,
  NAlert,
  NModal
} from 'naive-ui'
import MarkdownIt from 'markdown-it'
import { examsApi, type Exam, type GradingResult, type QuestionInExam } from '@/api/exams'
import { aiApi } from '@/api/ai'
import { useExamStore } from '@/stores/exam'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const examStore = useExamStore()
const md = new MarkdownIt()

const examId = route.params.id as string
const loading = ref(false)
const exam = ref<Exam | null>(null)
const result = ref<GradingResult | null>(null)
const questions = ref<QuestionInExam[]>([])
const showDetails = ref(false)
const generatingReport = ref(false)
const showReportModal = ref(false)
const aiReport = ref('')
const manualScores = ref<Record<string, number>>({})
const manualFeedbacks = ref<Record<string, string>>({})
const manualGrades = ref<Record<string, any>>({})

// 正确率
const correctRate = computed(() => {
  if (!result.value) return 0
  return Math.round((result.value.correct_count / result.value.total_score) * 100)
})

// 获取结果状态
function getResultStatus() {
  if (!result.value) return 'info'
  const rate = correctRate.value
  if (rate >= 90) return 'success'
  if (rate >= 60) return 'warning'
  return 'error'
}

// 获取结果标题
function getResultTitle() {
  if (!result.value) return ''
  const rate = correctRate.value
  if (rate >= 90) return '优秀！'
  if (rate >= 80) return '良好！'
  if (rate >= 60) return '及格'
  return '需要加油'
}

// 查看详情
function viewDetails() {
  showDetails.value = !showDetails.value
}

// 解析选项
function parseOptions(options?: string) {
  if (!options) return {}
  try {
    return JSON.parse(options)
  } catch {
    return {}
  }
}

// 格式化时间
function formatTime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h}小时${m}分${s}秒`
  }
  if (m > 0) {
    return `${m}分${s}秒`
  }
  return `${s}秒`
}

function getTypeLabel(type: string) {
  const map: Record<string, string> = {
    single: '单选',
    multiple: '多选',
    judge: '判断',
    essay: '简述'
  }
  return map[type] || type
}

// 生成 AI 报告
async function handleGenerateReport() {
  generatingReport.value = true
  try {
    const response = await aiApi.generateReport(examId)
    aiReport.value = response.report
    showReportModal.value = true
  } catch (error: any) {
    message.error('生成报告失败')
  } finally {
    generatingReport.value = false
  }
}

// 渲染 Markdown
function renderMarkdown(text: string) {
  return md.render(text)
}

// 手动评分
async function handleManualGrade(questionId: string) {
  const score = manualScores.value[questionId]
  if (score === undefined || score === null) {
    message.error('请输入分数')
    return
  }
  
  try {
    await examsApi.manualGrade(
      examId,
      questionId,
      score,
      manualFeedbacks.value[questionId]
    )
    message.success('评分成功')
    
    // 保存评分信息
    manualGrades.value[questionId] = {
      score,
      feedback: manualFeedbacks.value[questionId]
    }
    
    // 更新总分
    if (exam.value) {
      exam.value.score += score
    }
  } catch (error: any) {
    message.error('评分失败')
  }
}

// 检查是否已评分
function isManualGraded(questionId: string) {
  return !!manualGrades.value[questionId]
}

// 获取评分信息
function getManualGrade(questionId: string) {
  return manualGrades.value[questionId] || {}
}

onMounted(async () => {
  loading.value = true
  try {
    // 获取考试详情
    exam.value = await examsApi.getExam(examId)
    
    // 获取题目和结果
    const examData = await examStore.fetchExamQuestions(examId)
    if (examStore.currentExam) {
      questions.value = examStore.currentExam.questions
    }
    
    // 解析结果
    if (exam.value.answers) {
      const answers = JSON.parse(exam.value.answers)
      result.value = {
        score: exam.value.score,
        total_score: exam.value.total_score,
        correct_count: exam.value.correct_count,
        wrong_count: exam.value.wrong_count,
        results: {}
      }
      
      // 构建结果详情
      questions.value.forEach(q => {
        const userAnswer = answers[q.id] || ''
        const isCorrect = checkAnswer(q, userAnswer)
        result.value!.results[q.id] = {
          correct: isCorrect,
          user_answer: userAnswer,
          correct_answer: q.answer || ''
        }
      })
    }
  } catch (error: any) {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
})

// 检查答案（简单版本，实际评分在后端）
function checkAnswer(question: QuestionInExam, userAnswer: string) {
  if (!userAnswer || !question.answer) return false
  
  if (question.type === 'multiple') {
    const correct = question.answer.replace(/,/g, '').split('').sort().join('')
    const user = userAnswer.replace(/,/g, '').split('').sort().join('')
    return correct === user
  }
  
  return userAnswer.toUpperCase() === question.answer.toUpperCase()
}
</script>

<style scoped>
.exam-result-page {
  padding: 20px;
}

.result-container {
  max-width: 1000px;
  margin: 0 auto;
}

.score-card {
  text-align: center;
}

.question-detail {
  padding: 16px 0;
}

.question-header {
  margin-bottom: 12px;
}

.question-content {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 12px;
}

.question-options {
  margin-left: 20px;
  margin-bottom: 12px;
}

.markdown-body {
  line-height: 1.6;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin-top: 24px;
  margin-bottom: 16px;
}

.markdown-body p {
  margin-bottom: 16px;
}

.markdown-body ul,
.markdown-body ol {
  margin-bottom: 16px;
  padding-left: 2em;
}
</style>
