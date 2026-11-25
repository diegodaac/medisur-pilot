#!/usr/bin/env bash
# Crea el Quality Gate PROPIO "MediSur" en SonarQube y lo asigna al proyecto.
# Sonar way (Community) evalúa sobre todo el código NUEVO; este gate evalúa el
# código TOTAL:  cobertura < 60 %  /  confiabilidad peor que A  /  seguridad peor que A.
#
# Uso (el token se pasa por entorno; NO se guarda en ningún archivo):
#   export SONAR_URL=http://localhost:9000
#   read -rs SONAR_TOKEN && export SONAR_TOKEN
#   ./infra/sonar-quality-gate.sh
set -euo pipefail

: "${SONAR_URL:?Define SONAR_URL}"
: "${SONAR_TOKEN:?Define SONAR_TOKEN (token de usuario de SonarQube)}"
GATE="MediSur"
PROJECT="medisur-pilot"

api() { curl -fsS -u "${SONAR_TOKEN}:" -X POST "$SONAR_URL/api/$1" "${@:2}"; echo; }

echo ">> Creando gate ${GATE}"
api qualitygates/create --data-urlencode "name=${GATE}"

echo ">> Condiciones sobre código total"
# op=LT -> falla si el valor es MENOR que el umbral; op=GT -> falla si es MAYOR.
# En los ratings 1=A, 2=B, ...  "peor que A" = mayor que 1.
api qualitygates/create_condition --data-urlencode "gateName=${GATE}" -d metric=coverage            -d op=LT -d error=60
api qualitygates/create_condition --data-urlencode "gateName=${GATE}" -d metric=reliability_rating  -d op=GT -d error=1
api qualitygates/create_condition --data-urlencode "gateName=${GATE}" -d metric=security_rating     -d op=GT -d error=1

echo ">> Creando el proyecto (si no existe) y asignando el gate"
api projects/create -d "project=${PROJECT}" --data-urlencode "name=MediSur Pilot" || true
api qualitygates/select -d "projectKey=${PROJECT}" --data-urlencode "gateName=${GATE}"

echo "Listo."
