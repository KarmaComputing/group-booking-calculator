#!/bin/bash

gunicorn -w 4 --bind :8000 app:app
