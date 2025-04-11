# ShopSentiment API Authentication Guide

*Last updated: April 18, 2025*

This guide explains the authentication mechanisms used by the ShopSentiment API and best practices for secure implementation.

## Authentication Methods

ShopSentiment supports the following authentication methods:

### API Key Authentication (v1)

The primary authentication method for API v1 is API key authentication using Bearer tokens.

#### Obtaining an API Key

1. Sign in to your [ShopSentiment Developer Console](https://shopsentiment.com/developer)
2. Navigate to "API Keys" in the sidebar
3. Click "Generate New API Key"
4. Name your key (e.g., "Development", "Production")
5. Choose the appropriate access level
6. Click "Create"

Your new API key will be displayed once. Make sure to copy and securely store it, as you won't be able to retrieve it again.

#### Using API Keys in Requests

Include your API key in the `Authorization` header using the Bearer scheme:

```bash
curl -X GET "https://api.shopsentiment.com/v1/products" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### OAuth 2.0 Authentication (v2)

API v2 uses OAuth 2.0 with JWT (JSON Web Tokens) for authentication, providing enhanced security and more flexibility.

#### Client Registration

To use OAuth 2.0:

1. Sign in to your [ShopSentiment Developer Console](https://shopsentiment.com/developer)
2. Navigate to "OAuth Applications" in the sidebar
3. Click "Register New Application"
4. Enter the application details:
   - Name
   - Redirect URIs
   - Scopes requested
5. Click "Register"

You will receive a client ID and client secret. Keep your client secret secure; it cannot be retrieved later.

#### OAuth 2.0 Flow

ShopSentiment supports the following OAuth 2.0 flows:

1. **Authorization Code Flow** (for server-side applications)
2. **Client Credentials Flow** (for service-to-service authentication)
3. **Implicit Flow** (for single-page applications)

##### Authorization Code Flow

1. Redirect the user to the authorization endpoint:

```
https://api.shopsentiment.com/v2/oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  scope=read:products+write:reviews&
  state=SECURE_RANDOM_STATE
```

2. User grants permission
3. ShopSentiment redirects back to your `redirect_uri` with an authorization code
4. Exchange the authorization code for an access token:

```bash
curl -X POST "https://api.shopsentiment.com/v2/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&
      code=AUTHORIZATION_CODE&
      client_id=YOUR_CLIENT_ID&
      client_secret=YOUR_CLIENT_SECRET&
      redirect_uri=YOUR_REDIRECT_URI"
```

5. Use the access token for API requests:

```bash
curl -X GET "https://api.shopsentiment.com/v2/products" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

##### Client Credentials Flow

For service-to-service authentication:

```bash
curl -X POST "https://api.shopsentiment.com/v2/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&
      client_id=YOUR_CLIENT_ID&
      client_secret=YOUR_CLIENT_SECRET&
      scope=read:products+write:reviews"
```

#### Token Response

A successful token request returns:

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA...",
  "scope": "read:products write:reviews"
}
```

#### Refreshing Tokens

When an access token expires, use the refresh token to get a new one:

```bash
curl -X POST "https://api.shopsentiment.com/v2/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&
      refresh_token=YOUR_REFRESH_TOKEN&
      client_id=YOUR_CLIENT_ID&
      client_secret=YOUR_CLIENT_SECRET"
```

## Scopes

OAuth 2.0 scopes control what operations your application can perform:

| Scope | Description |
|-------|-------------|
| `read:products` | Read-only access to product data |
| `write:products` | Create and update products |
| `delete:products` | Delete products |
| `read:reviews` | Read-only access to review data |
| `write:reviews` | Create and update reviews |
| `delete:reviews` | Delete reviews |
| `analyze:sentiment` | Access to sentiment analysis features |
| `search:all` | Access to search functionality |
| `webhooks:manage` | Create and manage webhooks |
| `feedback:read` | Read feedback data |
| `feedback:write` | Submit and update feedback |

Request only the scopes your application needs.

## Security Best Practices

### API Key Security

1. **Never expose API keys in client-side code**
   - Keep API keys on your server
   - Don't include them in mobile apps or frontend JavaScript

2. **Use environment variables**
   - Store API keys in environment variables
   - Don't hardcode them in your application

3. **Implement key rotation**
   - Regularly rotate your API keys
   - Update keys after team member departures

4. **Use different keys for different environments**
   - Separate keys for development, staging, and production
   - Limit production key access to essential personnel

### OAuth Security

1. **Protect client secrets**
   - Never expose client secrets in public code
   - Store securely using environment variables or a secrets manager

2. **Validate state parameter**
   - Always use and validate the `state` parameter to prevent CSRF attacks
   - Generate a cryptographically secure random value

3. **Validate redirect URIs**
   - Only use pre-registered redirect URIs
   - Use exact URI matching

4. **Implement PKCE for public clients**
   - Use PKCE (Proof Key for Code Exchange) for mobile and SPA applications
   - Generate and validate code challenges

5. **Secure token storage**
   - Store tokens securely (HTTPOnly cookies, secure storage)
   - Don't store in localStorage for web applications
   - Use secure storage mechanisms in mobile apps

6. **Verify JWT signatures**
   - Always verify the JWT signature before trusting token claims
   - Use a JWT library that validates signatures correctly

## Troubleshooting

### Common Error Codes

| HTTP Status | Error Code | Description | Solution |
|-------------|------------|-------------|----------|
| 401 | `invalid_token` | API key is invalid or expired | Generate a new API key |
| 401 | `expired_token` | OAuth token has expired | Refresh the access token |
| 401 | `invalid_client` | Client authentication failed | Check client ID and secret |
| 403 | `insufficient_scope` | Token lacks required scopes | Request additional scopes |
| 403 | `access_denied` | User denied authorization | Prompt user to grant access |
| 429 | `too_many_requests` | Rate limit exceeded | Implement backoff strategy |

### Debugging Tips

1. **Check response headers**
   - Look for `WWW-Authenticate` header for auth issues
   - Check for rate limit headers (`X-RateLimit-*`)

2. **Inspect token claims**
   - Decode (but don't manually verify) JWTs at [jwt.io](https://jwt.io/)
   - Verify scopes and expiration times

3. **Use verbose mode in API requests**
   - Add `-v` flag to curl commands to see headers
   - Check request/response details

## Migrating Between Authentication Methods

### From API Key to OAuth 2.0

When migrating from v1 (API Key) to v2 (OAuth):

1. Register an OAuth application
2. Update your authorization mechanism
3. Request appropriate scopes
4. Update your request headers
5. Implement token refresh logic

See the [Authentication Migration Guide](https://api.shopsentiment.com/docs/migration/authentication) for a step-by-step walkthrough.

## Support

If you encounter authentication issues:

1. Check our [Authentication FAQ](https://shopsentiment.com/developers/faq/authentication)
2. Post in the [Developer Forum](https://community.shopsentiment.com/developers)
3. Contact [api-support@shopsentiment.com](mailto:api-support@shopsentiment.com) 