pipeline {
    agent {
        label 'ansible'
    }
    stages {
        stage('Prepare environment') {
            steps {
                checkout scm
                sh "pip install -r req.txt --index-url https://pypi.org/pypi/simple --trusted-host pypi.org --user"
            }
        }
        stage('Start audit proccess') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'stash_creds', usernameVariable: 'stash_login', passwordVariable: 'stash_pass')]){
                    sh "python audit_out.py $stash_login $stash_pass $stash_url"
                }

            }
        }
        stage('Print user blacklist'){
            steps {
                sh "cat audit_result.txt"
            }
        }
    }
    post {
        cleanup {
            node('ansible') {
                cleanWs()
            }
        }
    }
}