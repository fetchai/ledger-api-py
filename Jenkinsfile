pipeline {

  agent none

  stages {

    stage('Unit Tests') {
      parallel {

        stage('Python2 uTests') {
          agent {
            docker {
              image "2.7-alpine"
            }
          }

          stages {
            stage('Setup environment') {
              steps {
                sh 'pip install .[test]'
              }
              steps {
                sh 'python setup.py'
              }
            }
            stage('Execute unit tests') {
              steps {
                sh 'pytest'
              }
            }
          }
        } // Python2 uTests

        stage('Python3 uTests') {
          agent {
            docker {
              image "3.6-alpine"
            }
          }

          stages {
            stage('Setup environment') {
              steps {
                sh 'pip3 install .[test]'
              }
              steps {
                sh 'python setup.py'
              }
            }
            stage('Execute unit tests') {
              steps {
                sh 'pytest'
              }
            }
          }
        } // Python3 uTests

      } // parallel
    } // build & test

  } // stages

} // pipeline

