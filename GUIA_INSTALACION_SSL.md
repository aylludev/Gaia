# Guía de Instalación de Certificado SSL/TLS - Proyecto Gaia

**Fecha:** 14 de noviembre de 2025
**Dominios:** agroinsumosmerkosur.com, www.agroinsumosmerkosur.com
**Servidor:** Ubuntu/Debian con Nginx + Gunicorn

---

## 📋 Tabla de Contenidos

1. [Prerequisitos](#prerequisitos)
2. [Instalación con Let's Encrypt (Certbot) - RECOMENDADO](#opción-1-lets-encrypt-certbot---gratuito-y-automático)
3. [Configuración de Nginx](#configuración-de-nginx)
4. [Configuración de Django](#configuración-de-django)
5. [Verificación y Testing](#verificación-y-testing)
6. [Renovación Automática](#renovación-automática)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisitos

### 1. Verificar Configuración Actual

```bash
# Ver sistema operativo
cat /etc/os-release

# Ver IP del servidor
hostname -I

# Verificar Nginx instalado
nginx -v

# Verificar Python y Django
python --version
cd /home/amawta/Documentos/Proyectos/Gaia
source env/bin/activate
python manage.py --version
```

### 2. Verificar DNS

Asegúrate que tus dominios apunten a tu servidor:

```bash
# Verificar DNS
nslookup agroinsumosmerkosur.com
nslookup www.agroinsumosmerkosur.com

# Alternativa con dig
dig agroinsumosmerkosur.com +short
dig www.agroinsumosmerkosur.com +short
```

**Debe mostrar:** `138.197.36.105` (tu IP del servidor)

Si no apunta correctamente, configura los registros DNS:
```
Tipo A:  agroinsumosmerkosur.com     → 138.197.36.105
Tipo A:  www.agroinsumosmerkosur.com → 138.197.36.105
```

### 3. Firewall

```bash
# Verificar firewall
sudo ufw status

# Permitir HTTP y HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Opción 1: Let's Encrypt (Certbot) - GRATUITO Y AUTOMÁTICO

**Recomendado:** Certificado SSL gratuito con renovación automática.

### Paso 1: Instalar Certbot

#### Para Ubuntu 22.04+ / Debian 11+

```bash
# Actualizar sistema
sudo apt update
sudo apt upgrade -y

# Instalar certbot
sudo apt install certbot python3-certbot-nginx -y

# Verificar instalación
certbot --version
```

#### Para Ubuntu 20.04 (si aplica)

```bash
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:certbot/certbot -y
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

### Paso 2: Obtener Certificado SSL

#### Opción A: Certificado Automático (Más Fácil)

Certbot configurará Nginx automáticamente:

```bash
# Generar certificado para ambos dominios
sudo certbot --nginx -d agroinsumosmerkosur.com -d www.agroinsumosmerkosur.com
```

**Durante la instalación te preguntará:**

1. **Email:** Ingresa tu email para notificaciones de renovación
2. **Términos de servicio:** Acepta (A)
3. **¿Compartir email?:** No es necesario (N)
4. **¿Redirigir HTTP a HTTPS?:** Selecciona **2** (Redirect)

#### Opción B: Solo Certificado (Configuración Manual)

Si prefieres configurar Nginx manualmente:

```bash
# Generar solo el certificado
sudo certbot certonly --nginx -d agroinsumosmerkosur.com -d www.agroinsumosmerkosur.com
```

### Paso 3: Verificar Certificados

```bash
# Ver certificados instalados
sudo certbot certificates

# Deberías ver algo como:
# Certificate Name: agroinsumosmerkosur.com
#   Domains: agroinsumosmerkosur.com www.agroinsumosmerkosur.com
#   Expiry Date: 2026-02-12 (válido por 90 días)
#   Certificate Path: /etc/letsencrypt/live/agroinsumosmerkosur.com/fullchain.pem
#   Private Key Path: /etc/letsencrypt/live/agroinsumosmerkosur.com/privkey.pem
```

---

## Configuración de Nginx

### Paso 1: Backup de Configuración Actual

```bash
# Hacer backup
sudo cp /etc/nginx/sites-available/gaia /etc/nginx/sites-available/gaia.backup.$(date +%Y%m%d)
```

### Paso 2: Crear/Actualizar Configuración de Nginx

```bash
# Editar configuración
sudo nano /etc/nginx/sites-available/gaia
```

**Pegar esta configuración completa:**

```nginx
# Redirigir www a no-www
server {
    listen 80;
    listen [::]:80;
    server_name www.agroinsumosmerkosur.com;
    return 301 https://agroinsumosmerkosur.com$request_uri;
}

# Redirigir HTTP a HTTPS (dominio principal)
server {
    listen 80;
    listen [::]:80;
    server_name agroinsumosmerkosur.com;
    return 301 https://$server_name$request_uri;
}

# Configuración HTTPS principal
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name agroinsumosmerkosur.com;

    # SSL/TLS Configuration
    ssl_certificate /etc/letsencrypt/live/agroinsumosmerkosur.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agroinsumosmerkosur.com/privkey.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logs
    access_log /var/log/nginx/gaia_access.log;
    error_log /var/log/nginx/gaia_error.log;

    # Django static files
    location /static/ {
        alias /home/amawta/Documentos/Proyectos/Gaia/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django media files
    location /media/ {
        alias /home/amawta/Documentos/Proyectos/Gaia/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security: Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### Paso 3: Verificar Configuración de Nginx

```bash
# Probar configuración
sudo nginx -t

# Debería mostrar:
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Paso 4: Reiniciar Nginx

```bash
# Reiniciar Nginx
sudo systemctl restart nginx

# Verificar estado
sudo systemctl status nginx

# Ver logs si hay error
sudo tail -f /var/log/nginx/gaia_error.log
```

---

## Configuración de Django

### 1. Actualizar settings.py

El archivo `.env` ya está configurado, pero verifica:

```bash
# Editar .env
nano /home/amawta/Documentos/Proyectos/Gaia/.env
```

**Asegúrate que tenga:**

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=agroinsumosmerkosur.com,www.agroinsumosmerkosur.com,138.197.36.105
```

### 2. Verificar settings.py

Las configuraciones de seguridad ya están implementadas en la rama de seguridad:

```python
# Ya está configurado en Gaia/settings.py
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # ... etc
```

### 3. Recolectar Archivos Estáticos

```bash
cd /home/amawta/Documentos/Proyectos/Gaia
source env/bin/activate
python manage.py collectstatic --noinput
```

### 4. Reiniciar Gunicorn

```bash
# Si usas systemd service
sudo systemctl restart gunicorn

# Verificar estado
sudo systemctl status gunicorn

# Ver logs si hay error
sudo journalctl -u gunicorn -n 50 --no-pager
```

---

## Verificación y Testing

### 1. Verificar SSL en Navegador

Abre tu navegador y visita:
- https://agroinsumosmerkosur.com
- http://agroinsumosmerkosur.com (debería redirigir a HTTPS)
- https://www.agroinsumosmerkosur.com (debería redirigir a sin www)

**Verifica:**
- ✅ Candado verde en la barra de direcciones
- ✅ Certificado válido al hacer clic en el candado
- ✅ Redirecciones funcionando

### 2. Test con OpenSSL

```bash
# Verificar certificado
echo | openssl s_client -servername agroinsumosmerkosur.com -connect agroinsumosmerkosur.com:443 2>/dev/null | openssl x509 -noout -dates

# Debería mostrar:
# notBefore=Nov 14 00:00:00 2025 GMT
# notAfter=Feb 12 23:59:59 2026 GMT
```

### 3. Test con SSL Labs

Visita: https://www.ssllabs.com/ssltest/

Ingresa: `agroinsumosmerkosur.com`

**Objetivo:** Calificación **A** o **A+**

### 4. Verificar Headers de Seguridad

```bash
# Verificar headers HTTPS
curl -I https://agroinsumosmerkosur.com

# Deberías ver:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
```

### 5. Test de Redirección

```bash
# HTTP debería redirigir a HTTPS
curl -I http://agroinsumosmerkosur.com

# Debería mostrar:
# HTTP/1.1 301 Moved Permanently
# Location: https://agroinsumosmerkosur.com/
```

---

## Renovación Automática

Let's Encrypt emite certificados válidos por **90 días**. Certbot configura renovación automática.

### Verificar Timer de Renovación

```bash
# Ver timer de renovación
sudo systemctl list-timers certbot

# Ver status del timer
sudo systemctl status certbot.timer
```

### Probar Renovación Manual

```bash
# Dry run (simular sin renovar)
sudo certbot renew --dry-run

# Si todo está bien, verás:
# Congratulations, all simulated renewals succeeded
```

### Renovación Manual (si es necesario)

```bash
# Renovar todos los certificados próximos a vencer
sudo certbot renew

# Renovar certificado específico
sudo certbot renew --cert-name agroinsumosmerkosur.com

# Después de renovar, reiniciar Nginx
sudo systemctl reload nginx
```

### Configurar Hook Post-Renovación

```bash
# Crear script para reiniciar Nginx después de renovar
sudo nano /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

**Contenido del script:**

```bash
#!/bin/bash
systemctl reload nginx
```

```bash
# Dar permisos de ejecución
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

---

## Troubleshooting

### Problema 1: "Connection Refused" al acceder a HTTPS

**Verificar:**

```bash
# ¿Nginx está corriendo?
sudo systemctl status nginx

# ¿Puerto 443 está abierto?
sudo ufw status
sudo ss -tlnp | grep :443
```

**Solución:**

```bash
sudo ufw allow 443/tcp
sudo systemctl restart nginx
```

### Problema 2: "SSL Certificate Problem"

**Verificar:**

```bash
# Ver certificados
sudo certbot certificates

# Verificar permisos
sudo ls -la /etc/letsencrypt/live/agroinsumosmerkosur.com/
```

**Solución:**

```bash
# Re-generar certificado
sudo certbot delete --cert-name agroinsumosmerkosur.com
sudo certbot --nginx -d agroinsumosmerkosur.com -d www.agroinsumosmerkosur.com
```

### Problema 3: "Too Many Redirects"

**Causa:** Loop de redirección entre Nginx y Django.

**Solución:** Verificar que Django tenga:

```python
# settings.py
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

Y Nginx tenga:

```nginx
proxy_set_header X-Forwarded-Proto $scheme;
```

### Problema 4: Archivos Estáticos No Cargan en HTTPS

**Verificar:**

```bash
# Ver logs de Nginx
sudo tail -f /var/log/nginx/gaia_error.log

# Verificar permisos
ls -la /home/amawta/Documentos/Proyectos/Gaia/staticfiles/
```

**Solución:**

```bash
# Recolectar estáticos
cd /home/amawta/Documentos/Proyectos/Gaia
source env/bin/activate
python manage.py collectstatic --clear --noinput

# Dar permisos
sudo chown -R www-data:www-data /home/amawta/Documentos/Proyectos/Gaia/staticfiles/
sudo chmod -R 755 /home/amawta/Documentos/Proyectos/Gaia/staticfiles/
```

### Problema 5: "Rate Limit Exceeded" de Let's Encrypt

**Causa:** Demasiados intentos de certificado.

**Límites de Let's Encrypt:**
- 5 certificados por dominio por semana
- 50 certificados por registered domain por semana

**Solución:**
- Usar `--dry-run` para probar primero
- Esperar una semana
- Usar certificado staging para testing:

```bash
sudo certbot --staging --nginx -d agroinsumosmerkosur.com -d www.agroinsumosmerkosur.com
```

---

## Checklist Final

### Antes de Poner en Producción

- [ ] DNS apunta a 138.197.36.105
- [ ] Firewall permite puertos 80 y 443
- [ ] Certbot instalado
- [ ] Certificado SSL generado
- [ ] Nginx configurado con SSL
- [ ] Django settings.py con SECURE_SSL_REDIRECT
- [ ] Archivos estáticos recolectados
- [ ] Gunicorn reiniciado
- [ ] HTTPS funciona en navegador
- [ ] HTTP redirige a HTTPS
- [ ] www redirige a sin www
- [ ] Headers de seguridad presentes
- [ ] SSL Labs calificación A/A+
- [ ] Renovación automática configurada
- [ ] Post-renewal hook creado

### Testing

- [ ] https://agroinsumosmerkosur.com carga correctamente
- [ ] Login funciona
- [ ] Archivos estáticos cargan (CSS, JS, imágenes)
- [ ] Panel admin accesible
- [ ] Sin errores en logs de Nginx
- [ ] Sin errores en logs de Gunicorn
- [ ] Sin errores en logs de Django

---

## Comandos Útiles de Referencia

```bash
# ===== CERTBOT =====
sudo certbot certificates                    # Ver certificados
sudo certbot renew --dry-run                 # Probar renovación
sudo certbot renew                           # Renovar ahora
sudo certbot delete --cert-name DOMAIN       # Eliminar certificado

# ===== NGINX =====
sudo nginx -t                                # Verificar configuración
sudo systemctl restart nginx                 # Reiniciar
sudo systemctl status nginx                  # Ver estado
sudo tail -f /var/log/nginx/gaia_error.log  # Ver logs

# ===== GUNICORN =====
sudo systemctl restart gunicorn              # Reiniciar
sudo systemctl status gunicorn               # Ver estado
sudo journalctl -u gunicorn -n 50            # Ver logs

# ===== DJANGO =====
cd /home/amawta/Documentos/Proyectos/Gaia
source env/bin/activate
python manage.py collectstatic --noinput    # Recolectar estáticos
python manage.py check --deploy             # Verificar seguridad

# ===== FIREWALL =====
sudo ufw status                              # Ver estado
sudo ufw allow 80/tcp                        # Permitir HTTP
sudo ufw allow 443/tcp                       # Permitir HTTPS

# ===== VERIFICACIÓN SSL =====
curl -I https://agroinsumosmerkosur.com     # Verificar headers
openssl s_client -connect agroinsumosmerkosur.com:443  # Verificar certificado
```

---

## Recursos Adicionales

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Django Security Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)

---

**Nota:** Esta guía asume que ya tienes Nginx y Gunicorn configurados. Si necesitas ayuda con la configuración inicial de Gunicorn, avísame.

**Tiempo estimado de instalación:** 15-30 minutos

**Validez del certificado:** 90 días (renovación automática cada 60 días)

**Costo:** Gratis con Let's Encrypt
