from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from django.contrib.auth import logout as logout_user
import elasticsearch
from elasticsearch import Elasticsearch
from uuid import uuid4
import hashlib
from django.core.mail import send_mail
from django.conf import settings
from random import randint

es = Elasticsearch(hosts=['192.168.116.82'])


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)


def base_view(request):
    return render(request, 'smfhcp/home.html')


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
            return None


def find_hash(input):
    return hashlib.sha256(str(input).encode('utf-8')).hexdigest()


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_email(request):
    data = request.POST.copy()
    body = {
        "user_name": data.get('user_name'),
        "email": data.get('email'),
        "password_hash": find_hash(data.get('password'))
    }
    if index_user(body) is False:
        return render(request, 'registrations/retry_signup.html')
    request.session['user_name'] = data.get('user_name')
    request.session['email'] = data.get('email')
    request.session['is_authenticated'] = True
    request.session['is_doctor'] = False
    return redirect('/')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_user(request):
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
        return redirect('/')
    else:
        return render(request, 'registrations/retry_signup.html')


def index_with_token(token, email_id):
    query_body = {
            "query": {
                "match": {
                    "email": email_id
                }
            }
        }
    res = es.search(index=['general-user', 'doctor'], body=query_body)
    if res['hits']['total']['value'] > 0:
        return False, "User already exists"
    try:
        es.get(index='doctor-activation', id=email_id)
        return False, "User already invited"
    except elasticsearch.NotFoundError:
        return True, "Sent Invite"


def send_invitation_email(receiver_email, token):
    subject = "Invitation to join SMFHCP as a Health care Professional"
    message = "Please open this link http://127.0.0.1:8000/doctor_signup to join SMFHCP.\n Please enter this OTP {} while signing up.".format(token)
    try:
        send_mail(subject, from_email=settings.EMAIL_HOST_USER, recipient_list=[receiver_email], message=message, fail_silently=False)
        return True
    except Exception:
        print("Error in sending mail")
        return False


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def send_invite(request):
    data = request.POST.copy()
    email_id = data.get('email_send_invite')
    token = random_with_N_digits(6)
    print(token)
    valid, message = index_with_token(token, email_id)
    if valid is True:
        res = send_invitation_email(email_id, token)
        if res is True:
            body = {
                "email": email_id,
                "token": token
            }
            #es.index(index='doctor-activation', id=email_id, body=body)
        return redirect('/')
    else:
        pass


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):
    logout_user(request)
    request.session['user_name'] = None
    request.session['email'] = None
    request.session['is_authenticated'] = False
    request.session['is_doctor'] = None
    request.session.modified = True
    return redirect('/')
