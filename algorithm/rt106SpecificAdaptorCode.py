# Copyright (c) General Electric Company, 2017.  All rights reserved.

# Rt 106
# Template for integrating a new algorithm.
# This is one of two required source files that need to be adapted for integrating an algorithm:
#     This Python script is for marshalling data and running the algorithm.
#     A JSON file that contains definitions with declarations.

# This template file has places where you need to add your own code for marshalling data and running your algorithm.
# If left unchanged, the template will result in a skeleton "algorithm" the registers itself and trivially responds
# to request messages.

# Please follow the numbered steps 1-5 below.

import os, glob, uuid, time, json, string, logging

# function: run_algorithm() -- Python function for marshalling your data and running your algorithm.
# parameters:
#   datastore: object to be used when interacting with the Data Store
#   context:  A JSON structure that should contain all the inputs and parameters your algorithm needs.
def run_algorithm(datastore, context):

    logging.info('run_algorithm: %r' % context)

    # cleanup the input and output directories
    for f in glob.glob('/rt106/input/*') + glob.glob('/rt106/output/*'):
        os.remove(f)
        
    # 1.    Add code here for marshalling your inputs.  You may receive URIs in 'context' that reference image or data
    #       files.  You need to fetch that data using the Data Store API.

    #       The 'datastore' object provides a method named 'retrieve_series', which takes two inputs. The 1st input identifies
    #       which series data should be retrieved from the datastore. The individual components of the path 'patient', 'study' and
    #       'series', identify the series data. The 2nd input specifies where the data should be placed within the container.
    #
    #        Following is an example of using this method:


    # # Make sure we have received the needed input.  We can't do anything without the inputSeries.
    # if (context['inputSeries'] == "" or not context['inputSeries']):
    #     status = "ERROR_NO_INPUT_SERIES"
    #     return { 'result' : {}, 'status' : status }

    # input_path = context['inputSeries']
    # #logging.info('input_path: %r' % input_path)
    # response_retrieve = datastore.retrieve_series(input_path,'/rt106/input')
    # #logging.info('response_retrieve: %r' % response_retrieve)

    # use this as reference: https://github.com/thrive-itcr/whole-cell-segmentation/blob/master/rt106SpecificAdaptorCode.py
    input_path1 = datastore.get_pathology_primary_path(context['slide'], context['region'], 'DAPI')
    input_image1 = 'DAPI.tif'
    datastore.get_instance(input_path1,'/rt106/input', input_image1, 'tiff16')

    if 'channel' in context:
        input_path2 = datastore.get_pathology_primary_path(context['slide'], context['region'], context['channel'])
        logging.info('input_path2 %s' % input_path2)
        input_image2 = 'Cell.tif'
        input_file2 = '/rt106/input/%s' % input_image2
        datastore.get_instance(input_path2,'/rt106/input', input_image2, 'tiff16')
   
    output_path1 = datastore.get_pathology_result_path(context['slide'], context['region'], context['branch'], 'NucSeg')
    output_image1 = 'NucSeg.tif'
    output_file1 = '/rt106/output/%s' % output_image1
    
    # 2.    Add code here for calling your algorithm.  This may be an "exec" of an external command-line driven process.
    #       Alternately, it may be a call into a Python library that you provide.
    #       This call should wait for your algorithm to complete to receive status and results.
    #       (Asynchronism and parallelism are handled elsewhere.)

    try:
        input_args = '/rt106/input/DAPI.tif ' + output_file1 + " " + \
            str(context['minLevel']) + " " + str(context['maxLevel']) + " " + \
            str(context['smoothingSigma']) + " " + str(context['maxCytoplasmThickness'])
        # add model and json files to input/model directory

        if 'channel' in context:
            input_args = input_args + " " + input_file2 + " " + str(context['cellSegSensitivity'])

        logging.info('input_args %s' % input_args)
        # run_algorithm = '/usr/bin/python3 testDAPISeg.py %s' % (input_args)
        run_algorithm = '/usr/bin/python3 testDAPISeg.py'
        logging.info('run Algorithm: %r' % run_algorithm)
        subprocess.check_call(run_algorithm, shell=True)
    except subprocess.CalledProcessError, e:
        logging.error('%d - %s' % (e.returncode, e.cmd))
        status = "EXECUTION_FINISHED_ERROR"
        result_context = {}
        return { 'result' : result_context, 'status' : status }


    # 3.    Based on the success or failure of your algorithm execution, set the 'status' variable to an appropriate string.
    status = "EXECUTION_FINISHED_SUCCESS"
    time.sleep(2)  # Temporary sleep to test sequencing of events in the execution scenario.  Remove this when you add your algorithm.

    # 4.    If you have result files, you need to store them in the Data Store, and obtain the URIs that refer to those files.

    #       Tha 'datastore' object provides a method named 'upload_series', which takes two inputs. The 1st input specifies
    #       the identity of the series to be created on the datastore. The 2nd input identifies where the data should be retrieved
    #       from the container, and placed into the series.
    #
    #       Following is an example of using this method:
    #
    #           datastore.upload_series('patientID/studyID/seriesID','/tmp/output')
    #
    
    # output_path = datastore.get_upload_series_path(input_path)
    # #logging.info('output_path: %r' % output_path)
    # response_upload = datastore.upload_series(output_path,'/rt106/input')
    # #logging.info('response_upload: %r' % response_upload)

    response_upload1 = datastore.post_instance(output_path1,  '/rt106/output', output_image1,  'tiff16', context['force'])
    
    if response_upload1 == 403:
        status = "EXECUTION_ERROR"    
    
    # 5.    You need to create the result_context JSON structure containing your results, including URIs obtained above in step 4.
    #       This example returns input series from about as an output series.
    #       Replace this code with whatever is appropriate for your algorithms outputs.

    # output_info = ""
    # if response_retrieve == 404:
    #     status = "EXECUTION_ABORTED_FILE_NOT_FOUND"
    # elif response_upload == 409:
    #     status = "EXECUTION_ABORTED_UPLOAD_PATH_CONFLICT"
    # else:
    #     output_info = response_upload.get('path')

    # result_context = {
    #     "outputSeries" : output_info,
    #     "calculatedValue"  : 999
    # }

    result_context = {
        "nucleiImage" : input_path1,
        "nucleiMap" : response_upload1['path']
        # "cellMap" : response_upload2['path']
    }    

    return { 'result' : result_context, 'status' : status }
