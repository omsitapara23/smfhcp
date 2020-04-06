from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
import elasticsearch
from elasticsearch import Elasticsearch
from django.conf import settings
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
import smfhcp.utils.utils as utils
import textile
import datetime
import smfhcp.constants as constants

smfhcp_utils = utils.SmfhcpUtils()
es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])


def index_post(request, data, post_type_case_study=True):
    res = es.get(index=constants.DOCTOR_INDEX, id=request.session['user_name'])
    print(request.session['user_name'])
    print(res)
    body = {
        "user_name": request.session['user_name'],
        "full_name": res['_source']['full_name'],
        "profession": res['_source']['profession'],
        "institution": res['_source']['institution'],
        "view_count": 1,
        "title": data.get('title'),
        "tags": [str(s).strip() for s in json.loads(data.get('tags'))['tags']],
        "date": datetime.datetime.now(datetime.timezone.utc),
        "comments": []
    }
    if post_type_case_study:
        body['history'] = textile.textile(data.get('history'))
        body['diagnosis'] = textile.textile(data.get('diagnosis'))
        body['examination'] = textile.textile(data.get('examination'))
        body['prevention'] = textile.textile(data.get('prevention'))
        body['treatment'] = textile.textile(data.get('treatment'))
        body['remarks'] = textile.textile(data.get('remarks'))
    else:
        body['description'] = textile.textile(data.get('description'))
    res = es.index(index=constants.POST_INDEX, body=body)
    return res['_id']


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_post(request, post_id):
    if request.session['is_authenticated']:
        res = {}
        try:
            res = es.get(index=constants.POST_INDEX, id=post_id)
        except elasticsearch.NotFoundError:
            context = {
                'found': False
            }
            return render(request, constants.VIEW_POST_HTML_PATH, context)
        dt = smfhcp_utils.create_time_from_utc_string(res['_source']['date'])
        res['_source']['found'] = True
        res['_source']['date'] = smfhcp_utils.pretty_date(dt)
        res["_source"]['isFollowing'] = smfhcp_utils.find_if_follows(request, res['_source']['user_name'], es)
        res["_source"]['post_id'] = post_id
        for i, comment in enumerate(res['_source']['comments']):
            dt = smfhcp_utils.create_time_from_utc_string(comment['date'])
            res['_source']['comments'][i]['date'] = smfhcp_utils.pretty_date(dt)
            for j, reply in enumerate(res['_source']['comments'][i]['replies']):
                dt = smfhcp_utils.create_time_from_utc_string(reply['date'])
                res['_source']['comments'][i]['replies'][j]['date'] = smfhcp_utils.pretty_date(dt)
        update_post_view_count(post_id)
        return render(request, constants.VIEW_POST_HTML_PATH, res['_source'])
    else:
        return redirect("/")


def update_post_count(request):
    body = {
        "script": {
            "source": "ctx._source.post_count += params.count",
            "lang": "painless",
            "params": {
                "count": 1
            }
        }
    }
    es.update(index=constants.DOCTOR_INDEX, id=request.session['user_name'], body=body)


def update_post_view_count(post_id):
    body = {
        "script": {
            "source": "ctx._source.view_count += params.count",
            "lang": "painless",
            "params": {
                "count": 1
            }
        }
    }
    es.update(index=constants.POST_INDEX, id=post_id, body=body)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def create_case_study(request):
    if request.method == 'POST':
        data = request.POST.copy()
        post_id = index_post(request, data)
        update_post_count(request)
        response_data = {
            'redirect': True,
            'redirect_url': '/view_post/' + str(post_id)
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type=constants.APPLICATION_JSON_TYPE
        )
    else:
        raise PermissionDenied()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def create_general_post(request):
    if request.method == 'POST':
        data = request.POST.copy()
        post_id = index_post(request, data, False)
        update_post_count(request)
        response_data = {
            'redirect': True,
            'redirect_url': '/view_post/' + str(post_id)
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type=constants.APPLICATION_JSON_TYPE
        )
    else:
        raise PermissionDenied()


def add_comment(request):
    if request.method == 'POST':
        comment_id = smfhcp_utils.find_hash(datetime.datetime.now())
        body = {
            "script": {
                "source": "ctx._source.comments.add(params.new_comment)",
                "lang": "painless",
                "params": {
                    "new_comment": {
                        "comment_body": request.POST.get('comment_text'),
                        "user_name": request.POST.get('user_name'),
                        "replies": [],
                        "comment_id": comment_id,
                        "date": datetime.datetime.now(datetime.timezone.utc)
                    }
                }
            }
        }
        es.update(index=constants.POST_INDEX, id=request.POST.get('post_id'), body=body)
        response = {
            'comment_id': comment_id
        }
        return HttpResponse(
            json.dumps(response),
            content_type=constants.APPLICATION_JSON_TYPE
        )
    else:
        raise PermissionDenied()


def add_reply(request):
    if request.method == 'POST':
        print(request.POST)
        body = {
            "script": {
                "source": "for(int i=0; i < ctx._source.comments.size(); i++){ if(ctx._source.comments[i].comment_id "
                          "== params.comment_id){ ctx._source.comments[i].replies.add(params.reply); } }",
                "lang": "painless",
                "params": {
                    "comment_id": request.POST.get('comment_id'),
                    "reply": {
                        "user_name": request.POST.get('user_name'),
                        "reply_body": request.POST.get('reply_text'),
                        "date": datetime.datetime.now(datetime.timezone.utc)
                    }
                }
            }
        }
        es.update(index=constants.POST_INDEX, id=request.POST.get('post_id'), body=body)
        return HttpResponse(
            json.dumps({}),
            content_type=constants.APPLICATION_JSON_TYPE
        )
    else:
        raise PermissionDenied()
