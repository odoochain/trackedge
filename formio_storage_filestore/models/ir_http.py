# Copyright Nova Code (http://www.novacode.nl)
# See LICENSE file for full licensing details.

import logging
import os

from urllib.parse import urlparse

from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate_formio_storage_filestore(cls, endpoint):
        auth_method = endpoint.routing["auth"]
        log = {
            'routes': endpoint.routing.get('routes'),
            'auth_method': auth_method,
            'request_user_id': request.env.user.id
        }
        _logger.info(log)

        if auth_method == 'user' and request.env.context.get('uid'):
            return super(IrHttp, cls)._authenticate(endpoint)
        else:
            # Security measurement for public POST (uploads), because
            # CSRF is disabled (needed) for this endpoint.
            #
            # The baseUrl param was set on the Formio (JavaScript)
            # object and send by the XMLHttpRequest to this
            # endpoint.
            base_url = request.httprequest.args.get('baseUrl')
            if not base_url:
                raise AccessDenied()
            url = urlparse(base_url)
            if url.path.startswith('/formio/public/form/new/current'):
                current_uuid = url.path.split('/')[-1]
                domain = [('current_uuid', '=', current_uuid), ('public', '=', True)]
                builder = request.env['formio.builder'].sudo().search(domain)
                if builder:
                    return cls._allow_public_formio_storage_filestore(base_url)
                else:
                    return False
            elif url.path.startswith('/formio/public/form/new'):
                uuid = url.path.split('/')[-1]
                domain = [('uuid', '=', uuid), ('public', '=', True)]
                builder = request.env['formio.builder'].sudo().search(domain)
                if builder:
                    return cls._allow_public_formio_storage_filestore(base_url)
                else:
                    return False
            elif url.path.startswith('/formio/public/form'):
                uuid = url.path.split('/')[-1]
                domain = [('uuid', '=', uuid), ('public', '=', True)]
                form = request.env['formio.form'].sudo().search(domain)
                if not form or not form.public_access:
                    return cls._allow_public_formio_storage_filestore(base_url)
                else:
                    return False
            else:
                return False

    @classmethod
    def _allow_public_formio_storage_filestore(cls, base_url):
        _logger.info('Allow public /formio/storage/filestore with baseUrl %s (become: auth=public)' % base_url)
        return 'public'

    @classmethod
    def _authenticate(cls, endpoint):
        """
        :param endpoint str: the endpoint config, for example (endpoint.__dict_):
            {'method': <bound method FormioStorageFilestoreController.form_file_post of <odoo.addons.formio_storage_filestore.controllers.main.FormioStorageFilestoreController object at 0x7fa358108520>>,
             'original': <function FormioStorageFilestoreController.form_file_post at 0x7fa35990a1f0>,
             'routing': {'type': 'http', 'auth': 'user', 'methods': ['POST'], 'routes': ['/formio/storage/filestore'], 'csrf': False},
             'arguments': {}
            }
        """
        if '/formio/storage/filestore' in endpoint.routing.get('routes', []):
            res = cls._authenticate_formio_storage_filestore(endpoint)
            if res:
                return res
            else:
                return super(IrHttp, cls)._authenticate(endpoint)
        else:
            return super(IrHttp, cls)._authenticate(endpoint)
