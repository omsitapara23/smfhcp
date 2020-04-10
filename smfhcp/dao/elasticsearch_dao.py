import elasticsearch
from django.conf import settings
import smfhcp.constants as constants
import smfhcp.utils.utils as utils
from smfhcp.esmapper.esmapper import ElasticsearchMapper
import json


class ElasticsearchDao:
    es = elasticsearch.Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])
    smfhcp_utils = utils.SmfhcpUtils()
    es_mapper = ElasticsearchMapper()

    def get_general_user_by_user_name(self, user_name):
        return self.es.get(index=constants.GENERAL_USER_INDEX, id=user_name)

    def get_doctor_by_user_name(self, user_name):
        return self.es.get(index=constants.DOCTOR_INDEX, id=user_name)

    def search_posts_by_doctor_name(self, doctor_name):
        query_body = {
            "query": {
                "match": {
                    "user_name": doctor_name
                }
            }
        }
        return self.es.search(index=[constants.POST_INDEX], body=query_body)

    def get_all_posts(self):
        query_body = {
            "query": {
                "match_all": {}
            }
        }
        return self.es.search(index=[constants.POST_INDEX], body=query_body)

    def search_users_by_email(self, email_id):
        query_body = {
            "query": {
                "match": {
                    "email": email_id
                }
            }
        }
        return self.es.search(index=[constants.GENERAL_USER_INDEX, constants.DOCTOR_INDEX], body=query_body)

    def get_doctor_activation_by_email_id(self, email_id):
        return self.es.get(index=constants.DOCTOR_ACTIVATION_INDEX, id=email_id)

    def index_doctor_activation(self, email_id, token):
        body = self.es_mapper.map_doctor_activation(email_id, token)
        self.es.index(index=constants.DOCTOR_ACTIVATION_INDEX, id=email_id, body=body)

    def index_doctor(self, data, profile_picture):
        body = self.es_mapper.map_doctor(data, profile_picture)
        self.es.index(index=constants.DOCTOR_INDEX, id=body['user_name'], body=body)

    def index_general_user(self, body):
        self.es.index(index=constants.GENERAL_USER_INDEX, id=body['user_name'], body=body)

    def get_forgot_password_token_by_user_name(self, user_name):
        return self.es.get(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=user_name)

    def add_token_to_forgot_password_token_list(self, user_name, token):
        body = {
            "script": {
                "source": "ctx._source.token.add(params.new_token)",
                "lang": "painless",
                "params": {
                    "new_token": token
                }
            }
        }
        self.es.update(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=user_name, body=body)

    def index_forgot_password_token(self, user_name, token):
        body = self.es_mapper.map_forgot_password_token(user_name, token)
        self.es.index(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=user_name, body=body)

    def delete_forgot_password_token(self, user_name):
        self.es.delete(index=constants.FORGOT_PASSWORD_TOKEN_INDEX, id=user_name)

    def update_password_by_user_name(self, user_name, new_password, is_doctor):
        body = {
            "script": {
                "source": "ctx._source.password_hash = params.new_password;",
                "lang": "painless",
                "params": {
                    "new_password": self.smfhcp_utils.find_hash(new_password)
                }
            }
        }
        if is_doctor:
            self.es.update(index=constants.DOCTOR_INDEX, id=user_name, body=body)
        else:
            self.es.update(index=constants.GENERAL_USER_INDEX, id=user_name, body=body)

    def index_post(self, user_name, user_info, data, post_type_case_study):
        body = self.es_mapper.map_post(user_name, user_info, data, post_type_case_study)
        return self.es.index(index=constants.POST_INDEX, body=body)

    def get_post_by_id(self, post_id):
        return self.es.get(index=constants.POST_INDEX, id=post_id)

    def update_post_count(self, user_name):
        body = {
            "script": {
                "source": "ctx._source.post_count += params.count",
                "lang": "painless",
                "params": {
                    "count": 1
                }
            }
        }
        self.es.update(index=constants.DOCTOR_INDEX, id=user_name, body=body)

    def update_post_view_count(self, post_id):
        body = {
            "script": {
                "source": "ctx._source.view_count += params.count",
                "lang": "painless",
                "params": {
                    "count": 1
                }
            }
        }
        self.es.update(index=constants.POST_INDEX, id=post_id, body=body)

    def add_comment_by_post_id(self, post_id, comment):
        body = {
            "script": {
                "source": "ctx._source.comments.add(params.new_comment)",
                "lang": "painless",
                "params": {
                    "new_comment": comment
                }
            }
        }
        self.es.update(index=constants.POST_INDEX, id=post_id, body=body)

    def add_reply_by_post_id_and_comment_id(self, post_id, comment_id, reply):
        body = {
            "script": {
                "source": "for(int i=0; i < ctx._source.comments.size(); i++){ if(ctx._source.comments[i].comment_id "
                          "== params.comment_id){ ctx._source.comments[i].replies.add(params.reply); } }",
                "lang": "painless",
                "params": {
                    "comment_id": comment_id,
                    "reply": reply
                }
            }
        }
        self.es.update(index=constants.POST_INDEX, id=post_id, body=body)

    def update_profile(self, user_name, data):
        inline_string = ""
        params = {}
        if data.get('password') is not None:
            inline_string += "ctx._source.password_hash = params.password_hash; "
            params['password_hash'] = str(self.smfhcp_utils.find_hash(data.get('password')))
        if len(json.loads(data.get('qualification'))['qualifications']) > 0:
            inline_string += "ctx._source.qualification.addAll(params.qualification); "
            params['qualification'] = [s.strip() for s in json.loads(data.get('qualification'))['qualifications']]
        if str(data.get('profession')) != '':
            inline_string += "ctx._source.profession = params.profession; "
            params['profession'] = str(data.get('profession'))
        if str(data.get('institution')) != '':
            inline_string += "ctx._source.institution = params.institution; "
            params['institution'] = str(data.get('institution'))
        if len(json.loads(data.get('researchInterests'))['researchInterests']) > 0:
            inline_string += "ctx._source.research_interests.addAll(params.research_interests); "
            params['research_interests'] = [s.strip() for s in
                                            json.loads(data.get('researchInterests'))['researchInterests']]
        if len(json.loads(data.get('clinicalInterests'))['clinicalInterests']) > 0:
            inline_string += "ctx._source.clinical_interests.addAll(params.clinical_interests); "
            params['clinical_interests'] = [s.strip() for s in
                                            json.loads(data.get('clinicalInterests'))['clinicalInterests']]
        body = {
            "script": {
                "inline": inline_string,
                "lang": "painless",
                "params": params
            }
        }
        self.es.update(index=constants.DOCTOR_INDEX, id=user_name, body=body)

    def update_follow_count(self, data):
        body = {
            "script": {
                "lang": "painless",
                "params": {
                    "count": 1
                }
            }
        }
        if data.get('follow') == "true":
            body['script']['source'] = "ctx._source.follower_count += params.count"
        else:
            body['script']['source'] = "if(ctx._source.follower_count > 0) {ctx._source.follower_count -= params.count}"
        self.es.update(index=constants.DOCTOR_INDEX, id=data.get('doctor_name'), body=body)

    def add_to_follow_list(self, user_name, doctor_user_name, is_doctor):
        body = {
            "script": {
                "inline": "ctx._source.follow_list.add(params.doctor_user_name);",
                "lang": "painless",
                "params": {
                    "doctor_user_name": doctor_user_name
                }
            }
        }
        if is_doctor:
            self.es.update(index=constants.DOCTOR_INDEX, id=user_name, body=body)
        else:
            self.es.update(index=constants.GENERAL_USER_INDEX, id=user_name, body=body)

    def remove_from_follow_list(self, user_name, doctor_user_name, is_doctor):
        body = {
            "script": {
                "source": "ctx._source.follow_list.remove(ctx._source.follow_list.indexOf(params.doctor_user_name))",
                "lang": "painless",
                "params": {
                    "doctor_user_name": doctor_user_name
                }
            }
        }
        if is_doctor:
            self.es.update(index=constants.DOCTOR_INDEX, id=user_name, body=body)
        else:
            self.es.update(index=constants.GENERAL_USER_INDEX, id=user_name, body=body)

    def search_for_doctors(self, query):
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
        return self.es.search(index=constants.DOCTOR_INDEX, body=query_body)

    def search_for_posts(self, query):
        with open(constants.SEARCH_QUERY_JSON) as file:
            query_body = json.load(file)
        for i, _ in enumerate(query_body["query"]["bool"]["should"]):
            query_body["query"]["bool"]["should"][i]["multi_match"]["query"] = query
        return self.es.search(index=constants.POST_INDEX, body=query_body)

    def search_for_tags(self, tag):
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
        return self.es.search(index=constants.POST_INDEX, body=query)
