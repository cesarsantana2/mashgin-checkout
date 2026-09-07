<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchMenu } from '@/api/menu'
import { ApiError, createOrder } from '@/api/orders'
import { useCartStore } from '@/stores/cart'
import type { MenuItem } from '@/types/menu'
import type { OrderRequest, OrderResponse } from '@/types/order'

const menuItems = ref<MenuItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const submitting = ref(false)
const checkoutError = ref<string | null>(null)
const completedOrder = ref<OrderResponse | null>(null)

const idempotencyKey = ref<string | null>(null)
const requestSignature = ref<string | null>(null)

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

function buildOrderRequest(): OrderRequest {
  return {
    items: cart.items.map((item) => ({
      menu_item_id: item.menuItem.id,
      quantity: item.quantity,
    })),
    payment: {
      method: 'card',
    },
  }
}

function getIdempotencyKey(order: OrderRequest): string {
  const signature = JSON.stringify(order)

  if (idempotencyKey.value === null || requestSignature.value !== signature) {
    idempotencyKey.value = crypto.randomUUID()
    requestSignature.value = signature
  }

  return idempotencyKey.value
}

async function submitOrder() {
  if (cart.items.length === 0 || submitting.value) {
    return
  }

  const order = buildOrderRequest()
  const key = getIdempotencyKey(order)

  submitting.value = true
  checkoutError.value = null

  try {
    completedOrder.value = await createOrder(order, key)

    cart.clearCart()
    idempotencyKey.value = null
    requestSignature.value = null
  } catch (caughtError) {
    if (caughtError instanceof ApiError) {
      if (caughtError.status === 409) {
        checkoutError.value =
          'An item in your order is no longer available. Please update your order and try again.'
      } else if (caughtError.status === 400 || caughtError.status === 422) {
        checkoutError.value =
          'Your order could not be submitted. Please review your cart and try again.'
      } else {
        checkoutError.value = 'Checkout is temporarily unavailable. Please try again.'
      }
    } else {
      checkoutError.value =
        'We could not reach checkout. Please check the connection and try again.'
    }
  } finally {
    submitting.value = false
  }
}

function startNewOrder() {
  completedOrder.value = null
  checkoutError.value = null
}
</script>

<template>
  <main class="checkout">
    <header class="checkout-header">
      <div>
        <p class="eyebrow">SELF CHECKOUT</p>
        <h1>Mashgin Checkout</h1>
      </div>

      <div class="status-badge">Ready</div>
    </header>

    <section v-if="loading" class="state-card">
      <div class="loader"></div>
      <h2>Loading menu</h2>
      <p>Just a moment while we prepare the checkout.</p>
    </section>

    <section v-else-if="error" class="state-card error-state">
      <div class="state-icon">!</div>
      <h2>Menu unavailable</h2>
      <p>{{ error }}</p>
    </section>

    <section v-else-if="completedOrder" class="state-card success-state">
      <div class="state-icon success-icon">✓</div>

      <p class="eyebrow">ORDER COMPLETE</p>
      <h2>You're all set!</h2>
      <p>Your order has been placed successfully.</p>

      <div class="receipt">
        <div>
          <span>Order</span>
          <strong>#{{ completedOrder.id }}</strong>
        </div>

        <div>
          <span>Total</span>
          <strong> ${{ (completedOrder.total_cents / 100).toFixed(2) }} </strong>
        </div>
      </div>

      <button type="button" class="primary-button new-order-button" @click="startNewOrder">
        Start new order
      </button>
    </section>

    <div v-else class="checkout-layout">
      <section class="menu-panel">
        <div class="section-heading">
          <div>
            <p class="eyebrow">SNACK BAR</p>
            <h2>Choose your items</h2>
          </div>

          <p class="section-help">Tap an item to add it to your order.</p>
        </div>

        <div class="product-grid">
          <article
            v-for="item in menuItems"
            :key="item.id"
            class="product-card"
            :class="{ unavailable: !item.available }"
          >
            <div class="product-icon">
              {{ item.name.charAt(0) }}
            </div>

            <div class="product-content">
              <h3>{{ item.name }}</h3>
              <p>{{ item.description }}</p>
            </div>

            <div class="product-footer">
              <strong class="product-price"> ${{ (item.price_cents / 100).toFixed(2) }} </strong>

              <button
                type="button"
                class="add-button"
                :disabled="!item.available || submitting"
                @click="cart.addItem(item)"
              >
                {{ item.available ? 'Add to order' : 'Unavailable' }}
              </button>
            </div>
          </article>
        </div>
      </section>

      <aside class="cart-panel">
        <div class="cart-header">
          <div>
            <p class="eyebrow">CURRENT ORDER</p>
            <h2>Your order</h2>
          </div>

          <span class="item-count">
            {{ cart.items.length }}
          </span>
        </div>

        <div v-if="cart.items.length === 0" class="empty-cart">
          <div class="empty-cart-icon">+</div>
          <h3>Your cart is empty</h3>
          <p>Select an item from the menu to get started.</p>
        </div>

        <template v-else>
          <div class="cart-items">
            <article v-for="cartItem in cart.items" :key="cartItem.menuItem.id" class="cart-item">
              <div class="cart-item-info">
                <strong>
                  {{ cartItem.menuItem.name }}
                </strong>

                <span>
                  ${{ ((cartItem.menuItem.price_cents * cartItem.quantity) / 100).toFixed(2) }}
                </span>
              </div>

              <div class="quantity-control">
                <button
                  type="button"
                  aria-label="Decrease quantity"
                  :disabled="submitting"
                  @click="cart.decreaseItem(cartItem.menuItem.id)"
                >
                  −
                </button>

                <strong>{{ cartItem.quantity }}</strong>

                <button
                  type="button"
                  aria-label="Increase quantity"
                  :disabled="submitting"
                  @click="cart.addItem(cartItem.menuItem)"
                >
                  +
                </button>
              </div>
            </article>
          </div>

          <div class="order-summary">
            <div class="total-row">
              <span>Total</span>

              <strong> ${{ (cart.totalCents / 100).toFixed(2) }} </strong>
            </div>

            <div class="payment-note">
              <div class="payment-icon">✓</div>

              <div>
                <strong>Simulated checkout</strong>
                <p>No payment details are collected or stored.</p>
              </div>
            </div>

            <p v-if="checkoutError" class="checkout-error" role="alert">
              {{ checkoutError }}
            </p>

            <button
              type="button"
              class="primary-button"
              :disabled="submitting"
              @click="submitOrder"
            >
              {{
                submitting
                  ? 'Processing...'
                  : `Complete order · $${(cart.totalCents / 100).toFixed(2)}`
              }}
            </button>

            <button
              type="button"
              class="clear-button"
              :disabled="submitting"
              @click="cart.clearCart()"
            >
              Clear order
            </button>
          </div>
        </template>
      </aside>
    </div>
  </main>
</template>
