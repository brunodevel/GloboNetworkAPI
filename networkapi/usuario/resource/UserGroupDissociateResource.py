# -*- coding:utf-8 -*-
'''
Title: Infrastructure NetworkAPI
Author: masilva / S2IT
Copyright: ( c )  2012 globo.com todos os direitos reservados.
'''

from __future__ import with_statement
from networkapi.admin_permission import AdminPermission
from networkapi.auth import has_perm
from networkapi.exception import InvalidValueError
from networkapi.grupo.models import GrupoError, UGrupo, UGrupoNotFoundError
from networkapi.usuario.models import Usuario, UsuarioGrupo, UsuarioError, UsuarioNotFoundError, UserGroupNotFoundError
from networkapi.infrastructure.xml_utils import dumps_networkapi
from networkapi.log import Log
from networkapi.rest import RestResource, UserNotAuthorizedError
from networkapi.util import is_valid_int_greater_zero_param
from networkapi.distributedlock import distributedlock, LOCK_USER_GROUP


class UserGroupDissociateResource(RestResource):

    log = Log('UserGroupDissociateResource')

    def handle_delete(self, request, user, *args, **kwargs):
        """Treat DELETE requests to dissociate User and Group.

        URL: usergroup/user/<id_user>/ugroup/<id_group>/dissociate/
        """

        try:

            self.log.info("Dissociate User and Group.")

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.USER_ADMINISTRATION,
                    AdminPermission.WRITE_OPERATION):
                self.log.error(
                    u'User does not have permission to perform the operation.')
                raise UserNotAuthorizedError(None)

            id_user = kwargs.get('id_user')
            id_group = kwargs.get('id_group')

            # Valid ID User
            if not is_valid_int_greater_zero_param(id_user):
                self.log.error(
                    u'The id_user parameter is not a valid value: %s.',
                    id_user)
                raise InvalidValueError(None, 'id_user', id_user)

            # Valid ID Group
            if not is_valid_int_greater_zero_param(id_group):
                self.log.error(
                    u'The id_group parameter is not a valid value: %s.',
                    id_group)
                raise InvalidValueError(None, 'id_group', id_group)

            # Find User by ID to check if it exist
            Usuario.get_by_pk(id_user)

            # Find Group by ID to check if it exist
            UGrupo.get_by_pk(id_group)

            # Find UserGroup by ID to check if it exist
            user_group = UsuarioGrupo.get_by_user_group(id_user, id_group)

            with distributedlock(LOCK_USER_GROUP % (id_user, id_group)):

                try:

                    # remove UserGroup
                    user_group.delete(user)

                except Exception as e:
                    self.log.error(u'Failed to remove the UserGroup.')
                    raise GrupoError(e, u'Failed to remove the UserGroup.')

                return self.response(dumps_networkapi({}))

        except InvalidValueError as e:
            return self.response_error(269, e.param, e.value)

        except UserNotAuthorizedError:
            return self.not_authorized()

        except UsuarioNotFoundError:
            return self.response_error(177, id_user)

        except UGrupoNotFoundError:
            return self.response_error(180, id_group)

        except UserGroupNotFoundError:
            return self.response_error(184, id_user, id_group)

        except (GrupoError, UsuarioError):
            return self.response_error(1)
