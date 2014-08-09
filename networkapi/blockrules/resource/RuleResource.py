# -*- coding:utf-8 -*-
from __future__ import with_statement

from networkapi.log import Log
from networkapi.blockrules.models import Rule, BlockRules
from networkapi.auth import has_perm
from networkapi.admin_permission import AdminPermission
from networkapi.rest import RestResource, UserNotAuthorizedError
from networkapi.infrastructure.xml_utils import dumps_networkapi, loads, XMLError
from networkapi.exception import InvalidValueError
from networkapi.util import is_valid_int_greater_zero_param
from networkapi.ambiente.models import AmbienteNotFoundError, Ambiente
from networkapi.blockrules.models import RuleContent
from networkapi.requisicaovips.models import RequisicaoVips


class RuleResource(RestResource):

    log = Log('RuleResource')

    def handle_get(self, request, user, *args, **kwargs):
        """Handles GET requests to find Rule by id.

        URL: /rule/get_by_id/<id_rule>
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

            id_rule = kwargs.get('id_rule')

            if not is_valid_int_greater_zero_param(id_rule):
                self.log.error(
                    u'Parameter id_rule is invalid. Value: %s.',
                    id_rule)
                raise InvalidValueError(None, 'id_rule', id_rule)

            rule = Rule.objects.get(pk=id_rule)
            contents = RuleContent.objects.filter(rule=rule)

            rule_contents = list()
            rule_blocks = list()
            for content in contents:
                block_id = 0
                try:
                    block = BlockRules.objects.get(
                        content=content.content,
                        environment=content.rule.environment)
                    block_id = block.id
                except Exception:
                    pass

                rule_contents.append(content.content)
                rule_blocks.append(block_id)

            return self.response(
                dumps_networkapi(
                    {
                        'rule': {
                            'name': rule.name,
                            'rule_contents': rule_contents,
                            'rule_blocks': rule_blocks}}))

        except InvalidValueError as e:
            self.log.error('Invalid param')
            return self.response_error(269, e.param, e.value)
        except Rule.DoesNotExist:
            return self.response_error(358)
        except Exception as e:
            self.logerror(e)
            return self.response_error(1)

    def handle_post(self, request, user, *args, **kwargs):
        """Handles POST requests to save a new Rule

        URL: rule/save/
        """
        try:
            self.log.info("Save rule to an environment")

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.VIP_VALIDATION,
                    AdminPermission.WRITE_OPERATION):
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

            rule_map = networkapi_map.get('map')
            if rule_map is None:
                return self.response_error(
                    3,
                    u'There is no value to the environment_vip tag  of XML request.')

            # Get XML data
            id_env = rule_map['id_env']
            name = rule_map['name']
            contents = rule_map['contents'] if isinstance(
                rule_map['contents'],
                list) else [
                rule_map['contents'],
            ]
            blocks_id = rule_map['blocks_id'] if isinstance(
                rule_map['blocks_id'],
                list) else [
                rule_map['blocks_id'],
            ]

            if not is_valid_int_greater_zero_param(id_env):
                self.log.error(
                    u'The id_env parameter is not a valid value: %s.',
                    id_env)
                raise InvalidValueError(None, 'id_env', id_env)

            if not name or len(name) > 80:
                self.log.error(
                    u'The name parameter is not a valid value: %s.',
                    name)
                raise InvalidValueError(None, 'name', name)

            environment = Ambiente.get_by_pk(id_env)

            new_rule = Rule()
            new_rule.name = name
            new_rule.environment = environment
            new_rule.save(user)

            self.__save_rule_contents(
                contents,
                blocks_id,
                environment,
                new_rule,
                user)

            return self.response(dumps_networkapi({}))

        except AmbienteNotFoundError as e:
            self.log.error('Environment not found')
            return self.response_error(112)
        except InvalidValueError as e:
            return self.response_error(269, e.param, e.value)
        except UserNotAuthorizedError:
            return self.not_authorized()
        except BlockRules.DoesNotExist:
            return self.response_error(359)
        except XMLError as x:
            self.log.error(u'Error reading the XML request.')
            return self.response_error(3, x)
        except Exception as e:
            return self.response_error(1)

    def handle_put(self, request, user, *args, **kwargs):
        """Handles PUT requests to update a given Rule

        URL: rule/update/
        """
        try:
            self.log.info("Update rule to an environment")

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.VIP_VALIDATION,
                    AdminPermission.WRITE_OPERATION):
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

            rule_map = networkapi_map.get('map')
            if rule_map is None:
                return self.response_error(
                    3,
                    u'There is no value to the environment_vip tag  of XML request.')

            # Get XML data
            id_rule = rule_map['id_rule']
            id_env = rule_map['id_env']
            name = rule_map['name']
            contents = rule_map['contents'] if isinstance(
                rule_map['contents'],
                list) else [
                rule_map['contents'],
            ]
            blocks_id = rule_map['blocks_id'] if isinstance(
                rule_map['blocks_id'],
                list) else [
                rule_map['blocks_id'],
            ]

            if not is_valid_int_greater_zero_param(id_rule):
                self.log.error(
                    u'The id_rule parameter is not a valid value: %s.',
                    id_rule)
                raise InvalidValueError(None, 'id_env', id_rule)

            if not is_valid_int_greater_zero_param(id_env):
                self.log.error(
                    u'The id_env parameter is not a valid value: %s.',
                    id_env)
                raise InvalidValueError(None, 'id_env', id_env)

            if not name or len(name) > 80:
                self.log.error(
                    u'The name parameter is not a valid value: %s.',
                    name)
                raise InvalidValueError(None, 'name', name)

            rule = Rule.objects.get(pk=id_rule)

            environment = Ambiente.get_by_pk(id_env)

            rule.name = name
            rule.environment = environment

            # Set NULL in rule field of all Vip Request related
            RequisicaoVips.objects.filter(rule=rule).update(rule=None)
            RequisicaoVips.objects.filter(
                rule_applied=rule).update(
                rule_applied=None)
            RequisicaoVips.objects.filter(
                rule_rollback=rule).update(
                rule_rollback=None)

            rule.save(user)

            for rule_cotent in rule.rulecontent_set.all():
                rule_cotent.delete(user)

            self.__save_rule_contents(
                contents,
                blocks_id,
                environment,
                rule,
                user)

            return self.response(dumps_networkapi({}))

        except AmbienteNotFoundError as e:
            self.log.error('Environment not found')
            return self.response_error(112)
        except InvalidValueError as e:
            return self.response_error(269, e.param, e.value)
        except Rule.DoesNotExist:
            return self.response_error(358)
        except BlockRules.DoesNotExist:
            return self.response_error(359)
        except UserNotAuthorizedError:
            return self.not_authorized()
        except XMLError as x:
            self.log.error(u'Error reading the XML request.')
            return self.response_error(3, x)
        except Exception as e:
            return self.response_error(1)

    def handle_delete(self, request, user, *args, **kwargs):
        """Treat requests DELETE to remove Rule.

        URL: rule/delete/<id_rule>/
        """
        try:

            self.log.info("Delete rule from an environment")

            # User permission
            if not has_perm(
                    user,
                    AdminPermission.VIP_VALIDATION,
                    AdminPermission.WRITE_OPERATION):
                self.log.error(
                    u'User does not have permission to perform the operation.')
                raise UserNotAuthorizedError(None)

            id_rule = kwargs.get('id_rule')

            if not is_valid_int_greater_zero_param(id_rule):
                self.log.error(
                    u'The id_rule parameter is not a valid value: %s.',
                    id_rule)
                raise InvalidValueError(None, 'id_rule', id_rule)

            rule = Rule.objects.get(pk=id_rule)
            rule.delete(user)

            return self.response(dumps_networkapi({}))

        except InvalidValueError as e:
            return self.response_error(269, e.param, e.value)
        except Rule.DoesNotExist:
            return self.response_error(358)
        except UserNotAuthorizedError:
            return self.not_authorized()
        except Exception as e:
            return self.response_error(1)

    def __save_rule_contents(
            self,
            contents,
            blocks_id,
            environment,
            rule,
            user):

        blocks_id = [int(id) for id in blocks_id]

        if not filter(
                lambda a: a != 0,
                blocks_id) == sorted(
                filter(
                lambda a: a != 0,
                blocks_id)):
            raise InvalidValueError(None, 'blocks_id', blocks_id)

        if len(blocks_id) > len(contents):
            raise InvalidValueError(None, 'contents', contents)
        if len(blocks_id) < len(contents):
            raise InvalidValueError(None, 'blocks_id', blocks_id)

        for i in range(len(contents)):
            rule_content = RuleContent()
            block = ''

            if blocks_id[i] and blocks_id[i] != '0':
                block = BlockRules.objects.get(
                    pk=blocks_id[i],
                    environment=environment)

            rule_content.content = block.content if block else contents[i]
            rule_content.order = i
            rule_content.rule = rule

            rule_content.save(user)
