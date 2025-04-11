# ShopSentiment API Documentation

This document describes the available API endpoints for the ShopSentiment application. The API allows clients to programmatically access product reviews, sentiment analysis, and other features of the application.

## Base URL

All API endpoints are accessible at `/api/v1/` relative to the base URL of the application.

For example, if the application is hosted at `https://shopsentiment.example.com`, the base URL for the API would be `https://shopsentiment.example.com/api/v1/`.

## Authentication

All API endpoints require authentication using a JWT token. To obtain a token, you need to authenticate using the `/api/v1/auth/login` endpoint.

Include the token in the Authorization header for all subsequent requests:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Authentication

#### POST /api/v1/auth/login

Authenticate and obtain a JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "username",
    "email": "user@example.com"
  }
}
```

#### POST /api/v1/auth/logout

Invalidate the current JWT token.

**Request:**
No request body needed. Include JWT token in Authorization header.

**Response:**
```json
{
  "status": "success",
  "message": "Successfully logged out"
}
```

### Product Reviews

#### GET /api/v1/reviews/{product_id}

Retrieve reviews for a specific product.

**Parameters:**
- `product_id` (path parameter): The ID of the product to retrieve reviews for.

**Query Parameters:**
- `page` (optional): The page number for pagination. Default is 1.
- `per_page` (optional): Number of reviews per page. Default is 20.
- `min_rating` (optional): Filter by minimum rating. Default is 1.
- `max_rating` (optional): Filter by maximum rating. Default is 5.
- `sentiment` (optional): Filter by sentiment ('positive', 'negative', 'neutral').
- `start_date` (optional): Filter reviews created after this date (YYYY-MM-DD).
- `end_date` (optional): Filter reviews created before this date (YYYY-MM-DD).
- `keyword` (optional): Filter reviews containing this keyword.

**Response:**
```json
{
  "status": "success",
  "data": {
    "product": {
      "id": "B07X5JDQMK",
      "platform": "amazon",
      "title": "Product Title",
      "brand": "Brand Name",
      "price": "49.99",
      "image_url": "https://example.com/image.jpg"
    },
    "reviews": [
      {
        "id": 123,
        "rating": 4,
        "title": "Great product",
        "content": "This product works really well...",
        "author": "John D.",
        "date": "2023-05-15",
        "sentiment": "positive",
        "sentiment_score": 0.85,
        "verified_purchase": true
      }
    ],
    "pagination": {
      "total_reviews": 157,
      "page": 1,
      "per_page": 20,
      "pages": 8
    },
    "stats": {
      "avg_rating": 4.2,
      "rating_distribution": {
        "1": 5,
        "2": 7,
        "3": 20,
        "4": 50,
        "5": 75
      },
      "sentiment_distribution": {
        "positive": 75,
        "neutral": 20,
        "negative": 5
      }
    }
  }
}
```

#### GET /api/v1/products

Retrieve a list of products that have been analyzed.

**Query Parameters:**
- `page` (optional): The page number for pagination. Default is 1.
- `per_page` (optional): Number of products per page. Default is 10.
- `platform` (optional): Filter by platform ('amazon', 'ebay', 'custom').

**Response:**
```json
{
  "status": "success",
  "data": {
    "products": [
      {
        "id": "B07X5JDQMK",
        "platform": "amazon",
        "title": "Product Title",
        "brand": "Brand Name",
        "price": "49.99",
        "image_url": "https://example.com/image.jpg",
        "review_count": 157,
        "avg_rating": 4.2,
        "last_updated": "2023-06-15T14:30:00Z"
      }
    ],
    "pagination": {
      "total_products": 25,
      "page": 1,
      "per_page": 10,
      "pages": 3
    }
  }
}
```

#### GET /api/v1/products/{product_id}

Retrieve details of a specific product.

**Parameters:**
- `product_id` (path parameter): The ID of the product to retrieve.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "B07X5JDQMK",
    "platform": "amazon",
    "title": "Product Title",
    "brand": "Brand Name",
    "price": "49.99",
    "image_url": "https://example.com/image.jpg",
    "description": "Product description...",
    "review_count": 157,
    "avg_rating": 4.2,
    "last_updated": "2023-06-15T14:30:00Z",
    "stats": {
      "rating_distribution": {
        "1": 5,
        "2": 7,
        "3": 20,
        "4": 50,
        "5": 75
      },
      "sentiment_distribution": {
        "positive": 75,
        "neutral": 20,
        "negative": 5
      }
    }
  }
}
```

### Analysis

#### POST /api/v1/analyze

Start a new product analysis.

**Request:**
```json
{
  "platform": "amazon",
  "product_id": "B07X5JDQMK",
  "url": null,
  "review_selector": null,
  "max_pages": 5
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "task_id": "abc123def456",
    "message": "Analysis started successfully",
    "status_url": "/api/v1/tasks/abc123def456"
  }
}
```

#### GET /api/v1/tasks/{task_id}

Check the status of an analysis task.

**Parameters:**
- `task_id` (path parameter): The ID of the task to check.

**Response:**
```json
{
  "status": "success",
  "data": {
    "task_id": "abc123def456",
    "status": "PROGRESS",
    "progress": {
      "current": 35,
      "total": 100,
      "message": "Scraping page 2 of 5"
    },
    "result": null
  }
}
```

For completed tasks:
```json
{
  "status": "success",
  "data": {
    "task_id": "abc123def456",
    "status": "SUCCESS",
    "progress": {
      "current": 100,
      "total": 100,
      "message": "Analysis complete"
    },
    "result": {
      "product_id": "B07X5JDQMK",
      "reviews_count": 157,
      "avg_rating": 4.2,
      "product_url": "/products/B07X5JDQMK"
    }
  }
}
```

### Export

#### GET /api/v1/export/{product_id}

Export product reviews in the specified format.

**Parameters:**
- `product_id` (path parameter): The ID of the product to export reviews for.

**Query Parameters:**
- `format` (required): Export format ('csv' or 'json').
- `include_sentiment` (optional): Include sentiment analysis in export. Default is true.
- `include_product_info` (optional): Include product details in export. Default is true.

**Response:**
For CSV format, the endpoint will return a CSV file download.

For JSON format, the endpoint will return a JSON file download.

Example JSON response structure:
```json
{
  "product": {
    "id": "B07X5JDQMK",
    "platform": "amazon",
    "title": "Product Title",
    "brand": "Brand Name",
    "price": "49.99",
    "image_url": "https://example.com/image.jpg"
  },
  "reviews": [
    {
      "id": 123,
      "rating": 4,
      "title": "Great product",
      "content": "This product works really well...",
      "author": "John D.",
      "date": "2023-05-15",
      "sentiment": "positive",
      "sentiment_score": 0.85,
      "verified_purchase": true
    }
  ],
  "stats": {
    "avg_rating": 4.2,
    "rating_distribution": {
      "1": 5,
      "2": 7,
      "3": 20,
      "4": 50,
      "5": 75
    },
    "sentiment_distribution": {
      "positive": 75,
      "neutral": 20,
      "negative": 5
    }
  },
  "export_date": "2023-06-15T14:30:00Z"
}
```

### Keywords and Insights

#### GET /api/v1/keywords/{product_id}

Retrieve extracted keywords and key phrases from reviews.

**Parameters:**
- `product_id` (path parameter): The ID of the product to retrieve keywords for.

**Response:**
```json
{
  "status": "success",
  "data": {
    "keywords": [
      {
        "keyword": "battery life",
        "count": 25,
        "sentiment_score": 0.65,
        "review_ids": [123, 456, 789]
      },
      {
        "keyword": "easy to use",
        "count": 18,
        "sentiment_score": 0.92,
        "review_ids": [234, 567, 890]
      }
    ]
  }
}
```

## Error Handling

All API endpoints follow a standard error response format:

```json
{
  "status": "error",
  "error": {
    "code": 404,
    "message": "Product not found"
  }
}
```

### Common Error Codes

- `400`: Bad Request - The request was malformed or contains invalid parameters
- `401`: Unauthorized - Authentication is required or failed
- `403`: Forbidden - The authenticated user does not have permission to access this resource
- `404`: Not Found - The requested resource does not exist
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - An unexpected error occurred on the server

## Rate Limiting

API requests are subject to rate limiting to prevent abuse. The current limits are:

- 60 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

The response headers include rate limiting information:

- `X-RateLimit-Limit`: The maximum number of requests allowed per time window
- `X-RateLimit-Remaining`: The number of requests remaining in the current time window
- `X-RateLimit-Reset`: The time when the current rate limit window resets (Unix timestamp)

When the rate limit is exceeded, a 429 Too Many Requests response will be returned.

## Pagination

API endpoints that return collections of resources support pagination through the following query parameters:

- `page`: The page number (starting from 1)
- `per_page`: The number of items per page

The response includes pagination metadata:

```json
"pagination": {
  "total": 157,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

## Versioning

The API is versioned to ensure backward compatibility as new features are added. The current version is v1, which is reflected in the base URL: `/api/v1/`.

When breaking changes are introduced, a new version (e.g., `/api/v2/`) will be released, and the previous version will continue to be supported for a specified deprecation period. 