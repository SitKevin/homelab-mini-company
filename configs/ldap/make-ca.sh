#!/usr/bin/env bash
# db01 (as root): internal CA + server certificate for slapd.
# Let's Encrypt can't be used here: .internal is not a public domain.
set -euo pipefail
mkdir -p /etc/ldap/tls && cd /etc/ldap/tls

# 1. Internal CA (10 years). ca.key must never leave db01.
openssl req -x509 -newkey rsa:4096 -nodes -days 3650 \
  -keyout ca.key -out ca.crt -subj "/CN=Homelab Internal CA"

# 2. Server key + CSR, signed by the CA. SAN must match the name clients use.
openssl req -newkey rsa:2048 -nodes -keyout ldap.key -out ldap.csr \
  -subj "/CN=db01.homelab.internal"
echo "subjectAltName=DNS:db01.homelab.internal,IP:192.168.196.12" > san.ext
openssl x509 -req -in ldap.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 825 -out ldap.crt -extfile san.ext

# 3. Permissions: slapd runs as "openldap"
chown root:openldap ldap.key && chmod 640 ldap.key
chmod 600 ca.key

# 4. Trust the CA locally (repeat on every client, e.g. web01, with ca.crt only)
cp ca.crt /usr/local/share/ca-certificates/homelab-ca.crt
update-ca-certificates
