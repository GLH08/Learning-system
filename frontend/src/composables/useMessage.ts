import { createDiscreteApi } from 'naive-ui'

const { message, notification, dialog, loadingBar } = createDiscreteApi(
  ['message', 'notification', 'dialog', 'loadingBar']
)

export function useMessage() {
  return message
}

export function useNotification() {
  return notification
}

export function useDialog() {
  return dialog
}

export function useLoadingBar() {
  return loadingBar
}
