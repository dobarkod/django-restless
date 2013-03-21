.. DjangoRestless documentation master file, created by
   sphinx-quickstart on Sat Jul  7 20:18:28 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Django Restless - A lightweight RESTful API framework
=====================================================

Django Restless is a lightweight RESTful API framework for Django.

As there are already plenty of REST API frameworks for Django (Tastypie,
Django REST Framework, Piston), why another one?

Restless helps you write APIs that loosely follow the RESTful
paradigm, without *forcing* you to do so. While that's possible to do in
other frameworks as well, it can be quite cumbersome. It's more like a set
of useful tools than a set thing you must comply with.

Restless provides only JSON support. If you need to support XML or
other formats, you probably want to take a look at some of the other frameworks
out there.

One of the main points of Restless is that it's lightweight, and reuses as much
of functionality in Django as possible. For example, JSON serialization is
using Django serializers, and input parsing and validation is done using
standard Django forms. This means you don't have to learn a whole new API
to use Restless.

Here's a simple view implementing an API endpoint greeting the caller::

    from restless.views import Endpoint

    class HelloWorld(Endpoint):
        def get(self, request):
            name = request.params.get('name', 'World')
            return {'message': 'Hello, %s!' % name}


Installation
------------

Django Restless is available from cheeseshop, so you can install it via pip::

    pip install DjangoRestless


For the latest and the greatest, you can also get it directly from git master::

    pip install -e git+ssh://github.com/senko/DjangoRestless/tree/master


Tutorial
========

After installation, first add "restless" to INSTALLED_APPS (this is not
strictly necessary, as restless is just a bunch of helper classes and
functions, but is good form nevertheless).

Views
-----

To implement API endpoints (resources), write class-based views subclassing
from :py:class:`restless.views.Endpoint`::

    from restless.views import Endpoint

    class HelloWorld(Endpoint):
        def get(self, request):
            name = request.params.get('name', 'World')
            return {'message': 'Hello, %s!' % name}

This view will return a HTTP 200 response with a JSON payload greeting the
caller. To return status code other than 200, use one of the
:py:class:`restless.views.JSONResponse` and pass the response in. Note that
error responses take a string (error description) and optional error details
keyword arguments.

Register the views in URLconf as you'd do with any other class-based view::

    url(r'^hello/$', HelloWorld.as_view())

To require authentication, subclass from appropriate mixin as well. For example,
if you're using HTTP Basic authentication, have all your views subclass
:py:class:`restless.auth.BasicHttpAuthMixin` and use
:py:class:`restless.auth.login_required` for requiring the user be
authenticated::

    from restless.auth import BasicHttpAuthMixin, login_required

    class SecretGreeting(Endpoint, BasicHttpAuthMixin):
        @login_required
        def get(self, request):
            return {'message': 'Hello, %s!' % request.user}

If you're using session-based username/password authentication, you can use
the :py:class:`restless.auth.UsernamePasswordAuthMixin` in the above example,
or just use :py:class:`restless.auth.AuthenticateEndpoint` which will do the
same, and return the serialized User object back to the authenticated user::

    url(r'^login/$', restless.auth.AuthenticateEndpoint.as_view())

Model serialization
-------------------

Model serialization can be as simple or as complex as needed. In the simplest
case, you just pass the object to :py:func:`restless.models.serialize`, and
get back a dictionary with all the model fields (except related models)
serialized::

    from restless.models import serialize

    class GetUserProfileData(Endpoint):
        def get(self, request, user_id):
            profile = User.objects.get(pk=user_id).get_profile()
            return serialize(profile)

In some cases, you want to serialize only a subset of fields. Do this by
passing a list of fields to serialize as the second argument::

    class GetUserData(Endpoint):
        def get(self, request, user_id):
            fields = ('id', 'username', 'first_name', 'last_name', 'email')
            user = User.objects.get(pk=user_id)
            return serialize(user, fields)

(Incidentally, this is exactly what
:py:class:`restless.auth.AuthenticateEndpoint` does).

Sometimes, you really need to complicate things. For example, get not only
the user profile, but the basic user data as well, as a single JSON object
(not nested), again taking care that only some user fields may be shown::

    class GetUser(Endpoint):
        def get(self, request, user_id):
            user_fields = ('id', 'username', 'first_name', 'last_name',
                'email')
            user = User.objects.get(pk=user_id)
            profile = user.get_profile()
            return serialize(profile, related={
                'user': (user_fields, None, True)
            })

Please see the :py:func:`restless.models.serialize` documentation for detailed
description how this works.

Data deserialization and validation
-----------------------------------

There is no deserialization support. Django already has awesome functionality
in this regard called ModelForms, and that's the easiest way to go about
parsing users' data and storing it into Django models.

Since Restless understands JSON payloads, it's easy to use Django forms to
parse and validate client input, even in more complex cases where several
models (or several forms) need to be parsed at once.

Let's say we have a Widget object that can be extended with Addon::

    class Widget(models.Model):
        title = models.CharField(max_length=255)

    class Addon(models.Model):
        parent = models.OneToOneField(Widget, related_name='addon')
        text = model.TextField()

    class WidgetForm(forms.ModelForm):
        class Meta:
            model = Widget

    class AddonForm(forms.ModelForm):
        class Meta:
            model = Addon

and the PUT request from user modifies the Widget object:

    { "title": "My widget!", "addon": { "text": "This is my addon" } }

A view handing the PUT request might look something like::

    class ModifyWidget(Endpoint):
        def put(self, request, widget_id):
            widget = Widget.objects.get(pk=widget_id)
            widget_form = WidgetForm(request.data, instance=widget)
            addon_form = AddonForm(request.data.get('addon', {}),
                instance=widget.addon)
            if widget_form.is_valid() and addon_form.is_valid():
                widget_form.save()
                addon_form.save()


You can find more examples in the sample project used to test restless in the
various files in the "testproject/testapp" folder of the source repository.

API Reference
=============

restless.views
--------------

Base classes for class-based views implementing the API endpoints.

.. automodule:: restless.views
   :members:

restless.models
---------------

Model serialization helper. The serializator uses built-in Django model
serializator, usually used for "dumpdata" management command.

.. automodule:: restless.models
   :members:

restless.auth
-------------

Authentication helpers.

.. automodule:: restless.auth
   :members:

restless.http
-------------

HTTP responses with JSON payload.

.. automodule:: restless.http
   :members:

How to contribute
=================

You've found (and hopefully fixed) a bug, or have a great idea you think
should be added to Django Restless? Patches welcome! :-)

When contributing code, please adhere to the Python coding style guide (PEP8).
Both bug fixes and new feature implementations should come with corresponding
unit/functional tests. For bug fixes, the test should exhibit the bug if the
fix is not applied.

Repository
----------

Restless is hosted on GitHub, using git version control. When checking
for bugs, always try the git master first::

    git clone http://github.com/senko/DjangoRestless.git


Tests and docs
--------------

To run the tests::

    make test

To run the tests and get coverage report::

    make coverage

To build Sphinx docs::

    make docs

To build everything, run the tests with coverage support, and build the
docs::

    make

To clean the build directory::

    make clean


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
