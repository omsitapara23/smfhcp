from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from elasticsearch import Elasticsearch
from django.conf import settings
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
import smfhcp.utils.utils as utils
import smfhcp.constants as constants

smfhcp_utils = utils.SmfhcpUtils()
es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_profile(request, user_name):
    if 'is_authenticated' in request.session and request.session['is_authenticated']:
        res_doctor = es.get(index=[constants.DOCTOR_INDEX], id=user_name)
        query_body = {
            "query": {
                "match": {
                    "user_name": user_name
                }
            }
        }
        posts = True
        res = es.search(index=[constants.POST_INDEX], body=query_body)
        post_list = res['hits']['hits']
        for post in post_list:
            dt = smfhcp_utils.create_time_from_utc_string(post['_source']['date'])
            post['_source']['date'] = smfhcp_utils.pretty_date(dt)
        if res['hits']['total']['value'] == 0:
            posts = False
        is_following = smfhcp_utils.find_if_follows(request, user_name, es)
        context = {
            'user_name': res_doctor['_source']['user_name'],
            'full_name': res_doctor['_source']['full_name'],
            'email': res_doctor['_source']['email'],
            'qualification': res_doctor['_source']['qualification'],
            'research_interests': res_doctor['_source']['research_interests'],
            'profession': res_doctor['_source']['profession'],
            'institution': res_doctor['_source']['institution'],
            'clinical_interests': res_doctor['_source']['clinical_interests'],
            'following_count': len(res_doctor['_source']['follow_list']),
            'post_count': res_doctor['_source']['post_count'],
            'follower_count': res_doctor['_source']['follower_count'],
            'posts_available': posts,
            'posts': post_list,
            'isFollowing': is_following
        }
        if 'profile_picture' in res_doctor['_source']:
            context['profile_picture'] = res_doctor['_source']['profile_picture']
        else:
            context['profile_picture'] = 'default.jpg'
        return render(request, constants.VIEW_PROFILE_HTML_PATH, context)
    else:
        return redirect("/")


def build_inline_string(data):
    inline_string = ""
    params = {}
    if data.get('password') is not None:
        inline_string += "ctx._source.password_hash = params.password_hash; "
        params['password_hash'] = str(smfhcp_utils.find_hash(data.get('password')))
    if len(json.loads(data.get('qualification'))['qualifications']) > 0:
        inline_string += "ctx._source.qualification.addAll(params.qualification); "
        params['qualification'] = [s.strip() for s in json.loads(data.get('qualification'))['qualifications']]
    if str(data.get('profession')) != '':
        inline_string += "ctx._source.profession = params.profession; "
        params['profession'] = str(data.get('profession'))
    if str(data.get('institution')) != '':
        inline_string += "ctx._source.institution = params.institution; "
        params['institution'] = str(data.get('institution'))
    if len(json.loads(data.get('researchInterests'))['researchInterests']) > 0:
        inline_string += "ctx._source.research_interests.addAll(params.research_interests); "
        params['research_interests'] = [s.strip() for s in json.loads(data.get('researchInterests'))['researchInterests']]
    if len(json.loads(data.get('clinicalInterests'))['clinicalInterests']) > 0:
        inline_string += "ctx._source.clinical_interests.addAll(params.clinical_interests); "
        params['clinical_interests'] = [s.strip() for s in json.loads(data.get('clinicalInterests'))['clinicalInterests']]
    return inline_string, params


def update_document(inline_string, params, index_name, doc_id):
    body = {
        "script": {
            "inline": inline_string,
            "lang": "painless",
            "params": params
        }
    }
    es.update(index=index_name, id=doc_id, body=body)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_profile(request):
    if request.method == 'POST':
        inline_string, params = build_inline_string(request.POST)
        update_document(inline_string, params, constants.DOCTOR_INDEX, str(request.session['user_name']))
        response_data = {
            'redirect': True,
            'redirect_url': '/view_profile/' + str(request.session['user_name'])
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type=constants.APPLICATION_JSON_TYPE
        )
    else:
        raise PermissionDenied()


def update_follow_count(data):
    body = {
        "script": {
            "lang": "painless",
            "params": {
                "count": 1
            }
        }
    }
    if data.get('follow') == "true":
        body['script']['source'] = "ctx._source.follower_count += params.count"
    else:
        body['script']['source'] = "if(ctx._source.follower_count > 0) {ctx._source.follower_count -= params.count}"
    es.update(index=constants.DOCTOR_INDEX, id=data.get('doctor_name'), body=body)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def follow_or_unfollow(request):
    if request.method == 'POST':
        data = request.POST.copy()
        body = {}
        if data.get('follow') == "true":
            print("here")
            body = {
                "script": {
                    "inline": "ctx._source.follow_list.add(params.doctor_user_name);",
                    "lang": "painless",
                    "params": {
                        "doctor_user_name": data.get('doctor_name')
                    }
                }
            }
            print("follow")
        else:
            body = {
                "script": {
                    "source": "ctx._source.follow_list.remove(ctx._source.follow_list.indexOf(params.doctor_user_name))",
                    "lang": "painless",
                    "params": {
                        "doctor_user_name": data.get('doctor_name')
                    }
                }
            }
        if request.session['is_doctor']:
            es.update(index=constants.DOCTOR_INDEX, id=request.session['user_name'], body=body)
        else:
            es.update(index=constants.GENERAL_USER_INDEX, id=request.session['user_name'], body=body)
        update_follow_count(data)
        return HttpResponse(
            json.dumps({}),
            content_type=constants.APPLICATION_JSON_TYPE
        )
    else:
        raise PermissionDenied()


def get_follow_list(request):
    if request.is_ajax():
        if 'is_authenticated' in request.session and request.session['is_authenticated']:
            me = {
                'id': request.session['user_name'],
                'name': request.session['user_name']
            }
            follow_list = []
            res = es.get(index=constants.DOCTOR_INDEX, id=request.session['user_name'])
            following = res['_source']['follow_list']
            for user in following:
                talk_body = {
                    'id': user,
                    'name': user
                }
                follow_list.append(talk_body)
            response = {
                'me': me,
                'follow_list': follow_list
            }
            return HttpResponse(
                json.dumps(response),
                content_type=constants.APPLICATION_JSON_TYPE
            )
        else:
            raise PermissionDenied()
    else:
        raise PermissionDenied()
