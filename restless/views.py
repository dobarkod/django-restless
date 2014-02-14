from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from django.http import HttpResponse
from .http import Http200, Http500, HttpError

import traceback
import json

__all__ = ['Endpoint']


class Endpoint(View):
    """
    Class-based Django view that should be extended to provide an API
    endpoint (resource). To provide GET, POST, PUT, HEAD or DELETE methods,
    implement the corresponding get(), post(), put(), head() or delete()
    method, respectively.

    If you also implement authenticate(request) method, it will be called
    before the main method to provide authentication, if needed. Auth mixins
    use this to provide authentication.

    The usual Django "request" object passed to methods is extended with a
    few more attributes:

      * request.content_type - the content type of the request
      * request.params - a dictionary with GET parameters
      * request.data - a dictionary with POST/PUT parameters, as parsed from
          either form submission or submitted application/json data payload
      * request.raw_data - string containing raw request body

    The view method should return either a HTTPResponse (for example, a
    redirect), or something else (usually a dictionary or a list). If something
    other than HTTPResponse is returned, it is first serialized into
    :py:class:`restless.http.JSONResponse` with a status code 200 (OK),
    then returned.

    The authenticate method should return either a HttpResponse, which will
    shortcut the rest of the request handling (the view method will not be
    called), or None (the request will be processed normally).

    Both methods can raise a :py:class:`restless.http.HttpError` exception
    instead of returning a HttpResponse, to shortcut the request handling and
    immediately return the error to the client.
    """

    @staticmethod
    def _parse_content_type(content_type):
        if ';' in content_type:
            ct, params = content_type.split(';', 1)
            try:
                params = dict(param.split('=') for param in params.split())
            except:
                params = {}
        else:
            ct = content_type
            params = {}
        return ct, params

    def _parse_body(self, request):
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return

        ct, ct_params = self._parse_content_type(request.content_type)
        if ct == 'application/json':
            charset = ct_params.get('charset', 'utf-8')
            try:
                data = request.body.decode(charset)
                request.data = json.loads(data)
            except Exception as ex:
                raise HttpError(400, 'invalid JSON payload: %s' % ex)
        elif ((ct == 'application/x-www-form-urlencoded') or
                (ct.startswith('multipart/form-data'))):
            request.data = dict((k, v) for (k, v) in request.POST.items())
        else:
            request.data = request.body

    def _process_authenticate(self, request):
        if hasattr(self, 'authenticate') and callable(self.authenticate):
            auth_response = self.authenticate(request)

            if isinstance(auth_response, HttpResponse):
                return auth_response
            elif auth_response is None:
                pass
            else:
                raise TypeError('authenticate method must return '
                    'HttpResponse instance or None')

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        request.content_type = request.META.get('CONTENT_TYPE', 'text/plain')
        request.params = dict((k, v) for (k, v) in request.GET.items())
        request.data = None
        request.raw_data = request.body

        try:
            self._parse_body(request)
            authentication_required = self._process_authenticate(request)
            if authentication_required:
                return authentication_required

            response = super(Endpoint, self).dispatch(request, *args, **kwargs)
        except HttpError as err:
            response = err.response
        except Exception as ex:
            if settings.DEBUG:
                response = Http500(str(ex), traceback=traceback.format_exc())
            else:
                raise

        if not isinstance(response, HttpResponse):
            response = Http200(response)
        return response
