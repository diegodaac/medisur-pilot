#!/usr/bin/env bash
# Prepara la rama de DEMO que hace fallar el Quality Gate por cobertura.
# Agrega un módulo grande sin pruebas: la cobertura total cae por debajo de 60 %,
# Sonar rechaza el build y NO se construye imagen (paso 4 de la demo).
#
# Uso (desde la raíz del repo, con la rama main limpia y actualizada):
#   ./infra/demo-sonar-falla.sh
#   git push -u origin demo/sonar-falla     # y abrir el PR en GitHub
set -euo pipefail

RAMA="demo/sonar-falla"
git rev-parse --is-inside-work-tree >/dev/null
git checkout -b "$RAMA"

{
  echo '"""Módulo de demostración SIN pruebas: existe solo para bajar la cobertura."""'
  for i in $(seq 1 60); do
    cat <<PY


def calcular_dosis_${i}(peso: float, factor: float) -> float:
    base = peso * factor
    if base > ${i}:
        return base - ${i}
    return base + ${i}
PY
  done
} > app/calculos_legacy.py

git add app/calculos_legacy.py
git commit -m "demo: módulo sin pruebas para que el Quality Gate falle por cobertura"
echo "Rama ${RAMA} lista. Súbela y abre el PR."
echo "Para corregir en la demo:  git rm app/calculos_legacy.py && git commit -m 'fix: elimina módulo sin pruebas' && git push"
