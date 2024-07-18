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
                withKubeCredentials([
                    [credentialsId: 'rpmls-jenkins-robot-token', serverUrl: 'https://34.126.107.187'],
                ]) {
                    script {
                        sh 'kubectl get namespaces'
                    }
                }
            }
        }
    }
}