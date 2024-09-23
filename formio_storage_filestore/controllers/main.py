# Copyright Nova Code (http://www.novacode.nl)
# See LICENSE file for full licensing details.

import base64
import io
import json

from urllib.parse import urlparse
from werkzeug.exceptions import Forbidden

from odoo import http, _
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class FormioStorageFilestoreController(http.Controller):
    """
    Although the type of authentication implies an authenticated user,
    requests for public (not authenticated) users will also be handled
    here. The override of the _authenticate method in the [ir.http]
    model handles this.
    """

    @http.route('/formio/storage/filestore', type='http', auth='user', methods=['POST'], csrf=False)
    def storage_filestore_post(self, **kwargs):
        """Process file upload from the Form and create the
        corresponding `ir.attachment`.

        Distinguish auth=user and auth=public, implemented in the ir.http model.
        """
        IrAttachment = request.env['ir.attachment']

        # Avoid using sudo when not necessary: internal users can
        # create attachments, as opposed to public and portal users.
        if not request.env.user.has_group('base.group_user'):
            IrAttachment = IrAttachment.sudo().with_context(binary_field_real_user=IrAttachment.env.user)

        uid = request.env.context.get('uid') or request.env.ref('base.public_user').id
        vals = {
            'name': kwargs.get('name'),
            'formio_storage_filestore_user_id': uid,
            'datas': base64.b64encode(kwargs.get('file').read()),
        }
        attachment = IrAttachment.create(vals)
        return request.make_response(
            data=json.dumps(attachment.read(['id', 'name', 'mimetype', 'file_size'])[0]),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/formio/storage/filestore', type='http', auth='user', methods=['GET'])
    def storage_filestore_get(self, **kwargs):
        """Get the file (uploaded) from the Form by searching the
        corresponding `ir.attachment`.
        """
        IrAttachment = request.env['ir.attachment']
        # Avoid using sudo when not necessary: internal users can
        # create attachments, as opposed to public and portal users.
        if not request.env.user.has_group('base.group_user'):
            IrAttachment = IrAttachment.sudo().with_context(binary_field_real_user=IrAttachment.env.user)

        # SECURITY RULE 1
        # file_name is the original filename with a uuidv4 suffix
        # added during the upload.
        # So the file_name is quite safe by uuidv4 obfuscation.
        file_name = kwargs.get('form')
        if file_name.startswith('/'):
            file_name = file_name[1:]

        if file_name:
            domain = [
                ('name', '=', file_name),
                ('formio_storage_filestore_user_id', '!=', False)
            ]
            attachment = IrAttachment.search(domain)
            if not attachment:
                _logger.warning('ir.attachment not found for name: %s' % file_name)
                return request.not_found(file_name)
            elif len(attachment) > 1:
                _logger.warning('Found multiple ir.attachment for name %s' % file_name)
                return request.not_found(file_name)
            else:
                attachment = attachment[0]
                is_user_public = not request.env.user or request.env.user.has_group('base.group_public')
                # access checks
                if attachment.res_id:
                    # SECURITY RULE 2
                    # Once a form has been submitted the
                    # attachment.res_id is set and this branch/check
                    # will apply.
                    Form = request.env['formio.form'].sudo()
                    form = Form.browse(attachment.res_id)
                    if is_user_public and form.sudo().public_share:
                        if not Form.get_public_form(form.uuid, public_share=True):
                            msg = 'The (once) public Form %s has been expired.'
                            _logger.info(msg % form.uuid)
                            raise Forbidden(_(msg) % form.uuid)
                    elif not Form.get_form(form.uuid, 'read'):
                        msg = 'Forbidden Form %s'
                        _logger.info(msg % form.uuid)
                        raise Forbidden(_(msg) % form.uuid)
                elif kwargs.get('baseUrl'):
                    Builder = request.env['formio.builder'].sudo()
                    Form = request.env['formio.form'].sudo()
                    base_url = kwargs.get('baseUrl')
                    url = urlparse(base_url)
                    if url.path.startswith('/formio/form') and not is_user_public:
                        uuid = url.path.split('/')[-1]
                        if not Form.get_form(uuid, 'read'):
                            msg = 'Forbidden Form /formio/form/%s'
                            _logger.info(msg % uuid)
                            raise Forbidden(_(msg) % uuid)
                    elif url.path.startswith('/formio/portal/form/new'):
                        builder_name = url.path.split('/')[-1]
                        domain = [('name', '=', builder_name), ('portal', '=', True)]
                        builder = Builder.search(domain)
                        if not builder:
                            msg = 'Forbidden Form /formio/portal/form/new/%s'
                            _logger.info(msg % uuid)
                            raise Forbidden(_(msg) % uuid)
                    elif url.path.startswith('/formio/portal/form') and not is_user_public:
                        uuid = url.path.split('/')[-1]
                        if not Form.get_form(uuid, 'read'):
                            msg = 'Forbidden Form /formio/portal/form/%s'
                            _logger.info(msg % uuid)
                            raise Forbidden(_(msg) % uuid)
                    elif url.path.startswith('/formio/public/form/new/current'):
                        current_uuid = url.path.split('/')[-1]
                        domain = [('current_uuid', '=', current_uuid), ('public', '=', True)]
                        builder = Builder.search(domain)
                        if not builder:
                            msg = 'Forbidden Form /formio/public/form/new/current/%s'
                            _logger.info(msg % current_uuid)
                            raise Forbidden(_(msg) % current_uuid)
                    elif url.path.startswith('/formio/public/form/new'):
                        uuid = url.path.split('/')[-1]
                        domain = [('uuid', '=', uuid), ('public', '=', True)]
                        builder = Builder.search(domain)
                        if not builder:
                            msg = 'Forbidden Form /formio/public/form/new/%s'
                            _logger.info(msg % uuid)
                            raise Forbidden(_(msg) % uuid)
                    elif url.path.startswith('/formio/public/form'):
                        uuid = url.path.split('/')[-1]
                        domain = [('uuid', '=', uuid), ('public', '=', True)]
                        form = Form.search(domain)
                        if not form:
                            msg = 'Forbidden Form /formio/public/form/%s'
                            _logger.info(msg % uuid)
                            raise Forbidden(_(msg) % uuid)
                    else:
                        msg = 'Forbidden Form file storage request'
                        raise Forbidden(_(msg))
                else:
                    msg = 'Forbidden Form file storage request'
                    raise Forbidden(_(msg))

                data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
                # TODO DeprecationWarning, deprecated
                # odoo.http.send_file is deprecated.
                #
                # But:
                # http.Stream.from_path only obtains the addons_path, not filestore!
                #
                # stream = http.Stream.from_path(fontfile_path)
                # return stream.get_response()
                response = http.send_file(data, filename=attachment['name'], as_attachment=True)
                return response
        else:
            _logger.warning('File not found or something went wrong')
            return request.not_found(file_name)
