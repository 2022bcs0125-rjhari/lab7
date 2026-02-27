pipeline {
    agent any

    environment {
        VENV_DIR = "venv"
        METRICS_FILE = "app/artifacts/metrics.json"
        DOCKER_IMAGE = "2022bcs0125rjhari/wine-infer-jenkins"
        CONTAINER_NAME = "wine-validation-container"
        API_URL = "http://localhost:8000"
    }

    stages {

        // =========================
        // Stage 1: Checkout
        // =========================
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // =========================
        // Stage 2: Setup Python Virtual Environment
        // =========================
        stage('Setup Python Virtual Environment') {
            steps {
                sh '''
                python3 -m venv $VENV_DIR
                . $VENV_DIR/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        // =========================
        // Stage 3: Train Model
        // =========================
        stage('Train Model') {
            steps {
                sh '''
                . $VENV_DIR/bin/activate
                python train.py
                '''
            }
        }

        // =========================
        // Stage 4: Read R2 and MSE
        // =========================
        stage('Read R2 and MSE') {
            steps {
                script {
                    def metrics = readJSON file: "${METRICS_FILE}"
                    env.CUR_R2 = metrics.r2_score.toString()
                    env.CUR_MSE = metrics.mse.toString()

                    echo "--------------------------------"
                    echo "Model Evaluation Metrics"
                    echo "R2 Score : ${env.CUR_R2}"
                    echo "MSE      : ${env.CUR_MSE}"
                    echo "--------------------------------"
                }
            }
        }

        // =========================
        // Stage 5: Compare R2 and MSE
        // =========================
        stage('Compare R2 and MSE') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'BEST_R2', variable: 'BEST_R2'),
                        string(credentialsId: 'BEST_MSE', variable: 'BEST_MSE_VAL')
                    ]) {

                        def curR2 = env.CUR_R2.toFloat()
                        def bestR2 = BEST_R2.toFloat()
                        def curMSE = env.CUR_MSE.toFloat()
                        def bestMSE = BEST_MSE_VAL.toFloat()

                        echo "Comparing model performance..."

                        if (curR2 > bestR2 && curMSE < bestMSE) {
                            env.BUILD_DOCKER = "true"
                            echo "Model improved. Docker build will proceed."
                        } else {
                            env.BUILD_DOCKER = "false"
                            echo "Model NOT improved. Skipping Docker build."
                        }
                    }
                }
            }
        }

        // =========================
        // Stage 6: Build Docker Image
        // =========================
        stage('Build Docker Image') {
            when {
                expression { env.BUILD_DOCKER == "true" }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    docker build -t $DOCKER_USER/wine-infer-jenkins:${BUILD_NUMBER} .
                    docker tag $DOCKER_USER/wine-infer-jenkins:${BUILD_NUMBER} $DOCKER_USER/wine-infer-jenkins:latest
                    '''
                }
            }
        }

        // =========================
        // Stage 7: Push Docker Image
        // =========================
        stage('Push Docker Image') {
            when {
                expression { env.BUILD_DOCKER == "true" }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                    docker push $DOCKER_USER/wine-infer-jenkins:${BUILD_NUMBER}
                    docker push $DOCKER_USER/wine-infer-jenkins:latest
                    '''
                }
            }
        }

        // =========================
        // Stage 8: Pull Latest Image
        // =========================
        stage('Pull Latest Image for Validation') {
            when {
                expression { env.BUILD_DOCKER == "true" }
            }
            steps {
                sh '''
                docker pull $DOCKER_IMAGE:latest
                '''
            }
        }

        // =========================
        // Stage 9: Run Container
        // =========================
        stage('Run Container for Validation') {
            when {
                expression { env.BUILD_DOCKER == "true" }
            }
            steps {
                sh '''
                docker run -d -p 8000:8000 --name $CONTAINER_NAME $DOCKER_IMAGE:latest
                '''
            }
        }

        // =========================
        // Stage 10: Wait for API Readiness
        // =========================
        stage('Wait for API Readiness') {
            when {
                expression { env.BUILD_DOCKER == "true" }
            }
            steps {
                script {
                    timeout(time: 60, unit: 'SECONDS') {
                        waitUntil {
                            def status = sh(
                                script: "curl -s -o /dev/null -w '%{http_code}' $API_URL/docs || true",
                                returnStdout: true
                            ).trim()
                            return (status == "200")
                        }
                    }
                }
            }
        }

        // =========================
        // Stage 11: Valid Inference Test
        // =========================
        stage('Valid Inference Test') {
            when {
                expression { env.BUILD_DOCKER == "true" }
            }
            steps {
                script {
                    def response = sh(
                        script: """
                        curl -s -X POST "$API_URL/predict" \
                        -H "Content-Type: application/json" \
                        -d '{
                            "fixed_acidity":7.4,
                            "volatile_acidity":0.7,
                            "citric_acid":0.0,
                            "residual_sugar":1.9,
                            "chlorides":0.076,
                            "free_sulfur_dioxide":11.0,
                            "total_sulfur_dioxide":34.0,
                            "density":0.9978,
                            "pH":3.51,
                            "sulphates":0.56,
                            "alcohol":9.4
                        }'
                        """,
                        returnStdout: true
                    ).trim()

                    echo "API Response: ${response}"

                    def json = readJSON text: response

                    if (!json.containsKey("wine_quality")) {
                        error("wine_quality field missing!")
                    }
                }
            }
        }

        // =========================
        // Stage 12: Invalid Inference Test
        // =========================
        stage('Invalid Inference Test') {
            when {
                expression { env.BUILD_DOCKER == "true" }
            }
            steps {
                script {
                    def status = sh(
                        script: """
                        curl -s -o /dev/null -w "%{http_code}" \
                        -X POST "$API_URL/predict" \
                        -H "Content-Type: application/json" \
                        -d '{"wrong_input":123}'
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Invalid Request Status: ${status}"

                    if (status == "200") {
                        error("Invalid request should not return 200!")
                    }
                }
            }
        }

        // =========================
        // Stage 13: Stop Container
        // =========================
        stage('Stop Validation Container') {
            when {
                expression { env.BUILD_DOCKER == "true" }
            }
            steps {
                sh '''
                docker stop $CONTAINER_NAME || true
                docker rm $CONTAINER_NAME || true
                '''
            }
        }

    }

    post {
        always {
            archiveArtifacts artifacts: 'app/artifacts/**', fingerprint: true
            sh '''
            docker stop $CONTAINER_NAME || true
            docker rm $CONTAINER_NAME || true
            '''
        }
    }
}
