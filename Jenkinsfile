// Jenkinsfile
node {
  def GITREPO         = "/Users/sumit.prakash/.jenkins/workspace/${env.JOB_NAME}"
  def GITREPOREMOTE   = "https://github.com/sprakash277/databricks-cicd-demo.git"
  def GITHUBCREDID    = "<github-token>"
  def CURRENTRELEASE  = "Master"
  def DBTOKEN         = "sumit-databricks-cicd-secret"
  def DBURL           = "https://e2-demo-field-eng.cloud.databricks.com/"
  def SCRIPTPATH      = "${GITREPO}/Automation/Deployments"
  def NOTEBOOKPATH    = "${GITREPO}/Workspace"
  def LIBRARYPATH     = "${GITREPO}/Libraries"
  def BUILDPATH       = "${GITREPO}/Builds/${env.JOB_NAME}-${env.BUILD_NUMBER}"
  def OUTFILEPATH     = "${BUILDPATH}/Validation/Output"
  def TESTRESULTPATH  = "${BUILDPATH}/Validation/reports/junit"
  def WORKSPACEPATH   = "/Shared/DEV_Sumit_CICD"
  def DBFSPATH        = "dbfs:/FileStore/sumit_data"
  def CLUSTERID       = "1005-013716-rides802"
  def CONDAPATH       = "/Users/sumit.prakash/opt/anaconda3/"
  def CONDAENV        = "base"

  stage('Setup') {
      withCredentials([string(credentialsId: DBTOKEN, variable: 'TOKEN')]) {
        sh """#!/bin/bash
            # Configure Conda environment for deployment & testing
            echo "Running Conda"
            source ${CONDAPATH}/bin/activate ${CONDAENV}

			echo "Running Configure"
            # Configure Databricks CLI for deployment
            echo "${DBURL}
            $TOKEN" | databricks configure --token

            # Configure Databricks Connect for testing
            echo "Running Connect"
            echo "${DBURL}
            $TOKEN
            ${CLUSTERID}
            0
            15001" | databricks-connect configure
           """
      }
  }
  
  stage('Checkout') { // for display purposes
    echo "Pulling ${CURRENTRELEASE} Branch from Github"
    git branch: CURRENTRELEASE, credentialsId: GITHUBCREDID, url: GITREPOREMOTE
  }

  stage('Run Unit Tests') {
    try {
        sh """#!/bin/bash

              # Enable Conda environment for tests
              source ${CONDAPATH}/bin/activate ${CONDAENV}

              # Python tests for libs
              python3 -m pytest --junit-xml=${TESTRESULTPATH}/TEST-libout.xml ${LIBRARYPATH}/python/dbxdemo/test*.py|| true
           """ 
    } catch(err) {
      step([$class: 'JUnitResultArchiver', testResults: '--junit-xml=${TESTRESULTPATH}/TEST-*.xml'])
      if (currentBuild.result == 'UNSTABLE')
        currentBuild.result = 'FAILURE'
      throw err
    }
  }
  stage('Package') {
    sh """#!/bin/bash

          # Enable Conda environment for tests
          source ${CONDAPATH}/bin/activate ${CONDAENV}

          # Package Python library to wheel
          cd ${LIBRARYPATH}/python/dbxdemo
          python3 setup.py sdist bdist_wheel
       """
  }
  stage('Build Artifact') {
    sh """mkdir -p ${BUILDPATH}/Workspace
          mkdir -p ${BUILDPATH}/Libraries/python
          mkdir -p ${BUILDPATH}/Validation/Output
          #Get modified files
          git diff --name-only --diff-filter=AMR HEAD^1 HEAD | xargs -I '{}' rsync -R '{}' ${BUILDPATH}

          # Get packaged libs
          find ${LIBRARYPATH} -name '*.whl' | xargs -I '{}' cp  '{}' ${BUILDPATH}/Libraries/python/

          # Generate artifact
          tar -czvf Builds/latest_build.tar.gz ${BUILDPATH}
       """
    archiveArtifacts artifacts: 'Builds/latest_build.tar.gz'
  }
  stage('Deploy') {
    sh """#!/bin/bash
          # Enable Conda environment for tests
          source ${CONDAPATH}/bin/activate ${CONDAENV}

          # Use Databricks CLI to deploy notebooks
          databricks workspace import_dir ${BUILDPATH}/Workspace ${WORKSPACEPATH}

          dbfs cp -r ${BUILDPATH}/Libraries/python ${DBFSPATH}
       """
    withCredentials([string(credentialsId: DBTOKEN, variable: 'TOKEN')]) {
        sh """#!/bin/bash

              #Get space delimited list of libraries
              LIBS=\$(find ${BUILDPATH}/Libraries/python/ -name '*.whl' | sed 's#.*/##' | paste -sd " ")

              #Script to uninstall, reboot if needed & instsall library
              python3 ${SCRIPTPATH}/installWhlLibrary.py --workspace=${DBURL}\
                        --token=$TOKEN\
                        --clusterid=${CLUSTERID}\
                        --libs=\$LIBS\
                        --dbfspath=${DBFSPATH}
           """
    }
  }
  stage('Run Integration Tests') {
    withCredentials([string(credentialsId: DBTOKEN, variable: 'TOKEN')]) {
        sh """python3 ${SCRIPTPATH}/executenotebook.py --workspace=${DBURL}\
                        --token=$TOKEN\
                        --clusterid=${CLUSTERID}\
                        --localpath=${NOTEBOOKPATH}/VALIDATION\
                        --workspacepath=${WORKSPACEPATH}/VALIDATION\
                        --outfilepath=${OUTFILEPATH}
           """
    }
    sh """sed -i -e 's #ENV# ${OUTFILEPATH} g' ${SCRIPTPATH}/evaluatenotebookruns.py
          python3 -m pytest --junit-xml=${TESTRESULTPATH}/TEST-notebookout.xml ${SCRIPTPATH}/evaluatenotebookruns.py || true
       """
  }
  stage('Report Test Results') {
    sh """find ${OUTFILEPATH} -name '*.json' -exec gzip --verbose {} \\;
          touch ${TESTRESULTPATH}/TEST-*.xml
       """
    junit "**/reports/junit/*.xml"
  }
}