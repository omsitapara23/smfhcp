from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from django.contrib.auth import logout as logout_user
import elasticsearch
from elasticsearch import Elasticsearch
import hashlib
from django.core.mail import send_mail
from django.conf import settings
from random import randint
import json
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib import messages

es = Elasticsearch(hosts=['192.168.116.82'])


def random_with_n_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)


def base_view(request):
    return render(request, 'smfhcp/home.html')


def handler404(request, exception):
    return render(request, 'smfhcp/404.html', status=404)


def handler500(request):
    return render(request, 'smfhcp/500.html', status=500)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    request.session['user_name'] = request.user.username
    request.session['email'] = request.user.email
    request.session['is_authenticated'] = True
    request.session['is_doctor'] = False
    body = {
        "user_name": request.user.username,
        "email": request.user.email
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
        res = es.search(index=['general-user', 'doctor'], body=query_body)
        if res['hits']['total']['value'] > 0:
            return False
        try:
            es.get(index='general-user', id=body['user_name'])
        except elasticsearch.NotFoundError:
            try:
                res_doctor = es.get(index=['doctor'], id=body['user_name'])
            except elasticsearch.NotFoundError:
                es.index(index='general-user', id=body['user_name'], body=body)
                return True
            return False
        return False
    else:
        es.index(index='general-user', id=body['user_name'], body=body)


def find_user(user_name):
    try:
        res_user = es.get(index=['general-user'], id=user_name)
        return res_user['_source'], False
    except elasticsearch.NotFoundError:
        try:
            res_doctor = es.get(index=['doctor'], id=user_name)
            return res_doctor['_source'], True
        except elasticsearch.NotFoundError:
            return None, None


def find_hash(input):
    return hashlib.sha256(str(input).encode('utf-8')).hexdigest()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_email(request):
    if request.method == 'POST':
        data = request.POST.copy()
        body = {
            "user_name": data.get('user_name'),
            "email": data.get('email'),
            "password_hash": find_hash(data.get('password'))
        }
        if index_user(body) is False:
            response_data = {
                "message": 'User name or email already exists.'
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
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
            content_type="application/json"
        )
    else:
        raise PermissionDenied()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_user(request):
    if request.method == 'POST':
        data = request.POST.copy()
        res, is_doctor = find_user(data.get('user_name'))
        if res is not None and find_hash(data.get('password')) == res['password_hash']:
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
                content_type="application/json"
            )
        else:
            response_data = {
                "message": 'Username/Password does not match.'
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
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
    res = es.search(index=['general-user', 'doctor'], body=query_body)
    if res['hits']['total']['value'] > 0:
        return False, "User already exists."
    try:
        es.get(index='doctor-activation', id=email_id)
        return False, "User already invited."
    except elasticsearch.NotFoundError:
        return True, "Sent Invite"


def send_invitation_email(receiver_email, token):
    subject = "Invitation to join SMFHCP as a Health care Professional"
    message = "Please open this link http://127.0.0.1:8000/doctor_signup/{} to join SMFHCP.\n".format(token)
    try:
        send_mail(subject, from_email=settings.EMAIL_HOST_USER,
                  recipient_list=[receiver_email], message=message, fail_silently=False)
        return True
    except Exception:
        print("Error in sending mail")
        return False


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def send_invite(request):
    email_id = request.POST.get('email')
    token = random_with_n_digits(6)
    print(token)
    valid, message = check_email_existence(email_id)
    if valid is True:
        res = send_invitation_email(email_id, token)
        if res is True:
            body = {
                "email": email_id,
                "token": token
            }
            es.index(index='doctor-activation', id=email_id, body=body)
            response_data = {
                "message": 'Invitation sent successfully.',
                "success": True
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )
        else:
            response_data = {
                "message": 'Could not send email.',
                "success": False
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )
    else:
        response_data = {
            "message": message,
            "success": False
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json"
        )


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def doctor_signup(request, otp):
    print(otp)
    if "is_authenticated" not in request.session or request.session['is_authenticated'] is False:
        messages.info(request, otp)
    return render(request, 'smfhcp/doctor_create_profile.html')


def index_doctor(request, res, data):
    request.session['user_name'] = data.get('user_name')
    request.session['email'] = data.get('email')
    request.session['is_authenticated'] = True
    request.session['is_doctor'] = True
    body = {
        "user_name": data.get('user_name'),
        "email": data.get('email'),
        "password_hash": find_hash(data.get('password')),
        "full_name": data.get('firstName') + ' ' + data.get('lastName'),
        "qualification": [s.strip() for s in json.loads(data.get('qualification'))['qualifications']],
        "research_interests": [s.strip() for s in json.loads(data.get('researchInterests'))['researchInterests']],
        "profession": data.get('profession'),
        "institution": data.get('institution'),
        "clinical_interests": [s.strip() for s in json.loads(data.get('clinicalInterests'))['clinicalInterests']]
    }
    es.index(index='doctor', id=body['user_name'], body=body)


def create_profile(request):
    if request.method == 'POST':
        data = request.POST.copy()
        res, _ = find_user(data.get('user_name'))
        if res is None:
            try:
                res = es.get(index='doctor-activation', id=data.get('email'))
                if str(res['_source']['token']) == str(data.get('otp')):
                    index_doctor(request, res, data)
                    response_data = {
                        "redirect": True,
                        "redirect_url": "/"
                    }
                    return HttpResponse(
                        json.dumps(response_data),
                        content_type="application/json"
                    )
                else:
                    response_data = {
                        "message": 'OTP, email pair do not match.'
                    }
                    return HttpResponse(
                        json.dumps(response_data),
                        content_type="application/json"
                    )
            except elasticsearch.NotFoundError:
                response_data = {
                    "message": 'This email id does not have an invite.'
                }
                return HttpResponse(
                    json.dumps(response_data),
                    content_type="application/json"
                )
        else:
            response_data = {
                "message": 'Username already exists.'
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )
    else:
        raise PermissionDenied()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_profile(request, user_name):
    res_doctor = es.get(index=['doctor'], id=user_name)
    print(res_doctor)
    context = {
        'user_name': res_doctor['_source']['user_name'],
        'full_name': res_doctor['_source']['full_name'],
        'email': res_doctor['_source']['email'],
        'qualification': res_doctor['_source']['qualification'],
        'research_interests': res_doctor['_source']['research_interests'],
        'profession': res_doctor['_source']['profession'],
        'institution': res_doctor['_source']['institution'],
        'clinical_interests': res_doctor['_source']['clinical_interests']
    }
    return render(request, 'smfhcp/view_profile.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_profile(request):
    print(request.POST.get('password'))
    # find the fields from the post request
    # update in database
    # send the relevant error messages
    # else redirect to /view_profile/{user_name}
    return redirect('/view_profile/' + str(request.session['user_name']))


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):
    logout_user(request)
    request.session['user_name'] = None
    request.session['email'] = None
    request.session['is_authenticated'] = False
    request.session['is_doctor'] = None
    request.session.modified = True
    return redirect('/')
