from django.conf.urls import patterns, include, url
import testapp.urls

urlpatterns = patterns('',
    url('', include(testapp.urls)),
)
