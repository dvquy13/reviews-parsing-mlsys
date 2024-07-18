pipeline {
    agent {
        kubernetes {
            yaml """
            apiVersion: v1
            kind: Pod
            spec:
              containers:
              - name: jnlp
                image: jenkins/inbound-agent
                args: ['$(JENKINS_SECRET)', '$(JENKINS_NAME)']
              - name: kubectl
                image: bitnami/kubectl
                command:
                - cat
                tty: true
            """
            defaultContainer 'kubectl'
            credentialsId 'rpmls-jenkins-robot-token'
        }
    }
    environment {
        KUBECONFIG = credentials('rpmls-jenkins-robot-token')
    }
    stages {
        stage('Test Kubernetes Connection') {
            steps {
                script {
                    // List Kubernetes namespaces
                    sh 'kubectl get namespaces'
                }
            }
        }
    }
}