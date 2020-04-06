from django.shortcuts import render, redirect
from elasticsearch import Elasticsearch
from django.conf import settings
import json
import smfhcp.utils.utils as utils
import smfhcp.constants as constants

smfhcp_utils = utils.SmfhcpUtils()
es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])


def search_for_doctors(query):
    query_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["user_name^2", "full_name^2", "institution", "profession"],
                "fuzziness": "AUTO",
                "type": "best_fields"
            }
        }
    }
    res = es.search(index=constants.DOCTOR_INDEX, body=query_body)
    return res['hits']['hits']


def search_for_posts(query):
    with open(constants.SEARCH_QUERY_JSON) as file:
        query_body = json.load(file)
    for i, _ in enumerate(query_body["query"]["bool"]["should"]):
        query_body["query"]["bool"]["should"][i]["multi_match"]["query"] = query
    res = es.search(index=constants.POST_INDEX, body=query_body)
    return res['hits']['hits']


def search(request):
    query = request.GET.get('q')
    res, _ = smfhcp_utils.find_user(request.session['user_name'], es)
    doctor_hits = search_for_doctors(query)
    context = {
        "doctors": [],
        "posts": [],
        "search_query": query
    }
    search_hits = False
    for hit in doctor_hits:
        search_hits = True
        if "profile_picture" in hit['_source'] and hit['_source']['profile_picture'] != "":
            hit['_source']['profile_picture'] = '/static/images/profiles/{}'.format(hit['_source']['profile_picture'])
        else:
            hit['_source']['profile_picture'] = '/static/images/profiles/default.jpg'
        context["doctors"].append(hit['_source'])
    post_hits = search_for_posts(query)
    for hit in post_hits:
        search_hits = True
        dt = smfhcp_utils.create_time_from_utc_string(hit['_source']['date'])
        hit['_source']['date'] = smfhcp_utils.pretty_date(dt)
        hit['_source']['id'] = hit['_id']
        if hit['_source']['user_name'] in res['follow_list']:
            hit['_source']['isFollowing'] = True
        else:
            hit['_source']['isFollowing'] = False
        context["posts"].append(hit['_source'])
    context["hits"] = search_hits
    return render(request, constants.SEARCH_HTML_PATH, context)


def search_for_tags(tag):
    # Query is NOT fuzzy because we want to find posts tagged with exactly same tag
    query = {
        "query": {
           "term": {
                "tags.keyword": {
                    "value": tag
                }
            }
        }
    }
    return es.search(index=constants.POST_INDEX, body=query)['hits']['hits']


def tagged(request, tag):
    if 'is_authenticated' in request.session and request.session['is_authenticated']:
        res, _ = smfhcp_utils.find_user(request.session['user_name'], es)
        context = {
            "did_find_any": False,
            "posts": [],
            "tag_searched": tag
        }
        post_hits = search_for_tags(tag)
        for hit in post_hits:
            context['did_find_any'] = True
            dt = smfhcp_utils.create_time_from_utc_string(hit['_source']['date'])
            hit['_source']['date'] = smfhcp_utils.pretty_date(dt)
            hit['_source']['id'] = hit['_id']
            if hit['_source']['user_name'] in res['follow_list']:
                hit['_source']['isFollowing'] = True
            else:
                hit['_source']['isFollowing'] = False
            context["posts"].append(hit['_source'])
        return render(request, constants.TAGGED_HTML_PATH, context)
    else:
        return redirect('/')
