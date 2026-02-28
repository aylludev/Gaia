#!/bin/bash
# ===========================================================
# fix_nginx_ssl.sh — Reconstruye el config de Nginx con SSL
#
# Uso: sudo bash deploy/fix_nginx_ssl.sh
# ===========================================================

set -eu

# ── CONFIGURACIÓN ──────────────────────────────────────────
DOMAIN="fermagrisas.com"
PROJECT_PATH="/home/amawta/Gaia"
SOCK="/tmp/gaia.sock"
NGINX_CONF="/etc/nginx/sites-available/gaia"
# ───────────────────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_ok()   { echo -e "${GREEN}  ✓${NC} $1"; }
log_info() { echo -e "${YELLOW}  →${NC} $1"; }
log_err()  { echo -e "${RED}  ✗${NC} $1" >&2; }
log_head() { echo -e "\n${BLUE}▶ $1${NC}"; }

if [ "$EUID" -ne 0 ]; then
    log_err "Ejecutá con sudo: sudo bash $0"
    exit 1
fi

# Verificar que los certificados existen
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"

if [ ! -f "$CERT_PATH" ]; then
    log_err "Certificado no encontrado: ${CERT_PATH}"
    log_info "Corré primero: certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
    exit 1
fi

log_head "1. Backup del config actual"
cp "$NGINX_CONF" "${NGINX_CONF}.bak_$(date +%Y%m%d_%H%M%S)"
log_ok "Backup creado"

log_head "2. Escribiendo config de Nginx con SSL"

cat > "$NGINX_CONF" <<EOF
upstream gaia {
    server unix:${SOCK};
}

# Redirigir HTTP → HTTPS
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};
    return 301 https://\$host\$request_uri;
}

# HTTPS
server {
    listen 443 ssl;
    server_name ${DOMAIN} www.${DOMAIN};

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 20M;

    location /static/ {
        alias ${PROJECT_PATH}/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias ${PROJECT_PATH}/media/;
        expires 30d;
    }

    location / {
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        proxy_pass http://gaia;
    }
}
EOF

log_ok "Config escrito en ${NGINX_CONF}"

log_head "3. Verificando sintaxis de Nginx"
nginx -t
log_ok "Sintaxis válida"

log_head "4. Recargando Nginx"
systemctl reload nginx
log_ok "Nginx recargado"

echo ""
echo "  ============================================"
echo -e "   ${GREEN}Nginx SSL configurado correctamente${NC}"
echo "  ============================================"
log_ok "HTTP  → redirige a HTTPS"
log_ok "HTTPS → ${DOMAIN} con Let's Encrypt"
log_ok "Static → ${PROJECT_PATH}/staticfiles/"
log_ok "Media  → ${PROJECT_PATH}/media/"
echo ""
echo "  Verificá: https://${DOMAIN}"
echo ""
