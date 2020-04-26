#!/bin/sh
# Copyright (c) General Electric Company, 2017.  All rights reserved.

/usr/bin/python ./rt106GenericAdaptorREST.py & sleep 3

if test ${DATASTORE_URI:-undefined} = 'undefined'; then
  datastore='http://datastore:5106'
else
  datastore=${DATASTORE_URI}
fi

if test ${TEST:-off} = 'on'; then
  #py.test --junitxml results.xml testGenericAdaptorAPIs.py
  #sleep 1
  #cp *.xml /rt106/test
  py.test --cov-report html --cov=. testGenericAdaptorAPIs.py
  sleep 1
  mv htmlcov htmlcov_rest
  py.test  --cov-report html --cov=. testGenericAdaptorAMQP.py --broker rabbitmq --dicom $datastore
fi

if test ${MSG_SYSTEM:-amqp} = 'amqp'; then
    /usr/bin/python ./rt106GenericAdaptorAMQP.py --broker rabbitmq --dicom $datastore
elif test ${MSG_SYSTEM} = 'sqs'; then
    /usr/bin/python ./rt106GenericAdaptorSQS.py --log /rt106/logfile --dicom $datastore --heartbeat 10 --workestimate 15
fi
