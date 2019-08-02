from base64 import b64encode

from rest_framework import HTTP_HEADER_ENCODING


def basic_auth_header(username, password):
    credentials = ('%s:%s' % (username, password))
    credentials = credentials.encode(HTTP_HEADER_ENCODING)
    return 'Basic %s' % b64encode(credentials).decode(HTTP_HEADER_ENCODING)
