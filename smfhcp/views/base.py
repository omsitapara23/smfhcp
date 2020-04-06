from django.shortcuts import render
from elasticsearch import Elasticsearch
from django.conf import settings
import smfhcp.utils.utils as utils
import smfhcp.constants as constants

smfhcp_utils = utils.SmfhcpUtils()
es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])


def handler404(request, exception):
    return render(request, constants.STATUS_404_HTML_PATH, status=404)


def handler500(request):
    return render(request, constants.STATUS_500_HTML_PATH, status=500)


def base_view(request):
    context = {
        'posts_available': False
    }
    if 'is_authenticated' in request.session and request.session['is_authenticated']:
        res_user, _ = smfhcp_utils.find_user(request.session['user_name'], es)
        follow_list = res_user['follow_list']
        post_list = []
        posts = False
        for user in follow_list:
            query_body = {
                "query": {
                    "match": {
                        "user_name": user
                    }
                }
            }
            res = es.search(index=[constants.POST_INDEX], body=query_body)
            post_list_temp = res['hits']['hits']
            for post in post_list_temp:
                posts = True
                dt = smfhcp_utils.create_time_from_utc_string(post['_source']['date'])
                post['_source']['date'] = smfhcp_utils.pretty_date(dt)
            post_list += post_list_temp
        context = {
            'post_count': len(post_list),
            'posts_available': posts,
            'posts': post_list
        }
    return render(request, constants.HOME_HTML_PATH, context)


def trending_view(request):
    query_body = {
        "query": {
            "match_all": {}
        }
    }
    res = es.search(index=[constants.POST_INDEX], body=query_body)
    post_list = res['hits']['hits']
    for post in post_list:
        dt = smfhcp_utils.create_time_from_utc_string(post['_source']['date'])
        post['_source']['date'] = smfhcp_utils.pretty_date(dt)
        post["_source"]['isFollowing'] = smfhcp_utils.find_if_follows(request, post['_source']['user_name'], es)
    # Sorting the post list based on view_count
    post_list.sort(key=lambda k: k['_source']['view_count'], reverse=True)
    context = {
        'post_count': len(post_list),
        'posts': post_list
    }
    return render(request, constants.TRENDING_HTML_PATH, context)
