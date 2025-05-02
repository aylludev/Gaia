#!/bin/bash

NAME="gaia"
DJANGODIR=$(dirname $(cd $(dirname $0) && pwd))
SOCKFILE=/tmp/gaia-apolo.sock
LOGDIR=${DJANGODIR}/logs/gunicorn.log
USER=amawta
GROUP=amawta
NUM_WORKERS=5
DJANGO_WSGI_MODULE=Gaia.wsgi

rm -frv $SOCKFILE

echo $DJANGODIR

cd $DJANGODIR

exec ${DJANGODIR}/env/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=$LOGDIR
