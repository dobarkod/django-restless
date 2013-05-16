from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm

from .views import Endpoint
from .http import HttpError, Http200, Http201

from .models import serialize

__all__ = ['ListEndpoint', 'DetailEndpoint']


def _get_form(form, model):
    if form:
        return form
    elif model:
        return type(model._meta.object_name + 'Form',
            (ModelForm,), {
                'Meta': type('Meta', (object,), {'model': model})})
    else:
        raise NotImplementedError('Form or Model class not specified')


class ListEndpoint(Endpoint):
    """
    List Endpoint supporting getting a list of objects and creating a new
    one. The endpoint exports two view methods by default: get (for getting
    the list of objects) and post (for creating a new object).

    The only required configuration for the endpoint is the `model`
    class attribute, which should be set to the model you want to have a list
    (and/or create) endpoints for.

    You can also provide a `form` class attribute, which should be the
    model form that's used for creating the model. If not provided, the
    default model class for the model will be created automatically.

    You can restrict the HTTP methods available by specifying the `methods`
    class variable.

    Further customization can be done by overriding the `get_query_set`
    method of the object (by default, it returns the queryset with all of
    the objects) and the `serialize` method (by default, uses the default
    `restless.models.serialize` behaviour).

    Here's a complete of a list endpoint definition:

        class MyList(ListEndpoint):
            model = MyModel
            form = MyModelForm  # optional
            methods = ['GET', 'POST']  # optional

            def get_query_self(self, request, *args, **kwargs):
                return MyModel.objects.filter(active=True)

            def serialize(self, objs):
                return restless.models.serialize(objs, fields=['name'])

    If you need further customization, you should implement the complete view
    yourself (subclass directly from `restless.views.Endpoint` class).
    """

    model = None
    form = None
    methods = ['GET', 'POST']

    def get_query_set(self, request, *args, **kwargs):
        if self.model:
            return self.model.objects.all()
        else:
            raise HttpError(404, 'Resource Not Found')

    def serialize(self, objs):
        return serialize(objs)

    def get(self, request, *args, **kwargs):
        if 'GET' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        qs = self.get_query_set(request, *args, **kwargs)
        return self.serialize(qs)

    def post(self, request, *args, **kwargs):
        if 'POST' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        Form = _get_form(self.form, self.model)
        form = Form(request.data or None, request.FILES)
        if form.is_valid():
            obj = form.save()
            return Http201(self.serialize(obj))


class DetailEndpoint(Endpoint):
    """
    DetailEndpoint supports getting a single object from the database
    (HTTP GET), updating it (HTTP PUT) and deleting it (HTTP DELETE).

    The only required configuration for the endpoint is the `model`
    class attribute, which should be set to the model you want to have the
    detail endpoints for.

    You can also provide a `form` class attribute, which should be the
    model form that's used for updating the model. If not provided, the
    default model class for the model will be created automatically.

    You can restrict the HTTP methods available by specifying the `methods`
    class variable.

    Further customization can be done by overriding the `get_query_set`
    method of the object (by default, it returns the queryset filtering the
    instance object whose primary key is equal to the `object_id` keyword
    argument), the `get_instance` method (if you need to override the actual
    getting of the instance from the database using queryset provided by
    `get_query_set` method) and the `serialize` method (by default, uses
    the default `restless.models.serialize` behaviour).

    Here's a complete of a detail endpoint definition:

        class MyList(DetailEndpoint):
            model = MyModel
            form = MyModelForm  # optional
            methods = ['GET', 'PUT', 'DELETE']  # optional

            def get_query_self(self, request, *args, **kwargs):
                return MyModel.objects.filter(id=kwargs['mymodel_id'])

            def serialize(self, objs):
                return restless.models.serialize(objs, fields=['name'])

    If you need further customization, you should implement the complete view
    yourself (subclass directly from `restless.views.Endpoint` class).
    """

    model = None
    form = None
    methods = ['GET', 'PUT', 'DELETE']

    def get_query_set(self, request, *args, **kwargs):
        if self.model and 'object_id' in kwargs:
            return self.model.objects.filter(pk=kwargs['object_id'])
        else:
            raise HttpError(404, 'Resource Not Found')

    def get_instance(self, request, *args, **kwargs):
        try:
            return self.get_query_set(request, *args, **kwargs).get()
        except ObjectDoesNotExist:
            raise HttpError(404, 'Resource Not Found')

    def serialize(self, obj):
        return serialize(obj)

    def get(self, request, *args, **kwargs):
        if 'GET' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        return self.serialize(self.get_instance(request, *args, **kwargs))

    def put(self, request, *args, **kwargs):
        if 'GET' not in self.methods:
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
        if 'GET' not in self.methods:
            raise HttpError(405, 'Method Not Allowed')

        instance = self.get_instance(request, *args, **kwargs)
        instance.delete()
        return {}
