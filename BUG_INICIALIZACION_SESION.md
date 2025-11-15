# Bug: Inicialización de Grupo y Moneda en Sesión

**Fecha de análisis:** 15 de noviembre de 2025
**Prioridad:** Media-Alta
**Componentes afectados:** Sistema de autenticación, Dashboard, Multi-moneda

---

## 📋 Descripción del Problema

Al iniciar sesión, el usuario debe tener automáticamente:
1. **Grupo activo** cargado en la sesión
2. **Moneda predeterminada** cargada en la sesión

**Comportamiento actual:**
- ❌ El grupo NO se carga automáticamente al hacer login
- ❌ La moneda NO se carga automáticamente al hacer login
- ⚠️ El grupo se carga solo cuando el usuario accede al Dashboard (fallback)
- ⚠️ La moneda NUNCA se carga automáticamente, el usuario debe seleccionarla manualmente

**Comportamiento esperado:**
- ✅ Al hacer login, el primer grupo del usuario debe cargarse en `request.session['group']`
- ✅ Al hacer login, una moneda predeterminada debe cargarse en `request.session['currency']`

---

## 🔍 Análisis del Código Actual

### 1. Modelo User - Método `get_group_sessions()`

**Ubicación:** `hades/models.py:47-57`

```python
def get_group_sessions(self):
    try:
        request = get_current_request()
        groups = self.groups.all()
        if groups.exists():
            if 'group' not in request.session:
                group = groups.first()
                request.session['group'] = [{'id': group.id, 'name': group.name}]
    except Exception as e:
        print(f"Error en get_group_sessions: {e}")
        pass
```

**Análisis:**
- ✅ El método existe y funciona correctamente
- ❌ **Problema:** Este método NUNCA se llama automáticamente al hacer login
- ⚠️ Solo se llama en vistas específicas (comentadas actualmente)

### 2. Vista de Login

**Ubicación:** `hades/views/login/views.py:11-22`

```python
class LoginFormView(LoginView):
    template_name = "user/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar Sesión'
        return context
```

**Análisis:**
- ❌ **Problema:** No inicializa grupo en sesión
- ❌ **Problema:** No inicializa moneda en sesión
- ❌ No sobrescribe el método `form_valid()` para ejecutar lógica post-login

### 3. DashboardView - Fallback Manual

**Ubicación:** `core/views.py:21-39`

```python
def get_active_group_name(self):
    """Obtiene el nombre del grupo activo de forma segura"""
    active_group = self.request.session.get('group')

    # Manejar diferentes formatos de grupo en sesión
    if isinstance(active_group, list) and active_group:
        return active_group[0].get('name', '')
    elif isinstance(active_group, dict):
        return active_group.get('name', '')
    elif isinstance(active_group, str):
        return active_group

    # Fallback: primer grupo del usuario
    if self.request.user.groups.exists():
        group_name = self.request.user.groups.first().name
        self.request.session['group'] = [{'name': group_name}]
        return group_name

    return ''
```

**Análisis:**
- ✅ Tiene lógica de fallback que funciona
- ⚠️ **Problema:** Solo se ejecuta cuando se accede al Dashboard
- ⚠️ **Problema:** Si el usuario va directamente a otra página (ej: /artemisa/product/list/), el grupo no se carga
- ⚠️ **Inconsistencia:** El fallback guarda `[{'name': group_name}]` pero le falta el 'id'

### 4. Context Processor de Moneda

**Ubicación:** `core/context_processors.py:3-10`

```python
def currency_context(request):
    currencies = Currency.objects.all()
    selected_code = request.session.get('currency', None)
    selected_currency = Currency.objects.filter(code=selected_code).first() if selected_code else None
    return {
        'currencies': currencies,
        'selected_currency': selected_currency,
    }
```

**Análisis:**
- ✅ Lee correctamente la moneda de la sesión
- ❌ **Problema:** Si no hay moneda en sesión, `selected_currency` es `None`
- ❌ **Problema:** No hay inicialización automática de moneda

### 5. Función `set_currency()`

**Ubicación:** `core/views.py:271-275`

```python
def set_currency(request, code):
    currency = Currency.objects.filter(code=code).first()
    if currency:
        request.session['currency'] = currency.code
    return redirect(request.META.get('HTTP_REFERER', '/'))
```

**Análisis:**
- ✅ Permite cambiar la moneda manualmente
- ❌ **Problema:** El usuario debe hacer clic manualmente para establecer una moneda
- ❌ No se llama automáticamente al hacer login

### 6. Código Comentado (Versión Anterior)

**Ubicación:** `core/views.py:140-237`

```python
"""
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name='dashboard.html'

    def get(self, request, *args, **kwargs):
        request.user.get_group_sessions()  # ← Aquí se llamaba antes
        return super().get(request, *args, **kwargs)
    # ...
"""
```

**Análisis:**
- ⚠️ La versión anterior sí llamaba a `get_group_sessions()` en el método `get()`
- ⚠️ Fue comentado, probablemente por refactorización
- ⚠️ La funcionalidad se perdió en el proceso

---

## 🐛 Resumen de Problemas Identificados

### Problema 1: Grupo No Se Inicializa al Login
**Impacto:** Alto

**Síntomas:**
- Al hacer login y acceder a cualquier página (excepto Dashboard), el grupo no está en sesión
- Las vistas que dependen de `request.session.get('group')` fallan o tienen comportamiento inesperado
- El mixin `ValidatePermissionRequiredMixin` puede fallar al verificar permisos

**Causa raíz:**
- `LoginFormView` no inicializa el grupo en sesión
- `get_group_sessions()` existe pero no se llama automáticamente

**Páginas afectadas:**
- Todas las páginas que usan `request.session.get('group')`
- Sistema de permisos personalizado

### Problema 2: Moneda No Se Inicializa al Login
**Impacto:** Medio

**Síntomas:**
- Al hacer login, no hay moneda seleccionada
- `selected_currency` es `None` en todos los templates
- El usuario debe seleccionar manualmente la moneda cada vez
- Los precios pueden no mostrarse correctamente sin moneda

**Causa raíz:**
- No existe ningún mecanismo automático para inicializar la moneda
- El context processor solo lee la sesión, no la inicializa

**Páginas afectadas:**
- Todas las páginas que muestran precios
- Sistema multi-moneda completo

### Problema 3: Inconsistencia en Formato de Grupo
**Impacto:** Bajo

**Síntomas:**
- El grupo se guarda con diferentes formatos:
  - `[{'id': 1, 'name': 'Admin'}]` en `get_group_sessions()`
  - `[{'name': 'Admin'}]` en fallback de Dashboard (sin id)

**Causa raíz:**
- Falta de estandarización en el formato de datos

---

## 💡 Soluciones Propuestas

### Solución 1: Signal Post-Login (RECOMENDADA)

Crear un signal que se ejecute automáticamente después de cada login exitoso.

**Ventajas:**
- ✅ Desacoplado del LoginView
- ✅ Se ejecuta automáticamente siempre que un usuario haga login
- ✅ No modifica código de terceros (LoginView de Django)
- ✅ Fácil de mantener y testear

**Desventajas:**
- Requiere crear un nuevo archivo de signals

**Implementación:**
```python
# hades/signals.py (NUEVO ARCHIVO)
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from core.models import Currency

@receiver(user_logged_in)
def initialize_user_session(sender, request, user, **kwargs):
    """
    Inicializa grupo y moneda en sesión al hacer login
    """
    # 1. Inicializar grupo
    if 'group' not in request.session:
        groups = user.groups.all()
        if groups.exists():
            group = groups.first()
            request.session['group'] = [{'id': group.id, 'name': group.name}]

    # 2. Inicializar moneda
    if 'currency' not in request.session:
        # Opción A: Usar moneda por defecto (COP para Colombia)
        default_currency = Currency.objects.filter(code='COP').first()

        # Opción B: Usar la primera moneda disponible
        if not default_currency:
            default_currency = Currency.objects.first()

        if default_currency:
            request.session['currency'] = default_currency.code
```

```python
# hades/apps.py (MODIFICAR)
from django.apps import AppConfig

class HadesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hades'

    def ready(self):
        import hades.signals  # Importar signals al iniciar la app
```

---

### Solución 2: Middleware Personalizado

Crear un middleware que verifique e inicialice grupo y moneda en cada request.

**Ventajas:**
- ✅ Se ejecuta en cada request
- ✅ Garantiza que siempre haya grupo y moneda en sesión
- ✅ Funciona incluso si el usuario accede directamente a una URL

**Desventajas:**
- ⚠️ Se ejecuta en CADA request (overhead de performance)
- ⚠️ Más complejo que un signal

**Implementación:**
```python
# hades/middleware.py (NUEVO ARCHIVO)
from core.models import Currency

class SessionInitializationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo para usuarios autenticados
        if request.user.is_authenticated:
            # Inicializar grupo si no existe
            if 'group' not in request.session:
                groups = request.user.groups.all()
                if groups.exists():
                    group = groups.first()
                    request.session['group'] = [{'id': group.id, 'name': group.name}]

            # Inicializar moneda si no existe
            if 'currency' not in request.session:
                default_currency = Currency.objects.filter(code='COP').first()
                if not default_currency:
                    default_currency = Currency.objects.first()
                if default_currency:
                    request.session['currency'] = default_currency.code

        response = self.get_response(request)
        return response
```

```python
# settings.py (MODIFICAR)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'hades.middleware.SessionInitializationMiddleware',  # ← AGREGAR AQUÍ
    'crum.CurrentRequestUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

---

### Solución 3: Sobrescribir `form_valid()` en LoginView

Modificar la vista de login para inicializar sesión al autenticarse.

**Ventajas:**
- ✅ Simple y directo
- ✅ Se ejecuta solo una vez al hacer login

**Desventajas:**
- ⚠️ Modifica el LoginView (menos desacoplado)
- ⚠️ No funciona si hay login mediante otros métodos (OAuth, API, etc.)

**Implementación:**
```python
# hades/views/login/views.py (MODIFICAR)
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from Gaia import settings
from core.models import Currency

class LoginFormView(LoginView):
    template_name = "user/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Sobrescribir para inicializar sesión"""
        response = super().form_valid(form)

        # Inicializar grupo
        user = self.request.user
        if 'group' not in self.request.session:
            groups = user.groups.all()
            if groups.exists():
                group = groups.first()
                self.request.session['group'] = [{'id': group.id, 'name': group.name}]

        # Inicializar moneda
        if 'currency' not in self.request.session:
            default_currency = Currency.objects.filter(code='COP').first()
            if not default_currency:
                default_currency = Currency.objects.first()
            if default_currency:
                self.request.session['currency'] = default_currency.code

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar Sesión'
        return context
```

---

## 🎯 Recomendación Final

**Implementar Solución 1: Signal Post-Login**

### ¿Por qué?

1. **Mejor práctica de Django:** Los signals son la forma recomendada para ejecutar código después de eventos
2. **Desacoplamiento:** No modifica las vistas existentes
3. **Mantenibilidad:** Fácil de entender y mantener
4. **Performance:** Solo se ejecuta al hacer login, no en cada request
5. **Extensibilidad:** Fácil agregar más lógica de inicialización en el futuro

### Plan de Implementación

#### Fase 1: Crear Signal (5 min)
1. Crear archivo `hades/signals.py`
2. Implementar signal `initialize_user_session`
3. Modificar `hades/apps.py` para importar signals

#### Fase 2: Configurar Moneda Predeterminada (2 min)
1. Decidir moneda predeterminada (COP recomendado para Colombia)
2. Opcional: Agregar configuración en `.env`
   ```env
   DEFAULT_CURRENCY_CODE=COP
   ```

#### Fase 3: Testing (10 min)
1. Crear usuario de prueba sin grupo/moneda en sesión
2. Hacer login
3. Verificar que `request.session['group']` existe
4. Verificar que `request.session['currency']` existe
5. Probar cambio de moneda con `set_currency()`
6. Probar cambio de grupo (si existe funcionalidad)

#### Fase 4: Limpieza de Código (5 min)
1. Eliminar código comentado en `core/views.py` (líneas 140-237)
2. Estandarizar formato de grupo en DashboardView fallback
3. Actualizar documentación

---

## ✅ Checklist de Verificación

### Antes de Implementar
- [ ] Verificar que existe al menos una moneda en la BD
- [ ] Verificar que los usuarios tienen grupos asignados
- [ ] Hacer backup de `hades/views/login/views.py`
- [ ] Hacer backup de `core/views.py`

### Durante la Implementación
- [ ] Crear `hades/signals.py`
- [ ] Modificar `hades/apps.py`
- [ ] Opcional: Agregar `DEFAULT_CURRENCY_CODE` a `.env`

### Después de Implementar
- [ ] Hacer logout
- [ ] Hacer login
- [ ] Verificar en Django shell:
  ```python
  from django.contrib.sessions.models import Session
  from django.contrib.auth import get_user_model

  User = get_user_model()
  user = User.objects.get(username='tu_usuario')

  # Ver datos de sesión
  session_key = request.session.session_key
  session = Session.objects.get(session_key=session_key)
  print(session.get_decoded())  # Debería mostrar 'group' y 'currency'
  ```
- [ ] Verificar en navegador:
  - [ ] Dashboard carga correctamente
  - [ ] Moneda se muestra en header/navbar
  - [ ] Permisos funcionan correctamente
- [ ] Probar con usuarios sin grupos asignados (no debería fallar)
- [ ] Probar con BD sin monedas (no debería fallar)

### Limpieza Final
- [ ] Eliminar código comentado en `core/views.py`
- [ ] Actualizar `CLAUDE.md` con nueva funcionalidad
- [ ] Crear tests unitarios para el signal
- [ ] Commit de cambios

---

## 📊 Comparación de Soluciones

| Criterio | Signal | Middleware | LoginView |
|----------|--------|------------|-----------|
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Desacoplamiento** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Mantenibilidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Django Best Practices** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Facilidad de Testing** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cobertura** | Login only | Todos los requests | Login only |
| **Overhead** | Bajo | Medio-Alto | Bajo |

**Ganador:** Signal Post-Login ⭐⭐⭐⭐⭐

---

## 🔗 Referencias

- [Django Signals Documentation](https://docs.djangoproject.com/en/5.2/topics/signals/)
- [Django Middleware Documentation](https://docs.djangoproject.com/en/5.2/topics/http/middleware/)
- [Django Sessions Documentation](https://docs.djangoproject.com/en/5.2/topics/http/sessions/)
- [Django user_logged_in Signal](https://docs.djangoproject.com/en/5.2/ref/signals/#django.contrib.auth.signals.user_logged_in)

---

## 📝 Notas Adicionales

### Moneda Predeterminada

Opciones para determinar la moneda predeterminada:

1. **Por país:** COP (Peso Colombiano) - Recomendado
2. **Por configuración:** Leer de `.env`
3. **Por usuario:** Agregar campo `default_currency` al modelo User
4. **Por primera disponible:** Usar `Currency.objects.first()`

**Recomendación:** Usar COP como predeterminada con fallback a la primera disponible.

### Cambio de Grupo

Actualmente existe la URL `hades:change_group/<pk>/` pero no se verificó su implementación en este análisis. Considerar documentar ese flujo también.

### Testing Manual

Para probar manualmente después de la implementación:

```python
# Django shell
python manage.py shell

from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

# Simular login y verificar sesión
from django.test import RequestFactory
from django.contrib.auth.signals import user_logged_in

factory = RequestFactory()
request = factory.get('/')
request.session = {}

# Ejecutar signal
user_logged_in.send(sender=user.__class__, request=request, user=user)

# Verificar
print(request.session.get('group'))     # Debería mostrar el grupo
print(request.session.get('currency'))  # Debería mostrar la moneda
```

---

**Tiempo estimado de implementación:** 30 minutos
**Nivel de riesgo:** Bajo
**Impacto en usuarios:** Alto (positivo)
