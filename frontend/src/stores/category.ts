import { defineStore } from 'pinia'
import { ref } from 'vue'
import { categoriesApi, Category, CategoryCreate, CategoryUpdate } from '@/api/categories'

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>([])
  const currentCategory = ref<Category | null>(null)
  const loading = ref(false)
  
  const fetchCategories = async () => {
    loading.value = true
    try {
      const response = await categoriesApi.getCategories()
      categories.value = response.data
    } finally {
      loading.value = false
    }
  }
  
  const fetchCategory = async (id: string) => {
    loading.value = true
    try {
      const response = await categoriesApi.getCategory(id)
      currentCategory.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }
  
  const createCategory = async (data: CategoryCreate) => {
    const response = await categoriesApi.createCategory(data)
    return response.data
  }
  
  const updateCategory = async (id: string, data: CategoryUpdate) => {
    const response = await categoriesApi.updateCategory(id, data)
    return response.data
  }
  
  const deleteCategory = async (id: string) => {
    await categoriesApi.deleteCategory(id)
  }
  
  return {
    categories,
    currentCategory,
    loading,
    fetchCategories,
    fetchCategory,
    createCategory,
    updateCategory,
    deleteCategory
  }
})
