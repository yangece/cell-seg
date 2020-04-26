# Copyright (c) General Electric Company, 2017.  All rights reserved.
#
# Rt 106 Generic Adaptor.
#

from flask import Flask, jsonify, make_response
import logging, json, argparse, pkg_resources

parser = argparse.ArgumentParser()
parser.add_argument('--ip', help='ip address of the interface to use', default='0.0.'+'0.0')  # trick sonar into not recognizing default ip 0.0.0.0
parser.add_argument('--port', help='port to host analytic', type=int, default=7106)
parser.add_argument('-m', '--module',
                    help='module containing the specific adaptor code for an analytic')

args = parser.parse_args()

# The following two lines suppress console output for every REST call.
# If this is not suppressed, every algorithm prints out 3 times every 5 seconds.
# If you actually want that output, just comment out these two lines.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

#
# REST API for setting and querying metadata about the algorithm.
#

# if specific adaptor is a module, then load definitions as resource. Otherwise, load from cwd
if args.module is not None:
    adaptorDefinitions = json.load(pkg_resources.resource_stream(args.module, 'rt106SpecificAdaptorDefinitions.json'))
else:
    with open('rt106SpecificAdaptorDefinitions.json') as definitionsFile:
        adaptorDefinitions = json.load(definitionsFile)

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error':'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error':'Bad Request'}), 400)

@app.route('/')
def status():
    return make_response(jsonify({'name':adaptorDefinitions['name'], 'version':adaptorDefinitions['version']}),200)

@app.route('/v1')
def v1status():
    return status()

@app.route('/v1/api')
def api():
    return make_response(jsonify(adaptorDefinitions['api']), 200)

@app.route('/v1/parameters')
def parameters():
    analytic_params = { adaptorDefinitions['name'] + '--'  + adaptorDefinitions['version'] : adaptorDefinitions['parameters'] }
    return make_response(jsonify(analytic_params), 200)

@app.route('/v1/results')
def results():
    analytic_results = { adaptorDefinitions['name'] + '--'  + adaptorDefinitions['version'] : adaptorDefinitions['results'] }
    return make_response(jsonify(analytic_results), 200)

@app.route('/v1/results/display')
def display():
    analytic_result_display = { adaptorDefinitions['name'] + '--' + adaptorDefinitions['version'] : adaptorDefinitions['result_display']}
    return make_response(jsonify(analytic_result_display), 200)

@app.route('/v1/queue')
def queue():
    return make_response(jsonify({'queue':adaptorDefinitions['queue']}), 200)

@app.route('/v1/documentation')
def documentation():
    return make_response(jsonify(adaptorDefinitions['doc']), 200)

@app.route('/v1/classification')
def classification():
    analytic_classification = { adaptorDefinitions['name'] + '--'  + adaptorDefinitions['version'] : adaptorDefinitions['classification'] }
    return make_response(jsonify(analytic_classification), 200)

# Start listening for REST requests.
if __name__ == '__main__':
    app.run(debug=False,threaded=True,host=args.ip,port=args.port)
