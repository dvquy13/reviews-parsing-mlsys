pipeline {
    agent any
    stages {
        stage('Print Credentials') {
            steps {
                withCredentials([string(credentialsId: 'rpmls-jenkins-robot-token', variable: 'TOKEN')]) {
                    script {
                        // Print the content of the credentials
                        echo "The content of the credential is: ${TOKEN}"
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