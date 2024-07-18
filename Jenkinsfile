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
        stage('Print Credentials and Test kubectl') {
            steps {
                withCredentials([string(credentialsId: 'rpmls-jenkins-robot-token', variable: 'TOKEN')]) {
                    script {
                        echo "KUBECONFIG: ${KUBECONFIG}"
                        // Verify kubectl is available
                        sh 'kubectl version --client'
                        ls ~/.kube
                    }
                }
            }
        }
    }
}

// pipeline {
//     agent {
//         kubernetes {
//             yaml '''
//             apiVersion: v1
//             kind: Pod
//             spec:
//               containers:
//               - name: jnlp
//                 image: jenkins/inbound-agent:latest
//                 args: ['$(JENKINS_SECRET)', '$(JENKINS_NAME)']
//               - name: kubectl
//                 image: bitnami/kubectl:latest
//                 command:
//                 - cat
//                 tty: true
//             '''
//             defaultContainer 'kubectl'
//         }
//     }
//     // environment {
//     //     KUBECONFIG = credentials('rpmls-jenkins-robot-token')
//     // }
//     stages {
//         stage('Test Kubernetes Connection') {
//             steps {
//                 withKubeCredentials([
//                     [credentialsId: 'rpmls-jenkins-robot-token', serverUrl: 'https://34.126.107.187'],
//                 ]) {
//                     script {
//                         sh 'echo $KUBECONFIG'
//                         // sh 'kubectl get namespaces'
//                     }
//                 }
//             }
//         }
//     }
// }