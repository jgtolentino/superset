# No Controllers Unless Unavoidable

## Core Principle

Odoo controllers (HTTP endpoints) should be avoided in favor of:

1. **XML-RPC/JSON-RPC** - Native Odoo external API
2. **Server Actions** - For automation triggered by UI
3. **Computed Fields** - For derived data
4. **Scheduled Actions** - For background tasks

## When Controllers ARE Acceptable

1. **Webhooks** - Receiving external system callbacks
2. **OAuth Callbacks** - Authentication flows
3. **File Downloads** - Custom report generation
4. **Public Pages** - Guest-accessible content

## Anti-Patterns to Avoid

### DON'T: Custom API endpoints for CRUD

```python
# BAD: Custom controller for data access
@http.route('/api/partners', type='json', auth='user')
def get_partners(self):
    return request.env['res.partner'].search_read([])
```

### DO: Use native RPC

```python
# GOOD: Use Odoo's built-in API
# Client calls: /web/dataset/call_kw
```

### DON'T: Custom controllers for actions

```python
# BAD: Controller for business logic
@http.route('/api/confirm_order', type='json', auth='user')
def confirm_order(self, order_id):
    order = request.env['sale.order'].browse(order_id)
    order.action_confirm()
```

### DO: Use server actions or direct model methods

```python
# GOOD: Call model method via RPC
# Client calls sale.order.action_confirm() via RPC
```

## If You Must Use Controllers

1. Place in `controllers/` directory
2. Use proper authentication (`auth='user'` or `auth='public'`)
3. Implement CSRF protection for POST requests
4. Document the endpoint in API docs
5. Add rate limiting for public endpoints

```python
from odoo import http
from odoo.http import request

class WebhookController(http.Controller):

    @http.route('/webhook/payment', type='json', auth='public', methods=['POST'], csrf=False)
    def payment_webhook(self, **kwargs):
        """
        Webhook endpoint for payment provider callbacks.

        Required because: External payment provider pushes notifications.
        Alternative considered: Polling (rejected due to latency requirements).
        """
        # Validate signature
        # Process payment
        return {'status': 'ok'}
```

## Justification Required

Any PR adding a controller MUST include:

1. Reason why native RPC is insufficient
2. Security considerations
3. Rate limiting strategy (if public)
4. Documentation
