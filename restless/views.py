from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from django.http import HttpResponse
from .http import Http400, Http200, Http500

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

    The view method should return either a HTTPResponse (for example, a
    redirect), or something else (usually a dictionary or a list). If something
    other than HTTPResponse is returned, it is first serialized into
    :py:class:`restless.http.JSONResponse` with a status code 200 (OK),
    then returned.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        request.content_type = request.META.get('CONTENT_TYPE', 'text/plain')
        request.params = dict((k, v) for (k, v) in request.GET.items())
        request.data = None
        if request.content_type == 'application/json':
            try:
                request.data = json.loads(request.body)
            except Exception as ex:
                return Http400('invalid JSON payload: %s' % ex)
        elif ((request.content_type == 'application/x-www-form-urlencoded') or
                (request.content_type.startswith('multipart/form-data'))):
            request.data = dict((k, v) for (k, v) in request.POST.items())
        else:
            request.data = request.body

        if hasattr(self, 'authenticate') and callable(self.authenticate):
            self.authenticate(request)

        try:
            response = super(Endpoint, self).dispatch(request, *args, **kwargs)
        except Exception as ex:
            if settings.DEBUG:
                response = Http500(str(ex), traceback=traceback.format_exc())
            else:
                raise

        if not isinstance(response, HttpResponse):
            response = Http200(response)
        return response
