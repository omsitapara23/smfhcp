from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
import smfhcp.utils.utils as utils
import smfhcp.constants as constants
from smfhcp.dao.elasticsearch_dao import ElasticsearchDao

smfhcp_utils = utils.SmfhcpUtils()
es_dao = ElasticsearchDao()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_profile(request, user_name):
    if 'is_authenticated' in request.session and request.session['is_authenticated']:
        res_doctor = es_dao.get_doctor_by_user_name(user_name)
        posts = True
        res = es_dao.search_posts_by_doctor_name(user_name)
        post_list = res['hits']['hits']
        for post in post_list:
            dt = smfhcp_utils.create_time_from_utc_string(post['_source']['date'])
            post['_source']['date'] = smfhcp_utils.pretty_date(dt)
        if res['hits']['total']['value'] == 0:
            posts = False
        is_following = smfhcp_utils.find_if_follows(request, user_name, es_dao)
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


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_profile(request):
    if request.method == 'POST':
        es_dao.update_profile(request.session['user_name'], request.POST)
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


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def follow_or_unfollow(request):
    if request.method == 'POST':
        data = request.POST.copy()
        if data.get('follow') == "true":
            es_dao.add_to_follow_list(request.session['user_name'], data.get('doctor_name'),
                                      request.session['is_doctor'])
        else:
            es_dao.remove_from_follow_list(request.session['user_name'], data.get('doctor_name'),
                                           request.session['is_doctor'])
        es_dao.update_follow_count(data)
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
            res = es_dao.get_doctor_by_user_name(request.session['user_name'])
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
