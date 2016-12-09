from django.conf.urls import url

try:
    from django.conf.urls import patterns
except ImportError:
    def patterns(prefix, *args):
        return args

from .views import *

urlpatterns = patterns('',
    url(r'^authors/$', AuthorList.as_view(),
        name='author_list'),
    url(r'^authors/(?P<author_id>\d+)$', AuthorDetail.as_view(),
        name='author_detail'),

    url(r'^fail-view/$', FailsIntentionally.as_view(),
        name='fail_view'),
    url(r'^login-view/$', TestLogin.as_view(),
        name='login_view'),
    url(r'^basic-auth-view/$', TestBasicAuth.as_view(),
        name='basic_auth_view'),
    url(r'^custom-auth/$', TestCustomAuthMethod.as_view(),
        name='custom_auth_method'),
    url(r'^echo-view/$', EchoView.as_view(),
        name='echo_view'),
    url(r'^error-raising-view/$', ErrorRaisingView.as_view(),
        name='error_raising_view'),

    url(r'^publishers/$', PublisherAutoList.as_view(),
        name='publisher_list'),
    url(r'^publishers-ready-only/$', ReadOnlyPublisherAutoList.as_view(),
        name='readonly_publisher_list'),
    url(r'^publishers/(?P<pk>\d+)$', PublisherAutoDetail.as_view(),
        name='publisher_detail'),
    url(r'^publishers/(?P<pk>\d+)/do_something$', PublisherAction.as_view(),
        name='publisher_action'),

    url(r'^books/(?P<isbn>\d+)$', BookDetail.as_view(),
        name='book_detail'),

    url(r'^.*$', WildcardHandler.as_view()),
)
