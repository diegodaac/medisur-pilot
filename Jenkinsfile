// =============================================================================
// Jenkinsfile — Pipeline declarativo de MediSur (Multibranch Pipeline)
//
//   CI (todas las ramas y PR): checkout -> [Hadolint | gitleaks] -> pruebas -> SonarQube
//                              -> Quality Gate -> docker build -> Trivy -> push a GHCR
//   CD (SOLO rama main):       secretos/manifiestos -> set image -> rollout status
//                              -> prueba de humo -> (si falla) rollout undo
//
// Si cualquier etapa de CI falla, NADA llega a Kubernetes.
//
// Credenciales esperadas en Jenkins (Manage Jenkins > Credentials). Ninguna vive
// en el repositorio:
//   ghcr-pat         Username with password   usuario de GitHub + PAT (write:packages)
//   kubeconfig-k8s   Secret file              kubeconfig de MicroK8s (IP privada de VM-K8S)
//   medisur-api-key  Secret text              valor de APP_API_KEY para el Secret de K8s
// Y en Manage Jenkins > System / Tools:
//   servidor SonarQube llamado 'sonarqube'    (con su token; y en SonarQube un webhook de vuelta a Jenkins)
//   herramienta SonarQube Scanner llamada 'sonar-scanner'
// =============================================================================

pipeline {

  // Se ejecuta en el propio nodo de VM-TOOLS (Jenkins nativo con acceso a Docker).
  agent any

  options {
    skipDefaultCheckout(true)                       // el checkout lo hacemos explícito en la etapa 1
    disableConcurrentBuilds()                       // un build a la vez por rama: evita carreras en el despliegue
    timestamps()                                    // marca de hora en cada línea del log
    timeout(time: 30, unit: 'MINUTES')              // tope global por si algo se cuelga
    buildDiscarder(logRotator(numToKeepStr: '20'))  // conserva solo los últimos 20 builds
  }

  environment {
    // --- AJUSTAR antes del primer build (no son secretos) ---
    GHCR_OWNER = 'diegodaac'                        // usuario de GitHub, en minúsculas
    K8S_HOST   = '172.16.0.4'                       // IP privada de VM-K8S (misma VNet que VM-TOOLS)
    // --------------------------------------------------------
    IMAGE_REPO = "ghcr.io/${GHCR_OWNER}/medisur-pilot"
    NODE_PORT  = '30080'                            // nodePort del Service (k8s/service.yaml)
    PY_IMAGE   = 'python:3.12-slim'                 // imagen donde corren las pruebas (Python 3.12 igual que producción)
    K8S_NS     = 'medisur'
    DEPLOYMENT = 'medisur-api'
    // Herramientas de seguridad (extras), en contenedores con versión fijada: nada que instalar en la VM.
    HADOLINT_IMAGE = 'hadolint/hadolint:v2.15.1'
    GITLEAKS_IMAGE = 'zricethezav/gitleaks:v8.30.1'
    TRIVY_IMAGE    = 'aquasec/trivy:0.76.2'
  }

  stages {

    // ---- 1. Checkout y registro del SHA corto --------------------------------
    stage('Checkout') {
      steps {
        checkout scm
        script {
          // SHA corto de 7 caracteres, la base de las etiquetas de la imagen.
          env.GIT_SHA_SHORT = sh(returnStdout: true, script: 'git rev-parse --short=7 HEAD').trim()
          env.APP_VERSION   = readFile('VERSION').trim()
          env.BUILD_DATE    = sh(returnStdout: true, script: 'date -u +%Y-%m-%dT%H:%M:%SZ').trim()
          // Etiquetas: <VERSION>-<sha> y <sha>. NUNCA 'latest'.
          env.TAG_FULL = "${env.APP_VERSION}-${env.GIT_SHA_SHORT}"
          echo "Rama=${env.BRANCH_NAME} versión=${env.APP_VERSION} sha=${env.GIT_SHA_SHORT} etiqueta=${env.TAG_FULL}"
        }
      }
    }

    // ---- Extra: seguridad estática, en paralelo (no dependen una de otra) ----
    stage('Seguridad estática') {
      parallel {
        // Hadolint revisa el Dockerfile contra buenas prácticas. Falla solo con
        // errores; las advertencias se muestran en el log sin detener el build.
        stage('Hadolint (Dockerfile)') {
          steps {
            sh 'docker run --rm -i "$HADOLINT_IMAGE" hadolint --failure-threshold error - < Dockerfile'
          }
        }
        // gitleaks busca secretos en TODO el historial de git (no solo en el commit
        // actual). Si encuentra uno, el build se detiene. --redact evita que el
        // valor aparezca en el log. Los falsos positivos revisados están en .gitleaksignore.
        stage('gitleaks (secretos)') {
          steps {
            sh 'docker run --rm -v "$WORKSPACE:/repo:ro" "$GITLEAKS_IMAGE" git --redact --no-banner --exit-code 1 /repo'
          }
        }
      }
    }

    // ---- 2 y 3. Dependencias fijadas en un venv + pruebas con cobertura -----
    // Corre dentro de un contenedor python:3.12-slim (la VM trae Python 3.10).
    // El workspace se monta en la MISMA ruta para que coverage.xml tenga rutas
    // que SonarQube pueda resolver. Importante: sin --cov-fail-under; la cobertura
    // la bloquea SonarQube en la etapa siguiente (Quality Gate propio).
    stage('Pruebas y cobertura') {
      steps {
        sh '''
          docker run --rm \
            --user "$(id -u):$(id -g)" -e HOME=/tmp \
            -v "$WORKSPACE:$WORKSPACE" -w "$WORKSPACE" \
            "$PY_IMAGE" sh -c '
              python -m venv .venv &&
              . .venv/bin/activate &&
              pip install --no-cache-dir -r requirements-dev.txt &&
              pytest --cov=app --cov-report=xml --cov-report=term-missing --junitxml=junit.xml
            '
        '''
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'junit.xml'   // resultados visibles en Jenkins
        }
      }
    }

    // ---- 4. Análisis estático con SonarScanner (código + coverage.xml) ------
    stage('Análisis SonarQube') {
      steps {
        script {
          def scannerHome = tool 'sonar-scanner'
          // withSonarQubeEnv inyecta la URL y el token del servidor 'sonarqube'.
          withSonarQubeEnv('sonarqube') {
            sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectVersion=${env.APP_VERSION}"
          }
        }
      }
    }

    // ---- 5. Quality Gate: si no pasa, el pipeline se aborta (build rojo) -----
    // Requiere el webhook de SonarQube -> http://172.16.0.5:8080/sonarqube-webhook/
    // (IP privada de VM-TOOLS; "localhost" no sirve porque SonarQube corre en un contenedor).
    stage('Quality Gate') {
      steps {
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    // ---- 6. Construcción de la imagen con metadatos de versión --------------
    stage('Docker build') {
      steps {
        sh '''
          docker build --pull \
            --build-arg APP_VERSION="$APP_VERSION" \
            --build-arg GIT_SHA="$GIT_SHA_SHORT" \
            --build-arg BUILD_DATE="$BUILD_DATE" \
            -t "$IMAGE_REPO:$TAG_FULL" \
            -t "$IMAGE_REPO:$GIT_SHA_SHORT" \
            .
        '''
      }
    }

    // ---- Extra: escaneo de vulnerabilidades de la imagen ANTES de publicarla ----
    // Trivy revisa paquetes del sistema y librerías de Python. Bloquea solo las
    // CRITICAL que ya tienen parche (--ignore-unfixed): si existe arreglo, no se
    // publica la imagen. Las HIGH se reportan sin bloquear, para revisarlas.
    // La base de datos de vulnerabilidades se guarda en el volumen trivy-cache.
    stage('Escaneo de imagen (Trivy)') {
      steps {
        sh '''
          TRIVY="docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache $TRIVY_IMAGE"
          $TRIVY image --quiet --no-progress --ignore-unfixed --severity HIGH --exit-code 0 "$IMAGE_REPO:$TAG_FULL"
          $TRIVY image --quiet --no-progress --ignore-unfixed --severity CRITICAL --exit-code 1 "$IMAGE_REPO:$TAG_FULL"
        '''
      }
    }

    // ---- 7. Publicación en GHCR con las dos etiquetas -----------------------
    stage('Push a GHCR') {
      steps {
        // Comillas simples: Groovy NO interpola el secreto, lo expande el shell
        // y Jenkins lo enmascara en el log.
        withCredentials([usernamePassword(credentialsId: 'ghcr-pat',
                                          usernameVariable: 'GHCR_USER',
                                          passwordVariable: 'GHCR_TOKEN')]) {
          sh '''
            echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
            docker push "$IMAGE_REPO:$TAG_FULL"
            docker push "$IMAGE_REPO:$GIT_SHA_SHORT"
            docker logout ghcr.io
          '''
        }
      }
    }

    // =========================== CD: SOLO en main ===========================

    // ---- 8a. Namespace, ConfigMap, Service y Secrets (los Secrets se generan aquí) ----
    stage('Preparar clúster') {
      when { branch 'main' }
      steps {
        withCredentials([file(credentialsId: 'kubeconfig-k8s', variable: 'KUBECONFIG'),
                         usernamePassword(credentialsId: 'ghcr-pat',
                                          usernameVariable: 'GHCR_USER',
                                          passwordVariable: 'GHCR_TOKEN'),
                         string(credentialsId: 'medisur-api-key', variable: 'API_KEY')]) {
          sh '''
            kubectl apply -f k8s/namespace.yaml
            kubectl apply -f k8s/configmap.yaml
            kubectl apply -f k8s/service.yaml

            # Secret de la aplicación: se genera al vuelo, nunca vive en el repo.
            kubectl -n "$K8S_NS" create secret generic medisur-api-secret \
              --from-literal=APP_API_KEY="$API_KEY" \
              --dry-run=client -o yaml | kubectl apply -f -

            # imagePullSecret por si el paquete de GHCR es privado.
            kubectl -n "$K8S_NS" create secret docker-registry ghcr-pull \
              --docker-server=ghcr.io \
              --docker-username="$GHCR_USER" \
              --docker-password="$GHCR_TOKEN" \
              --dry-run=client -o yaml | kubectl apply -f -
          '''
        }
      }
    }

    // ---- 8b y 9. Despliegue: set image + espera del rollout -----------------
    stage('Desplegar a Kubernetes') {
      when { branch 'main' }
      steps {
        withCredentials([file(credentialsId: 'kubeconfig-k8s', variable: 'KUBECONFIG')]) {
          script {
            // A partir de aquí, si algo falla, el bloque post{} hace rollout undo.
            env.DEPLOY_STARTED = 'true'
          }
          sh '''
            # Aplica el Deployment declarativo (probes, recursos, replicas: 2, RollingUpdate)
            # con la imagen ya sustituida; así el manifiesto del repo es la fuente de verdad
            # y la primera vez el Deployment se crea con una imagen real.
            sed "s|__IMAGE__|$IMAGE_REPO:$TAG_FULL|" k8s/deployment.yaml | kubectl apply -f -

            # Cambio explícito de imagen (idempotente): es la orden que dispara/confirma
            # la actualización gradual.
            kubectl -n "$K8S_NS" set image deployment/"$DEPLOYMENT" api="$IMAGE_REPO:$TAG_FULL"
            kubectl -n "$K8S_NS" annotate deployment/"$DEPLOYMENT" \
              kubernetes.io/change-cause="build ${BUILD_NUMBER}: ${TAG_FULL}" --overwrite

            # Espera a que todas las réplicas nuevas estén listas (falla si pasan 120 s).
            kubectl -n "$K8S_NS" rollout status deployment/"$DEPLOYMENT" --timeout=120s
          '''
        }
      }
    }

    // ---- 10. Prueba de humo: /health responde y /version trae el SHA recién construido ----
    stage('Prueba de humo') {
      when { branch 'main' }
      steps {
        sh '''
          URL="http://$K8S_HOST:$NODE_PORT"

          # Hasta 30 s de reintentos por si el Service aún no enruta.
          for i in $(seq 1 15); do
            curl -fsS "$URL/health" > /dev/null && break
            sleep 2
          done

          curl -fsS "$URL/health"
          echo
          BODY=$(curl -fsS "$URL/version")
          echo "/version -> $BODY"

          # El commit que responde el clúster debe ser el que acabamos de construir.
          [ "$(echo "$BODY" | jq -r .commit)" = "$GIT_SHA_SHORT" ] \
            || { echo "El SHA desplegado no coincide con $GIT_SHA_SHORT"; exit 1; }
        '''
      }
    }
  }

  post {
    // ---- 11. Reversión automática: solo si el fallo ocurrió ya en la fase de despliegue ----
    failure {
      script {
        if (env.DEPLOY_STARTED == 'true') {
          echo 'Falló el despliegue: revirtiendo a la revisión anterior (rollout undo).'
          withCredentials([file(credentialsId: 'kubeconfig-k8s', variable: 'KUBECONFIG')]) {
            // Si es el primer despliegue no hay revisión previa; no ocultamos el fallo original.
            sh '''
              kubectl -n "$K8S_NS" rollout undo deployment/"$DEPLOYMENT" || echo "Sin revisión previa a la cual volver"
              kubectl -n "$K8S_NS" rollout status deployment/"$DEPLOYMENT" --timeout=120s || true
            '''
          }
        }
      }
    }
    always {
      // Libera disco en VM-TOOLS (64 GB): borra imágenes viejas sin uso.
      sh 'docker image prune -af --filter "until=72h" || true'
    }
  }
}
