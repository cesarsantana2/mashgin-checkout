import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from '@/App.vue'
import { fetchMenu } from '@/api/menu'
import { ApiError, createOrder } from '@/api/orders'
import type { MenuItem } from '@/types/menu'
import type { OrderRequest, OrderResponse } from '@/types/order'

vi.mock('@/api/menu', () => ({
  fetchMenu: vi.fn<() => Promise<MenuItem[]>>(),
}))

vi.mock('@/api/orders', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/orders')>()

  return {
    ...actual,
    createOrder: vi.fn<
      (
        order: OrderRequest,
        idempotencyKey: string,
      ) => Promise<OrderResponse>
    >(),
  }
})

const menu: MenuItem[] = [
  {
    id: 1,
    name: 'Chips',
    description: 'Classic potato chips',
    price_cents: 199,
    available: true,
  },
]

const completedOrder: OrderResponse = {
  id: 42,
  status: 'completed',
  total_cents: 199,
  items: [
    {
      menu_item_id: 1,
      item_name: 'Chips',
      quantity: 1,
      unit_price_cents: 199,
    },
  ],
}

function mountApp() {
  return mount(App, {
    global: {
      plugins: [createPinia()],
    },
  })
}

async function addChipsToCart(
  wrapper: ReturnType<typeof mountApp>,
) {
  await flushPromises()

  const addButton = wrapper
    .findAll('button')
    .find((button) => button.text() === 'Add to order')

  expect(addButton).toBeDefined()

  await addButton!.trigger('click')
}

function findCheckoutButton(
  wrapper: ReturnType<typeof mountApp>,
) {
  const checkoutButton = wrapper
    .findAll('button')
    .find(
      (button) =>
        button.text() === 'Complete order · $1.99',
    )

  expect(checkoutButton).toBeDefined()

  return checkoutButton!
}

describe('checkout', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(fetchMenu).mockResolvedValue(menu)
    vi.mocked(createOrder).mockResolvedValue(completedOrder)
  })

  it('loads the menu and adds an item to the cart', async () => {
    const wrapper = mountApp()

    await addChipsToCart(wrapper)

    expect(wrapper.text()).toContain('Chips')
    expect(wrapper.text()).toContain('Total')
    expect(wrapper.text()).toContain('$1.99')
    expect(wrapper.text()).toContain(
      'Complete order · $1.99',
    )
  })

  it('submits the order and shows the confirmation', async () => {
    const wrapper = mountApp()

    await addChipsToCart(wrapper)
    await findCheckoutButton(wrapper).trigger('click')
    await flushPromises()

    expect(createOrder).toHaveBeenCalledExactlyOnceWith({
        items: [
          {
            menu_item_id: 1,
            quantity: 1,
          },
        ],
        payment: {
          method: 'card',
        },
      }, expect.any(String))


    expect(wrapper.text()).toContain("You're all set!")
    expect(wrapper.text()).toContain('#42')
    expect(wrapper.text()).toContain('$1.99')
  })

  it('keeps the cart and reuses the idempotency key after a network failure', async () => {
    vi.mocked(createOrder)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(completedOrder)

    const wrapper = mountApp()

    await addChipsToCart(wrapper)
    await findCheckoutButton(wrapper).trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain(
      'We could not reach checkout. Please check the connection and try again.',
    )

    expect(wrapper.text()).toContain('Chips')
    expect(wrapper.text()).toContain(
      'Complete order · $1.99',
    )

    const firstKey =
      vi.mocked(createOrder).mock.calls[0]?.[1]

    await findCheckoutButton(wrapper).trigger('click')
    await flushPromises()

    const secondKey =
      vi.mocked(createOrder).mock.calls[1]?.[1]

    expect(firstKey).toBeDefined()
    expect(secondKey).toBe(firstKey)

    expect(wrapper.text()).toContain("You're all set!")
    expect(wrapper.text()).toContain('#42')
  })

  it('shows a useful message when an item becomes unavailable', async () => {
    vi.mocked(createOrder).mockRejectedValueOnce(
      new ApiError(409, 'Menu item 1 is unavailable'),
    )

    const wrapper = mountApp()

    await addChipsToCart(wrapper)
    await findCheckoutButton(wrapper).trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain(
      'An item in your order is no longer available. Please update your order and try again.',
    )

    expect(wrapper.text()).toContain('Chips')
    expect(wrapper.text()).toContain(
      'Complete order · $1.99',
    )
  })

  it('shows a useful message when the order is invalid', async () => {
    vi.mocked(createOrder).mockRejectedValueOnce(
      new ApiError(422, 'Invalid order'),
    )

    const wrapper = mountApp()

    await addChipsToCart(wrapper)
    await findCheckoutButton(wrapper).trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain(
      'Your order could not be submitted. Please review your cart and try again.',
    )

    expect(wrapper.text()).toContain('Chips')
  })
})