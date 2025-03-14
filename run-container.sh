#!/bin/bash

docker run --rm -p 8000:8000 -v $PWD/static:/usr/src/app/static --env-file=.env booking
