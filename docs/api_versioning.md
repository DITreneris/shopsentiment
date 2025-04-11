# ShopSentiment API Documentation

*Last updated: April 18, 2025*

This document provides detailed information about the ShopSentiment API versions, endpoints, and how to work with our versioned API system.

## API Versioning

ShopSentiment uses semantic versioning for its API, with version information included in the URL path:

```
https://api.shopsentiment.com/v1/products
```

### Current Versions

| Version | Status | Released | Support Until | Notes |
|---------|--------|----------|---------------|-------|
| v1      | Active | Jan 2025 | Jan 2027      | Current stable version |
| v2-beta | Beta   | Mar 2025 | TBD           | Developer preview |

### Version Lifecycle

Each API version goes through the following stages:

1. **Developer Preview** - Early access for testing and feedback
2. **Beta** - Feature complete but may have changes before final release
3. **General Availability** - Stable release for production use
4. **Active Support** - Fully supported with all updates and fixes
5. **Maintenance Mode** - Security updates only
6. **Deprecated** - No updates, scheduled for removal
7. **Sunset** - Removed from service

### Version Headers

All API responses include version information in the headers:

```
X-API-Version: 1.3.2
X-API-Deprecated: false
X-API-Sunset-Date: null
```

For deprecated versions:

```
X-API-Version: 1.0.0
X-API-Deprecated: true
X-API-Sunset-Date: 2026-04-30
X-API-Migration-Guide: https://api.shopsentiment.com/docs/migration/v1-to-v2
```

## API v1 Endpoints

The following endpoints are available in API v1:

### Authentication

| Method | Endpoint             | Description                      |
|--------|----------------------|----------------------------------|
| POST   | `/v1/auth/token`     | Get an authentication token      |
| POST   | `/v1/auth/refresh`   | Refresh an expired token         |
| POST   | `/v1/auth/revoke`    | Revoke an active token           |

### Products

| Method | Endpoint                      | Description                      |
|--------|-------------------------------|----------------------------------|
| GET    | `/v1/products`                | List all products                |
| POST   | `/v1/products`                | Create a new product             |
| GET    | `/v1/products/{id}`           | Get a specific product           |
| PUT    | `/v1/products/{id}`           | Update a product                 |
| DELETE | `/v1/products/{id}`           | Delete a product                 |
| GET    | `/v1/products/{id}/stats`     | Get product statistics           |
| GET    | `/v1/products/{id}/sentiment` | Get product sentiment analysis   |

### Reviews

| Method | Endpoint                         | Description                      |
|--------|----------------------------------|----------------------------------|
| GET    | `/v1/reviews`                    | List all reviews                 |
| GET    | `/v1/products/{id}/reviews`      | Get reviews for a product        |
| POST   | `/v1/products/{id}/reviews`      | Add a review to a product        |
| GET    | `/v1/reviews/{id}`               | Get a specific review            |
| PUT    | `/v1/reviews/{id}`               | Update a review                  |
| DELETE | `/v1/reviews/{id}`               | Delete a review                  |
| GET    | `/v1/reviews/{id}/sentiment`     | Get sentiment for a review       |

### Sentiment Analysis

| Method | Endpoint                    | Description                         |
|--------|-----------------------------|-------------------------------------|
| POST   | `/v1/analyze/sentiment`     | Analyze sentiment of provided text  |
| POST   | `/v1/analyze/keywords`      | Extract keywords from provided text |
| POST   | `/v1/analyze/entities`      | Extract entities from provided text |

### Search

| Method | Endpoint                   | Description                           |
|--------|----------------------------|---------------------------------------|
| GET    | `/v1/search/reviews`       | Search for reviews                    |
| GET    | `/v1/search/products`      | Search for products                   |
| GET    | `/v1/search/unified`       | Search across all content types       |

### Feedback

| Method | Endpoint                   | Description                           |
|--------|----------------------------|---------------------------------------|
| GET    | `/v1/feedback`             | List all feedback                     |
| POST   | `/v1/feedback`             | Submit new feedback                   |
| GET    | `/v1/feedback/{id}`        | Get specific feedback                 |
| PUT    | `/v1/feedback/{id}`        | Update feedback                       |
| DELETE | `/v1/feedback/{id}`        | Delete feedback                       |

### Webhooks

| Method | Endpoint                   | Description                           |
|--------|----------------------------|---------------------------------------|
| GET    | `/v1/webhooks`             | List registered webhooks              |
| POST   | `/v1/webhooks`             | Register a new webhook                |
| GET    | `/v1/webhooks/{id}`        | Get a specific webhook               |
| PUT    | `/v1/webhooks/{id}`        | Update a webhook                      |
| DELETE | `/v1/webhooks/{id}`        | Delete a webhook                      |
| POST   | `/v1/webhooks/{id}/test`   | Test a webhook                        |

## API v2 Endpoints (Beta)

API v2 introduces several new features and improvements:

### New Features in v2

- Improved sentiment analysis with aspect-based sentiment
- Enhanced search capabilities with faceting and filtering
- Real-time data processing via WebSockets
- Expanded webhook event types
- Batch operations for improved performance

### Breaking Changes in v2

| Change | v1 Behavior | v2 Behavior |
|--------|-------------|-------------|
| Authentication | Token-based | OAuth 2.0 with JWT |
| Review Response | Flat structure | Nested structure with metadata |
| Error Format | Simple status codes | Detailed error objects with codes |
| Pagination | Offset-based | Cursor-based for improved performance |
| Date Format | ISO 8601 with timezone | Unix timestamp (seconds) |

See the [v1 to v2 Migration Guide](https://api.shopsentiment.com/docs/migration/v1-to-v2) for details on these changes.

### New v2 Endpoints

| Method | Endpoint                      | Description                      |
|--------|-------------------------------|----------------------------------|
| GET    | `/v2/analytics/trends`        | Get sentiment trends over time   |
| GET    | `/v2/analytics/comparisons`   | Compare products or categories   |
| GET    | `/v2/analytics/keywords`      | Get keyword frequency analysis   |
| WS     | `/v2/realtime`                | WebSocket for real-time updates  |
| POST   | `/v2/batch`                   | Perform batch operations         |

## Using API Versions

### Specifying a Version

Include the version in the URL path for all requests:

```bash
# Using v1
curl -X GET "https://api.shopsentiment.com/v1/products" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Using v2 (beta)
curl -X GET "https://api.shopsentiment.com/v2/products" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Version Compatibility

- **Minor Versions** (e.g., v1.1 to v1.2) maintain backward compatibility
- **Major Versions** (e.g., v1 to v2) may include breaking changes
- We recommend testing thoroughly when upgrading between major versions

### Version Support Timeline

- Each major version is actively supported for at least 12 months after the next major version is released
- At least 6 months notice will be given before any version is deprecated
- After deprecation, endpoints will continue to function for at least 3 more months before being removed

## Error Handling

API errors include version-specific information:

### v1 Error Format

```json
{
  "status": "error",
  "code": 400,
  "message": "Invalid product ID format"
}
```

### v2 Error Format

```json
{
  "error": {
    "type": "validation_error",
    "code": "invalid_product_id",
    "message": "Invalid product ID format",
    "details": {
      "field": "product_id",
      "reason": "must be a valid UUID"
    }
  },
  "request_id": "req_1234567890",
  "documentation_url": "https://api.shopsentiment.com/docs/errors#invalid_product_id"
}
```

## Versioning Best Practices

1. **Specify Explicit Versions**: Always include the version in your API requests
2. **Test Before Upgrading**: Test your integration with new versions before switching
3. **Monitor Deprecation Notices**: Watch headers for deprecation warnings
4. **Subscribe to Updates**: Join our developer newsletter for version announcements
5. **Use Our SDKs**: Our official SDKs handle versioning details for you

## Migration Resources

When migrating between versions, the following resources can help:

- [v1 to v2 Migration Guide](https://api.shopsentiment.com/docs/migration/v1-to-v2)
- [Migration Checklist](https://api.shopsentiment.com/docs/migration/checklist)
- [Version Comparison Tool](https://api.shopsentiment.com/tools/version-compare)
- [API Changelog](https://api.shopsentiment.com/docs/changelog)

For additional help with API versions or migration, contact our [API Support Team](mailto:api-support@shopsentiment.com). 