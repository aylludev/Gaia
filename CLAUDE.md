# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gaia** is a Django-based ERP system for Agroinsumos Merkosur, an agricultural supplies company in Colombia. The system manages inventory, sales, purchases, payments, and financial reporting.

## Development Setup

### Virtual Environment
```bash
# Activate virtual environment
source env/bin/activate

# Install dependencies
pip install -r requeriments.txt
```

### Database
- PostgreSQL database configured in `Gaia/db.py`
- Database name: `ams`
- Run migrations: `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`

### Running the Server
```bash
# Development server
python manage.py runserver

# Collect static files (required for production)
python manage.py collectstatic
```

### Common Django Commands
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Django shell for testing
python manage.py shell

# Create app
python manage.py startapp app_name
```

## Architecture Overview

### App Structure (Greek Gods Theme)

The project is organized into domain-specific apps named after Greek deities:

- **hades**: User authentication, authorization, custom User model, BaseModel with audit fields
- **artemisa**: Inventory management, products, categories, purchases, providers, price history
- **ilitia**: Sales, clients, quotations (DetSale links to artemisa.Product)
- **hermes**: Financial management, purchase/sale payments, cash closing
- **apolo**: Reporting system (uses WeasyPrint for PDF generation)
- **core**: Shared utilities, multi-currency support, dashboard
- **homepage**: Landing page

### Key Architectural Patterns

#### BaseModel Pattern
All business models inherit from `hades.models.BaseModel`, providing:
- `created_by` / `updated_by`: Foreign keys to User (uses django-crum for automatic population)
- `created_at` / `updated_at`: Automatic timestamps
- `to_json()`: Standard method for JSON serialization

#### Custom User Model
- Location: `hades.models.User`
- Extends `AbstractUser`
- Includes group session management via `get_group_sessions()`
- Settings: `AUTH_USER_MODEL = 'hades.User'`

#### Permission System
All views use `ValidatePermissionRequiredMixin` from `hades.mixins`:
- Group-based permissions stored in session
- Users can switch groups: `hades:change_group/<pk>/`
- Permission format: `'view_entity'`, `'add_entity'`, etc.
- Superusers bypass all checks

#### Multi-Currency Support
- Currency model in `core.models.Currency`
- Session-based currency selection
- Context processor: `core.context_processors.currency_context`
- Utility: `core.utils.convert_price(price, request)`

### Standard View Pattern

All views follow this structure:

```python
class EntityListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Entity
    template_name = 'entity/list.html'
    permission_required = 'view_entity'

    def post(self, request, *args, **kwargs):
        # AJAX endpoint for data
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

Forms return JSON responses for AJAX handling:

```python
class EntityForm(ModelForm):
    class Meta:
        model = Entity
        fields = '__all__'
        widgets = {
            'field': forms.Select(attrs={'class': 'select2', 'style': 'width: 100%'}),
        }

    def save(self, commit=True):
        data = {}
        form = super()
        try:
            if form.is_valid():
                form.save()
            else:
                data['error'] = form.errors
        except Exception as e:
            data['error'] = str(e)
        return data
```

### AJAX Architecture

The entire application uses AJAX for form submissions and data loading:

- Frontend: `submit_with_ajax()` in `/static/js/functions.js`
- Views handle POST requests with `action` parameter
- Forms submit without page reload
- Responses are JSON with `error` key on failure
- Success messages use SweetAlert2

### Template Structure

```
templates/
├── hzt/body.html           # Base layout
├── pages/index2.html       # Dashboard with sidebar
├── list.html               # Generic DataTables list
├── form.html               # Generic AJAX form
└── delete.html             # Generic delete confirmation

app/templates/entity/
├── list.html               # Extends generic list.html
└── form.html               # Extends generic form.html (if custom)
```

Templates override blocks:
- `{% block head %}` - CSS/JS includes
- `{% block app-content %}` - Main content
- `{% block javascript %}` - Page scripts

### URL Namespacing

All apps use namespaced URLs:
```python
# In app/urls.py
app_name = 'artemisa'

urlpatterns = [
    path('product/list/', ProductListView.as_view(), name='product_list'),
    path('product/add/', ProductCreateView.as_view(), name='product_create'),
    path('product/update/<int:pk>/', ProductUpdateView.as_view(), name='product_update'),
    path('product/delete/<int:pk>/', ProductDeleteView.as_view(), name='product_delete'),
]

# Usage in templates
{% url 'artemisa:product_list' %}
{% url 'artemisa:product_update' product.id %}
```

### Data Relationships

Key cross-app dependencies:
- `artemisa.Product` → used by `ilitia.Sale` (DetSale)
- `artemisa.Purchase` → tracked by `hermes.PurchasePayment`
- `ilitia.Sale` → tracked by `hermes.SalePayment`
- All models → `hades.User` (created_by, updated_by)

### Stock Management

Inventory automatically updates:
- Purchases: Increase product stock (in PurchaseDetail save)
- Sales: Decrease product stock (in DetSale save)
- Use `django.db.transaction.atomic()` for consistency

## Adding New Features

### Creating a New CRUD Entity

1. **Model** (`app/models.py`):
```python
class Entity(BaseModel):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name

    def to_json(self):
        item = model_to_dict(self)
        item['created_at'] = self.created_at.strftime('%Y-%m-%d')
        return item
```

2. **Form** (`app/forms.py`):
```python
class EntityForm(ModelForm):
    class Meta:
        model = Entity
        fields = '__all__'

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

3. **Views** (`app/views.py`):
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

class EntityCreateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, CreateView):
    model = Entity
    form_class = EntityForm
    template_name = 'form.html'
    success_url = reverse_lazy('app:entity_list')
    permission_required = 'add_entity'

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                form = self.get_form()
                form.instance.created_by = request.user
                data = form.save()
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)
```

4. **URLs** (`app/urls.py`):
```python
urlpatterns = [
    path('entity/list/', EntityListView.as_view(), name='entity_list'),
    path('entity/add/', EntityCreateView.as_view(), name='entity_create'),
    path('entity/update/<int:pk>/', EntityUpdateView.as_view(), name='entity_update'),
    path('entity/delete/<int:pk>/', EntityDeleteView.as_view(), name='entity_delete'),
]
```

5. **Template** (`app/templates/entity/list.html`):
```django
{% extends 'list.html' %}
{% load static %}

{% block columns %}
    <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Options</th>
    </tr>
{% endblock %}

{% block javascript %}
    <script>
        // DataTable configuration
        var table = $('#data').DataTable({
            // standard config
        });
    </script>
{% endblock %}
```

6. **Migrations**:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Generating PDFs with WeasyPrint

```python
from django.template.loader import get_template
from weasyprint import HTML, CSS
from django.conf import settings
import os

class EntityPdfView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        entity = get_object_or_404(Entity, pk=self.kwargs['pk'])
        template = get_template('entity/pdf.html')

        context = {'entity': entity}
        html = template.render(context)

        css_url = os.path.join(settings.BASE_DIR, 'static/lib/bootstrap-4.6.0/css/bootstrap.min.css')
        pdf = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(
            stylesheets=[CSS(css_url)]
        )

        return HttpResponse(pdf, content_type='application/pdf')
```

### Working with Transactions

For operations that modify multiple models (e.g., sales with inventory updates):

```python
from django.db import transaction

def post(self, request, *args, **kwargs):
    data = {}
    try:
        with transaction.atomic():
            # Create sale
            sale = Sale.objects.create(...)

            # Create sale details
            for detail in details:
                DetSale.objects.create(sale=sale, ...)

                # Update stock
                product.stock -= detail.cant
                product.save()

    except Exception as e:
        data['error'] = str(e)
    return JsonResponse(data)
```

## Frontend Libraries

- **jQuery 3.7.1**: DOM manipulation and AJAX
- **Bootstrap 4.6.0**: UI framework
- **DataTables 1.10.24**: Interactive tables (all list views)
- **Select2**: Enhanced select dropdowns
- **SweetAlert2**: Alerts and confirmations
- **jQuery-confirm**: Modal confirmations
- **Moment.js**: Date manipulation
- **Tempus Dominus**: Date/time picker

## Configuration Notes

### Database Configuration
Database settings are in `Gaia/db.py` (separate from settings.py):
```python
POSTGRESQL = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ams',
        # ... connection details
    }
}
```

### Static Files
- Development: Served automatically when `DEBUG=True`
- Production: Run `python manage.py collectstatic` first
- Location: `/static/` for source, `/staticfiles/` for collected

### Security Settings
Production settings already configured:
- `DEBUG = False`
- `ALLOWED_HOSTS` configured
- `CSRF_TRUSTED_ORIGINS` set
- `CSRF_COOKIE_SECURE = True`
- `SESSION_COOKIE_SECURE = True`

### Localization
- Language: Spanish (Colombia) - `'es-co'`
- Timezone: `'America/Bogota'`
- All dates stored in UTC, displayed in local time

## Important Conventions

### Model Conventions
- All models inherit from `BaseModel`
- Implement `to_json()` method
- Use `verbose_name` and `verbose_name_plural` in Meta
- Foreign keys use descriptive names, not generic `fk`

### View Conventions
- Always use mixins: `LoginRequiredMixin`, `ValidatePermissionRequiredMixin`
- POST method handles AJAX requests with `action` parameter
- Return `JsonResponse` for AJAX, not redirect
- Set `created_by` in CreateView: `form.instance.created_by = request.user`

### Template Conventions
- Extend generic templates when possible: `list.html`, `form.html`
- Override specific blocks, don't duplicate layout
- Use `{% url %}` tag, never hardcode URLs
- Use `{% load static %}` for static files

### JavaScript Conventions
- Global utilities in `/static/js/functions.js`
- App-specific JS in `app/static/entity/js/`
- Use `submit_with_ajax()` for form submissions
- Handle errors with `message_error(obj)`
- Always include CSRF token in AJAX requests

### Naming Conventions
- URLs: `entity_list`, `entity_create`, `entity_update`, `entity_delete`
- Templates: `entity/list.html`, `entity/form.html`
- Views: `EntityListView`, `EntityCreateView`, etc.
- Forms: `EntityForm`

## Debugging

### Common Issues

**ImportError: No module 'django'**
- Activate virtual environment: `source env/bin/activate`

**CSRF verification failed**
- Check CSRF token in AJAX: `csrftoken = getCookie('csrftoken')`
- Verify `CSRF_TRUSTED_ORIGINS` in settings

**Permission denied**
- Check user has correct group assigned
- Verify group has the required permission
- Check `permission_required` attribute in view

**Static files not loading**
- Development: Ensure `DEBUG=True`
- Production: Run `python manage.py collectstatic`

**Database connection error**
- Verify PostgreSQL is running
- Check credentials in `Gaia/db.py`
- Ensure database `ams` exists

## File Structure Quick Reference

```
Gaia/
├── manage.py
├── requeriments.txt
├── Gaia/                    # Project settings
│   ├── settings.py
│   ├── urls.py             # Root URL configuration
│   ├── db.py               # Database settings
│   └── wsgi.py
├── env/                     # Virtual environment
├── static/                  # Global static files
├── templates/               # Global templates
├── media/                   # User uploads
├── hades/                   # Auth & Users
├── artemisa/                # Inventory & Purchases
├── ilitia/                  # Sales & Clients
├── hermes/                  # Payments & Finance
├── apolo/                   # Reports
├── core/                    # Shared utilities
└── homepage/                # Landing page
```
