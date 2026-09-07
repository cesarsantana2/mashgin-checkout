import type { OrderRequest, OrderResponse } from '@/types/order'

const API_URL = 'http://127.0.0.1:8000/api/v1'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown }

    if (typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // The API did not return a JSON error body.
  }

  return 'Failed to create order'
}

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
    const message = await getErrorMessage(response)

    throw new ApiError(response.status, message)
  }

  return response.json()
}
