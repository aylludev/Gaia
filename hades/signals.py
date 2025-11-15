"""
Signals para el módulo hades (autenticación y usuarios)

Este módulo contiene signals que se ejecutan automáticamente
en respuesta a eventos del sistema de autenticación.
"""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from core.models import Currency
from decouple import config


@receiver(user_logged_in)
def initialize_user_session(sender, request, user, **kwargs):
    """
    Inicializa grupo y moneda en sesión automáticamente al hacer login.

    Este signal se ejecuta cada vez que un usuario hace login exitosamente,
    asegurando que la sesión tenga los datos necesarios para el funcionamiento
    del sistema.

    Inicializa:
    1. Grupo activo del usuario (primer grupo asignado)
    2. Moneda predeterminada del sistema

    Args:
        sender: La clase del modelo User
        request: HttpRequest actual
        user: Instancia del usuario que acaba de hacer login
        **kwargs: Argumentos adicionales del signal

    Example:
        Este signal se ejecuta automáticamente, no necesita ser llamado manualmente.
        Al hacer login, request.session['group'] y request.session['currency']
        estarán disponibles.
    """

    # ========================================
    # 1. Inicializar Grupo
    # ========================================
    if 'group' not in request.session:
        groups = user.groups.all()
        if groups.exists():
            group = groups.first()
            request.session['group'] = [{'id': group.id, 'name': group.name}]
            print(f"[Signal] Grupo inicializado en sesión: {group.name} (ID: {group.id})")
        else:
            print(f"[Signal] Advertencia: Usuario '{user.username}' no tiene grupos asignados")

    # ========================================
    # 2. Inicializar Moneda
    # ========================================
    if 'currency' not in request.session:
        # Opción 1: Usar moneda configurada en .env (recomendado)
        default_code = config('DEFAULT_CURRENCY_CODE', default='COP')
        default_currency = Currency.objects.filter(code=default_code).first()

        # Opción 2: Si no existe la moneda configurada, usar la primera disponible
        if not default_currency:
            default_currency = Currency.objects.first()
            if default_currency:
                print(f"[Signal] Advertencia: Moneda '{default_code}' no encontrada, usando '{default_currency.code}' como fallback")

        if default_currency:
            request.session['currency'] = default_currency.code
            print(f"[Signal] Moneda inicializada en sesión: {default_currency.code} ({default_currency.name})")
        else:
            print("[Signal] Advertencia: No hay monedas configuradas en la base de datos")
