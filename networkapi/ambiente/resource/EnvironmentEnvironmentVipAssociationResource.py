# -*- coding:utf-8 -*-

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import with_statement
from networkapi.admin_permission import AdminPermission
from networkapi.auth import has_perm
from networkapi.exception import InvalidValueError, OptionVipNotFoundError, EnvironmentVipNotFoundError, OptionVipError, EnvironmentVipError, OptionVipEnvironmentVipError, OptionVipEnvironmentVipDuplicatedError, OptionVipEnvironmentVipNotFoundError, \
    EnvironmentEnvironmentVipNotFoundError, EnvironmentNotFoundError, EnvironmentEnvironmentVipDuplicatedError, \
    EnvironmentEnvironmentVipError, EnvironmentEnvironmentServerPoolRequestVipLinked
from networkapi.log import Log
from networkapi.requisicaovips.models import OptionVip, OptionVipEnvironmentVip, RequisicaoVips
from networkapi.rest import RestResource, UserNotAuthorizedError
from networkapi.util import is_valid_int_greater_zero_param
from networkapi.ambiente.models import EnvironmentVip, Ambiente, EnvironmentEnvironmentVip
from django.forms.models import model_to_dict
from networkapi.infrastructure.xml_utils import dumps_networkapi
from networkapi.distributedlock import distributedlock, LOCK_ENVIRONMENT_VIP


class EnvironmentEnvironmentVipAssociationResource(RestResource):

    log = Log('EnvironmentEnvironmentVipAssociationResource')

    def handle_put(self, request, user, *args, **kwargs):
        """
        Handles PUT requests to create a relationship of Environment with EnvironmentVip.

        URL: environment/<environment_id>/environmentvip/<environment_vip_id>/
        """

        self.log.info("Create a relationship of Environment with EnvironmentVip")

        try:

            # Commons Validations

            # User permission
            if not has_perm(user, AdminPermission.ENVIRONMENT_MANAGEMENT, AdminPermission.WRITE_OPERATION):
                self.log.error(u'User does not have permission to perform the operation.')
                raise UserNotAuthorizedError(None)

            # Valid Environment
            environment_id = kwargs.get('environment_id')
            if not is_valid_int_greater_zero_param(environment_id):
                self.log.error(u'The environment_id parameter is not a valid value: %s.', environment_id)
                raise InvalidValueError(None, 'environment_id', environment_id)

            # Valid EnvironmentVip ID
            environment_vip_id = kwargs.get('environment_vip_id')
            if not is_valid_int_greater_zero_param(environment_vip_id):
                self.log.error(u'The id_environment_vip parameter is not a valid value: %s.', environment_vip_id)
                raise InvalidValueError(None, 'environment_vip_id', environment_vip_id)

            # Business Validations

            # Existing Environment ID
            environment = Ambiente.get_by_pk(environment_id)

            # Existing EnvironmentVip ID
            environment_vip = EnvironmentVip.get_by_pk(environment_vip_id)

            with distributedlock(LOCK_ENVIRONMENT_VIP % environment_vip_id):

                # Business Rules

                # Set new values
                environment_environment_vip = EnvironmentEnvironmentVip()
                environment_environment_vip.environment = environment
                environment_environment_vip.environment_vip = environment_vip

                # Existing EnvironmentEnvironmentVip
                environment_environment_vip.validate()

                # Persist
                environment_environment_vip.save(user)

                # Return XML
                environment_environment_vip_map = {}
                environment_environment_vip_map['environment_environment_vip'] = model_to_dict(environment_environment_vip, fields=['id'])

                return self.response(dumps_networkapi(environment_environment_vip_map))

        except UserNotAuthorizedError:
            return self.not_authorized()
        except InvalidValueError, e:
            return self.response_error(269, e.param, e.value)
        except EnvironmentNotFoundError:
            return self.response_error(112)
        except EnvironmentVipNotFoundError:
            return self.response_error(283)
        except EnvironmentEnvironmentVipDuplicatedError:
            return self.response_error(392)
        except Exception, error:
            return self.response_error(1)

    def handle_delete(self, request, user, *args, **kwargs):
        """
        Handles DELETE requests to create a relationship of Environment with EnvironmentVip.

        URL: environment/<environment_id>/environmentvip/<environment_vip_id>/
        """

        self.log.info("Remove a relationship of Environment with EnvironmentVip")

        try:

            # Commons Validations

            # User permission
            if not has_perm(user, AdminPermission.ENVIRONMENT_MANAGEMENT, AdminPermission.WRITE_OPERATION):
                self.log.error(u'User does not have permission to perform the operation.')
                raise UserNotAuthorizedError(None)

            # Valid Environment
            environment_id = kwargs.get('environment_id')
            if not is_valid_int_greater_zero_param(environment_id):
                self.log.error(u'The environment_id parameter is not a valid value: %s.', environment_id)
                raise InvalidValueError(None, 'environment_id', environment_id)

            # Valid EnvironmentVip ID
            environment_vip_id = kwargs.get('environment_vip_id')
            if not is_valid_int_greater_zero_param(environment_vip_id):
                self.log.error(u'The id_environment_vip parameter is not a valid value: %s.', environment_vip_id)
                raise InvalidValueError(None, 'environment_vip_id', environment_vip_id)

            # Business Validations

            # Existing Environment ID
            environment = Ambiente.get_by_pk(environment_id)

            # Existing EnvironmentVip ID
            environment_vip = EnvironmentVip.get_by_pk(environment_vip_id)

            # Business Rules

            # Find
            environment_environment_vip = EnvironmentEnvironmentVip().get_by_environment_environment_vip(environment.id, environment_vip.id)

            request_vip_list = RequisicaoVips.get_vip_request_is_related_with_server_pool(environment_environment_vip)

            if request_vip_list:
                cause = self._get_cause(environment, request_vip_list)
                raise EnvironmentEnvironmentServerPoolRequestVipLinked(cause)

            # Delete
            environment_environment_vip.delete(user)

            # Return nothing
            return self.response(dumps_networkapi({}))

        except UserNotAuthorizedError:
            return self.not_authorized()
        except InvalidValueError, e:
            return self.response_error(269, e.param, e.value)
        except EnvironmentEnvironmentVipNotFoundError:
            return self.response_error(393)
        except EnvironmentNotFoundError:
            return self.response_error(112)
        except EnvironmentVipNotFoundError:
            return self.response_error(283)
        except EnvironmentEnvironmentServerPoolRequestVipLinked, error:
            return self.response_error(394, error.cause.get('environment'), error.cause.get('vip_request_description'))
        except Exception, error:
            return self.response_error(1)

    def _get_cause(self, environment, request_vip_list):

        description_vip_list = []
        cause = {}

        for vip_request in request_vip_list:
            if vip_request.ip:
                vip_desc = '{}-{}'.format(vip_request.id, vip_request.ip.descricao or '')
                description_vip_list.append(vip_desc)
            else:
                vip_desc = '{}-{}'.format(vip_request.id, vip_request.ipv6.descricao or '')
                description_vip_list.append(vip_desc)

        cause['vip_request_description'] = ', '.join(description_vip_list)
        cause['environment'] = environment.name

        return cause
