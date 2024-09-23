# Changelog

## 17.0.2.0.0

Technical/API compatibility change for the `formio.form` methods `_after_create` and `_after_write`:
- Removed the `vals` argument because the respective caller methods `create` and `write` raised a Singleton Error upon `copy`.\
  This also simplifies the `formio.form` base `create` and `write` methods.
- Call the `_process_storage_filestore_ir_attachments` method per record iteration.

## 17.0.1.2.0

Add description with recommended module in the `formio.builder.js.options` data.\
So it is not overwritten by merging `formio.builder.js.options` records.

## 17.0.1.1.0

Improve the data for `formio.builder.js.options`:\
Record xmlid: `formio.formio_builder_js_options_storage_filestore`

## 17.0.1.0.0

Fixed (multi) file upload retrieval for backend, portal and public forms (request context/env).\
This applies to `GET /formio/storage/filestore` requests immediately after the upload, e.g. to preview images, that resulted in HTTP 403 Forbidden errors.\
This required to fixing and improving the URL/route authentication checks.\
Also done another security audit, so uploaded files cannot be retrieved without proper access/permission.

## 17.0.0.1

Initial release.
