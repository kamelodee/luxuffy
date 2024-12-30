# Brand API Documentation

## Endpoints

Base URL: `/api/brands/`

## List Brands

**GET** `/api/brands/`

Lists all brands with pagination.

### Query Parameters
- `search`: Search brands by name or description
- `ordering`: Order results by field (prefix with `-` for descending)
  - Available fields: `name`, `created_at`
- `page`: Page number
- `page_size`: Number of items per page

### Response
```json
{
    "count": 123,
    "next": "http://api.example.org/brands/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Nike",
            "slug": "nike",
            "logo": "http://example.com/media/brands/nike-logo.png",
            "product_count": 25
        }
    ]
}
```

## Get Brand Detail

**GET** `/api/brands/{id}/`

Retrieve detailed information about a specific brand.

### Response
```json
{
    "id": 1,
    "name": "Nike",
    "slug": "nike",
    "description": "Just Do It",
    "logo": "http://example.com/media/brands/nike-logo.png",
    "website": "https://nike.com",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z",
    "product_count": 25,
    "products": [
        {
            "id": 1,
            "name": "Air Max",
            "slug": "air-max",
            "price": "199.99",
            "thumbnail": "http://example.com/media/products/air-max.png",
            "status": "active"
        }
    ]
}
```

## Create Brand

**POST** `/api/brands/`

Create a new brand. Requires authentication.

### Request Body
```json
{
    "name": "Nike",
    "description": "Just Do It",
    "logo": null,  // File upload
    "website": "https://nike.com"
}
```

### Response
```json
{
    "id": 1,
    "name": "Nike",
    "slug": "nike",
    "description": "Just Do It",
    "logo": null,
    "website": "https://nike.com"
}
```

## Update Brand

**PUT/PATCH** `/api/brands/{id}/`

Update an existing brand. Requires authentication.

### Request Body (PUT)
```json
{
    "name": "Nike",
    "description": "Just Do It - Updated",
    "logo": null,  // File upload
    "website": "https://nike.com"
}
```

### Request Body (PATCH)
```json
{
    "description": "Just Do It - Updated"
}
```

### Response
```json
{
    "id": 1,
    "name": "Nike",
    "slug": "nike",
    "description": "Just Do It - Updated",
    "logo": null,
    "website": "https://nike.com"
}
```

## Delete Brand

**DELETE** `/api/brands/{id}/`

Delete a brand. Requires authentication.

### Response
```
Status: 204 No Content
```

## Error Responses

### 400 Bad Request
```json
{
    "name": ["A brand with this name already exists."]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```
