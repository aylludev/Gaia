# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gaia** is a Django 5.2 ERP system for Agroinsumos Merkosur, an agricultural supplies company in Colombia. The system manages inventory, sales, purchases, payments, and financial reporting. No REST API — purely Django views with AJAX (jQuery).

## Development Setup

```bash
# Activate virtual environment
source env/bin/activate

# Install dependencies
pip install -r requeriments.txt

# Run development server (port 9000)
bash deploy/server.sh
# or: python manage.py runserver 0.0.0.0:9000

# Apply migrations
python manage.py migrate

# Collect static files (production)
python manage.py collectstatic
```

**Deploy scripts** in `deploy/`:
- `server.sh` — dev server on port 9000
- `gunicorn.sh` — production WSGI (5 workers, Unix socket)
- `backup.sh` — PostgreSQL backup

**Environment variables** managed via `python-decouple`. Key var: `DEFAULT_CURRENCY_CODE` (auto-set in session on login via `hades/signals.py`).

## Architecture Overview

### App Structure (Greek Gods Theme)

- **hades**: User auth, custom User model, `BaseModel`, `ValidatePermissionRequiredMixin`, signals
- **artemisa**: Inventory — products, categories, purchases, providers, price history, signals
- **ilitia**: Sales, clients, quotations (`DetSale` links to `artemisa.Product`)
- **hermes**: Payments (purchase/sale), cash closing
- **apolo**: PDF reports (WeasyPrint)
- **core**: Dashboard, multi-currency, shared utils
- **homepage**: Landing page

### Views Directory Structure

Complex apps organize views in subdirectories, NOT a single `views.py`:

```
artemisa/
└── views/
    ├── product/views.py
    ├── purchase/views.py
    ├── provider/views.py
    └── ...
```

When adding a new view to an existing app, check if it uses the subdirectory pattern first.

### BaseModel Pattern

All business models inherit from `hades.models.BaseModel`:
- `created_by` / `updated_by`: Auto-populated via `django-crum`
- `created_at` / `updated_at`: Auto timestamps
- `to_json()`: Required method for AJAX serialization

`core.models.Currency` is the exception — it does NOT inherit BaseModel.

### Permission System

All views use `ValidatePermissionRequiredMixin` from `hades/mixins.py`:
- Group-based permissions stored in **session**, not standard Django permissions
- Session key: `request.session['group']` → list of `{'id': id, 'name': name}`
- Permission check: `group.permissions.filter(codename=perm).exists()`
- Superusers bypass all checks
- Users switch groups at `hades:change_group/<pk>/`

### Multi-Currency System

- `core.models.Currency`: `code`, `name`, `symbol`, `exchange_rate_to_base`, `image`
- Session key: `request.session['currency']` = currency code
- Auto-initialized on login via `hades/signals.py` (reads `DEFAULT_CURRENCY_CODE` from env)
- Conversion utility: `core.utils.convert_price(price, request)` — divides by `exchange_rate_to_base`
- Context processor `core.context_processors.currency_context` adds all currencies to templates

### Signals (Hidden Behaviors)

**`hades/signals.py`** — triggers on `user_logged_in`:
- Auto-initializes `request.session['group']` from user's first group
- Auto-initializes `request.session['currency']` from `DEFAULT_CURRENCY_CODE` env var

**`artemisa/signals.py`** — triggers `pre_save` on `Product`:
- Creates a `PriceHistory` record whenever `purchase_price` or `sale_price` changes
- Fires BEFORE the product is saved

### Stock Management

Stock changes are embedded in model save/delete methods (no Celery, all synchronous):
- **Purchases** → `PurchaseDetail.save()` increases `product.stock`
- **Sales** → `DetSale.save()` decreases `product.stock`
- **Deleting a Sale or Cotization** → custom `delete()` reverses all stock changes for every `DetSale`

Always wrap multi-model operations in `transaction.atomic()`.

### Standard View Pattern

```python
class EntityListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Entity
    template_name = 'entity/list.html'
    permission_required = 'view_entity'

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = [i.to_json() for i in Entity.objects.all()]
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Entity List'
        context['create_url'] = reverse_lazy('app:entity_create')
        return context
```

### Form Pattern

Forms handle their own save and return JSON (not standard Django form flow):

```python
class EntityForm(ModelForm):
    def save(self, commit=True):
        data = {}
        try:
            form = super()
            if form.is_valid():
                instance = form.save()
                data = instance.to_json()
            else:
                data['error'] = form.errors
        except Exception as e:
            data['error'] = str(e)
        return data
```

### AJAX Architecture

- Frontend utility: `submit_with_ajax()` and `message_error()` in `/static/js/functions.js`
- All views handle POST with `action` parameter (`'searchdata'`, `'add'`, `'edit'`, `'delete'`)
- Responses: JSON with `error` key on failure, model data on success
- Success feedback: SweetAlert2

### Template Structure

```
templates/
├── hzt/body.html          # Base layout
├── pages/index2.html      # Dashboard with sidebar
├── list.html              # Generic DataTables list
├── form.html              # Generic AJAX form
└── delete.html            # Generic delete confirmation

app/templates/entity/
├── list.html              # Extends generic list.html
└── form.html              # Custom form if needed
```

Template blocks: `{% block head %}`, `{% block app-content %}`, `{% block javascript %}`

### URL Namespacing

```python
app_name = 'artemisa'
# Usage: {% url 'artemisa:product_list' %}
# Usage: {% url 'artemisa:product_update' product.id %}
```

## Adding a New CRUD Entity

1. **Model** (`app/models.py`) — inherit `BaseModel`, implement `to_json()`
2. **Form** (`app/forms.py`) — override `save()` to return JSON dict
3. **Views** — in `app/views/entity/views.py` if app uses subdirectory pattern, else `app/views.py`
4. **URLs** (`app/urls.py`) — standard `entity_list/create/update/delete` names
5. **Template** (`app/templates/entity/list.html`) — extend `list.html`
6. **Migrations** — `python manage.py makemigrations && python manage.py migrate`

## PDF Generation (WeasyPrint)

```python
from weasyprint import HTML, CSS

pdf = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(
    stylesheets=[CSS(os.path.join(settings.BASE_DIR, 'static/lib/bootstrap-4.6.0/css/bootstrap.min.css'))]
)
return HttpResponse(pdf, content_type='application/pdf')
```

WeasyPrint runs synchronously — no background task queue exists in this project.

## Frontend Libraries

- **jQuery 3.7.1** + **Bootstrap 4.6.0**
- **DataTables 1.10.24** — all list views
- **Select2** — enhanced selects (`class='select2'`)
- **SweetAlert2** — alerts/confirmations
- **Tempus Dominus** + **Moment.js** — date/time pickers

## Configuration Notes

- **Database**: Settings in `Gaia/db.py`, imported in `settings.py`. DB name: `ams`
- **Django secret key and DB credentials** are stored in the repo (not environment-managed) — be careful not to expose them
- **Localization**: `LANGUAGE_CODE = 'es-co'`, `TIME_ZONE = 'America/Bogota'`
- **No test suite** — all `tests.py` files are empty stubs. No pytest, no CI.

## Debugging

**ImportError: No module 'django'** → `source env/bin/activate`

**CSRF verification failed** → Check `csrftoken = getCookie('csrftoken')` in AJAX; verify `CSRF_TRUSTED_ORIGINS`

**Permission denied in view** → Confirm user's group has the `permission_required` codename; superuser bypasses

**Session/currency not initialized** → Check `hades/signals.py` is registered in `hades/apps.py` `ready()`

**Static files not loading** → Development: `DEBUG=True`; Production: `python manage.py collectstatic`

**Stock inconsistency** → Check if `transaction.atomic()` wraps the operation; verify `delete()` overrides exist on related models
