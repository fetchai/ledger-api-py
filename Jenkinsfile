pipeline {

  agent none

  stages {

    stage('Unit Tests') {
      parallel {

        stage('Python2 uTests') {
          agent {
            docker {
              image "python:2.7-alpine"
            }
          }

          stages {
            stage('Setup env python2.7') {
              steps {
                sh 'pip install .[test]'

                sh 'python setup.py install'
              }
            }
            stage('Execute unit tests python2.7') {
              steps {
                sh 'pytest'
              }
            }
          }
        } // Python2 uTests

        stage('Python3 uTests') {
          agent {
            docker {
              image "python:3.6-alpine"
            }
          }

          stages {
            stage('Setup env python3.6') {
              steps {
                sh 'pip install .[test]'

                sh 'python setup.py install'
              }
            }
            stage('Execute unit tests python3.6') {
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

