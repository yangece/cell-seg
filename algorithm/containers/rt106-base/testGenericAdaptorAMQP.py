# Copyright (c) General Electric Company, 2017.  All rights reserved.

# Prototype code for testing rt106GenericAdaptorAMQP.py

import unittest,json,requests,uuid,os,time,logging
import sys
print(sys.argv)
idx = sys.argv.index('testGenericAdaptorAMQP.py')
sys.argv = sys.argv[idx:]
if '--dicom' in sys.argv:
    idxd = sys.argv.index('--dicom')
    dataserver = sys.argv[idxd+1]

if '--broker' in sys.argv:
    brokeridx = sys.argv.index('--broker')

from rt106GenericAdaptorAMQP import *

patientList = ['AGA_260_3','pat001','pat002','pat003','pat004','pat005','pat006']
studyList = ['studyA']
seriesList = ['cardiac_Bias_600_Cardiac_3T_series6_PURE']
imageName = 'i851332.MRDC.1'
slideList = ['AGA_260_3']
regionList = ['021']
channelList = ['DAPI']
# we assume the data used for testing uploading functions are in /rt106/test/upload

class TestGenericAMQP(unittest.TestCase):

    def setUp(self):    # NOSONAR
        self.datastore = dataStore(dataserver,str(uuid.uuid4()))
        self.create_test_directory()

    def create_test_directory(self):
        file_path = '/rt106/test/radiology'
        if not os.path.exists(file_path) :
            os.makedirs(file_path)
        #else:
        #    for f in glob.glob(file_path+'/*'):
        #        os.remove(f)
        file_path = '/rt106/test/pathology'
        if not os.path.exists(file_path) :
            os.makedirs(file_path)
        #else:
        #    for f in glob.glob(file_path+'/*'):
        #        os.remove(f)

    def test_retrieve_series(self):
        input_path = str(patientList[1]) + '/' + str(studyList[0]) + '/'+ str(seriesList[0])
        response_code = self.datastore.retrieve_series(input_path, '/rt106/test/radiology')
        self.assertEqual(response_code, 200)

    def test_upload_series(self):
        input_path = str(patientList[1]) + '/' + str(studyList[0]) + '/'+ str(seriesList[0]) + '_' + str(uuid.uuid4())
        response = self.datastore.upload_series(input_path, '/rt106/test/upload/radiology')
        self.assertTrue(any(response))
        self.assertNotEqual(len(response['filename']), 0)

    def test_retrieve_pathology_image(self):
        input_path = str(slideList[0]) + '/' + str(regionList[0])+'/source/'+ str(channelList[0])
        input_image = 'DAPI.tif'
        response_code = self.datastore.retrieve_pathology_image(input_path, '/rt106/test/pathology', input_image)
        self.assertEqual(response_code, 200)

    def test_retrieve_multi_channel_pathology_image(self):
        input_path = str(slideList[0]) + '/' + str(regionList[0])
        response_code = self.datastore.retrieve_multi_channel_pathology_image(input_path, '/rt106/test/pathology')
        self.assertEqual(response_code, 200)

    def test_upload_pathology_result_file(self):
        input_path = str(slideList[0]) + '/' + str(regionList[0])+'/test/'+ str(channelList[0])
        response = self.datastore.upload_pathology_result_file(input_path, '/rt106/test/upload/pathology/DAPI.tif')
        self.assertTrue(any(response))
        self.assertNotEqual(len(response['filename']), 0)

    def test_retrieve_annotation(self):
        input_path = str(patientList[1]) + '/' + str(studyList[0]) + '/'+ str(seriesList[0])
        #self.assertEqual(input_path, 200)
        response_code = self.datastore.retrieve_annotation(input_path, '/rt106/test/radiology')
        self.assertEqual(response_code, 200)

    def test_start_req_queue(self):
        #startReqQueue()
        pass

    def test_on_request(self):
        pass


if __name__ == '__main__':
    unittest.main()
