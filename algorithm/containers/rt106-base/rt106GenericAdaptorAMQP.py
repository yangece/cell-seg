# Copyright (c) General Electric Company, 2017.  All rights reserved.

#
# Rt 106 Generic Adaptor.
#

import pika, requests, tarfile, logging, json, uuid, time, os, argparse, glob, pkg_resources,uuid
from logging.handlers import RotatingFileHandler

#
# Set up parser for command line arguments.
#

parser = argparse.ArgumentParser(description='')
parser.add_argument('-b', '--broker',
                    help='ip address of RabbitMQ server',
                    required=True)

parser.add_argument('-d', '--dicom',
                    help='ip address of dicom object store',
                    required=True)

parser.add_argument('-m', '--module',
                    help='module containing the specific adaptor code for an analytic')

args = parser.parse_args()

# may need to load the specific adaptor as a module, otherwise we assume it is in cwd
if args.module is not None:
    import importlib
    rt106SpecificAdaptorCode = importlib.import_module(args.module + '.rt106SpecificAdaptorCode')
else:
    import rt106SpecificAdaptorCode

class DataStore:
    def __init__(self,url, execution_id, pipeline_id):
        self.url = url
        self.pipeline_id = pipeline_id
        self.execution_id = execution_id

    def retrieve_series(self,series_path,output_dir):
        retrieve_series_request = '%s/v1/series%s/archive'  % (self.url,series_path)
        logging.debug('http request - %s' % retrieve_series_request)
        response = requests.get(retrieve_series_request)
        if response.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response.status_code,retrieve_series_request))
            return response.status_code
        with open('%s/input.tar' % output_dir,'wb') as f:
            f.write(response.content)
            tar = tarfile.open('%s/input.tar' % output_dir)
            tar.extractall(path=output_dir)
            tar.close()
            os.remove('%s/input.tar' % output_dir)
        return response.status_code

    def get_upload_series_path(self, input_path):
        inputs = input_path.split('/')
        patient = inputs[inputs.index('Patients')+1]
        study = inputs[inputs.index('Imaging')+1]
        series = inputs[inputs.index('Imaging')+2]
        pipeline = self.pipeline_id
        execid = self.execution_id
        path_request = '%s/v1/patients/%s/results/%s/steps/%s/imaging/studies/%s/series'  % (self.url,patient,pipeline,execid,study)
        logging.debug('http request - %s' %  path_request)
        response = requests.get(path_request)
        if response.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response.status_code,path_request))
            return response.status_code
        json_response = json.loads(response.text)
        output_path = json_response['path']+'/'+ str(uuid.uuid4())
        return output_path

    def upload_series(self,series_path,input_dir):
        tar = tarfile.open('/tmp/output.tar','w')
        for f in glob.glob('%s/*' % input_dir):
            filename = os.path.basename(f)
            tar.add(f,arcname=filename)
        tar.close()
        upload_series_request = self.url + '/v1/series' + series_path + '/tar'
        logging.debug('http post request - %s' % upload_series_request)
        archive = { 'file' : open('/tmp/output.tar' ,'rb') }
        response = requests.post(upload_series_request,files=archive)
        os.remove('/tmp/output.tar')
        if response.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response.status_code, upload_series_request))
            return response.status_code
        return response.json()

    # retrieve an annotation
    def retrieve_annotation(self,annotation_path,output_dir):
        retrieve_annotation_request = '%s/v1/annotation/%s'  % (self.url,annotation_path)
        logging.debug('http request - %s' % retrieve_annotation_request)
        response = requests.get(retrieve_annotation_request)
        if response.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response.status_code,retrieve_annotation_request))
            return response.status_code
        return response.status_code

    # retrieve a primary (source) pathology image path.
    def get_pathology_primary_path(self,slide,region,channel):
        pathology_path_request = '%s/v1/pathology/slides/%s/regions/%s/channels/%s/image' % (self.url,slide,region,channel)
        logging.info('http request - %s' % pathology_path_request)
        response = requests.get(pathology_path_request)
        if response.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response.status_code,pathology_path_request))
            return response.status_code
        path = json.loads(response.text)
        if len(path) > 0:
            path = path[0]
        else:
            path = ""
        return path

    # retrieve a result pathology path location.  (i.e.  This is the directory without file name.)
    def get_pathology_result_path(self,slide,region,pipelineid,execid):
        pathology_path_request = '%s/v1/pathology/slides/%s/regions/%s/results/%s/steps/%s/data' % (self.url,slide,region,pipelineid,execid)
        logging.info('http request - %s' % pathology_path_request)
        response = requests.get(pathology_path_request)
        if response.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response.status_code,pathology_path_request))
            return response.status_code
        path = json.loads(response.text)
        return path

    # return the full path for a result pathology image.
    def get_pathology_result_image_path(self, slide, region, pipelineid, execid):
        pathology_path_request = '%s/v1/pathology/slides/%s/regions/%s/results/%s/steps/%s/instances' % (self.url, slide, region, pipelineid, execid)
        logging.info('http request - %s' % pathology_path_request)
        response = requests.get(pathology_path_request)
        logging.info('http response code - %s, response text - %s' % (response.status_code, response.text))
        if response.status_code != requests.codes.ok:
            logging.error('request failed (%d) - %s' % (response.status_code, pathology_path_request))
            return response.status_code
        if not json.loads(response.text):
            logging.error('request failed, empty list returned - %s' % pathology_path_request)
            return 404
        paths = json.loads(response.text)
        return paths[0]

    # get an instance, which could be an image file or other type of file.
    def get_instance(self,path,filedir,filename,format):
        retrieve_instance_request = '%s/v1/instance%s/%s' % (self.url,path,format)
        logging.info('http request - %s' % retrieve_instance_request)
        response_file = requests.get(retrieve_instance_request)
        if response_file.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response_file.status_code,retrieve_instance_request))
            return response_file.status_code
        with open('%s/%s' % (filedir,filename),'wb') as f:
            f.write(response_file.content)
        return response_file.status_code

    # post a pathology result file
    def post_instance(self,path,filedir,filename,format,force):
        logging.info('post_instance: path=%s, filedir=%s, filename=%s, format=%s' % (path,filedir,filename,format))
        try:
            if force:
                upload_instance_request = '%s/v1/instance%s/%s/force' % (self.url,path,format)
            else:
                upload_instance_request = '%s/v1/instance%s/%s' % (self.url,path,format)
            archive = { 'file' : open('%s/%s' % (filedir,filename),'rb') }
            response_file = requests.post(upload_instance_request,files=archive)
            if response_file.status_code != requests.codes.ok :
                logging.error('request failed (%d) - %s' % (response_file.status_code, upload_instance_request))
                return response_file.status_code
            return response_file.json()
        except:
            pass
        return json.dumps({'error': 'error posting instance'})

    # retrieve images from all channels for a region, each channel contains one image
    def retrieve_multi_channel_pathology_image(self,slide,region,output_dir):
        channel_list_request = '%s/v1/pathology/slides/%s/regions/%s/channels' % (self.url,slide,region)
        logging.debug('http request - %s' % channel_list_request)
        response = requests.get(channel_list_request)
        logging.debug('retrieve_multi_channel_pathology_image response: %s' % response.content)
        if response.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response.status_code,channel_list_request))
            return response.status_code
        channels = json.loads(response.text)
        for channel in channels:
            filename = '%s.tiff' % channel
            image_path = self.get_pathology_primary_path(slide, region, channel)
            self.get_instance(image_path, output_dir, filename, 'tiff16')
        return response.status_code
  
broker_ip = args.broker
dicom_url = args.dicom

# if specific adaptor is a module, then load definitions as resource. Otherwise, load from cwd
if args.module is not None:
    adaptor_definitions = json.load(pkg_resources.resource_stream(args.module, 'rt106SpecificAdaptorDefinitions.json'))
else:
    with open('rt106SpecificAdaptorDefinitions.json') as definitions_file:
        adaptor_definitions = json.load(definitions_file)


#
# Set up queue request handler.
#

def on_request(channel, method, properties, body):
    run = json.loads(body)
    logging.info('run: %r' % run)
    hc_pipeline_id = run['header']['pipelineId']
    hc_execution_id = run['header']['executionId']
    hc_creation_time = properties.headers.get('creationTime')

    logging.debug('executionId: %r' % hc_execution_id)
    logging.debug('creationTime: %r' % hc_creation_time)
    logging.debug('routing key: %r' % properties.reply_to)
    logging.debug('correlation_id: %r' % properties.correlation_id)

    logging.debug("Request to run " + adaptor_definitions['name'] + ":" + adaptor_definitions['version'])

    algorithm_result = rt106SpecificAdaptorCode.run_algorithm(DataStore(dicom_url, hc_execution_id, hc_pipeline_id),run['context'])

    response_body = {
        'header': {
            'messageId': str(uuid.uuid4()),
            'pipelineId': hc_pipeline_id, 
            'executionId': hc_execution_id,
            'creationTime': int(time.time())
        },
        'result': algorithm_result['result'],
        'status': algorithm_result['status']
    }

    channel.basic_publish(exchange='',
                          routing_key=properties.reply_to,
                          properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                          body=json.dumps(response_body))
    channel.basic_ack(delivery_tag=method.delivery_tag)

def start_req_queue():
    global channel

    # Connect to the job queuing system.  If queuing is not up yet, then backoff for a bit and try again
    queuing_up = False
    queue = adaptor_definitions['queue']
    while not queuing_up:
        logging.info("Request queue is " + queue)
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=broker_ip))
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(on_request,queue=queue, no_ack=False)
            queuing_up = True
            logging.info('Queues are now available.')
        except:
            logging.info('Queues are not available yet. Backing off.')
            time.sleep(5)

    logging.debug('[*] waiting for messages.')
    try:
        channel.start_consuming()
    except pika.exceptions.ConnectionClosed, e:
        logging.info('client connection is closed')

logging.basicConfig(format='%(levelname)s:%(name)s %(message)s', level=logging.DEBUG)
pika_logger = logging.getLogger('pika')
pika_logger.setLevel(logging.INFO)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

file_handler = RotatingFileHandler('/rt106/logfile',maxBytes=10000,backupCount=1)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

if __name__ == '__main__':
    start_req_queue()
