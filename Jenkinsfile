pipeline {

  agent none

  stages {

    stage('Unit Tests') {
      parallel {

        stage('Python 2.7') {

          agent {
            docker {
              image "python:2.7-alpine"
            }
          }

          steps {
            sh 'pip install tox'
            sh 'tox -e py27'
          }

        } // Python 2.7

        stage('Python 3.5') {

          agent {
            docker {
              image "python:3.5-alpine"
            }
          }

          steps {
            sh 'pip install tox'
            sh 'tox -e py35'
          }

        } // Python 3.5

        stage('Python 3.6') {

          agent {
            docker {
              image "python:3.6-alpine"
            }
          }

          steps {
            sh 'pip install tox'
            sh 'tox -e py36'
          }

        } // Python 3.6

        stage('Python 3.7') {

          agent {
            docker {
              image "python:3.7-alpine"
            }
          }

          steps {
            sh 'pip install tox'
            sh 'tox -e py37'
          }

        } // Python 3.7

      } // parallel
    } // build & test

  } // stages

} // pipeline

