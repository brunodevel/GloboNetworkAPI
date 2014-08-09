# -*- coding:utf-8 -*-

from networkapi.admin_permission import AdminPermission
from networkapi.auth import has_perm
from networkapi.equipamento.models import Equipamento, EquipamentoError,\
    EquipamentoNotFoundError
from networkapi.grupo.models import GrupoError
from networkapi.infrastructure.xml_utils import XMLError, dumps_networkapi
from networkapi.log import Log
from networkapi.rest import RestResource
from networkapi.requisicaovips.models import VipPortToPool, RequisicaoVips
from networkapi.util import mount_ipv4_string, mount_ipv6_string,\
    is_valid_int_greater_zero_param
from networkapi.exception import InvalidValueError


class EquipmentGetRealRelated(RestResource):

    log = Log('EquipmentGetRealRelateds')

    def handle_get(self, request, user, *args, **kwargs):
        """Handles GET requests to list all real related equipment.

        URLs: equipamento/get_real_related/<id_equip>
        """

        try:

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.VIPS_REQUEST,
                    AdminPermission.READ_OPERATION):
                self.log.error(
                    u'User does not have permission to perform the operation.')
                return self.not_authorized()

            id_equip = kwargs.get('id_equip')

            # Valid equipment ID
            if not is_valid_int_greater_zero_param(id_equip):
                self.log.error(
                    u'The id_equip parameter is not a valid value: %s.',
                    id_equip)
                raise InvalidValueError(None, 'id_equip', id_equip)

            equipment = Equipamento.get_by_pk(id_equip)

            map_dicts = []

            # IPV4
            for ip_equip in equipment.ipequipamento_set.all():
                vip_dict = dict()

                ip = ip_equip.ip

                for server_pool_member in ip.serverpoolmember_set.all():
                    server_pool_id = server_pool_member.server_pool_id
                    vip_port_to_pool = VipPortToPool.objects.get(
                        server_pool__id=server_pool_id)
                    vip = RequisicaoVips.get_by_pk(
                        vip_port_to_pool.requisicao_vip.id)

                    if vip.id not in vip_dict:
                        vip_dict = {str(vip.id): list()}

                    host_name = vip.variables_to_map()['host']

                    map_dicts.append(
                        {
                            'server_pool_member_id': server_pool_member.id,
                            'id_vip': vip.id,
                            'host_name': host_name,
                            'port_vip': vip_port_to_pool.port_vip,
                            'port_real': server_pool_member.port_real,
                            'ip': mount_ipv4_string(ip)})

            # IPV6
            for ip_equip in equipment.ipv6equipament_set.all():
                vip_dict = dict()

                ip = ip_equip.ip

                for server_pool_member in ip.serverpoolmember_set.all():
                    server_pool_id = server_pool_member.server_pool_id
                    vip_port_to_pool = VipPortToPool.objects.get(
                        server_pool__id=server_pool_id)
                    vip = RequisicaoVips.get_by_pk(
                        vip_port_to_pool.requisicao_vip.id)

                    if vip.id not in vip_dict:
                        vip_dict = {str(vip.id): list()}

                    host_name = vip.variables_to_map()['host']

                    map_dicts.append(
                        {
                            'server_pool_member_id': server_pool_member.id,
                            'id_vip': vip.id,
                            'host_name': host_name,
                            'port_vip': vip_port_to_pool.port_vip,
                            'port_real': server_pool_member.port_real,
                            'ip': mount_ipv6_string(ip)})

            vip_map = dict()
            vip_map["vips"] = map_dicts
            vip_map["equip_name"] = equipment.nome

            # Return XML
            return self.response(dumps_networkapi(vip_map))

        except EquipamentoNotFoundError as e:
            return self.response_error(117, id_equip)
        except InvalidValueError as e:
            return self.response_error(269, e.param, e.value)
        except (EquipamentoError, GrupoError):
            return self.response_error(1)
        except XMLError as x:
            self.log.error(u'Error reading the XML request.')
            return self.response_error(3, x)
        except Exception as e:
            return self.response_error(1)
