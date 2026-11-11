#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cert_dir="${project_dir}/certs"
mkdir -p "${cert_dir}"

ca_key="${cert_dir}/smca-local-ca.key"
ca_cert="${cert_dir}/smca-local-ca.crt"
server_key="${cert_dir}/smca-control.key"
server_cert="${cert_dir}/smca-control.crt"
server_csr="${cert_dir}/smca-control.csr"
server_ext="${cert_dir}/smca-control.ext"
ca_serial="${cert_dir}/smca-local-ca.srl"

# Une autorité locale dédiée est plus fiable qu'un certificat serveur
# auto-signé importé directement comme racine dans Windows.
openssl req -x509 -newkey rsa:3072 -sha256 -nodes \
  -days 3650 \
  -keyout "${ca_key}" \
  -out "${ca_cert}" \
  -subj "/C=MA/O=SMCA Mini-Projet/CN=SMCA Control Local CA" \
  -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -addext "subjectKeyIdentifier=hash"

openssl req -new -newkey rsa:3072 -sha256 -nodes \
  -keyout "${server_key}" \
  -out "${server_csr}" \
  -subj "/C=MA/O=SMCA Mini-Projet/CN=smca-control.test"

printf '%s\n' \
  "subjectAltName=DNS:smca-control.test" \
  "basicConstraints=critical,CA:FALSE" \
  "keyUsage=critical,digitalSignature,keyEncipherment" \
  "extendedKeyUsage=serverAuth" \
  "authorityKeyIdentifier=keyid,issuer" \
  "subjectKeyIdentifier=hash" > "${server_ext}"

openssl x509 -req -sha256 \
  -in "${server_csr}" \
  -CA "${ca_cert}" \
  -CAkey "${ca_key}" \
  -CAcreateserial \
  -CAserial "${ca_serial}" \
  -days 825 \
  -out "${server_cert}" \
  -extfile "${server_ext}"

rm -f "${server_csr}" "${server_ext}" "${ca_serial}"

chmod 600 "${ca_key}" "${server_key}"
chmod 644 "${ca_cert}" "${server_cert}"

echo "Autorité locale à importer dans Windows : ${ca_cert}"
echo "Certificat serveur créé : ${server_cert}"
echo "Clé privée serveur créée : ${server_key}"
echo "Copiez uniquement smca-local-ca.crt vers Windows."
echo "Ne copiez et ne partagez jamais les fichiers .key."

