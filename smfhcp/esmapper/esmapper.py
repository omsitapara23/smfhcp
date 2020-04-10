from smfhcp.utils.utils import SmfhcpUtils
import json
import datetime


class ElasticsearchMapper:
    smfhcp_utils = SmfhcpUtils()

    def map_doctor(self, data, profile_picture):
        return {
            "user_name": data.get('user_name'),
            "email": data.get('email'),
            "password_hash": self.smfhcp_utils.find_hash(data.get('password')),
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

    def map_doctor_activation(self, email_id, token):
        return {
            "email": email_id,
            "token": token
        }

    def map_forgot_password_token(self, user_name, token):
        return {
            "user_name": user_name,
            "token": [token]
        }

    def map_general_user(self, user_name, email, password=None):
        if password is not None:
            return {
                "user_name": user_name,
                "email": email,
                "password_hash": self.smfhcp_utils.find_hash(password),
                "follow_list": []
            }
        else:
            return {
                "user_name": user_name,
                "email": email,
                "follow_list": []
            }

    def map_post(self, user_name, user_info, data, post_type_case_study):
        body = {
            "user_name": user_name,
            "full_name": user_info['full_name'],
            "profession": user_info['profession'],
            "institution": user_info['institution'],
            "view_count": 1,
            "title": data.get('title'),
            "tags": [str(s).strip() for s in json.loads(data.get('tags'))['tags']],
            "date": datetime.datetime.now(datetime.timezone.utc),
            "comments": []
        }
        import textile
        if post_type_case_study:
            body['history'] = textile.textile(data.get('history'))
            body['diagnosis'] = textile.textile(data.get('diagnosis'))
            body['examination'] = textile.textile(data.get('examination'))
            body['prevention'] = textile.textile(data.get('prevention'))
            body['treatment'] = textile.textile(data.get('treatment'))
            body['remarks'] = textile.textile(data.get('remarks'))
        else:
            body['description'] = textile.textile(data.get('description'))
        return body

    def map_comment(self, data, comment_id):
        return {
            "comment_body": data.get('comment_text'),
            "user_name": data.get('user_name'),
            "replies": [],
            "comment_id": comment_id,
            "date": datetime.datetime.now(datetime.timezone.utc)
        }

    def map_reply(self, data):
        return {
            "user_name": data.get('user_name'),
            "reply_body": data.get('reply_text'),
            "date": datetime.datetime.now(datetime.timezone.utc)
        }
