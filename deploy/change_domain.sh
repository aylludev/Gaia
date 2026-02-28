#!/bin/bash
# ===========================================================
# change_domain.sh — Cambia el dominio del ERP Gaia
#
# Uso: sudo bash deploy/change_domain.sh
# Ejecutar en el droplet como root o con sudo
# ===========================================================

set -eu

# ── CONFIGURACIÓN ──────────────────────────────────────────
# Ajustá estas variables antes de ejecutar el script

OLD_DOMAIN="agroinsumosmerkosur.com"
NEW_DOMAIN="fermagrisas.com"

PROJECT_PATH="/home/amawta/Gaia"      # Ruta absoluta del proyecto en el droplet
NGINX_CONF_NAME="gaia"                 # Nombre del archivo en /etc/nginx/sites-available/
SUPERVISOR_PROGRAM="gaia"              # Nombre del [program:xxx] en /etc/supervisor/conf.d/
CERTBOT_EMAIL=""                       # Email para Let's Encrypt (requerido si no hay cert previo)

# ───────────────────────────────────────────────────────────

NGINX_CONF="/etc/nginx/sites-available/${NGINX_CONF_NAME}"
ENV_FILE="${PROJECT_PATH}/.env"
SETTINGS_FILE="${PROJECT_PATH}/Gaia/settings.py"
CERTBOT_SKIP=false

# Colores
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

log_ok()   { echo -e "${GREEN}  ✓${NC} $1"; }
log_info() { echo -e "${YELLOW}  →${NC} $1"; }
log_warn() { echo -e "${YELLOW}  !${NC} $1"; }
log_err()  { echo -e "${RED}  ✗${NC} $1" >&2; }
log_head() { echo -e "\n${BLUE}▶ $1${NC}"; }

# ── VALIDACIONES PREVIAS ───────────────────────────────────

if [ "$EUID" -ne 0 ]; then
    log_err "Ejecutá este script con sudo: sudo bash $0"
    exit 1
fi

if [ ! -d "$PROJECT_PATH" ]; then
    log_err "Proyecto no encontrado en: ${PROJECT_PATH}"
    log_info "Editá la variable PROJECT_PATH al inicio del script"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    log_err ".env no encontrado en: ${ENV_FILE}"
    exit 1
fi

if [ ! -f "$SETTINGS_FILE" ]; then
    log_err "settings.py no encontrado en: ${SETTINGS_FILE}"
    exit 1
fi

echo ""
echo "  ============================================"
echo "   Gaia — Cambio de dominio"
echo "   ${OLD_DOMAIN}  →  ${NEW_DOMAIN}"
echo "  ============================================"

# ── 1. BACKUP ──────────────────────────────────────────────
log_head "1. Creando backups"

BACKUP_DIR="${PROJECT_PATH}/deploy/backups/domain_change_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp "$ENV_FILE" "${BACKUP_DIR}/.env.bak"
log_ok ".env  →  ${BACKUP_DIR}/.env.bak"

cp "$SETTINGS_FILE" "${BACKUP_DIR}/settings.py.bak"
log_ok "settings.py  →  ${BACKUP_DIR}/settings.py.bak"

if [ -f "$NGINX_CONF" ]; then
    cp "$NGINX_CONF" "${BACKUP_DIR}/nginx.conf.bak"
    log_ok "nginx config  →  ${BACKUP_DIR}/nginx.conf.bak"
fi

# ── 2. .env — DJANGO_ALLOWED_HOSTS ────────────────────────
log_head "2. Actualizando .env"

if grep -q "^DJANGO_ALLOWED_HOSTS=" "$ENV_FILE"; then
    sed -i "s|^DJANGO_ALLOWED_HOSTS=.*|DJANGO_ALLOWED_HOSTS=${NEW_DOMAIN},www.${NEW_DOMAIN},localhost|" "$ENV_FILE"
    log_ok "DJANGO_ALLOWED_HOSTS actualizado"
else
    echo "DJANGO_ALLOWED_HOSTS=${NEW_DOMAIN},www.${NEW_DOMAIN},localhost" >> "$ENV_FILE"
    log_warn "DJANGO_ALLOWED_HOSTS no existía en .env — fue agregado"
fi

# ── 3. settings.py — CSRF_TRUSTED_ORIGINS ─────────────────
log_head "3. Actualizando settings.py"

python3 - <<PYEOF
import sys

settings_path = "${SETTINGS_FILE}"

with open(settings_path, "r") as f:
    content = f.read()

old_domain = "${OLD_DOMAIN}"
new_domain = "${NEW_DOMAIN}"

if old_domain not in content:
    print(f"  ADVERTENCIA: '{old_domain}' no encontrado en settings.py")
    print(f"  Verificá CSRF_TRUSTED_ORIGINS manualmente en {settings_path}")
    sys.exit(0)

updated = content.replace(
    f"https://{old_domain}", f"https://{new_domain}"
).replace(
    f"https://www.{old_domain}", f"https://www.{new_domain}"
)

with open(settings_path, "w") as f:
    f.write(updated)

print(f"  CSRF_TRUSTED_ORIGINS: {old_domain} → {new_domain}")
PYEOF

log_ok "settings.py actualizado"

# ── 4. Nginx ───────────────────────────────────────────────
log_head "4. Actualizando configuración de Nginx"

if [ ! -f "$NGINX_CONF" ]; then
    log_err "Config de Nginx no encontrado: ${NGINX_CONF}"
    log_info "Archivos en /etc/nginx/sites-available/:"
    ls /etc/nginx/sites-available/ || true
    log_info "Editá la variable NGINX_CONF_NAME al inicio del script"
    exit 1
fi

sed -i "s/${OLD_DOMAIN}/${NEW_DOMAIN}/g" "$NGINX_CONF"
log_ok "server_name actualizado en ${NGINX_CONF}"

log_info "Verificando sintaxis de Nginx..."
nginx -t
log_ok "Sintaxis de Nginx válida"

# ── 5. SSL con Certbot ─────────────────────────────────────
log_head "5. Certificado SSL (Let's Encrypt)"

if ! command -v certbot &> /dev/null; then
    log_warn "certbot no está instalado — saltando SSL"
    log_info "Para instalarlo:"
    log_info "  snap install --classic certbot"
    log_info "  ln -s /snap/bin/certbot /usr/bin/certbot"
    log_info "Luego ejecutá manualmente:"
    log_info "  certbot --nginx -d ${NEW_DOMAIN} -d www.${NEW_DOMAIN}"
    CERTBOT_SKIP=true
else
    CERTBOT_ARGS=(
        --nginx
        -d "${NEW_DOMAIN}"
        -d "www.${NEW_DOMAIN}"
        --non-interactive
        --agree-tos
        --redirect
    )

    if [ -n "$CERTBOT_EMAIL" ]; then
        CERTBOT_ARGS+=(--email "$CERTBOT_EMAIL")
    else
        CERTBOT_ARGS+=(--register-unsafely-without-email)
        log_warn "CERTBOT_EMAIL no configurado — usando --register-unsafely-without-email"
    fi

    log_info "Solicitando certificado para ${NEW_DOMAIN} y www.${NEW_DOMAIN}..."
    certbot "${CERTBOT_ARGS[@]}"
    log_ok "Certificado SSL obtenido y configurado"
fi

# ── 6. Reload Nginx ────────────────────────────────────────
log_head "6. Recargando Nginx"

systemctl reload nginx
log_ok "Nginx recargado"

# ── 7. Reiniciar Gaia via Supervisor ──────────────────────
log_head "7. Reiniciando Gaia"

# Asegurar que los scripts de deploy sean ejecutables
find "${PROJECT_PATH}/deploy" -name "*.sh" -exec chmod +x {} \;
log_ok "Permisos de ejecución aplicados a deploy/*.sh"

if supervisorctl status "${SUPERVISOR_PROGRAM}" &> /dev/null 2>&1; then
    supervisorctl restart "${SUPERVISOR_PROGRAM}"
    log_ok "Gaia (supervisor:${SUPERVISOR_PROGRAM}) reiniciado"
else
    log_err "Programa supervisor '${SUPERVISOR_PROGRAM}' no encontrado"
    log_info "Programas disponibles:"
    supervisorctl status || true
    log_info "Editá la variable SUPERVISOR_PROGRAM al inicio del script"
    exit 1
fi

# ── RESUMEN ────────────────────────────────────────────────
echo ""
echo "  ============================================"
echo -e "   ${GREEN}Cambio de dominio completado exitosamente${NC}"
echo "  ============================================"
log_ok ".env — DJANGO_ALLOWED_HOSTS: ${NEW_DOMAIN}"
log_ok "settings.py — CSRF_TRUSTED_ORIGINS: ${NEW_DOMAIN}"
log_ok "Nginx — server_name: ${NEW_DOMAIN}"

if [ "$CERTBOT_SKIP" = "true" ]; then
    log_warn "SSL — pendiente, ejecutar certbot manualmente"
else
    log_ok "SSL — certificado Let's Encrypt activo"
fi

log_ok "Gunicorn — reiniciado vía supervisor"
echo ""
log_info "Backups en: ${BACKUP_DIR}"
echo ""
echo "  Verificá que el sitio funcione en:"
echo "    https://${NEW_DOMAIN}"
echo "    https://www.${NEW_DOMAIN}"
echo ""
