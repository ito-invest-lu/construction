pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building...'
                withPythonEnv('python') {
                    sh './build.sh'
                    
                }
            }
        }
        stage('Test') {
            steps {
                echo 'No Automatic Testing So Far...'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying....'
                
            }
        }
    }
}