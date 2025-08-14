# https://docs.gunicorn.org/en/latest/settings.html#settings

chdir = '/opt/nodeseekmcp'

workers = 2

# https://www.uvicorn.org/deployment/#gunicorn
# https://github.com/benoitc/gunicorn/issues/1539
worker_class = 'nodeseekmcp.uvicorn_worker.MyUvicornWorker'

worker_connections = 1024

max_requests = 200

max_requests_jitter = 20

timeout = 10

loglevel = 'info'
errorlog = '-'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
capture_output = True

# gunicorn -c gunicorn.conf.py -b '0.0.0.0:8866' -b '[::]:8866'  nodeseekmcp.app:app

# gunicorn -c gunicorn.conf.py -b '[::]:8866'  nodeseekmcp.app:app
