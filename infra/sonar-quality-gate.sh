#!/usr/bin/env bash
# Crea (o corrige) el Quality Gate PROPIO "MediSur" en SonarQube y lo asigna al proyecto.
# Sonar way (Community) evalúa sobre todo el código NUEVO; este gate evalúa SOLO el
# código TOTAL:  cobertura < 60 %  /  confiabilidad peor que A  /  seguridad peor que A.
#
# Idempotente: se puede volver a correr. SonarQube 10.x agrega por su cuenta condiciones
# "Clean as You Code" (new_*) al crear un gate; este script las elimina.
#
# Uso (el token se pide sin mostrarse; NO se guarda en ningún archivo):
#   cd ~/medisur-pilot && export SONAR_URL=http://localhost:9000 \
#     && read -rs -p "Token: " SONAR_TOKEN && export SONAR_TOKEN && echo \
#     && ./infra/sonar-quality-gate.sh
set -euo pipefail

: "${SONAR_URL:?Define SONAR_URL}"
: "${SONAR_TOKEN:?Define SONAR_TOKEN (token de usuario de SonarQube)}"
command -v jq >/dev/null || { echo "Falta jq"; exit 1; }
GATE="MediSur"
PROJECT="medisur-pilot"

# POST a la API; devuelve el código de curl (falla si HTTP >= 400).
api_post() { curl -fsS -u "${SONAR_TOKEN}:" -X POST "$SONAR_URL/api/$1" "${@:2}" >/dev/null; }
api_get()  { curl -fsS -u "${SONAR_TOKEN}:" -G "$SONAR_URL/api/$1" "${@:2}"; }

echo ">> Gate ${GATE}"
if api_get qualitygates/show --data-urlencode "name=${GATE}" >/dev/null 2>&1; then
  echo "   ya existe"
else
  api_post qualitygates/create --data-urlencode "name=${GATE}"
  echo "   creado"
fi

echo ">> Quitando condiciones sobre código nuevo (new_*) que agrega SonarQube"
api_get qualitygates/show --data-urlencode "name=${GATE}" \
  | jq -r '.conditions[] | select(.metric | startswith("new_")) | "\(.id) \(.metric)"' \
  | while read -r id metrica; do
      api_post qualitygates/delete_condition -d "id=${id}"
      echo "   eliminada: ${metrica}"
    done

echo ">> Condiciones sobre código total"
# op=LT -> falla si el valor es MENOR que el umbral; op=GT -> falla si es MAYOR.
# En los ratings 1=A, 2=B, ...  "peor que A" = mayor que 1.
existentes="$(api_get qualitygates/show --data-urlencode "name=${GATE}" | jq -r '.conditions[].metric')"
for cond in "coverage LT 60" "reliability_rating GT 1" "security_rating GT 1"; do
  read -r metrica op umbral <<<"$cond"
  if grep -qx "$metrica" <<<"$existentes"; then
    echo "   ya existe: ${metrica}"
  else
    api_post qualitygates/create_condition --data-urlencode "gateName=${GATE}" \
      -d "metric=${metrica}" -d "op=${op}" -d "error=${umbral}"
    echo "   creada: ${metrica} ${op} ${umbral}"
  fi
done

echo ">> Proyecto ${PROJECT} y asignación del gate"
if api_get projects/search -d "projects=${PROJECT}" | jq -e '.components | length > 0' >/dev/null; then
  echo "   el proyecto ya existe"
else
  api_post projects/create -d "project=${PROJECT}" --data-urlencode "name=MediSur Pilot"
  echo "   proyecto creado"
fi
api_post qualitygates/select -d "projectKey=${PROJECT}" --data-urlencode "gateName=${GATE}"

echo ">> Estado final del gate"
api_get qualitygates/show --data-urlencode "name=${GATE}" \
  | jq -r '.conditions[] | "   \(.metric) \(.op) \(.error)"'
echo "Listo."
