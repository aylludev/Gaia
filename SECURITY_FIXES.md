# Correcciones de Seguridad Críticas - Proyecto Gaia

**Fecha:** 14 de noviembre de 2025
**Rama:** `security/fix-critical-vulnerabilities`

## Resumen de Cambios

Este documento describe las correcciones de seguridad críticas implementadas en el proyecto Gaia para resolver vulnerabilidades identificadas en el análisis de buenas prácticas de Django.

---

## 🔒 Vulnerabilidades Corregidas

### 1. SECRET_KEY Expuesta ✅
- **Problema:** La SECRET_KEY estaba hardcodeada en `settings.py`
- **Solución:**
  - Generada nueva SECRET_KEY segura
  - Migrada a variable de entorno usando `python-decouple`
  - SECRET_KEY ahora se carga desde archivo `.env`

### 2. Credenciales de Base de Datos Expuestas ✅
- **Problema:** Contraseña de PostgreSQL hardcodeada en `db.py`
- **Solución:**
  - Todas las credenciales de BD migradas a variables de entorno
  - Configuración ahora usa `python-decouple` para cargar valores desde `.env`

### 3. Configuraciones de Seguridad HTTP Faltantes ✅
- **Problema:** Faltaban headers de seguridad HTTP importantes
- **Solución:** Agregadas las siguientes configuraciones en producción:
  - `SECURE_SSL_REDIRECT = True` - Redirige HTTP a HTTPS
  - `SECURE_HSTS_SECONDS = 31536000` - HSTS por 1 año
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
  - `SECURE_HSTS_PRELOAD = True`
  - `SECURE_CONTENT_TYPE_NOSNIFF = True`
  - `SECURE_BROWSER_XSS_FILTER = True`
  - `X_FRAME_OPTIONS = 'DENY'`
  - `SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'`
  - `SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'`

### 4. Bug en BaseModel.to_json() ✅
- **Problema:** Typo en líneas 22-24 de `hades/models.py`
  - `item['update_by']` se asignaba dos veces
  - `updated_at` se trataba como string en vez de datetime
- **Solución:** Corregidos los nombres de las claves del diccionario

---

## 📦 Dependencias Agregadas

```txt
python-decouple==3.8
```

Actualizar el entorno:
```bash
pip install -r requeriments.txt
```

---

## 📁 Archivos Modificados

### Archivos de Configuración
- ✅ `Gaia/settings.py` - Migrado a variables de entorno
- ✅ `Gaia/db.py` - Migrado a variables de entorno
- ✅ `.gitignore` - Agregadas exclusiones de archivos sensibles
- ✅ `requeriments.txt` - Agregado python-decouple

### Archivos Creados
- ✅ `.env` - Variables de entorno (NO en git)
- ✅ `.env.example` - Plantilla de variables de entorno (SÍ en git)
- ✅ `ANALISIS_BUENAS_PRACTICAS_DJANGO.md` - Análisis completo
- ✅ `SECURITY_FIXES.md` - Este documento

### Modelos
- ✅ `hades/models.py` - Corregido bug en BaseModel.to_json()

---

## 🚀 Instrucciones de Despliegue

### Para Desarrollo Local

1. **Copiar archivo de entorno:**
   ```bash
   cp .env.example .env
   ```

2. **Editar `.env` con valores reales:**
   ```bash
   nano .env
   ```

3. **Generar nueva SECRET_KEY (si es necesario):**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Activar entorno virtual e instalar dependencias:**
   ```bash
   source env/bin/activate
   pip install -r requeriments.txt
   ```

5. **Verificar configuración:**
   ```bash
   python manage.py check --deploy
   ```

### Para Producción

1. **Crear archivo `.env` en el servidor:**
   ```bash
   nano /home/amawta/Documentos/Proyectos/Gaia/.env
   ```

2. **Configurar variables de entorno:**
   ```env
   DJANGO_SECRET_KEY=nueva-clave-secreta-generada
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=138.197.36.105,agroinsumosmerkosur.com,www.agroinsumosmerkosur.com

   DB_NAME=ams
   DB_USER=postgres
   DB_PASSWORD=contraseña-segura
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. **Verificar permisos del archivo .env:**
   ```bash
   chmod 600 .env
   ```

4. **Reiniciar servidor:**
   ```bash
   sudo systemctl restart gunicorn  # o el servidor que uses
   ```

---

## ⚠️ Notas Importantes

### Seguridad del Archivo .env

- ❌ **NUNCA** commitear el archivo `.env` al repositorio
- ✅ El archivo `.env` está en `.gitignore`
- ✅ Solo el archivo `.env.example` debe estar en git
- ⚠️ Usar permisos restrictivos: `chmod 600 .env`

### Rotación de SECRET_KEY

Si necesitas rotar la SECRET_KEY sin perder sesiones activas:

```python
# Gaia/settings.py
from decouple import config

SECRET_KEY = config('DJANGO_SECRET_KEY')
SECRET_KEY_FALLBACKS = [
    config('OLD_SECRET_KEY_1', default=''),
    config('OLD_SECRET_KEY_2', default=''),
]
```

### Verificación de Seguridad

Ejecutar antes de desplegar a producción:

```bash
# Verificar configuración de seguridad
python manage.py check --deploy

# Verificar que .env no esté en git
git status

# Verificar que SECRET_KEY no esté en el historial
git log --all --full-history -- "Gaia/settings.py" | grep -i secret
```

---

## ✅ Checklist de Verificación

### Antes de Mergear

- [x] python-decouple instalado
- [x] Nueva SECRET_KEY generada
- [x] Archivo .env creado
- [x] Archivo .env.example creado
- [x] .gitignore actualizado
- [x] settings.py usa variables de entorno
- [x] db.py usa variables de entorno
- [x] Configuraciones de seguridad HTTP agregadas
- [x] Bug en BaseModel corregido
- [x] `python manage.py check --deploy` pasa sin errores
- [x] Archivo .env NO está en git
- [ ] Documentación actualizada (README.md)

### Antes de Desplegar

- [ ] Archivo .env configurado en servidor
- [ ] Permisos de .env configurados (600)
- [ ] SECRET_KEY única en producción
- [ ] DEBUG=False en producción
- [ ] ALLOWED_HOSTS configurado correctamente
- [ ] Certificado SSL instalado y configurado
- [ ] Servidor reiniciado
- [ ] Verificación de HTTPS funcionando
- [ ] Headers de seguridad verificados

---

## 📚 Referencias

- [Django Security Documentation](https://docs.djangoproject.com/en/5.2/topics/security/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [python-decouple Documentation](https://github.com/HBNetwork/python-decouple)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

## 🔄 Próximos Pasos

Ver `ANALISIS_BUENAS_PRACTICAS_DJANGO.md` para:
- Fase 2: Configuración y Estabilidad (Logging, Email, etc.)
- Fase 3: Calidad de Código (Tests, optimizaciones)
- Fase 4: Mejoras Avanzadas (CSP, CDN, monitoreo)

---

**Autor:** Claude Code
**Revisión requerida:** Sí
**Nivel de impacto:** CRÍTICO
**Requiere backup:** Sí
