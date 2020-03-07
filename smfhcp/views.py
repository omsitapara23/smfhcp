from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.contrib.auth import logout as logout_user
from elasticsearch import Elasticsearch
import hashlib

es = Elasticsearch(hosts=['192.168.116.82'])


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    body = {
        "user_name": request.user.username,
        "email": request.user.email
    }
    index_user(body)
    return render(request, 'smfhcp/home.html')


def index_user(body):
    #
    res = es.index(index='general-user', id=body['user_name'], body=body)
    print(res)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_email(request):
    data = request.POST.copy()
    body = {
        "user_name": data.get('user_name'),
        "email": data.get('email'),
        "password_hash": hashlib.sha256(str(data.get('password')).encode('utf-8')).hexdigest()
    }
    index_user(body)
    request.user = {
        "user_name": data.get('user_name'),
        "email": data.get('email'),
        "is_authenticated": True
    }
    return render(request, 'smfhcp/home.html')


@login_required
def logout(request):
    logout_user(request)
    request.session.modified = True
    return redirect('/')
