import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import type { MenuItem } from '@/types/menu'

export interface CartItem {
  menuItem: MenuItem
  quantity: number
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])

  const totalCents = computed(() =>
    items.value.reduce(
      (total, item) => total + item.menuItem.price_cents * item.quantity,
      0,
    ),
  )

  function addItem(menuItem: MenuItem) {
    const existingItem = items.value.find(
      (item) => item.menuItem.id === menuItem.id,
    )

    if (existingItem) {
      existingItem.quantity += 1
      return
    }

    items.value.push({
      menuItem,
      quantity: 1,
    })
  }

  function decreaseItem(menuItemId: number) {
    const item = items.value.find(
      (cartItem) => cartItem.menuItem.id === menuItemId,
    )

    if (!item) {
      return
    }

    if (item.quantity === 1) {
      items.value = items.value.filter(
        (cartItem) => cartItem.menuItem.id !== menuItemId,
      )
      return
    }

    item.quantity -= 1
  }

  function clearCart() {
    items.value = []
  }

  return {
    items,
    totalCents,
    addItem,
    decreaseItem,
    clearCart,
  }
})