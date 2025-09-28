from flask import Flask, Response, request
import os
import json

app = Flask(__name__)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, name)
    if not os.path.exists(path):
        return ""
    with open(path, 'r') as f:
        return f.read()

@app.route('/metrics')
def metrics():
    # fixture query ?f=idle|low|bursty|mem
    f = request.args.get('f', os.environ.get('DCGM_FIXTURE', 'idle'))
    content = load_fixture(f + '.prom')
    if content == '':
        # annotate response so callers can see what fixture was requested
        resp = Response('# no fixture', mimetype='text/plain')
        resp.headers['X-DCGM-FIXTURE'] = f
        app.logger.warning('No fixture found for %s', f)
        return resp
    resp = Response(content, mimetype='text/plain')
    resp.headers['X-DCGM-FIXTURE'] = f
    app.logger.info('Serving fixture %s', f)
    return resp

@app.route('/')
def index():
    return "dcgm-mock: try /metrics?f=idle|low|bursty|mem"


@app.route('/health')
def health():
    # return 200 if the default fixture exists; otherwise 503
    default = os.environ.get('DCGM_FIXTURE', 'idle')
    content = load_fixture(default + '.prom')
    if content == '':
        app.logger.error('Health check failed: fixture %s missing', default)
        return Response(json.dumps({'ok': False, 'fixture': default}), status=503, mimetype='application/json')
    return Response(json.dumps({'ok': True, 'fixture': default}), status=200, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9100)
