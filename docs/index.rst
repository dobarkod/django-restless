Django Restless - JSON-based RESTful APIs tools for Django
==========================================================

Django Restless is a lightweight set of tools for implementing JSON-based
RESTful APIs in Django. It helps you to write APIs that loosely follow
the RESTful paradigm, without forcing you to do so, and without imposing a
full-blown REST framework.

Restless provides only JSON support. If you need to support XML or
other formats, you probably want to take a look at some of the other frameworks
out there (we recommend Django REST framework).

Here is a simple view implementing an API endpoint greeting the caller::

    from restless.views import Endpoint

    class HelloWorld(Endpoint):
        def get(self, request):
            name = request.params.get('name', 'World')
            return {'message': 'Hello, %s!' % name}

One of the main ideas behind Restless is that it's lightweight and reuses
as much of functionality in Django as possible. For example, input parsing and
validation is done using standard Django forms. This means you don't have to
learn a whole new API to use Restless.

Besides giving you a set of tools to implement your own APIs, Restless comes
with a few endpoints modelled after Django's generic class-based views for
common use-cases.

For example, here's how to implement list and detail endpoints for `MyModel`
class allowing the users to list, create, get details of, update and delete
the models via API::

    from restless.modelviews import ListEndpoint, DetailEndpoint
    from myapp.models import MyModel

    class MyList(ListEndpoint):
        model = MyModel

    class MyDetail(DetailEndpoint):
        model = MyModel


Installation
------------

Django Restless is available from cheeseshop, so you can install it via pip::

    pip install DjangoRestless


For the latest and the greatest, you can also get it directly from git master::

    pip install -e git+ssh://github.com/dobarkod/django-restless/tree/master

The supported Python versions are 2.6, 2.7 and 3.3.

Usage
=====

After installation, first add `restless` to `INSTALLED_APPS` (this is not
strictly necessary, as restless is just a bunch of helper classes and
functions, but is good form nevertheless)::

    INSTALLED_APPS += ('restless',)

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

    from django.contrib.auth import get_user_model
    from restless.models import serialize

    User = get_user_model()

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

Or you may only want to exclude a certain field::

    class GetUserData(Endpoint):
        def get(self, request, user_id):
            user = User.objects.get(pk=user_id)
            return serialize(user, exclude=['password'])

Sometimes, you really need to complicate things. For example, for a book
author, you want to retrieve all the books they've written, and for each
book, all the user reviews, as well as the average rating for the author
accross all their books::

    class GetAuthorWithBooks(Endpoint):
        def get(self, request, author_id):
            author = Author.objects.get(pk=author_id)
            return serialize(author, include=[
                ('books', dict(  # for each book
                    fields=[
                        'title',
                        'isbn',
                        ('reviews', dict()) # get a list of all reviews
                    ]
                )),
                ('average_rating',
                    lambda a: a.books.all().aggregate(
                        Avg('rating'))['avg_rating'])
            ])


Please see the :py:func:`restless.models.serialize` documentation for detailed
description how this works.

.. note::

    The `serialize` function changed in 0.0.4, and the `related` way of
    specifying sub-objects is now deprecated.

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

and the PUT request from user modifies the Widget object::

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

Generic views for CRUD operations on models
-------------------------------------------

If you need a generic object CRUD operations, you can make
use of the :py:class:`restless.modelviews.ListEndpoint` and
:py:class:`restless.modelviews.DetailEndpoint` views. Here's an example of
the list and detail views providing an easy way to list, create, get, update
and delete a Book objects in a database::

    # views.py
    class BookList(ListEndpoint):
        model = Book

    class BookDetail(DetailEndpoint):
        model = Book

    # urls.py
    urlpatterns += patterns('',
        url(r'^books/$', BookList.as_view(),
            name='book_list'),
        url(r'^books/(?P<pk>\d+)$', BookDetail.as_view(),
            name='book_detail'))

The `pk` parameter here was automatically used by the detail view.
The parameter name can be customized if needed.

There are a number of ways to customize the generic views, explained in the
API reference in more detail.

RPC-style API for model views
-----------------------------

Sometimes a RPC-style API on models is needed (for example, to set a flag on
the model). The :py:class:`restless.modelviews.ActionEndpoint` provides an
easy way to do it. ActionEndpoint is a subclass of
:py:class:`restless.modelviews.DetailEndpoint` allowing only `POST` HTTP
request by default, which invoke the
:py:meth:`restless.modelviews.DetailEndpoint.action` method.

Here's an example of a Book endpoint on which a POST marks the book as
borrowed by the current user::

    class BorrowBook(ActionEndpoint):
        model = Book

        @login_required
        def action(self, request, obj, *args, **kwargs):
            obj.borrowed_by = request.user
            obj.save()
            return serialize(obj)

API Reference
=============

restless.views
--------------

Base classes for class-based views implementing the API endpoints.

.. automodule:: restless.views
   :members:

restless.modelviews
-------------------

Generic class-based views providing CRUD API for the models.

.. automodule:: restless.modelviews
   :members:

restless.models
---------------

Model serialization helper.

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

Bugs (and feature requests) are reported via the GitHub Issue tracker:
https://github.com/dobarkod/django-restless/issues/

If you have a bug fix or a patch for a feature you'd like to include, here's
how to submit the patch:

* Fork the https://github.com/dobarkod/django-restless.git
  repository
* Make the changes in a branch in your fork
* Make a pull request from the branch in your fork to dobarkod/django-restless master

If you're suggesting adding a feature, please file a feature request first
before implementing it, so we can discuss your proposed solution.

When contributing code, please adhere to the Python coding style guide (PEP8).
Both bug fixes and new feature implementations should come with corresponding
unit/functional tests. For bug fixes, the test should exhibit the bug if the
fix is not applied.

You can see the list of the contributors in the AUTHORS.md file in the
Django Restless source code.


Repository
----------

Restless is hosted on GitHub, using git version control. When checking
for bugs, always try the git master first::

    git clone https://github.com/dobarkod/django-restless.git


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
