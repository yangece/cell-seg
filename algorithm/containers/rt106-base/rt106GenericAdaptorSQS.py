# Copyright (c) General Electric Company, 2017.  All rights reserved.

import requests, tarfile, logging, json, uuid, time, signal, os, argparse, glob, pkg_resources
import Queue, threading, sched
import boto3, botocore

from logging.handlers import Rotatingfile_handler

class DataStore:
    def __init__(self,url):
        self.url = url

    def upload_series(self,series_path,input_dir):
        tar = tarfile.open('/tmp/output.tar','w')
        for f in glob.glob('%s/*' % input_dir):
            filename = os.path.basename(f)
            tar.add(f,arcname=filename)
        tar.close()
        upload_series_request = 'http://' + self.url + '/v1/series/' + series_path + '/archive.tar'
        logging.info('upload_series_request: %s' % upload_series_request)
        archive = { 'file' : open('/tmp/output.tar' ,'rb') }
        response = requests.post(upload_series_request,files=archive)
        os.remove('/tmp/output.tar')
        if response.status_code != requests.codes.ok :
           logging.error('request failed (%d) - %s' % (response.status_code, upload_series_request))
           return response.status_code
        return response.json()

    def retrieve_series(self,series_path,output_dir):
        retrieve_series_request = 'http://%s/v1/series/%s'  % (self.url,series_path)
        logging.info('retrieve_series_request: %s' % retrieve_series_request)
        response = requests.get(retrieve_series_request)
        if response.status_code != requests.codes.ok :
            logging.error('request failed (%d) - %s' % (response.status_code,retrieve_series_request))
            return
        with open('%s/input.tar' % output_dir,'wb') as f:
            f.write(response.content)
            tar = tarfile.open('%s/input.tar' % output_dir)
            tar.extractall(path=output_dir)
            tar.close()
            os.remove('%s/input.tar' % output_dir)

class SignalHandler:
    stopper = None
    def __init__(self,stopper):
        self.stopper = stopper

    def __call__(self,signum,frame):
        self.stopper.set()

#
# Set up parser for command line arguments.
#

parser = argparse.ArgumentParser(description='')
parser.add_argument('-l', '--log', help='name of the log_file',
                    required=True)
parser.add_argument('-d', '--dicom', help='ip address of dicom object store',
                    required=True)
parser.add_argument('--work_estimate', help='how long it takes for algorithm to create result',
                    type=long,
                    required=True)
parser.add_argument('--heartbeat', help='period of the heartbeat that monitors algorithm progress',
                    type=float,
                    required=False)
parser.add_argument('-m', '--module',
                    help='module containing the specific adaptor code for an analytic')
args = parser.parse_args()

dicom_url = args.dicom
work_estimate = args.work_estimate
heartbeat_period = args.heartbeat
log_file = args.log

# may need to load the specific adaptor as a module, otherwise we assume it is in cwd
if args.module is not None:
    import importlib
    rt106SpecificAdaptorCode = importlib.import_module(args.module + '.rt106SpecificAdaptorCode')
else:
    import rt106SpecificAdaptorCode

# if specific adaptor is a module, then load definitions as resource. Otherwise, load from cwd
if args.module is not None:
    adaptor_definitions = json.load(pkg_resources.resource_stream(args.module, 'rt106Specificadaptor_definitions.json'))
else:
    with open('rt106Specificadaptor_definitions.json') as definitionsFile:
        adaptor_definitions = json.load(definitionsFile)

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('nose').setLevel(logging.CRITICAL)

if log_file is not None:
    logging.info('log_file: %r' % log_file)
    file_handler = Rotatingfile_handler(log_file,maxBytes=10000,backupCount=1)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

logging.info('rt106GenericAdaptor - starting')
logging.debug('work_estimate=%r' % work_estimate)
logging.debug('heartbeat_period=%r' % heartbeat_period)


sqs_resource = None

aws_region = os.getenv('AWS_REGION',None)
if aws_region is not None:
    logging.info("[SQS] service requests using region '%s'" % aws_region)
    sqs_resource = boto3.resource('sqs',region_name=aws_region);
else:
    sqs_resource = boto3.resource('sqs')

request_queue_name = os.getenv('Rt106_ALGORITHM_request_queue',adaptor_definitions['queue'])
request_queue = sqs_resource.get_queue_by_name(QueueName=request_queue_name)

class HeartbeatThread(threading.Thread):
    msg_queue = None
    msg = None
    stop_heartbeat = None
    period = None
    heartbeatSchedule = None
    heartbeatStartupTime = None
    msgStartupTime = None

    def __init__(self,period,stopper):
        super(HeartbeatThread,self).__init__()
        self.msg_queue = Queue.Queue()
        self.msg = None
        self.stop_heartbeat = stopper
        self.heartbeatSchedule = sched.scheduler(time.time,time.sleep)
        self.period = period
        self.heartbeatStartupTime = None
        self.msgStartupTime = None

    def heartbeat_action(self):
        while not self.msg_queue.empty():
            self.msg = self.msg_queue.get(False)
            self.msgStartupTime = time.time()
        if self.msg is None:
            self.msgStartupTime = None
        if self.msg != None:
            dt = time.time() - self.msgStartupTime
            self.msg.change_visibility(VisibilityTimeout=work_estimate)
            logging.debug('heartbeat @ %d - setting msg visibility to %r ' % (dt,work_estimate))

    def periodic(self,scheduler,interval,action,actionargs=()):
        if not self.stop_heartbeat.is_set() and self.period is not None:
            scheduler.enter(interval,1, self.periodic, (scheduler,interval,action,actionargs))
            action(*actionargs)

    def run(self):
        self.heartbeatStartupTime = time.time()
        self.periodic(self.heartbeatSchedule,self.period,self.heartbeat_action)
        self.heartbeatSchedule.run()
        logging.info('rt106GenericAdaptor - exiting heartbeat thread')

    def setmsg(self,msg): self.msg_queue.put(msg)

class MessagingThread(threading.Thread):
    stop_messaging = None
    def __init__(self, sqs_queue,stopper):
        super(MessagingThread,self).__init__()
        self.queue = sqs_queue
        self.stop_messaging = stopper

    def run(self):
        logging.info('[%s] waiting for messages.' % request_queue.url)
        while not self.stop_messaging.is_set():
            try:
                msgs = request_queue.receive_messages(WaitTimeSeconds=20, MaxNumberOfMessages=1,
                                                     MessageAttributeNames=['ReplyTo'])
            except botocore.exceptions.ClientError as e:
                logging.error('receive_messages failed - %r' % e)
                self.stop_messaging.set() # will also stop the heartbeat

            for msg in msgs:
                run = json.loads(msg.body)
                hc_execution_id = run['header']['executionId']
                logging.info("Request Received: executionId=%r" % hc_execution_id)
                #logging.debug("Receipt Handle: %r" % msg.receipt_handle)

                msg.change_visibility(VisibilityTimeout=work_estimate)
                heartbeat.setmsg(msg)

                response_body = None
                context = run.get('context',None)

                if context is None:
                    logging.warning("Invalid message body, 'context' is missing.");
                    logging.debug('message body: \n%r' % msg.body);
                    response_body = {
                        'header': {
                            'messageId': str(uuid.uuid4()), 'executionId': hc_execution_id, 'creationTime': int(time.time())
                        },
                        'result': None, 'status': 'EXECUTION_FINISHED_ERROR'
                    }
                else:
                    algorithm_start_time = time.time()
                    algorithm_result = rt106SpecificAdaptorCode.run_algorithm(DataStore(dicom_url),context)
                    algorithm_end_time = time.time()
                    logging.info('algorithm_runTime: %r' % (algorithm_end_time - algorithm_start_time))
                    response_body = {
                        'header': {
                            'messageId': str(uuid.uuid4()), 'executionId': hc_execution_id, 'creationTime': int(time.time())
                        },
                        'result': algorithm_result['result'], 'status': algorithm_result['status']
                    }

                logging.debug('message_attributes: %r' % msg.message_attributes);
                if msg.message_attributes is not None:
                    response_queue = msg.message_attributes.get('ReplyTo').get('StringValue')
                    logging.debug('response_queue: %r' % response_queue)

                    msg_attributes = {
                        'CreationTime': { 'StringValue':str(int(time.time())), 'DataType':'String'},
                        'ExecutionId': { 'StringValue':str(hc_execution_id), 'DataType':'String' },
                        'ReplyTo': { 'StringValue':response_queue, 'DataType':'String' } }

                    try:
                        q = sqs_resource.Queue(url=response_queue)
                        q.send_message(MessageBody=json.dumps(response_body), MessageAttributes=msg_attributes)
                    except botocore.exceptions.ClientError as e:
                        logging.warning('send message failed - %r %r' % (response_queue,e))

                heartbeat.setmsg(None)
                msg.delete() #logging.debug('deleting msg %r' % msg.receipt_handle)
        logging.debug('rt106GenericAdaptor - exiting messaging thread')

if __name__ == '__main__':

    stopper = threading.Event()
    handler = SignalHandler(stopper)
    signal.signal(signal.SIGINT,handler)

    heartbeat = HeartbeatThread(heartbeat_period,stopper)
    heartbeat.start()

    messenger = MessagingThread(request_queue,stopper)
    messenger.start()

    while heartbeat.isAlive() or messenger.isAlive():
        heartbeat.join(5)
        messenger.join(5)

    logging.info('rt106GenericAdaptor - exiting')
