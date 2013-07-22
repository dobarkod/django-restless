from django.forms.models import modelform_factory

from .views import Endpoint
from .http import HttpError, Http200, Http201

from .models import serialize

__all__ = ['ListEndpoint', 'DetailEndpoint', 'ActionEndpoint']


def _get_form(form, model):
    if form:
        return form
    elif model:
        return modelform_factory(model)
    else:
        raise NotImplementedError('Form or Model class not specified')


class ListEndpoint(Endpoint):
    """
    List :py:class:`restless.views.Endpoint` supporting getting a list of
    objects and creating a new one. The endpoint exports two view methods by
    default: get (for getting the list of objects) and post (for creating a
    new object).

    The only required configuration for the endpoint is the `model`
    class attribute, which should be set to the model you want to have a list
    (and/or create) endpoints for.

    You can also provide a `form` class attribute, which should be the
    model form that's used for creating the model. If not provided, the
    default model class for the model will be created automatically.

    You can restrict the HTTP methods available by specifying the `methods`
    class variable.
    """

    model = None
    form = None
    methods = ['GET', 'POST']

    def get_query_set(self, request, *args, **kwargs):
        """Return a QuerySet that this endpoint represents.

        If `model` class attribute is set, this method returns the `all()`
        queryset for the model. You can override the method to provide custom
        behaviour. The `args` and `kwargs` parameters are passed in directly
        from the URL pattern match.

        If the method raises a :py:class:`restless.http.HttpError` exception,
        the rest of the request processing is terminated and the error is
        immediately returned to the client.
        """

        if self.model:
            return self.model.objects.all()
        else:
            raise HttpError(404, 'Resource Not Found')

    def serialize(self, objs):
        """Serialize the objects in the response.

        By default, the method uses the :py:func:`restless.models.serialize`
        function to serialize the objects with default behaviour. Override the
        method to customize the serialization.
        """

        return serialize(objs)

    def get(self, request, *args, **kwargs):
        """Return a serialized list of objects in this endpoint."""

        if 'GET' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        qs = self.get_query_set(request, *args, **kwargs)
        return self.serialize(qs)

    def post(self, request, *args, **kwargs):
        """Create a new object."""

        if 'POST' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        Form = _get_form(self.form, self.model)
        form = Form(request.data or None, request.FILES)
        if form.is_valid():
            obj = form.save()
            return Http201(self.serialize(obj))
            
        raise HttpError(400, 'Invalid Data', errors=form.errors)


class DetailEndpoint(Endpoint):
    """
    Detail :py:class:`restless.views.Endpoint` supports getting a single
    object from the database (HTTP GET), updating it (HTTP PUT) and deleting
    it (HTTP DELETE).

    The only required configuration for the endpoint is the `model`
    class attribute, which should be set to the model you want to have the
    detail endpoints for.

    You can also provide a `form` class attribute, which should be the
    model form that's used for updating the model. If not provided, the
    default model class for the model will be created automatically.

    You can restrict the HTTP methods available by specifying the `methods`
    class variable.

    """
    model = None
    form = None
    lookup_field = 'pk'
    methods = ['GET', 'PUT', 'DELETE']

    def get_instance(self, request, *args, **kwargs):
        """Return a model instance represented by this endpoint.

        If `model` is set and the primary key keyword argument is present,
        the method attempts to get the model with the primary key equal
        to the url argument.

        By default, the primary key keyword argument name is `pk`. This can
        be overridden by setting the `lookup_field` class attribute.

        You can override the method to provide custom behaviour. The `args`
        and `kwargs` parameters are passed in directly from the URL pattern
        match.

        If the method raises a :py:class:`restless.http.HttpError` exception,
        the rest of the request processing is terminated and the error is
        immediately returned to the client.
        """

        if self.model and self.lookup_field in kwargs:
            try:
                return self.model.objects.get(**{
                    self.lookup_field: kwargs.get(self.lookup_field)
                })
            except self.model.DoesNotExist:
                raise HttpError(404, 'Resource Not Found')
        else:
            raise HttpError(404, 'Resource Not Found')

    def serialize(self, obj):
        """Serialize the object in the response.

        By default, the method uses the :py:func:`restless.models.serialize`
        function to serialize the object with default behaviour. Override the
        method to customize the serialization.
        """

        return serialize(obj)

    def get(self, request, *args, **kwargs):
        """Return the serialized object represented by this endpoint."""

        if 'GET' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        return self.serialize(self.get_instance(request, *args, **kwargs))

    def put(self, request, *args, **kwargs):
        """Update the object represented by this endpoint."""

        if 'PUT' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        Form = _get_form(self.form, self.model)
        instance = self.get_instance(request, *args, **kwargs)
        form = Form(request.data or None, request.FILES,
            instance=instance)
        if form.is_valid():
            obj = form.save()
            return Http200(self.serialize(obj))
        raise HttpError(400, 'Invalid data', errors=form.errors)

    def delete(self, request, *args, **kwargs):
        """Delete the object represented by this endpoint."""

        if 'DELETE' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        instance = self.get_instance(request, *args, **kwargs)
        instance.delete()
        return {}


class ActionEndpoint(DetailEndpoint):
    """
    A variant of :py:class:`DetailEndpoint` for supporting a RPC-style action
    on a resource. All the documentation for DetailEndpoint applies, but
    only the `POST` HTTP method is allowed by default, and it invokes the
    :py:meth:`ActionEndpoint.action` method to do the actual work.

    If you want to support any of the other HTTP methods with their default
    behaviour as in DetailEndpoint, just modify the `methods` list to
    include the methods you need.

    """
    methods = ['POST']

    def post(self, request, *args, **kwargs):
        if 'POST' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        instance = self.get_instance(request, *args, **kwargs)
        return self.action(request, instance, *args, **kwargs)

    def action(self, request, obj, *args, **kwargs):
        raise HttpError(405, 'Method Not Allowed')
