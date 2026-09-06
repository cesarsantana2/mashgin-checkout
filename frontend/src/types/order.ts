export interface OrderItemRequest {
  menu_item_id: number
  quantity: number
}

export interface OrderRequest {
  items: OrderItemRequest[]
  payment: {
    method: 'card'
  }
}

export interface OrderItemResponse {
  menu_item_id: number
  item_name: string
  quantity: number
  unit_price_cents: number
}

export interface OrderResponse {
  id: number
  status: string
  total_cents: number
  items: OrderItemResponse[]
}