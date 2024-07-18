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
                - /bin/sh
                tty: true
            '''
            defaultContainer 'kubectl'
        }
    }
    stages {
        stage('Print Environment and Test kubectl') {
            steps {
                container('kubectl') {
                    script {
                        sh 'printenv'
                        sh 'kubectl version'
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
//     stages {
//         stage('Print Credentials and Test kubectl') {
//             steps {
//                 withCredentials([string(credentialsId: 'rpmls-jenkins-robot-token', variable: 'TOKEN')]) {
//                     script {
//                         // Verify kubectl is available
//                         sh 'kubectl version --client'
//                         // Check if ~/.kube/config file exists
//                         sh '''
//                         if [ -f ~/.kube/config ]; then
//                             echo "~/.kube/config exists"
//                         else
//                             echo "~/.kube/config does not exist"
//                         fi
//                         '''
//                         // Print the content of the KUBECONFIG environment variable
//                         sh 'echo $KUBECONFIG'
//                     }
//                 }
//             }
//         }
//     }
// }

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