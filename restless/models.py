from django.core import serializers
from django.db import models


def serialize(src, fields=None, related=None):
    """Serialize Model or QuerySet to JSON format.

    By default, all of the model fields (including 'id') are serialized, and
    foreign key fields are serialized as the id of the referenced object.

    If 'fields' tuple/list is specified, only fields listed in it are
    serialized. If 'related' dict is specified, fields listed in it
    will be fully (recursively) serialized.

    Format of 'related' is:
        field_name -> (related_object_fields, related_object_related,
            flatten)
    As a shortcut, field_name -> None is equivalent to
        field_name -> (None, None, False)

    The values in 'related' specify 'fields' and 'related' arguments
    to be passed to the related object serialization. If 'flatten' is True,
    the items from the sub-dict will be added to the current dict instead of
    adding a single subdict under the 'field_name' key (useful for OneToOne
    relations, where a model basically just extends the base one).
    """

    # for m2m fields we'll get a Manager instead of a Model; deal with it
    # by just getting all the items

    if (isinstance(src, models.Manager) or
        isinstance(src, models.query.QuerySet)):
            return [serialize(item, fields, related) for item in src.all()]

    # we use the Django python serializer to serialize the model
    # and optionally recurse into related fields
    elif isinstance(src, models.Model):
        # serialize fields
        data = serializers.serialize('python', [src], fields=fields)
        data = data[0]['fields']
        if fields is None or 'id' in fields:
            data['id'] = src.id

        # recursively serialize full fields, if any
        if related:
            for k, v in related.items():
                if v is None:
                    v = (None, None, False)
                (sub_fields, sub_related, flatten) = v
                sub = serialize(getattr(src, k), sub_fields, sub_related)
                if flatten:
                    for subk, subv in sub.items():
                        data[subk] = subv
                    if k in data:
                        del data[k]
                else:
                    data[k] = sub

        return data

    # just in case ordinary Python data sneaked past us, just return it
    else:
        return src
