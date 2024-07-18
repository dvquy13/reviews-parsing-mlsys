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
            '''
            defaultContainer 'kubectl'
        }
    }
    stages {
        stage('Test Kubernetes Connection') {
            steps {
                withCredentials([string(credentialsId: 'rpmls-jenkins-robot-token', variable: 'KUBECONFIG')]) {
                    script {
                        // List Kubernetes namespaces
                        sh 'kubectl get namespaces'
                    }
                }
            }
        }
    }
}