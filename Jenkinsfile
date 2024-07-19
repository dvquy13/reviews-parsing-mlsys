pipeline {
    agent {
        kubernetes {
            yaml '''
            apiVersion: v1
            kind: Pod
            spec:
              containers:
              - name: jnlp
                image: jenkins/inbound-agent:latest
                args: ['$(JENKINS_SECRET)', '$(JENKINS_NAME)']
              - name: kubectl
                image: bitnami/kubectl:latest
                command:
                - cat
                tty: true
                # Below securityContext is to prevent Jenkins hangs infinitely at `sh` command
                # Ref: https://stackoverflow.com/a/61012758
                securityContext:
                  runAsUser: 0
            '''
            defaultContainer 'kubectl'
        }
    }
    environment {
        GKE_CLUSTER_API_SERVER_URL = credentials('gke-cluster-api-server-url')
    }
    stages {
        stage('Test Kubernetes Connection') {
            steps {
                withKubeCredentials([
                    [credentialsId: 'rpmls-jenkins-robot-token', serverUrl: "${env.GKE_CLUSTER_API_SERVER_URL}"],
                ]) {
                    script {
                        sh 'kubectl get namespaces'
                    }
                }
            }
        }
        stage('Wait for User Input') {
            steps {
                input 'Proceed with deployment?'
            }
        }
        stage('Deploy') {
            steps {
                withKubeCredentials([
                    [credentialsId: 'rpmls-jenkins-robot-token', serverUrl: "${env.GKE_CLUSTER_API_SERVER_URL}"],
                ]) {
                    script {
                        sh '''
                            kubectl annotate \
                                -n default \
                                inferenceservice reviews-parsing-ner-aspects-mlserver \
                                deploy_timestamp=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                                --overwrite
                            latest_revision=$(kubectl get revisions -l serving.knative.dev/service=reviews-parsing-ner-aspects-mlserver-predictor -o jsonpath='{.items[-1:].metadata.name}')
                            kubectl wait --for=condition=ready revision $latest_revision --timeout=300s
                            kubectl wait -n default --selector='!job-name' --for=condition=ready --all po --timeout=300s
                        '''
                    }
                }
            }
        }
    }
}
