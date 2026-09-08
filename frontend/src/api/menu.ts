import type { MenuItem } from '@/types/menu'

const API_URL = '/api/v1'

export async function fetchMenu(): Promise<MenuItem[]> {
  const response = await fetch(`${API_URL}/menu`)

  if (!response.ok) {
    throw new Error('Failed to load menu')
  }

  return response.json()
}
