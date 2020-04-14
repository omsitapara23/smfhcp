from django.shortcuts import render, redirect
import smfhcp.utils.utils as utils
import smfhcp.constants as constants
from smfhcp.dao.elasticsearch_dao import ElasticsearchDao

smfhcp_utils = utils.SmfhcpUtils()
es_dao = ElasticsearchDao()


def search(request):
    if 'is_authenticated' in request.session and request.session['is_authenticated']:
        query = request.GET.get('q')
        res, _ = smfhcp_utils.find_user(request.session['user_name'], es_dao)
        doctor_hits = es_dao.search_for_doctors(query)['hits']['hits']
        context = {
            "doctors": [],
            "posts": [],
            "search_query": query
        }
        search_hits = False
        for hit in doctor_hits:
            search_hits = True
            get_profile_picture(hit)
            context["doctors"].append(hit['_source'])
        post_hits = es_dao.search_for_posts(query)['hits']['hits']
        for hit in post_hits:
            search_hits = True
            dt = smfhcp_utils.create_time_from_utc_string(hit['_source']['date'])
            hit['_source']['date'] = smfhcp_utils.pretty_date(dt)
            hit['_source']['id'] = hit['_id']
            find_if_follows(hit, res)
            context["posts"].append(hit['_source'])
        context["hits"] = search_hits
        return render(request, constants.SEARCH_HTML_PATH, context)
    else:
        return redirect('/')


def tagged(request, tag):
    if 'is_authenticated' in request.session and request.session['is_authenticated']:
        res, _ = smfhcp_utils.find_user(request.session['user_name'], es_dao)
        context = {
            "did_find_any": False,
            "posts": [],
            "tag_searched": tag
        }
        post_hits = es_dao.search_for_tags(tag)['hits']['hits']
        for hit in post_hits:
            context['did_find_any'] = True
            dt = smfhcp_utils.create_time_from_utc_string(hit['_source']['date'])
            hit['_source']['date'] = smfhcp_utils.pretty_date(dt)
            hit['_source']['id'] = hit['_id']
            find_if_follows(hit, res)
            context["posts"].append(hit['_source'])
        return render(request, constants.TAGGED_HTML_PATH, context)
    else:
        return redirect('/')


def get_profile_picture(hit):
    if "profile_picture" in hit['_source'] and hit['_source']['profile_picture'] != "":
        hit['_source']['profile_picture'] = constants.PROFILE_PICTURE_PATH_BASE + hit['_source']['profile_picture']
    else:
        hit['_source']['profile_picture'] = constants.DEFAULT_PROFILE_PICTURE


def find_if_follows(hit, res):
    if hit['_source']['user_name'] in res['follow_list']:
        hit['_source']['isFollowing'] = True
    else:
        hit['_source']['isFollowing'] = False
