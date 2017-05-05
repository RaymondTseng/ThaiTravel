from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import logging
import json
import dbhelper
logger = logging.getLogger('mylogger')

@csrf_exempt
def register(request):
    db = None
    try:
        if request.method == 'POST':
            db = dbhelper.DBHelper()
            account = request.POST('account', '')
            password = request.POST('password', '')
            user_name = request.POST('user_name', '')
            result = db.register(account, password, user_name)
            return HttpResponse(json.dumps(result))
    except Exception as e:
        return HttpResponse('404 Not Found!')

@csrf_exempt
def login(request):
    db = None
    try:
        if request.method == 'POST':
            db = dbhelper.DBHelper()
            account = request.REQUEST.get('account', '')
            password = request.REQUEST.get('password', '')
            result = db.login(account, password)
            return HttpResponse(json.dumps(result))
    except Exception as e:
        return HttpResponse('404 Not Found!')