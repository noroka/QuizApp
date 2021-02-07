#!/usr/local/bin/python3
from wsgiref.handlers import CGIHandler
from QuizApp import app
CGIHandler().run(app)