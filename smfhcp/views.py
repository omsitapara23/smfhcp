from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from django.contrib.auth import logout as logout_user
import elasticsearch
from elasticsearch import Elasticsearch
import hashlib

es = Elasticsearch(hosts=['192.168.116.82'])


def base_view(request):
    return render(request, 'smfhcp/home.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    request.session['user_name'] = request.user.username
    request.session['email'] = request.user.email
    request.session['is_authenticated'] = True
    body = {
        "user_name": request.user.username,
        "email": request.user.email
    }
    index_user(body)
    return redirect('/')


def index_user(body):
    if 'password_hash' in body:
        query_body = {
            "query": {
                "match": {
                    "email": body['email']
                }
            }
        }
        res = es.search(index='general-user', body=query_body)
        if res['hits']['total']['value'] > 0:
            return False
        try:
            es.get(index='general-user', id=body['user_name'])
        except elasticsearch.NotFoundError:
            es.index(index='general-user', id=body['user_name'], body=body)
            return True
        return False
    else:
        es.index(index='general-user', id=body['user_name'], body=body)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_email(request):
    data = request.POST.copy()
    body = {
        "user_name": data.get('user_name'),
        "email": data.get('email'),
        "password_hash": hashlib.sha256(str(data.get('password')).encode('utf-8')).hexdigest()
    }
    if index_user(body) is False:
        return render(request, 'registrations/retry_signup.html')
    request.session['user_name'] = data.get('user_name')
    request.session['email'] = data.get('email')
    request.session['is_authenticated'] = True
    return redirect('/')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):
    logout_user(request)
    request.session['user_name'] = None
    request.session['email'] = None
    request.session['is_authenticated'] = False
    request.session.modified = True
    return redirect('/')
