from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
import elasticsearch
from django.core.mail import send_mail
from smtplib import SMTPException
from django.conf import settings
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
import smfhcp.utils.utils as utils
from smfhcp.views.base import handler404
import smfhcp.constants as constants
from smfhcp.dao.elasticsearch_dao import ElasticsearchDao

smfhcp_utils = utils.SmfhcpUtils()
es_dao = ElasticsearchDao()


def send_password_reset_email(res, token):
    subject = constants.PASSWORD_RESET_REQUEST_SUBJECT
    message = render_to_string(constants.RESET_PASSWORD_EMAIL_HTML_PATH, {
        'username': res['user_name'],
        'otp': token,
        'server_address': '127.0.0.1:8000'
    })
    try:
        send_mail(subject, from_email=settings.EMAIL_HOST_USER,
                  recipient_list=[res['email']], html_message=message, fail_silently=False, message="")

        return True
    except SMTPException:
        return False


def forgot_password(request):
    if request.method == 'POST':
        res, _ = smfhcp_utils.find_user(request.POST.get('user_name'), es_dao)
        if res is not None:
            if 'password_hash' not in res:
                response_data = {
                    "message": 'User has signed up through a third-party service.',
                    "success": False
                }
                return HttpResponse(
                    json.dumps(response_data),
                    content_type=constants.APPLICATION_JSON_TYPE
                )
            from django.utils.crypto import get_random_string
            token = get_random_string(length=16)
            try:
                es_dao.get_forgot_password_token_by_user_name(request.POST.get("user_name"))
                es_dao.add_token_to_forgot_password_token_list(request.POST.get('user_name'), token)
                send_password_reset_email(res, token)
            except elasticsearch.NotFoundError:
                es_dao.index_forgot_password_token(request.POST.get('user_name'), token)
                send_password_reset_email(res, token)
            response_data = {
                "message": 'A password reset conformation mail has been sent to {}'.format(res['email']),
                "success": True
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
        else:
            response_data = {
                "message": 'User does not exist',
                "success": False
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type=constants.APPLICATION_JSON_TYPE
            )
    else:
        raise PermissionDenied()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def reset_password(request, user_name, otp):
    if request.method == 'GET':
        try:
            res = es_dao.get_forgot_password_token_by_user_name(user_name)
            if otp in res['_source']['token']:
                return render(request, constants.RESET_PASSWORD_HTML_PATH, {
                    'user_name': user_name,
                    'otp': otp
                })
            else:
                return handler404(request, None)
        except elasticsearch.NotFoundError:
            return handler404(request, None)
    elif request.method == 'POST':
        es_dao.delete_forgot_password_token(user_name)
        res, is_doctor = smfhcp_utils.find_user(user_name, es_dao)
        if is_doctor:
            request.session['is_doctor'] = True
            es_dao.update_password_by_user_name(user_name, request.POST.get("new_password"), True)
        else:
            request.session['is_doctor'] = False
            es_dao.update_password_by_user_name(user_name, request.POST.get("new_password"), False)
        request.session['user_name'] = user_name
        request.session['email'] = res['email']
        request.session['is_authenticated'] = True
        return redirect('/')
    else:
        raise PermissionDenied()
