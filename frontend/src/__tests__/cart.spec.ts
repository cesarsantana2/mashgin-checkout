import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useCartStore } from '@/stores/cart'
import type { MenuItem } from '@/types/menu'

const chips: MenuItem = {
  id: 1,
  name: 'Chips',
  description: 'Classic potato chips',
  price_cents: 199,
  available: true,
}

const chocolate: MenuItem = {
  id: 2,
  name: 'Chocolate Bar',
  description: 'Milk chocolate bar',
  price_cents: 249,
  available: true,
}

describe('cart store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('adds an item to the cart', () => {
    const cart = useCartStore()

    cart.addItem(chips)

    expect(cart.items).toHaveLength(1)
    expect(cart.items[0]?.menuItem.id).toBe(chips.id)
    expect(cart.items[0]?.quantity).toBe(1)
  })

  it('increments the quantity when the same item is added twice', () => {
    const cart = useCartStore()

    cart.addItem(chips)
    cart.addItem(chips)

    expect(cart.items).toHaveLength(1)
    expect(cart.items[0]?.quantity).toBe(2)
  })

  it('calculates the total in cents', () => {
    const cart = useCartStore()

    cart.addItem(chips)
    cart.addItem(chips)
    cart.addItem(chocolate)

    expect(cart.totalCents).toBe(647)
  })

  it('decreases the quantity of an item', () => {
    const cart = useCartStore()

    cart.addItem(chips)
    cart.addItem(chips)

    cart.decreaseItem(chips.id)

    expect(cart.items[0]?.quantity).toBe(1)
  })

  it('removes an item when its quantity reaches zero', () => {
    const cart = useCartStore()

    cart.addItem(chips)

    cart.decreaseItem(chips.id)

    expect(cart.items).toHaveLength(0)
  })

  it('clears the cart', () => {
    const cart = useCartStore()

    cart.addItem(chips)
    cart.addItem(chocolate)

    cart.clearCart()

    expect(cart.items).toHaveLength(0)
    expect(cart.totalCents).toBe(0)
  })
})
