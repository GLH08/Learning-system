import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { aiApi } from '@/api/ai'
import { useMessage } from '@/composables/useMessage'

export interface QueueItem {
    id: string
    content: string
    status: 'pending' | 'processing' | 'completed' | 'failed' | 'retrying'
    result?: string
    error?: string
    retryCount: number
}

export const useAIQueueStore = defineStore('aiQueue', () => {
    const message = useMessage()
    const queue = ref<QueueItem[]>([])
    const isProcessing = ref(false)
    const isPaused = ref(false)
    const concurrentLimit = ref(1) // Default to 1 to differ to rate limits
    const activeCount = ref(0)

    // Computed
    const pendingCount = computed(() => queue.value.filter(i => i.status === 'pending').length)
    const processingCount = computed(() => queue.value.filter(i => i.status === 'processing').length)
    const completedCount = computed(() => queue.value.filter(i => i.status === 'completed').length)
    const failedCount = computed(() => queue.value.filter(i => i.status === 'failed').length)
    const totalCount = computed(() => queue.value.length)

    const hasPending = computed(() => pendingCount.value > 0 || processingCount.value > 0)

    // Actions
    function addToQueue(questions: any[]) {
        const newItems = questions
            .filter(q => !queue.value.find(item => item.id === q.id)) // Avoid duplicates
            .map(q => ({
                id: q.id,
                content: q.content,
                status: 'pending' as const,
                retryCount: 0
            }))

        queue.value.push(...newItems)
        message.success(`已添加 ${newItems.length} 个任务到队列`)

        if (!isProcessing.value && !isPaused.value) {
            processQueue()
        }
    }

    function clearCompleted() {
        queue.value = queue.value.filter(i => i.status !== 'completed')
    }

    function clearAll() {
        queue.value = []
        isProcessing.value = false
        activeCount.value = 0
    }

    function pause() {
        isPaused.value = true
    }

    function resume() {
        isPaused.value = false
        processQueue()
    }

    function remove(id: string) {
        const index = queue.value.findIndex(i => i.id === id)
        if (index > -1) {
            if (queue.value[index].status === 'processing') {
                activeCount.value = Math.max(0, activeCount.value - 1)
            }
            queue.value.splice(index, 1)
        }
    }

    function retryFailed() {
        queue.value.forEach(item => {
            if (item.status === 'failed') {
                item.status = 'pending'
                item.retryCount = 0
                item.error = undefined
            }
        })
        if (!isProcessing.value && !isPaused.value) {
            processQueue()
        }
    }

    async function processQueue() {
        if (isPaused.value || activeCount.value >= concurrentLimit.value) return

        // Find next pending item
        const nextItem = queue.value.find((i: QueueItem) => i.status === 'pending')
        if (!nextItem) {
            isProcessing.value = activeCount.value > 0
            return
        }

        isProcessing.value = true
        activeCount.value++
        nextItem.status = 'processing'

        // Trigger next immediately if concurrency allows
        if (activeCount.value < concurrentLimit.value) {
            processQueue()
        }

        try {
            await aiApi.completeQuestion({
                questionId: nextItem.id,
                type: 'both' // Default to complete both
            })
            nextItem.status = 'completed'
        } catch (error: any) {
            nextItem.error = error.message || '请求失败'

            // Check for Rate Limit (429) or other specific errors
            if (nextItem.error?.includes('429') || nextItem.error?.includes('Quota') || nextItem.error?.includes('exhausted')) {
                // Critical: Rate limit hit. Pause immediately to prevent more failures.
                message.error('触发 AI 频率限制，任务已自动暂停。请稍后手动继续，或降低并发数。')
                nextItem.status = 'pending' // Return to pending
                nextItem.retryCount = 0     // Reset retry count for later
                activeCount.value-- // Decrement active count since we are bailing out
                pause() // Global pause
                isProcessing.value = activeCount.value > 0
                return // Stop processing this branch
            }

            if (nextItem.retryCount < 2) {
                nextItem.status = 'retrying'
                nextItem.retryCount++

                // Exponential backoff for normal retries
                const delay = 2000 * Math.pow(2, nextItem.retryCount)

                setTimeout(() => {
                    if (nextItem.status === 'retrying') {
                        nextItem.status = 'pending'
                        if (!isPaused.value) processQueue()
                    }
                }, delay)
            } else {
                nextItem.status = 'failed'
            }
        } finally {
            // Only decrement if we didn't bail out earlier (which we did for 429)
            // But wait, if we bailed out, we already decremented. 
            // If we finished successfully or failed normally:
            if (nextItem.status !== 'pending') { // 'pending' means we put it back (429 case)
                activeCount.value--
                // Process next if not paused
                if (!isPaused.value) processQueue()
            }
        }
    }

    return {
        queue,
        isProcessing,
        isPaused,
        concurrentLimit,
        activeCount,

        pendingCount,
        processingCount,
        completedCount,
        failedCount,
        totalCount,
        hasPending,

        addToQueue,
        clearCompleted,
        clearAll,
        pause,
        resume,
        remove,
        retryFailed
    }
})
