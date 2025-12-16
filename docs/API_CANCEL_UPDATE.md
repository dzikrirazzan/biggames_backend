# API Documentation - Cancel Reservation & Update Order Status

Dokumentasi untuk fitur baru yang ditambahkan pada backend BigGames.

---

## 1. Cancel Reservation

### Endpoint
```
POST /api/reservations/{reservation_id}/cancel
```

### Authentication
**Required:** Bearer Token (User atau Admin)

### Description
Endpoint ini digunakan untuk membatalkan reservasi. User hanya bisa membatalkan reservasi milik mereka sendiri, sedangkan Admin bisa membatalkan reservasi siapa saja.

### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `reservation_id` | UUID | ID reservasi yang akan dibatalkan |

### Request Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

### Request Body
Tidak ada (empty body)

### Response Success (200 OK)
```json
{
  "message": "Reservation cancelled successfully"
}
```

### Response Errors

#### 404 Not Found
```json
{
  "detail": "Reservation not found"
}
```

#### 403 Forbidden
```json
{
  "detail": "You don't have permission to cancel this reservation"
}
```

#### 400 Bad Request
```json
{
  "detail": "Cannot cancel reservation with status: completed"
}
```

### Business Rules
1. **Ownership Check**: User hanya bisa cancel reservasi sendiri, kecuali jika user adalah Admin
2. **Status Validation**: Reservasi tidak bisa dibatalkan jika statusnya sudah `COMPLETED` atau `CANCELLED`
3. **Payment Update**: Jika ada payment terkait, statusnya akan otomatis diubah menjadi `CANCELLED`

### Example Usage

#### cURL
```bash
curl -X POST \
  'https://your-api.com/api/reservations/c9b60940-2904-4cfc-9175-fa6b702e0614/cancel' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json'
```

#### JavaScript/TypeScript (Fetch)
```typescript
const cancelReservation = async (reservationId: string) => {
  const response = await fetch(
    `${API_BASE_URL}/api/reservations/${reservationId}/cancel`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
};
```

#### Axios
```typescript
import axios from 'axios';

const cancelReservation = async (reservationId: string) => {
  try {
    const response = await axios.post(
      `/api/reservations/${reservationId}/cancel`,
      {}, // empty body
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error cancelling reservation:', error.response?.data);
    throw error;
  }
};
```

---

## 2. Update F&B Order Status (Admin)

### Endpoint
```
POST /api/admin/fb/orders/{order_id}/status
PUT /api/admin/fb/orders/{order_id}/status
```

**Note:** Endpoint mendukung **POST** dan **PUT** method untuk backward compatibility.

### Authentication
**Required:** Bearer Token (Admin only)

### Description
Endpoint ini digunakan oleh Admin untuk mengubah status pesanan F&B (misalnya dari PENDING → PREPARING → READY → DELIVERED).

### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `order_id` | UUID | ID pesanan F&B yang akan diupdate |

### Request Headers
```http
Authorization: Bearer {admin_access_token}
Content-Type: application/json
```

### Request Body
```json
{
  "status": "DELIVERED"
}
```

#### Available Status Values
- `PENDING` - Pesanan baru, belum diproses
- `PREPARING` - Sedang disiapkan
- `READY` - Siap untuk diambil/diantar
- `DELIVERED` - Sudah diterima customer
- `CANCELLED` - Dibatalkan

### Response Success (200 OK)
```json
{
  "id": "86f88a75-57df-44f9-bd37-b51321d15045",
  "user_id": "uuid",
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "reservation_id": "uuid",
  "items": [
    {
      "id": "uuid",
      "menu_item_id": "uuid",
      "menu_item_name": "Nasi Goreng",
      "qty": 2,
      "price": 25000,
      "subtotal": 50000
    }
  ],
  "subtotal": 50000,
  "total_amount": 50000,
  "status": "DELIVERED",
  "notes": "Extra pedas",
  "created_at": "2025-12-16T10:30:00Z"
}
```

### Response Errors

#### 404 Not Found
```json
{
  "detail": "Order not found"
}
```

#### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### Example Usage

#### cURL (POST method)
```bash
curl -X POST \
  'https://your-api.com/api/admin/fb/orders/86f88a75-57df-44f9-bd37-b51321d15045/status' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{"status": "DELIVERED"}'
```

#### JavaScript/TypeScript (Fetch)
```typescript
const updateOrderStatus = async (
  orderId: string, 
  newStatus: 'PENDING' | 'PREPARING' | 'READY' | 'DELIVERED' | 'CANCELLED'
) => {
  const response = await fetch(
    `${API_BASE_URL}/api/admin/fb/orders/${orderId}/status`,
    {
      method: 'POST', // atau 'PUT'
      headers: {
        'Authorization': `Bearer ${adminToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status: newStatus }),
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
};
```

#### Axios
```typescript
import axios from 'axios';

const updateOrderStatus = async (orderId: string, newStatus: string) => {
  try {
    const response = await axios.post(
      `/api/admin/fb/orders/${orderId}/status`,
      { status: newStatus },
      {
        headers: {
          'Authorization': `Bearer ${adminToken}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error updating order status:', error.response?.data);
    throw error;
  }
};
```

#### React Example (with state management)
```tsx
const AdminOrderManagement = () => {
  const [orders, setOrders] = useState([]);
  
  const handleStatusUpdate = async (orderId: string, newStatus: string) => {
    try {
      const updatedOrder = await updateOrderStatus(orderId, newStatus);
      
      // Update local state
      setOrders(prevOrders => 
        prevOrders.map(order => 
          order.id === orderId ? updatedOrder : order
        )
      );
      
      toast.success('Order status updated successfully');
    } catch (error) {
      toast.error(`Failed to update: ${error.message}`);
    }
  };
  
  return (
    <div>
      {orders.map(order => (
        <OrderCard 
          key={order.id}
          order={order}
          onStatusChange={handleStatusUpdate}
        />
      ))}
    </div>
  );
};
```

---

## Testing

### Test Cancel Reservation

1. **Test sebagai User (cancel reservasi sendiri)**
```bash
# Login dulu
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"password"}'

# Dapat token, lalu cancel reservasi
curl -X POST http://localhost:8000/api/reservations/{id}/cancel \
  -H 'Authorization: Bearer {token}'
```

2. **Test sebagai Admin (cancel reservasi user lain)**
```bash
# Login sebagai admin
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"admin_password"}'

# Cancel reservasi user lain
curl -X POST http://localhost:8000/api/reservations/{other_user_reservation_id}/cancel \
  -H 'Authorization: Bearer {admin_token}'
```

### Test Update Order Status

```bash
# Login sebagai admin
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"admin_password"}'

# Update order status
curl -X POST http://localhost:8000/api/admin/fb/orders/{order_id}/status \
  -H 'Authorization: Bearer {admin_token}' \
  -H 'Content-Type: application/json' \
  -d '{"status":"DELIVERED"}'
```

---

## Migration Notes

### Frontend Changes Required

#### 1. Cancel Reservation
Pastikan endpoint yang dipanggil adalah:
```
POST /api/reservations/{id}/cancel
```
**Bukan:** `/api/reservations/{id}/delete`

#### 2. Update Order Status
Method bisa menggunakan **POST** atau **PUT**, keduanya supported:
```
POST /api/admin/fb/orders/{id}/status   ✅
PUT /api/admin/fb/orders/{id}/status    ✅
```

---

## Deployment Notes

File yang diupdate:
- `app/api/routes/reservations.py` - Endpoint cancel reservation
- `app/api/routes/admin.py` - Support POST method untuk FB order status
- `app/services/reservation.py` - Logic cancel reservation

Setelah deploy:
1. Restart service: `docker-compose restart api` (local)
2. Render akan auto-deploy saat push ke GitHub
3. Test endpoints menggunakan Swagger UI: `/docs`

---

## Troubleshooting

### Error: "You don't have permission to cancel this reservation"
**Solusi:** User coba cancel reservasi orang lain. Pastikan:
- User login dengan akun yang benar
- Atau gunakan akun admin untuk cancel reservasi siapa saja

### Error: "Cannot cancel reservation with status: completed"
**Solusi:** Reservasi sudah completed/cancelled, tidak bisa dicancel lagi. Ini by design untuk data integrity.

### Error: "Admin access required"
**Solusi:** Update order status hanya bisa dilakukan admin. Pastikan:
- Token yang digunakan adalah token admin
- User yang login memiliki `is_admin: true`

---

## Related Endpoints

### Get All Reservations (Admin)
```
GET /api/admin/reservations
```

### Get User's Reservations
```
GET /api/reservations/me
```

### Get All FB Orders (Admin)
```
GET /api/admin/fb/orders
```

### Get User's FB Orders
```
GET /api/fb/orders/me
```

---

**Last Updated:** December 16, 2025
**Version:** 1.0
