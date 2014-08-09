# -*- coding:utf-8 -*-
'''
Title: Infrastructure NetworkAPI
Author: masilva / S2IT
Copyright: ( c )  2009 globo.com todos os direitos reservados.
'''

from networkapi.admin_permission import AdminPermission

from networkapi.rest import RestResource, UserNotAuthorizedError

from networkapi.ambiente.models import EnvironmentVip

from networkapi.auth import has_perm

from networkapi.infrastructure.xml_utils import dumps_networkapi, loads, XMLError

from networkapi.log import Log

from networkapi.util import is_valid_int_greater_zero_param, is_valid_string_maxsize, is_valid_text

from networkapi.exception import InvalidValueError, EnvironmentVipError, EnvironmentVipNotFoundError
from django.forms.models import model_to_dict
from networkapi.grupo.models import GrupoError


class EnvironmentVipSearchResource(RestResource):

    '''Class that receives requests related to the table 'EnvironmentVip'.'''

    log = Log('EnvironmentVipSearchResource')

    def handle_post(self, request, user, *args, **kwargs):
        """Treat requests POST to search Environment VIP by parameters

        URL: environmentvip/search/
        """

        try:

            self.log.info("Search Environment VIP by parameters")

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.ENVIRONMENT_VIP,
                    AdminPermission.READ_OPERATION):
                self.log.error(
                    u'User does not have permission to perform the operation.')
                raise UserNotAuthorizedError(None)

            # Load XML data
            xml_map, attrs_map = loads(request.raw_post_data)

            # XML data format
            networkapi_map = xml_map.get('networkapi')
            if networkapi_map is None:
                return self.response_error(
                    3,
                    u'There is no value to the networkapi tag  of XML request.')

            environmentvip_map = networkapi_map.get('environment_vip')
            if environmentvip_map is None:
                return self.response_error(
                    3,
                    u'There is no value to the environment_vip tag  of XML request.')

            # Get XML data
            id_environment_vip = environmentvip_map.get('id_environment_vip')
            finalidade = environmentvip_map.get('finalidade_txt')
            cliente = environmentvip_map.get('cliente_txt')
            ambiente_p44 = environmentvip_map.get('ambiente_p44_txt')

            # Valid Parameters is none
            if id_environment_vip is None and finalidade is None and cliente is None and ambiente_p44 is None:
                self.log.error(
                    u'At least one of the parameters have to be informed to query')
                return self.response_error(287)

            # New Queryset by Environment Vip
            queryset = EnvironmentVip.objects.filter()

            if id_environment_vip is not None:

                # Valid Environment VIP ID
                if not is_valid_int_greater_zero_param(id_environment_vip):
                    self.log.error(
                        u'The id_environment_vip parameter is not a valid value: %s.',
                        id_environment_vip)
                    raise InvalidValueError(
                        None,
                        'id_environment_vip',
                        id_environment_vip)

                queryset = queryset.filter(id=id_environment_vip)

                # Checks if there Vip Environment and all other  parameters are
                # null
                if len(
                        queryset) == 0 and finalidade is None and cliente is None and ambiente_p44 is None:
                    raise EnvironmentVipNotFoundError(None)

            if id_environment_vip is None or len(queryset) == 0:

                # New Queryset none if finalidade, cliente and is none
                if finalidade is None and cliente is None and ambiente_p44 is None:
                    queryset = EnvironmentVip.objects.none()

                else:

                    # New Queryset by Environment Vip
                    queryset = EnvironmentVip.objects.filter().order_by('id')

                    if finalidade is not None:

                        # finalidade_txt can NOT be greater than 50
                        if not is_valid_string_maxsize(
                                finalidade,
                                50,
                                True) or not is_valid_text(finalidade):
                            self.log.error(
                                u'Parameter finalidade_txt is invalid. Value: %s.',
                                finalidade)
                            raise InvalidValueError(
                                None,
                                'finalidade_txt',
                                finalidade)

                        queryset = queryset.filter(finalidade_txt=finalidade)

                    if cliente is not None:

                        # cliente_txt can NOT be greater than 50
                        if not is_valid_string_maxsize(
                                cliente,
                                50,
                                True) or not is_valid_text(cliente):
                            self.log.error(
                                u'Parameter cliente_txt is invalid. Value: %s.',
                                cliente)
                            raise InvalidValueError(
                                None,
                                'cliente_txt',
                                cliente)

                        queryset = queryset.filter(cliente_txt=cliente)

                    if ambiente_p44 is not None:

                        # ambiente_p44_txt can NOT be greater than 50
                        if not is_valid_string_maxsize(
                                ambiente_p44,
                                50,
                                True) or not is_valid_text(ambiente_p44):
                            self.log.error(
                                u'Parameter ambiente_p44_txt is invalid. Value: %s.',
                                ambiente_p44)
                            raise InvalidValueError(
                                None,
                                'ambiente_p44_txt',
                                ambiente_p44)

                        queryset = queryset.filter(
                            ambiente_p44_txt=ambiente_p44)

            evips = []
            for evip in queryset:
                request_evip_map = {}
                request_evip_map['id'] = evip.id
                request_evip_map['finalidade_txt'] = evip.finalidade_txt
                request_evip_map['cliente_txt'] = evip.cliente_txt
                request_evip_map['ambiente_p44_txt'] = evip.ambiente_p44_txt
                evips.append(request_evip_map)

            return self.response(dumps_networkapi({'environment_vip': evips}))

        except InvalidValueError as e:
            return self.response_error(269, e.param, e.value)

        except UserNotAuthorizedError:
            return self.not_authorized()

        except XMLError as x:
            self.log.error(u'Error reading the XML request.')
            return self.response_error(3, x)

        except EnvironmentVipNotFoundError:
            return self.response_error(283)

        except EnvironmentVipError:
            return self.response_error(1)

        except Exception as e:
            return self.response_error(1)

    def handle_get(self, request, user, *args, **kwargs):
        """Treat GET requests list all Environment VIP Availables.

        URL: environmentvip/search/id_vlan
        """
        try:

            id_vlan = int(kwargs['id_vlan'])

            self.log.info("List all Environment VIP availables")

            # Commons Validations

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.ENVIRONMENT_VIP,
                    AdminPermission.READ_OPERATION):
                self.log.error(
                    u'User does not have permission to perform the operation.')
                return self.not_authorized()

            # Business Rules
            evips = EnvironmentVip.objects.all()
            evip_list = EnvironmentVip.available_evips(
                EnvironmentVip(),
                evips,
                id_vlan)

            return self.response(
                dumps_networkapi({'environment_vip': evip_list}))

        except (EnvironmentVipError, GrupoError) as e:
            self.log.error(e)
            return self.response_error(1)
        except BaseException as e:
            self.log.error(e)
            return self.response_error(1)
