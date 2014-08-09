# -*- coding:utf-8 -*-
from __future__ import with_statement

from networkapi.log import Log
from networkapi.blockrules.models import Rule, BlockRules
from django.forms.models import model_to_dict
from networkapi.rest import RestResource, UserNotAuthorizedError
from networkapi.infrastructure.xml_utils import dumps_networkapi
from networkapi.ambiente.models import Ambiente
from networkapi.auth import has_perm
from networkapi.admin_permission import AdminPermission
from networkapi.exception import InvalidValueError
from networkapi.util import is_valid_int_greater_zero_param


class RuleGetResource(RestResource):

    """Treat requests GET to get Rules in Environment.

    URL: environment/rule/all/<id_environment>/
    """
    log = Log('RuleResource')

    def handle_get(self, request, user, *args, **kwargs):
        try:
            self.log.info("Get rules in Environment")

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.VIP_VALIDATION,
                    AdminPermission.WRITE_OPERATION):
                self.log.error(
                    u'User does not have permission to perform the operation.')
                raise UserNotAuthorizedError(None)

            id_env = kwargs.get('id_env')

            if not is_valid_int_greater_zero_param(id_env):
                self.log.error(
                    u'The id_env parameter is not a valid value: %s.',
                    id_env)
                raise InvalidValueError(None, 'id_env', id_env)

            Ambiente.objects.get(pk=id_env)
            rules = Rule.objects.filter(environment=id_env, vip=None)
            rule_list = []
            for rule in rules:
                rule_list.append(model_to_dict(rule))
            return self.response(dumps_networkapi({'rules': rule_list}))

        except InvalidValueError as e:
            self.log.error(
                u'Parameter %s is invalid. Value: %s.',
                e.param,
                e.value)
            return self.response_error(269, e.param, e.value)
        except UserNotAuthorizedError:
            return self.not_authorized()
        except Exception as e:
            self.log.error(e)
            return self.response_error(1)
