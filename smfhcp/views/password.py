from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
import elasticsearch
from elasticsearch import Elasticsearch
from django.core.mail import send_mail
from django.conf import settings
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
import smfhcp.utils.utils as utils
from smfhcp.views.base import handler404
import smfhcp.constants as constants

smfhcp_utils = utils.SmfhcpUtils()
es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])


def send_password_reset_email(res, token):
    subject = "Password reset request for SMFHCP"
    message = render_to_string(constants.RESET_PASSWORD_EMAIL_HTML_PATH, {
        'username': res['user_name'],
        'otp': token,
        'server_address': '127.0.0.1:8000'
    })
    try:
        send_mail(subject, from_email=settings.EMAIL_HOST_USER,
                  recipient_list=[res['email']], html_message=message, fail_silently=False, message="")

        return True
    except Exception:
        print("Error in sending mail")
        return False


def forgot_password(request):
    if request.method == 'POST':
        res, _ = smfhcp_utils.find_user(request.POST.get('user_name'), es)
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
                _ = es.get(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=request.POST.get("user_name"))
                body = {
                    "script": {
                        "source": "ctx._source.token.add(params.new_token)",
                        "lang": "painless",
                        "params": {
                            "new_token": token
                        }
                    }
                }
                es.update(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=request.POST.get('user_name'), body=body)
                send_password_reset_email(res, token)
            except elasticsearch.NotFoundError:
                body = {
                    "user_name": request.POST.get('user_name'),
                    "token": [token]
                }
                es.index(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=request.POST.get('user_name'), body=body)
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
            res = es.get(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=user_name)
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
        _ = es.delete(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=user_name)
        body = {
            "script": {
                "source": "ctx._source.password_hash = params.new_password;",
                "lang": "painless",
                "params": {
                    "new_password": smfhcp_utils.find_hash(request.POST.get("new_password"))
                }
            }
        }
        res, is_doctor = smfhcp_utils.find_user(user_name, es)
        if is_doctor:
            request.session['is_doctor'] = True
            es.update(index=constants.DOCTOR_INDEX, id=user_name, body=body)
        else:
            request.session['is_doctor'] = False
            es.update(index=constants.GENERAL_USER_INDEX, id=user_name, body=body)
        request.session['user_name'] = user_name
        request.session['email'] = res['email']
        request.session['is_authenticated'] = True
        return redirect('/')
