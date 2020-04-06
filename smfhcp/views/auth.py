from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from django.contrib.auth import logout as logout_user
import elasticsearch
from elasticsearch import Elasticsearch
from django.core.mail import send_mail
from django.conf import settings
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.template.loader import render_to_string
import smfhcp.utils.utils as utils
import smfhcp.constants as constants

smfhcp_utils = utils.SmfhcpUtils()
es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_view(request):
    if 'is_authenticated' in request.session and request.session['is_authenticated']:
        return redirect('/')
    else:
        return render(request, constants.LOGIN_HTML_PATH)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    request.session['user_name'] = request.user.username
    request.session['email'] = request.user.email
    request.session['is_authenticated'] = True
    request.session['is_doctor'] = False
    try:
        es.get(index=constants.GENERAL_USER_INDEX, id=request.user.username)
    except elasticsearch.NotFoundError:
        body = {
            "user_name": request.user.username,
            "email": request.user.email,
            "follow_list": []
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
        res = es.search(index=[constants.GENERAL_USER_INDEX, constants.DOCTOR_INDEX], body=query_body)
        if res['hits']['total']['value'] > 0:
            return False
        try:
            es.get(index=constants.GENERAL_USER_INDEX, id=body['user_name'])
        except elasticsearch.NotFoundError:
            try:
                es.get(index=[constants.DOCTOR_INDEX], id=body['user_name'])
            except elasticsearch.NotFoundError:
                es.index(index=constants.GENERAL_USER_INDEX, id=body['user_name'], body=body)
                return True
            return False
        return False
    else:
        es.index(index=constants.GENERAL_USER_INDEX, id=body['user_name'], body=body)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_email(request):
    if request.method == 'POST':
        data = request.POST.copy()
        body = {
            "user_name": data.get('user_name'),
            "email": data.get('email'),
            "password_hash": smfhcp_utils.find_hash(data.get('password')),
            "follow_list": []
        }
        if index_user(body) is False:
            response_data = {
                "message": 'User name or email already exists.'
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
        request.session['user_name'] = data.get('user_name')
        request.session['email'] = data.get('email')
        request.session['is_authenticated'] = True
        request.session['is_doctor'] = False
        response_data = {
            "redirect": True,
            "redirect_url": "/"
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type=constants.APPLICATION_JSON_TYPE
        )
    else:
        raise PermissionDenied()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_user(request):
    if request.method == 'POST':
        data = request.POST.copy()
        res, is_doctor = smfhcp_utils.find_user(data.get('user_name'), es)
        if res is not None and smfhcp_utils.find_hash(data.get('password')) == res['password_hash']:
            request.session['user_name'] = res['user_name']
            request.session['email'] = res['email']
            request.session['is_authenticated'] = True
            if is_doctor is True:
                request.session['is_doctor'] = True
            else:
                request.session['is_doctor'] = False
            response_data = {
                "redirect": True,
                "redirect_url": "/"
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
        else:
            response_data = {
                "message": 'Username/Password does not match.'
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
    else:
        raise PermissionDenied()


def check_email_existence(email_id):
    query_body = {
        "query": {
            "match": {
                "email": email_id
            }
        }
    }
    res = es.search(index=[constants.GENERAL_USER_INDEX, constants.DOCTOR_INDEX], body=query_body)
    if res['hits']['total']['value'] > 0:
        return False, "User already exists."
    try:
        es.get(index=constants.DOCTOR_ACTIVATION_INDEX, id=email_id)
        return False, "User already invited."
    except elasticsearch.NotFoundError:
        return True, "Sent Invite"


def send_invitation_email(receiver_email, token):
    subject = "Invitation to join SMFHCP as a Health care Professional"
    message = render_to_string(constants.REGISTER_THROUGH_EMAIL_HTML_PATH, {
        'username': str(receiver_email).split('@')[0],
        'otp': token,
        'server_address': '127.0.0.1:8000'
    })
    try:
        send_mail(subject, from_email=settings.EMAIL_HOST_USER,
                  recipient_list=[receiver_email], html_message=message, fail_silently=False, message="")
        return True
    except Exception:
        print("Error in sending mail")
        return False


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def send_invite(request):
    email_id = request.POST.get('email')
    token = smfhcp_utils.random_with_n_digits(6)
    print(token)
    valid, message = check_email_existence(email_id)
    if valid is True:
        res = send_invitation_email(email_id, token)
        if res is True:
            body = {
                "email": email_id,
                "token": token
            }
            es.index(index=constants.DOCTOR_ACTIVATION_INDEX, id=email_id, body=body)
            response_data = {
                "message": 'Invitation sent successfully.',
                "success": True
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
        else:
            response_data = {
                "message": 'Could not send email.',
                "success": False
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
    else:
        response_data = {
            "message": message,
            "success": False
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type=constants.APPLICATION_JSON_TYPE
        )


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def doctor_signup(request, otp):
    print(otp)
    if "is_authenticated" not in request.session or request.session['is_authenticated'] is False:
        messages.info(request, otp)
    return render(request, constants.DOCTOR_CREATE_PROFILE_HTML_PATH)


def save_profile_picture(request):
    for key, file in request.FILES.items():
        print('here')
        file_type = str(file.name).split('.')[-1]
        name = request.POST.get('user_name')
        if key == 'profilePicture':
            import os
            file_path = os.path.join(os.path.dirname(__file__), 'static/images/profiles/{}.{}'.format(name, file_type))
            dest = open(file_path, 'wb')
            if file.multiple_chunks:
                for c in file.chunks():
                    dest.write(c)
            else:
                dest.write(file.read())
            dest.close()
            return '{}.{}'.format(name, file_type)


def index_doctor(request, res, data, profile_picture):
    request.session['user_name'] = data.get('user_name')
    request.session['email'] = data.get('email')
    request.session['is_authenticated'] = True
    request.session['is_doctor'] = True
    body = {
        "user_name": data.get('user_name'),
        "email": data.get('email'),
        "password_hash": smfhcp_utils.find_hash(data.get('password')),
        "full_name": data.get('firstName') + ' ' + data.get('lastName'),
        "qualification": [s.strip() for s in json.loads(data.get('qualification'))['qualifications']],
        "research_interests": [s.strip() for s in json.loads(data.get('researchInterests'))['researchInterests']],
        "profession": data.get('profession'),
        "institution": data.get('institution'),
        "clinical_interests": [s.strip() for s in json.loads(data.get('clinicalInterests'))['clinicalInterests']],
        "follow_list": [],
        "follower_count": 0,
        "post_count": 0,
        "posts": [],
        "profile_picture": profile_picture
    }
    es.index(index=constants.DOCTOR_INDEX, id=body['user_name'], body=body)


def create_profile(request):
    if request.method == 'POST':
        data = request.POST.copy()
        res, _ = smfhcp_utils.find_user(data.get('user_name'), es)
        if res is None:
            try:
                res = es.get(index=constants.DOCTOR_ACTIVATION_INDEX, id=data.get('email'))
                if str(res['_source']['token']) == str(data.get('otp')):
                    profile_picture = save_profile_picture(request)
                    index_doctor(request, res, data, profile_picture)
                    response_data = {
                        "redirect": True,
                        "redirect_url": "/"
                    }
                    return HttpResponse(
                        json.dumps(response_data),
                        content_type=constants.APPLICATION_JSON_TYPE
                    )
                else:
                    response_data = {
                        "message": 'OTP, email pair do not match.'
                    }
                    return HttpResponse(
                        json.dumps(response_data),
                        content_type=constants.APPLICATION_JSON_TYPE
                    )
            except elasticsearch.NotFoundError:
                response_data = {
                    "message": 'This email id does not have an invite.'
                }
                return HttpResponse(
                    json.dumps(response_data),
                    content_type=constants.APPLICATION_JSON_TYPE
                )
        else:
            response_data = {
                "message": 'Username already exists.'
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
    else:
        raise PermissionDenied()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):
    logout_user(request)
    request.session['user_name'] = None
    request.session['email'] = None
    request.session['is_authenticated'] = False
    request.session['is_doctor'] = None
    request.session.modified = True
    return redirect('/')
