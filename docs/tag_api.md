# Tag API Documentation

## Endpoints

Base URL: `/api/tags/`

## List Tags

**GET** `/api/tags/`

Lists all tags with pagination.

### Query Parameters
- `search`: Search tags by name or description
- `ordering`: Order results by field (prefix with `-` for descending)
  - Available fields: `name`, `created_at`
- `page`: Page number
- `page_size`: Number of items per page

### Response
```json
{
    "count": 123,
    "next": "http://api.example.org/tags/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Summer Collection",
            "product_count": 15
        }
    ]
}
```

## Get Tag Detail

**GET** `/api/tags/{id}/`

Retrieve detailed information about a specific tag.

### Response
```json
{
    "id": 1,
    "name": "Summer Collection",
    "description": "Summer 2023 Collection",
    "created_at": "2023-01-01T00:00:00Z",
    "product_count": 15,
    "products": [
        {
            "id": 1,
            "name": "Beach Shirt",
            "slug": "beach-shirt",
            "price": "29.99",
            "thumbnail": "http://example.com/media/products/beach-shirt.png",
            "status": "active"
        }
    ]
}
```

## Create Tag

**POST** `/api/tags/`

Create a new tag. Requires authentication.

### Request Body
```json
{
    "name": "Summer Collection",
    "description": "Summer 2023 Collection"
}
```

### Response
```json
{
    "id": 1,
    "name": "Summer Collection",
    "description": "Summer 2023 Collection"
}
```

## Update Tag

**PUT/PATCH** `/api/tags/{id}/`

Update an existing tag. Requires authentication.

### Request Body (PUT)
```json
{
    "name": "Summer Collection",
    "description": "Summer 2023 Collection - Updated"
}
```

### Request Body (PATCH)
```json
{
    "description": "Summer 2023 Collection - Updated"
}
```

### Response
```json
{
    "id": 1,
    "name": "Summer Collection",
    "description": "Summer 2023 Collection - Updated"
}
```

## Delete Tag

**DELETE** `/api/tags/{id}/`

Delete a tag. Requires authentication.

### Response
```
Status: 204 No Content
```

## Error Responses

### 400 Bad Request
```json
{
    "name": ["A tag with this name already exists."]
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
