import api from './index'

export interface Category {
  id: string
  name: string
  parentId: string | null
  description: string | null
  sortOrder: number
  questionCount: number
  children: Category[]
  createdAt: string
  updatedAt: string
}

export interface CategoryCreate {
  name: string
  parentId?: string | null
  description?: string
  sortOrder?: number
}

export interface CategoryUpdate {
  name?: string
  parentId?: string | null
  description?: string
  sortOrder?: number
}

export const categoriesApi = {
  // Get category tree
  getCategories() {
    return api.get<any, { data: Category[] }>('/categories')
  },
  
  // Get category details
  getCategory(id: string) {
    return api.get<any, { data: Category }>(`/categories/${id}`)
  },
  
  // Create category
  createCategory(data: CategoryCreate) {
    return api.post<any, { data: Category }>('/categories', data)
  },
  
  // Update category
  updateCategory(id: string, data: CategoryUpdate) {
    return api.put<any, { data: Category }>(`/categories/${id}`, data)
  },
  
  // Delete category
  deleteCategory(id: string) {
    return api.delete(`/categories/${id}`)
  }
}
