from restless.views import Endpoint
from restless.models import serialize
from restless.http import Http201, Http404, Http400
from restless.auth import (AuthenticateEndpoint, BasicHttpAuthMixin,
    login_required)

import json

from .models import *
from .forms import *

__all__ = ['AuthorList', 'AuthorDetail', 'FailsIntentionally', 'TestLogin',
    'TestBasicAuth', 'WildcardHandler', 'EchoView']


class AuthorList(Endpoint):
    def get(self, request):
        return serialize(Author.objects.all())

    def post(self, request):
        form = AuthorForm(request.data)
        if form.is_valid():
            author = form.save()
            return Http201(serialize(author))
        else:
            return Http400(reason='invalid author data',
                details=form.errors)


class AuthorDetail(Endpoint):
    def get(self, request, author_id=None):
        author_id = int(author_id)
        try:
            return serialize(Author.objects.get(id=author_id))
        except Author.DoesNotExist:
            return Http404(reason='no such author')

    def delete(self, request, author_id=None):
        author_id = int(author_id)
        Author.objects.get(id=author_id).delete()
        return 'ok'

    def put(self, request, author_id=None):
        author_id = int(author_id)
        try:
            author = Author.objects.get(id=author_id)
        except Author.DoesNotExist:
            return Http404(reason='no such author')

        form = AuthorForm(request.data, instance=author)
        if form.is_valid():
            author = form.save()
            return serialize(author)
        else:
            return Http400(reason='invalid author data',
                details=form.errors)


class FailsIntentionally(Endpoint):
    def get(self, request):
        raise Exception("I'm being a bad view")


class TestLogin(AuthenticateEndpoint):
    pass


class TestBasicAuth(Endpoint, BasicHttpAuthMixin):
    @login_required
    def get(self, request):
        return serialize(request.user)


class WildcardHandler(Endpoint):
    def dispatch(self, request, *args, **kwargs):
        return Http404('no such resource: %s %s' % (
            request.method, request.path))


class EchoView(Endpoint):
    def post(self, request):
        return {
            'headers': dict((k, str(v)) for k, v in request.META.iteritems()),
            'raw_data': str(request.raw_data)
        }

    def get(self, request):
        return self.post(request)

    def put(self, request):
        return self.post(request)
