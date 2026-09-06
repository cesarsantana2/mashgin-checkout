<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchMenu } from '@/api/menu'
import { useCartStore } from '@/stores/cart'
import type { MenuItem } from '@/types/menu'

const menuItems = ref<MenuItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const cart = useCartStore()

onMounted(async () => {
  try {
    menuItems.value = await fetchMenu()
  } catch {
    error.value = 'We could not load the menu. Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main>
    <h1>Mashgin Checkout</h1>

    <p v-if="loading">Loading menu...</p>

    <p v-else-if="error">
      {{ error }}
    </p>

    <template v-else>
      <section>
        <h2>Menu</h2>

        <article v-for="item in menuItems" :key="item.id">
          <h3>{{ item.name }}</h3>
          <p>{{ item.description }}</p>
          <strong>${{ (item.price_cents / 100).toFixed(2) }}</strong>

          <div>
            <button
              type="button"
              :disabled="!item.available"
              @click="cart.addItem(item)"
            >
              {{ item.available ? 'Add to order' : 'Unavailable' }}
            </button>
          </div>
        </article>
      </section>

      <aside>
        <h2>Your order</h2>

        <p v-if="cart.items.length === 0">Your cart is empty.</p>

        <article
          v-for="cartItem in cart.items"
          v-else
          :key="cartItem.menuItem.id"
        >
          <strong>{{ cartItem.menuItem.name }}</strong>

          <div>
            <button
              type="button"
              @click="cart.decreaseItem(cartItem.menuItem.id)"
            >
              −
            </button>

            <span>{{ cartItem.quantity }}</span>

            <button type="button" @click="cart.addItem(cartItem.menuItem)">
              +
            </button>
          </div>
        </article>

        <div v-if="cart.items.length > 0">
          <h3>Total: ${{ (cart.totalCents / 100).toFixed(2) }}</h3>

          <button type="button" @click="cart.clearCart()">
            Clear order
          </button>
        </div>
      </aside>
    </template>
  </main>
</template>