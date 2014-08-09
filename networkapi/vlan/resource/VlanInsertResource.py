# -*- coding:utf-8 -*-
'''
Title: Infrastructure NetworkAPI
Author: avanzolin / TQI
Copyright: ( c )  2009 globo.com todos os direitos reservados.
'''

from networkapi.admin_permission import AdminPermission
from networkapi.auth import has_perm
from networkapi.infrastructure.xml_utils import loads, XMLError, dumps_networkapi
from networkapi.log import Log
from networkapi.rest import RestResource
from networkapi.util import is_valid_int_greater_zero_param, is_valid_string_minsize, is_valid_string_maxsize, \
    destroy_cache_function
from networkapi.vlan.models import VlanError, Vlan, VlanNameDuplicatedError, VlanNumberNotAvailableError, VlanACLDuplicatedError, VlanNumberEnvironmentNotAvailableError
from networkapi.exception import InvalidValueError
from networkapi.ambiente.models import  AmbienteError, Ambiente, AmbienteNotFoundError,\
    ConfigEnvironmentInvalidError
import re
from networkapi.ip.models import NetworkIPv4, NetworkIPv6
from networkapi.vlan.models import TipoRede
from networkapi.ip.models import NetworkIPv4AddressNotAvailableError, IpNotAvailableError
from django.core.exceptions import ObjectDoesNotExist


class VlanInsertResource(RestResource):

    log = Log('VlanInsertResource')

    def handle_post(self, request, user, *args, **kwargs):
        '''Treat POST requests to insert vlan

        URL: vlan/insert/
        '''

        try:
            # Generic method for v4 and v6
            network_version = kwargs.get('network_version')

            # Commons Validations

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.VLAN_MANAGEMENT,
                    AdminPermission.WRITE_OPERATION):
                self.log.error(
                    u'User does not have permission to perform the operation.')
                return self.not_authorized()

            # Business Validations

            # Load XML data
            xml_map, attrs_map = loads(request.raw_post_data)

            # XML data format
            networkapi_map = xml_map.get('networkapi')
            if networkapi_map is None:
                msg = u'There is no value to the networkapi tag of XML request.'
                self.log.error(msg)
                return self.response_error(3, msg)
            vlan_map = networkapi_map.get('vlan')
            if vlan_map is None:
                msg = u'There is no value to the vlan tag of XML request.'
                self.log.error(msg)
                return self.response_error(3, msg)

            # Get XML data
            environment_id = vlan_map.get('environment_id')
            number = vlan_map.get('number')
            name = vlan_map.get('name')
            acl_file = vlan_map.get('acl_file')
            acl_file_v6 = vlan_map.get('acl_file_v6')
            description = vlan_map.get('description')
            network_ipv4 = vlan_map.get('network_ipv4')
            network_ipv6 = vlan_map.get('network_ipv6')

            # Valid environment_id ID
            if not is_valid_int_greater_zero_param(environment_id):
                self.log.error(
                    u'Parameter environment_id is invalid. Value: %s.',
                    environment_id)
                raise InvalidValueError(None, 'environment_id', environment_id)

            # Valid number of Vlan
            if not is_valid_int_greater_zero_param(number):
                self.log.error(
                    u'Parameter number is invalid. Value: %s',
                    number)
                raise InvalidValueError(None, 'number', number)

            # Valid name of Vlan
            if not is_valid_string_minsize(
                    name,
                    3) or not is_valid_string_maxsize(
                    name,
                    50):
                self.log.error(u'Parameter name is invalid. Value: %s', name)
                raise InvalidValueError(None, 'name', name)

            if not network_ipv4 or not str(network_ipv4).isdigit():
                self.log.error(
                    u'Parameter network_ipv4 is invalid. Value: %s.',
                    network_ipv4)
                raise InvalidValueError(None, 'network_ipv4', network_ipv4)

            if not network_ipv6 or not str(network_ipv6).isdigit():
                self.log.error(
                    u'Parameter network_ipv6 is invalid. Value: %s.',
                    network_ipv6)
                raise InvalidValueError(None, 'network_ipv6', network_ipv6)

            network_ipv4 = int(network_ipv4)
            network_ipv6 = int(network_ipv6)

            if network_ipv4 not in range(0, 2):
                self.log.error(
                    u'Parameter network_ipv4 is invalid. Value: %s.',
                    network_ipv4)
                raise InvalidValueError(None, 'network_ipv4', network_ipv4)

            if network_ipv6 not in range(0, 2):
                self.log.error(
                    u'Parameter network_ipv6 is invalid. Value: %s.',
                    network_ipv6)
                raise InvalidValueError(None, 'network_ipv6', network_ipv6)

            p = re.compile("^[A-Z0-9-_]+$")
            m = p.match(name)

            if not m:
                name = name.upper()
                m = p.match(name)

                if not m:
                    raise InvalidValueError(None, 'name', name)

            # Valid description of Vlan
            if not is_valid_string_minsize(
                    description,
                    3,
                    False) or not is_valid_string_maxsize(
                    description,
                    200,
                    False):
                self.log.error(
                    u'Parameter description is invalid. Value: %s',
                    description)
                raise InvalidValueError(None, 'description', description)

            vlan = Vlan()

            # Valid acl_file Vlan
            if acl_file is not None:
                if not is_valid_string_minsize(
                        acl_file,
                        3) or not is_valid_string_maxsize(
                        acl_file,
                        200):
                    self.log.error(
                        u'Parameter acl_file is invalid. Value: %s',
                        acl_file)
                    raise InvalidValueError(None, 'acl_file', acl_file)
                p = re.compile("^[A-Z0-9-_]+$")
                m = p.match(acl_file)
                if not m:
                    raise InvalidValueError(None, 'acl_file', acl_file)

                # VERIFICA SE VLAN COM MESMO ACL JA EXISTE OU NAO
                vlan.get_vlan_by_acl(acl_file)

            # Valid acl_file_v6 Vlan
            if acl_file_v6 is not None:
                if not is_valid_string_minsize(
                        acl_file_v6,
                        3) or not is_valid_string_maxsize(
                        acl_file_v6,
                        200):
                    self.log.error(
                        u'Parameter acl_file_v6 is invalid. Value: %s',
                        acl_file_v6)
                    raise InvalidValueError(None, 'acl_file_v6', acl_file_v6)
                p = re.compile("^[A-Z0-9-_]+$")
                m = p.match(acl_file_v6)
                if not m:
                    raise InvalidValueError(None, 'acl_file_v6', acl_file_v6)

                # VERIFICA SE VLAN COM MESMO ACL JA EXISTE OU NAO
                vlan.get_vlan_by_acl_v6(acl_file_v6)

            ambiente = Ambiente()
            ambiente = ambiente.get_by_pk(environment_id)

            vlan.acl_file_name = acl_file
            vlan.acl_file_name_v6 = acl_file_v6
            vlan.num_vlan = number
            vlan.nome = name
            vlan.descricao = description
            vlan.ambiente = ambiente
            vlan.ativada = 0
            vlan.acl_valida = 0
            vlan.acl_valida_v6 = 0

            vlan.insert_vlan(user)

            if network_ipv4:
                NetworkIPv4().add_network_ipv4(user, vlan.id, None, None, None)

            if network_ipv6:
                NetworkIPv6().add_network_ipv6(user, vlan.id, None, None, None)

            map = dict()
            listaVlan = dict()
            listaVlan['id'] = vlan.id
            listaVlan['nome'] = vlan.nome
            listaVlan['acl_file_name'] = vlan.acl_file_name
            listaVlan['descricao'] = vlan.descricao
            listaVlan['id_ambiente'] = vlan.ambiente.id
            listaVlan['ativada'] = vlan.ativada
            listaVlan['acl_valida'] = vlan.acl_valida
            map['vlan'] = listaVlan

            # Delete vlan's cache
            # destroy_cache_function()

            # Return XML
            return self.response(dumps_networkapi(map))

        except VlanACLDuplicatedError as e:
            return self.response_error(311, acl_file)
        except InvalidValueError as e:
            return self.response_error(269, e.param, e.value)
        except AmbienteNotFoundError as e:
            return self.response_error(112)
        except VlanNameDuplicatedError as e:
            return self.response_error(108)
        except VlanNumberNotAvailableError as e:
            return self.response_error(306, vlan.num_vlan)
        except VlanNumberEnvironmentNotAvailableError as e:
            return self.response_error(315, e.message)
        except XMLError as e:
            self.log.error(u'Error reading the XML request.')
            return self.response_error(3, e)
        except (VlanError, AmbienteError) as e:
            return self.response_error(1)
        except ConfigEnvironmentInvalidError as e:
            return self.response_error(294)
        except NetworkIPv4AddressNotAvailableError as e:
            return self.response_error(294)
        except IpNotAvailableError as e:
            return self.response_error(150, e)
        except ObjectDoesNotExist as e:
            return self.response_error(111, e)
