import type { OrderRequest, OrderResponse } from '@/types/order'

const API_URL = 'http://127.0.0.1:8000/api/v1'

export async function createOrder(
  order: OrderRequest,
  idempotencyKey: string,
): Promise<OrderResponse> {
  const response = await fetch(`${API_URL}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey,
    },
    body: JSON.stringify(order),
  })

  if (!response.ok) {
    throw new Error('Failed to create order')
  }

  return response.json()
}