pipeline {
    agent {
        docker {
            image 'python:3'
        }
    }

    stages {
        stage('Build') {
            steps {
                echo 'Building..'
                sh 'whoami'
                sh 'ls -al'
                withPythonEnv('python') {
                    sh './build.sh'
                }
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying....'
            }
        }
    }
}