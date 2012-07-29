from django.conf.urls import patterns, url

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
    url(r'^.*$', WildcardHandler.as_view())
)
