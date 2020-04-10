from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
import elasticsearch
from elasticsearch import Elasticsearch
from django.conf import settings
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
import smfhcp.utils.utils as utils
import datetime
import smfhcp.constants as constants
from smfhcp.dao.elasticsearch_dao import ElasticsearchDao
from smfhcp.esmapper.esmapper import ElasticsearchMapper

smfhcp_utils = utils.SmfhcpUtils()
es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])
es_dao = ElasticsearchDao()
es_mapper = ElasticsearchMapper()


def index_post(request, data, post_type_case_study=True):
    res = es_dao.get_doctor_by_user_name(request.session['user_name'])
    res = es_dao.index_post(request.session['user_name'], res['_source'], data, post_type_case_study)
    return res['_id']


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_post(request, post_id):
    if request.session['is_authenticated']:
        res = {}
        try:
            res = es_dao.get_post_by_id(post_id)
        except elasticsearch.NotFoundError:
            context = {
                'found': False
            }
            return render(request, constants.VIEW_POST_HTML_PATH, context)
        dt = smfhcp_utils.create_time_from_utc_string(res['_source']['date'])
        res['_source']['found'] = True
        res['_source']['date'] = smfhcp_utils.pretty_date(dt)
        res["_source"]['isFollowing'] = smfhcp_utils.find_if_follows(request, res['_source']['user_name'], es_dao)
        res["_source"]['post_id'] = post_id
        for i, comment in enumerate(res['_source']['comments']):
            dt = smfhcp_utils.create_time_from_utc_string(comment['date'])
            res['_source']['comments'][i]['date'] = smfhcp_utils.pretty_date(dt)
            for j, reply in enumerate(res['_source']['comments'][i]['replies']):
                dt = smfhcp_utils.create_time_from_utc_string(reply['date'])
                res['_source']['comments'][i]['replies'][j]['date'] = smfhcp_utils.pretty_date(dt)
        es_dao.update_post_view_count(post_id)
        return render(request, constants.VIEW_POST_HTML_PATH, res['_source'])
    else:
        return redirect("/")


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def create_case_study(request):
    if request.method == 'POST':
        data = request.POST.copy()
        post_id = index_post(request, data)
        es_dao.update_post_count(request.session['user_name'])
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
        es_dao.update_post_count(request.session['user_name'])
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
        comment = es_mapper.map_comment(request.POST, comment_id)
        es_dao.add_comment_by_post_id(request.POST.get('post_id'), comment)
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
        reply = es_mapper.map_reply(request.POST)
        es_dao.add_reply_by_post_id_and_comment_id(request.POST.get('post_id'), request.POST.get('comment_id'), reply)
        return HttpResponse(
            json.dumps({}),
            content_type=constants.APPLICATION_JSON_TYPE
        )
    else:
        raise PermissionDenied()
