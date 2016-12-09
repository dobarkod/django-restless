from django.conf.urls import include, url
import testapp.urls

try:
    from django.conf.urls import patterns
except ImportError:
    def patterns(prefix, *args):
        return args


urlpatterns = patterns('',
    url('', include(testapp.urls)),
)
