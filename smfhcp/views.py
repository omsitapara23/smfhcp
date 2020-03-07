from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as logout_user
from elasticsearch import Elasticsearch

es = Elasticsearch(hosts=['192.168.116.82'])


@login_required
def index(request):
    index_user(request.user)
    return render(request, 'smfhcp/home.html')


def index_user(user):
    body = {
        "user_name": user.username,
        "email": user.email
    }
    res = es.index(index='general-user', id=user.username, body=body)
    print(res)
    # if res['_shards']['successful'] == 0:
    #     print(res)


@login_required
def logout(request):
    logout_user(request)
    return HttpResponseRedirect('/')
