try:
    from django.urls import reverse
except ImportError:  # Will be removed in Django 2.0
    from django.core.urlresolvers import reverse

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.exceptions import AuthenticationFailed

from social_django.views import NAMESPACE
from social_django.utils import load_backend, load_strategy
from social_core.exceptions import MissingBackend
from social_core.utils import requests

from drf_social_oauth2.settings import DRFSO2_URL_NAMESPACE


class SocialAuthentication(BaseAuthentication):
    """
    Authentication backend using `python-social-auth`

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header with the backend used, prepended with the string "Bearer ".

    For example:

        Authorization: Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a
    """

    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """
        auth_header = get_authorization_header(request).decode(HTTP_HEADER_ENCODING)
        auth = auth_header.split()

        if not auth or auth[0].lower() != 'bearer':
            return None

        if len(auth) == 1:
            message = 'Invalid token header. No backend provided.'
            raise AuthenticationFailed(message)
        elif len(auth) == 2:
            message = 'Invalid token header. No credentials provided.'
            raise AuthenticationFailed(message)
        elif len(auth) > 3:
            message = 'Invalid token header. Token string should not contain spaces.'
            raise AuthenticationFailed(message)

        token = auth[2]
        backend = auth[1]

        strategy = load_strategy(request=request)

        try:
            backend = load_backend(
                strategy, backend, reverse(f'{NAMESPACE}:complete', args=(backend,)),
            )

            user = backend.do_auth(access_token=token)
        except MissingBackend:
            message = 'Invalid token header. Invalid backend.'
            raise AuthenticationFailed(message)
        except requests.HTTPError as e:
            raise AuthenticationFailed(e.response.text)

        if not user:
            raise AuthenticationFailed('Bad credentials')
        return user, token

    def authenticate_header(self, request):
        """
        Bearer is the only finalized type currently
        """
        return 'Bearer backend realm="%s"' % self.www_authenticate_realm