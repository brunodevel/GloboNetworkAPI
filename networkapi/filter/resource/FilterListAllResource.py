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
from networkapi.rest import RestResource
from networkapi.filter.models import Filter
from networkapi.auth import has_perm
from networkapi.infrastructure.xml_utils import dumps_networkapi
import logging
from django.forms.models import model_to_dict


class FilterListAllResource(RestResource):

    '''Class that receives requests to list all Filters.'''

    log = logging.getLogger('FilterListAllResource')

    def handle_get(self, request, user, *args, **kwargs):
        """Treat GET requests list all Filters.

        URL: filter/all/
        """

        try:

            self.log.info("List all Filters")
            # Commons Validations

            # User permission
            if not has_perm(user, AdminPermission.ENVIRONMENT_MANAGEMENT, AdminPermission.READ_OPERATION):
                self.log.error(
                    u'User does not have permission to perform the operation.')
                return self.not_authorized()

            # Business Rules
            filters = Filter.objects.all()

            filter_list = []
            for filter_ in filters:
                filter_dict = model_to_dict(filter_)
                filter_dict['equip_types'] = list()

                for fil_equip_type in filter_.filterequiptype_set.all():
                    filter_dict['equip_types'].append(
                        model_to_dict(fil_equip_type.equiptype))

                filter_list.append(filter_dict)

            return self.response(dumps_networkapi({'filter': filter_list}))

        except BaseException, e:
            return self.response_error(1)
