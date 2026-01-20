<template>
  <div class="exam-answer-page">
    <n-spin :show="examStore.loading">
      <div v-if="examStore.currentExam" class="exam-container">
        <!-- 顶部信息栏 -->
        <n-card class="exam-header">
          <n-space justify="space-between" align="center">
            <div>
              <h2>{{ examStore.currentExam.exam.title }}</h2>
              <n-space>
                <n-tag :type="getModeType(examStore.currentExam.exam.mode)">
                  {{ getModeLabel(examStore.currentExam.exam.mode) }}
                </n-tag>
                <span>共 {{ examStore.currentExam.exam.total_count }} 题</span>
                <span>总分 {{ examStore.currentExam.exam.total_score }} 分</span>
              </n-space>
            </div>
            
            <n-space>
              <!-- 计时器 -->
              <div v-if="examStore.currentExam.exam.time_limit" class="timer">
                <n-icon :component="TimeOutline" size="20" />
                <span :class="{ 'time-warning': timeRemaining < 300 }">
                  {{ formatTime(timeRemaining) }}
                </span>
              </div>
              
              <!-- 解析开关 -->
              <div v-if="canToggleAnswer" style="display: flex; align-items: center; margin-right: 12px">
                <n-switch v-model:value="showAnalysis">
                  <template #checked>显示解析</template>
                  <template #unchecked>隐藏解析</template>
                </n-switch>
              </div>
              
              <n-button type="primary" @click="handleSubmit">
                提交试卷
              </n-button>
            </n-space>
          </n-space>
        </n-card>

        <n-grid :cols="4" :x-gap="20">
          <!-- 题目区域 -->
          <n-gi :span="3">
            <n-card class="question-area">
              <div v-for="(question, index) in examStore.currentExam.questions" :key="question.id" class="question-item">
                <n-divider v-if="index > 0" />
                
                <div class="question-header">
                  <n-space align="center">
                    <n-tag>{{ index + 1 }}</n-tag>
                    <n-tag :type="getDifficultyType(question.difficulty)">
                      {{ getDifficultyLabel(question.difficulty) }}
                    </n-tag>
                    <n-tag>{{ getTypeLabel(question.type) }}</n-tag>
                  </n-space>
                </div>
                
                <div class="question-content">
                  {{ question.content }}
                </div>
                
                <!-- 选择题选项 -->
                <div v-if="question.type === 'single'" class="question-options">
                  <n-radio-group v-model:value="answers[question.id]" @update:value="() => saveAnswer(question.id)">
                    <n-space vertical>
                      <n-radio v-for="(value, key) in parseOptions(question.options)" :key="key" :value="key">
                        {{ key }}. {{ value }}
                      </n-radio>
                    </n-space>
                  </n-radio-group>
                </div>
                
                <div v-else-if="question.type === 'multiple'" class="question-options">
                  <n-checkbox-group v-model:value="multipleAnswers[question.id]" @update:value="() => handleMultipleChange(question.id)">
                    <n-space vertical>
                      <n-checkbox v-for="(value, key) in parseOptions(question.options)" :key="key" :value="key">
                        {{ key }}. {{ value }}
                      </n-checkbox>
                    </n-space>
                  </n-checkbox-group>
                </div>
                
                <div v-else-if="question.type === 'judge'" class="question-options">
                  <n-radio-group v-model:value="answers[question.id]" @update:value="() => saveAnswer(question.id)">
                    <n-space>
                      <n-radio value="TRUE">正确</n-radio>
                      <n-radio value="FALSE">错误</n-radio>
                    </n-space>
                  </n-radio-group>
                </div>
                
                <div v-else-if="question.type === 'essay'" class="question-options">
                  <n-input
                    v-model:value="answers[question.id]"
                    type="textarea"
                    :rows="4"
                    placeholder="请输入答案"
                    @blur="() => saveAnswer(question.id)"
                  />
                </div>
                
                <!-- 练习模式和背题模式显示答案 -->
                <div v-if="showAnswer" class="question-answer">
                  <n-alert type="success" style="margin-top: 16px">
                    <template #header>正确答案</template>
                    {{ question.answer }}
                  </n-alert>
                  
                  <n-alert v-if="question.explanation" type="info" style="margin-top: 8px">
                    <template #header>解析</template>
                    {{ question.explanation }}
                  </n-alert>
                </div>
              </div>
            </n-card>
          </n-gi>

          <!-- 答题卡 -->
          <n-gi :span="1">
            <n-card title="答题卡" class="answer-card">
              <div class="answer-grid">
                <div
                  v-for="(question, index) in examStore.currentExam.questions"
                  :key="question.id"
                  class="answer-item"
                  :class="{
                    'answered': answers[question.id],
                    'current': currentQuestionIndex === index
                  }"
                  @click="scrollToQuestion(index)"
                >
                  {{ index + 1 }}
                </div>
              </div>
              
              <n-divider />
              
              <n-space vertical>
                <div>已答: {{ answeredCount }} / {{ examStore.currentExam.exam.total_count }}</div>
                <div>未答: {{ unansweredCount }}</div>
              </n-space>
            </n-card>
          </n-gi>
        </n-grid>
      </div>
    </n-spin>

    <!-- 提交确认对话框 -->
    <n-modal v-model:show="showSubmitModal" preset="dialog" title="提交试卷">
      <p>确定要提交试卷吗？</p>
      <p v-if="unansweredCount > 0" style="color: #f5222d">
        还有 {{ unansweredCount }} 道题未作答
      </p>
      <template #action>
        <n-space>
          <n-button @click="showSubmitModal = false">取消</n-button>
          <n-button type="primary" @click="confirmSubmit">确定提交</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  useMessage,
  NSpin,
  NCard,
  NSpace,
  NTag,
  NIcon,
  NButton,
  NGrid,
  NGi,
  NDivider,
  NRadioGroup,
  NRadio,
  NCheckboxGroup,
  NCheckbox,
  NInput,
  NAlert,
  NModal,
  NSwitch
} from 'naive-ui'
import { TimeOutline, EyeOutline, EyeOffOutline } from '@vicons/ionicons5'
import { useExamStore } from '@/stores/exam'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const examStore = useExamStore()

const examId = route.params.id as string
const answers = ref<Record<string, string>>({})
const multipleAnswers = ref<Record<string, string[]>>({})
const currentQuestionIndex = ref(0)
const showSubmitModal = ref(false)
const timeRemaining = ref(0)
const showAnalysis = ref(false) // 控制是否显示解析
let timer: number | null = null

// 是否显示答案（练习模式下可切换，背题模式常显）
const showAnswer = computed(() => {
  if (!examStore.currentExam?.exam) return false
  const mode = examStore.currentExam.exam.mode
  
  if (mode === 'review') return true
  if (mode === 'practice') return showAnalysis.value
  return false
})

// 是否允许切换答案显示
const canToggleAnswer = computed(() => {
  return examStore.currentExam?.exam.mode === 'practice'
})

// 已答题数
const answeredCount = computed(() => {
  return Object.keys(answers.value).filter(k => answers.value[k]).length
})

// 未答题数
const unansweredCount = computed(() => {
  return (examStore.currentExam?.exam.total_count || 0) - answeredCount.value
})

// 解析选项
function parseOptions(options?: string) {
  if (!options) return {}
  try {
    return JSON.parse(options)
  } catch {
    return {}
  }
}

// 处理多选题变化
function handleMultipleChange(questionId: string) {
  const selected = multipleAnswers.value[questionId] || []
  answers.value[questionId] = selected.sort().join(',')
  saveAnswer(questionId)
}

// 保存答案
async function saveAnswer(questionId: string) {
  const answer = answers.value[questionId]
  if (!answer) return
  
  try {
    await examStore.saveAnswer(examId, questionId, answer)
  } catch (error: any) {
    message.error('保存答案失败')
  }
}

// 滚动到指定题目
function scrollToQuestion(index: number) {
  currentQuestionIndex.value = index
  const element = document.querySelectorAll('.question-item')[index]
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 提交试卷
function handleSubmit() {
  showSubmitModal.value = true
}

// 确认提交
async function confirmSubmit() {
  try {
    const result = await examStore.submitExam(examId, answers.value)
    message.success('提交成功')
    showSubmitModal.value = false
    router.push(`/exams/${examId}/result`)
  } catch (error: any) {
    message.error(error.message || '提交失败')
  }
}

// 格式化时间
function formatTime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 获取模式标签
function getModeLabel(mode: string) {
  const map: Record<string, string> = {
    exam: '考试模式',
    practice: '练习模式',
    review: '背题模式'
  }
  return map[mode] || mode
}

function getModeType(mode: string) {
  const map: Record<string, any> = {
    exam: 'error',
    practice: 'success',
    review: 'info'
  }
  return map[mode] || 'default'
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

function getDifficultyLabel(difficulty: string) {
  const map: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return map[difficulty] || difficulty
}

function getDifficultyType(difficulty: string) {
  const map: Record<string, any> = {
    easy: 'success',
    medium: 'warning',
    hard: 'error'
  }
  return map[difficulty] || 'default'
}

// 启动计时器
function startTimer() {
  if (!examStore.currentExam?.exam.time_limit) return
  
  const startTime = examStore.currentExam.exam.start_time
  const timeLimit = examStore.currentExam.exam.time_limit
  
  if (!startTime) return
  
  const updateTimer = () => {
    const elapsed = Math.floor((Date.now() - new Date(startTime).getTime()) / 1000)
    timeRemaining.value = Math.max(0, timeLimit - elapsed)
    
    if (timeRemaining.value === 0) {
      message.warning('考试时间已到，自动提交')
      confirmSubmit()
    }
  }
  
  updateTimer()
  timer = window.setInterval(updateTimer, 1000)
}

onMounted(async () => {
  await examStore.fetchExamQuestions(examId)
  
  if (examStore.currentExam) {
    // 加载已保存的答案
    examStore.currentExam.questions.forEach(q => {
      if (q.user_answer) {
        answers.value[q.id] = q.user_answer
        
        // 多选题需要转换为数组
        if (q.type === 'multiple') {
          multipleAnswers.value[q.id] = q.user_answer.split(',')
        }
      }
    })
    
    // 启动计时器
    if (examStore.currentExam.exam.mode === 'exam') {
      startTimer()
    }
  }
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.exam-answer-page {
  padding: 20px;
}

.exam-container {
  max-width: 1400px;
  margin: 0 auto;
}

.exam-header {
  margin-bottom: 20px;
}

.timer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}

.time-warning {
  color: #f5222d;
}

.question-area {
  min-height: 600px;
}

.question-item {
  padding: 16px 0;
}

.question-header {
  margin-bottom: 12px;
}

.question-content {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 16px;
}

.question-options {
  margin-left: 20px;
}

.answer-card {
  position: sticky;
  top: 20px;
}

.answer-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}

.answer-item {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.answer-item:hover {
  border-color: #40a9ff;
  color: #40a9ff;
}

.answer-item.answered {
  background-color: #52c41a;
  color: white;
  border-color: #52c41a;
}

.answer-item.current {
  border-color: #1890ff;
  border-width: 2px;
}
</style>
