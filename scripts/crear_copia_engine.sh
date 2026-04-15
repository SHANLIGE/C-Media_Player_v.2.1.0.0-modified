#!/usr/bin/env bash
set -euo pipefail

# Crea una copia local del repositorio actual o lo publica en un repositorio nuevo de GitHub.
# Uso local:
#   ./scripts/crear_copia_engine.sh
# Uso GitHub:
#   GITHUB_TOKEN=*** ./scripts/crear_copia_engine.sh --github TU_USUARIO_O_ORG

ORIGEN_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESTINO_BASE="$(dirname "$ORIGEN_REPO")"
REPO_NOMBRE="C-Media_Player_Engine"

crear_copia_local() {
  local destino_repo="$DESTINO_BASE/$REPO_NOMBRE"

  if [[ -e "$destino_repo" ]]; then
    echo "El destino ya existe: $destino_repo"
    echo "Elimina o renombra esa carpeta y vuelve a ejecutar este script."
    exit 1
  fi

  git clone --no-hardlinks "$ORIGEN_REPO" "$destino_repo"
  echo "Copia local creada en: $destino_repo"
}

publicar_en_github() {
  local owner="$1"

  if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "Debes definir GITHUB_TOKEN para publicar en GitHub."
    exit 1
  fi

  local api_url="https://api.github.com"
  local remote_url="https://x-access-token:${GITHUB_TOKEN}@github.com/${owner}/${REPO_NOMBRE}.git"

  local status_code
  status_code="$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    "${api_url}/repos/${owner}/${REPO_NOMBRE}")"

  if [[ "$status_code" == "404" ]]; then
    local auth_user
    auth_user="$(curl -s \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      "${api_url}/user" | sed -n 's/.*"login"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"

    if [[ "$owner" == "$auth_user" ]]; then
      curl -s -X POST "${api_url}/user/repos" \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        -H "Accept: application/vnd.github+json" \
        -d "{\"name\":\"${REPO_NOMBRE}\",\"private\":true}" > /dev/null
    else
      curl -s -X POST "${api_url}/orgs/${owner}/repos" \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        -H "Accept: application/vnd.github+json" \
        -d "{\"name\":\"${REPO_NOMBRE}\",\"private\":true}" > /dev/null
    fi
    echo "Repositorio creado en GitHub: ${owner}/${REPO_NOMBRE}"
  elif [[ "$status_code" != "200" ]]; then
    echo "No se pudo validar el repositorio en GitHub (HTTP $status_code)."
    exit 1
  else
    echo "El repositorio ya existe en GitHub: ${owner}/${REPO_NOMBRE}"
  fi

  local tmpdir
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT

  git clone --bare "$ORIGEN_REPO" "$tmpdir/repo.git" > /dev/null
  git --git-dir "$tmpdir/repo.git" push --mirror "$remote_url"

  echo "Repositorio publicado en GitHub: https://github.com/${owner}/${REPO_NOMBRE}"
}

if [[ "${1:-}" == "--github" ]]; then
  if [[ -z "${2:-}" ]]; then
    echo "Uso: GITHUB_TOKEN=*** ./scripts/crear_copia_engine.sh --github TU_USUARIO_O_ORG"
    exit 1
  fi
  publicar_en_github "$2"
else
  crear_copia_local
fi
