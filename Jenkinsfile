pipeline {

  agent none

  stages {

    stage('Unit Tests') {
      parallel {

        stage('Python 3.6') {

          agent {
            docker {
              image "python:3.6-alpine"
            }
          }

          steps {
            sh 'python -m pip install pipenv'
            sh 'pipenv --python 3.6 install --dev --deploy'
            sh 'pipenv run pytest'
          }

        } // Python 3.6

        stage('Python 3.7') {

          agent {
            docker {
              image "python:3.7-alpine"
            }
          }

          steps {
            sh 'python -m pip install pipenv'
            sh 'pipenv --python 3.7 install --dev --deploy'
            sh 'pipenv run pytest'
          }

        } // Python 3.7

        stage('Python 3.8') {

          agent {
            docker {
              image "python:3.8-alpine"
            }
          }

          steps {
            sh 'python -m pip install pipenv'
            sh 'pipenv --python 3.8 install --dev --deploy'
            sh 'pipenv run pytest'
          }

        } // Python 3.8

      } // parallel
    } // build & test

  } // stages

} // pipeline
