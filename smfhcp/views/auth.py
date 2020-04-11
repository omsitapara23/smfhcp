from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from django.contrib.auth import logout as logout_user
import elasticsearch
from django.core.mail import send_mail
from smtplib import SMTPException
from django.conf import settings
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
import smfhcp.utils.utils as utils
import smfhcp.constants as constants
from smfhcp.dao.elasticsearch_dao import ElasticsearchDao
from smfhcp.esmapper.esmapper import ElasticsearchMapper

smfhcp_utils = utils.SmfhcpUtils()
es_dao = ElasticsearchDao()
es_mapper = ElasticsearchMapper()


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
        es_dao.get_general_user_by_user_name(request.user.username)
    except elasticsearch.NotFoundError:
        body = es_mapper.map_general_user(request.user.username, request.user.email)
        index_general_user(body)
    return redirect('/')


def index_general_user(body):
    if 'password_hash' in body:
        res = es_dao.search_users_by_email(body['email'])
        if res['hits']['total']['value'] > 0:
            return False
        try:
            es_dao.get_general_user_by_user_name(body['user_name'])
        except elasticsearch.NotFoundError:
            try:
                es_dao.get_doctor_by_user_name(body['user_name'])
            except elasticsearch.NotFoundError:
                es_dao.index_general_user(body)
                return True
            return False
        return False
    else:
        es_dao.index_general_user(body)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_email(request):
    if request.method == 'POST':
        data = request.POST.copy()
        body = es_mapper.map_general_user(data.get('user_name'), data.get('email'), password=data.get('password'))
        if index_general_user(body) is False:
            response_data = {
                "message": constants.USER_OR_EMAIL_ALREADY_EXISTS_MESSAGE
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
        res, is_doctor = smfhcp_utils.find_user(data.get('user_name'), es_dao)
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
                "message": constants.USERNAME_AND_PASSWORD_DO_NOT_MATCH
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
    else:
        raise PermissionDenied()


def check_email_existence(email_id):
    res = es_dao.search_users_by_email(email_id)
    if res['hits']['total']['value'] > 0:
        return False, constants.USER_ALREADY_EXISTS
    try:
        _ = es_dao.get_doctor_activation_by_email_id(email_id)
        return False, constants.USER_ALREADY_INVITED
    except elasticsearch.NotFoundError:
        return True, constants.SENT_INVITE


def send_invitation_email(receiver_email, token):
    subject = constants.INVITE_EMAIL_SUBJECT
    message = render_to_string(constants.REGISTER_THROUGH_EMAIL_HTML_PATH, {
        'username': str(receiver_email).split('@')[0],
        'otp': token,
        'server_address': '127.0.0.1:8000'
    })
    try:
        send_mail(subject, from_email=settings.EMAIL_HOST_USER,
                  recipient_list=[receiver_email], html_message=message, fail_silently=False, message="")
        return True
    except SMTPException:
        return False


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def send_invite(request):
    email_id = request.POST.get('email')
    token = smfhcp_utils.random_with_n_digits(6)
    valid, message = check_email_existence(email_id)
    if valid is True:
        res = send_invitation_email(email_id, token)
        if res is True:
            es_dao.index_doctor_activation(email_id, token)
            response_data = {
                "message": constants.INVITATION_SENT_SUCCESSFULLY,
                "success": True
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
        else:
            response_data = {
                "message": constants.COULD_NOT_SEND_EMAIL,
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
    context = {}
    if "is_authenticated" not in request.session or request.session['is_authenticated'] is False:
        context['info'] = otp
    return render(request, constants.DOCTOR_CREATE_PROFILE_HTML_PATH, context)


def save_profile_picture(request):
    for key, file in request.FILES.items():
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


def index_doctor(request, data, profile_picture):
    request.session['user_name'] = data.get('user_name')
    request.session['email'] = data.get('email')
    request.session['is_authenticated'] = True
    request.session['is_doctor'] = True
    es_dao.index_doctor(data, profile_picture)


def create_profile(request):
    if request.method == 'POST':
        data = request.POST.copy()
        res, _ = smfhcp_utils.find_user(data.get('user_name'), es_dao)
        if res is None:
            try:
                res = es_dao.get_doctor_activation_by_email_id(data.get('email'))
                if str(res['_source']['token']) == str(data.get('otp')):
                    profile_picture = save_profile_picture(request)
                    index_doctor(request, data, profile_picture)
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
                        "message": constants.OTP_EMAIL_PAIR_DOES_NOT_MATCH
                    }
                    return HttpResponse(
                        json.dumps(response_data),
                        content_type=constants.APPLICATION_JSON_TYPE
                    )
            except elasticsearch.NotFoundError:
                response_data = {
                    "message": constants.EMAIL_DOES_NOT_HAVE_INVITE
                }
                return HttpResponse(
                    json.dumps(response_data),
                    content_type=constants.APPLICATION_JSON_TYPE
                )
        else:
            response_data = {
                "message": constants.USERNAME_ALREADY_EXISTS
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
    return redirect('/')
