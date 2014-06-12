from django.test import TestCase
from django.test.client import Client, MULTIPART_CONTENT
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import json
from decimal import Decimal
import base64
import warnings
import six

from .models import *
from restless.models import serialize, flatten

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


class TestClient(Client):

    @staticmethod
    def process(response):
        try:
            raw_data = response.content.decode('utf-8')
            response.json = json.loads(response.content.decode('utf-8'))
        except:
            response.json = None
        finally:
            return response

    def get(self, url_name, data={}, follow=False, extra={}, *args, **kwargs):
        return self.process(
            super(TestClient, self).get(
                reverse(url_name, args=args, kwargs=kwargs),
                data=data,
                follow=follow,
                **extra))

    def post(self, url_name, data={}, content_type=MULTIPART_CONTENT,
            follow=False, extra={}, *args, **kwargs):
        return self.process(
            super(TestClient, self).post(
                reverse(url_name, args=args, kwargs=kwargs),
                content_type=content_type,
                data=data,
                follow=follow,
                **extra))

    def put(self, url_name, data={}, content_type=MULTIPART_CONTENT,
            follow=False, *args, **kwargs):
        return self.process(
            super(TestClient, self).put(
                reverse(url_name, args=args, kwargs=kwargs),
                content_type=content_type, data=data, follow=follow))

    def delete(self, url_name, data={}, content_type=MULTIPART_CONTENT,
            follow=False, *args, **kwargs):
        return self.process(
            super(TestClient, self).delete(
                reverse(url_name, args=args, kwargs=kwargs),
                content_type=content_type, data=data, follow=follow))


class TestSerialization(TestCase):

    def setUp(self):
        self.author = Author.objects.create(name='User Foo')
        self.publisher = Publisher.objects.create(name='Publisher')
        self.books = []
        for i in range(10):
            b = self.author.books.create(author=self.author,
                title='Book %d' % i,
                isbn='123-1-12-123456-%d' % i,
                price=Decimal("10.0"),
                publisher=self.publisher)
            self.books.append(b)

    def test_full_shallow(self):
        """Test simple serialization, all fields, without recursing"""

        s = serialize(self.author)
        self.assertEqual(s, {'name': 'User Foo', 'id': self.author.id})

    def test_partial_shallow(self):
        """Test serialization of only selected fields"""

        s = serialize(self.author, ['name'])
        self.assertEqual(s, {'name': 'User Foo'})

    def test_shallow_foreign_key_serialization(self):
        """Test that foreign key fields are serialized as integer IDs."""

        s = serialize(self.books[0])
        self.assertEqual(s['author'], self.author.id)

    def test_serialize_related_deprecated(self):
        """Test serialization of related model"""

        with warnings.catch_warnings(record=True):
            s = serialize(self.author, related={'books': None})
        self.assertEqual(s['name'], 'User Foo')
        self.assertEqual(len(s['books']), len(self.books))
        for b in s['books']:
            self.assertTrue(b['title'].startswith('Book '))
            self.assertTrue(b['isbn'].startswith('123-1-12-123456-'))

    def test_serialize_related(self):
        """Test serialization of related model"""

        s = serialize(self.author, include=[('books', dict())])
        self.assertEqual(s['name'], 'User Foo')
        self.assertEqual(len(s['books']), len(self.books))
        for b in s['books']:
            self.assertTrue(b['title'].startswith('Book '))
            self.assertTrue(b['isbn'].startswith('123-1-12-123456-'))

    def test_serialize_related_partial_deprecated(self):
        """Test serialization of some fields of related model"""

        with warnings.catch_warnings(record=True):
            s = serialize(self.author, related={
                'books': ('title', None, False)
            })
        self.assertEqual(s['name'], 'User Foo')
        self.assertEqual(len(s['books']), len(self.books))
        for b in s['books']:
            self.assertTrue(b['title'].startswith('Book '))
            self.assertTrue('isbn' not in b)

    def test_serialize_related_partial(self):
        """Test serialization of some fields of related model"""

        s = serialize(self.author, include=[
            ('books', dict(
                fields=['title']
            ))
        ])
        self.assertEqual(s['name'], 'User Foo')
        self.assertEqual(len(s['books']), len(self.books))
        for b in s['books']:
            self.assertTrue(b['title'].startswith('Book '))
            self.assertTrue('isbn' not in b)

    def test_serialize_related_deep_deprecated(self):
        """Test serialization of twice-removed related model"""

        with warnings.catch_warnings(record=True):
            s = serialize(self.author, related={
                'books': (None, {
                    'publisher': None,
                }, None)})

        self.assertEqual(s['name'], 'User Foo')
        self.assertEqual(len(s['books']), len(self.books))
        for b in s['books']:
            self.assertTrue(b['title'].startswith('Book '))
            self.assertEqual(b['publisher']['name'], 'Publisher')

    def test_serialize_related_deep(self):
        """Test serialization of twice-removed related model"""

        s = serialize(self.author, include=[
            ('books', dict(
                include=[('publisher', dict())]
            ))
        ])

        self.assertEqual(s['name'], 'User Foo')
        self.assertEqual(len(s['books']), len(self.books))
        for b in s['books']:
            self.assertTrue(b['title'].startswith('Book '))
            self.assertEqual(b['publisher']['name'], 'Publisher')

    def test_serialize_related_flatten_deprecated(self):
        """Test injection of related models' fields into the serialized one"""

        b = self.books[0]
        s = serialize(b, related={
            'author': (None, None, True)
        })
        self.assertEqual(s['name'], b.author.name)

    def test_serialize_related_flatten(self):
        """Test injection of related models' fields into the serialized one"""

        b = self.books[0]
        s = serialize(b, fields=[
            ('author', dict())
        ], fixup=flatten('author'))

        self.assertEqual(s['name'], b.author.name)

    def test_serialize_queryset(self):
        """Test queryset serialization"""

        Author.objects.all().delete()
        a1 = Author.objects.create(name="foo")
        a2 = Author.objects.create(name="bar")
        qs = Author.objects.all()
        _ = list(qs)  # force sql query execution

        # Check that the same (cached) queryset is used, instead of a clone
        with self.assertNumQueries(0):
            s = serialize(qs)

        self.assertEqual(s,
            [
                {'name': a1.name, 'id': a1.id},
                {'name': a2.name, 'id': a2.id},
            ]
        )

    def test_serialize_list(self):
        """Test that list serialization deep-serializes list elements"""

        Author.objects.all().delete()
        a1 = Author.objects.create(name="foo")
        a2 = Author.objects.create(name="bar")
        s = serialize(list(Author.objects.all()))
        self.assertEqual(s,
            [
                {'name': a1.name, 'id': a1.id},
                {'name': a2.name, 'id': a2.id},
            ]
        )

    def test_serialize_dict(self):
        """Test that dict serialization deep-serializes dict values"""

        Author.objects.all().delete()
        a1 = Author.objects.create(name="foo")
        a2 = Author.objects.create(name="bar")
        s = serialize({'a1': a1, 'a2': a2})

        self.assertEqual(s['a1']['name'], a1.name)
        self.assertEqual(s['a2']['name'], a2.name)

    def test_serialize_set(self):
        """
        Test that set serialization deep-serializes set values and
        returns a list (since sets can't contain a dict and aren't JSON
        serializable).
        """

        Author.objects.all().delete()
        a1 = Author.objects.create(name="bar")
        a2 = Author.objects.create(name="foo")
        s = serialize(set(Author.objects.all()))
        self.assertTrue(isinstance(s, list))
        # Must cast back to set to ignore ordering
        self.assertEqual(sorted(s, key=lambda el: el['name']),
            [
                {'name': a1.name, 'id': a1.id},
                {'name': a2.name, 'id': a2.id},
            ]
        )

    def test_passthrough(self):
        """Test that non-ORM types just pass through the serializer"""

        data = {'a': ['b', 'c'], 'd': 1, 'e': "foo"}
        self.assertEqual(data, serialize(data))

    def test_serialize_takes_fields_tuple(self):
        s = serialize(self.author, fields=('id',), include=('name',))
        self.assertEqual(s, {
            'id': self.author.id,
            'name': self.author.name
        })

    def test_serialize_doesnt_mutate_fields(self):
        runs = [0]

        def accessor(obj):
            runs[0] += 1
            return 'foo'

        # If fields are appended on, 'desc' will be twice in the list
        # for the second run, so in total the accessor function will be
        # run 3 instead of 2 times
        serialize([self.author, self.author], fields=['id'],
            include=[('desc', accessor)])

        self.assertEqual(runs[0], 2)


class TestEndpoint(TestCase):

    def setUp(self):
        self.client = TestClient()
        self.author = Author.objects.create(name='User Foo')

    def test_author_list(self):
        """Exercise a simple GET request"""

        r = self.client.get('author_list')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json), 1)
        self.assertEqual(r.json[0]['id'], self.author.id)

    def test_author_details(self):
        """Exercise passing parameters to GET request"""

        r = self.client.get('author_detail', author_id=self.author.id)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['id'], self.author.id)
        self.assertEqual(r.json['name'], 'User Foo')

    def test_author_details_not_found(self):
        """Exercise returning arbitrary HTTP status codes from view"""

        r = self.client.get('author_detail', author_id=self.author.id + 9999)
        self.assertEqual(r.status_code, 404)

    def test_author_details_invalid_method(self):
        """Exercise 405 if POST request doesn't pass form validation"""
        r = self.client.post('author_detail', author_id=self.author.id)
        self.assertEqual(r.status_code, 405)

    def test_create_author_form_encoded(self):
        """Exercise application/x-www-form-urlencoded POST"""

        r = self.client.post('author_list', data=urlencode({
            'name': 'New User',
        }), content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json['name'], 'New User')
        self.assertEqual(r.json['name'],
            Author.objects.get(id=r.json['id']).name)

    def test_create_author_multipart(self):
        """Exercise multipart/form-data POST"""

        r = self.client.post('author_list', data={
            'name': 'New User',
        })  # multipart/form-data is default in test client
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json['name'], 'New User')
        self.assertEqual(r.json['name'],
            Author.objects.get(id=r.json['id']).name)

    def test_create_author_json(self):
        """Exercise application/json POST"""

        r = self.client.post('author_list', data=json.dumps({
            'name': 'New User',
        }), content_type='application/json; charset=utf-8')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json['name'], 'New User')
        self.assertEqual(r.json['name'],
            Author.objects.get(id=r.json['id']).name)

    def test_invalid_json_payload(self):
        """Exercise invalid JSON handling"""

        r = self.client.post('author_list', data='xyz',
            content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_delete_author(self):
        """Exercise DELETE request"""

        r = self.client.delete('author_detail', author_id=self.author.id)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Author.objects.count(), 0)

    def test_change_author(self):
        """Exercise PUT request"""

        r = self.client.put('author_detail', data=json.dumps({
            'name': 'User Bar'
        }), author_id=self.author.id, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['name'], 'User Bar')
        self.assertEqual(r.json['name'],
            Author.objects.get(id=r.json['id']).name)

    def test_view_failure(self):
        """Exercise exception handling"""

        with self.settings(DEBUG=True):
            r = self.client.get('fail_view')

        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.json['error'], "I'm being a bad view")
        self.assertTrue('traceback' in r.json)

    def test_raw_request_body(self):
        raw = b'\x01\x02\x03'
        r = self.client.post('echo_view', data=raw,
            content_type='text/plain')

        self.assertEqual(base64.b64decode(r.json['raw_data'].encode('ascii')),
            raw)

    def test_get_payload_is_ignored(self):
        """Test that body of the GET request is always ignored."""
        r = self.client.get('echo_view', extra={
            'CONTENT_TYPE': 'application/json'})
        # If the GET request body is not ignored, it (empty string) will be an
        # invalid JSON and will return 400 instead of 200.
        self.assertEqual(r.status_code, 200)

    def test_raising_http_error_returns_it(self):
        r = self.client.get('error_raising_view')
        self.assertEqual(r.status_code, 400)


class TestAuth(TestCase):

    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='foo', password='bar')

    def test_login_success(self):
        """Test that correct username/password login succeeds"""

        r = self.client.get('login_view', data={
            'username': 'foo', 'password': 'bar',
        })
        self.assertEqual(r.status_code, 200)

    def test_login_failure(self):
        """Test that incorrect username/password login fails"""

        r = self.client.get('login_view', data={
            'username': 'nonexistent', 'password': 'pwd',
        })
        self.assertEqual(r.status_code, 403)

    def test_basic_auth_challenge(self):
        """Test that HTTP Basic Auth challenge is issued"""
        r = self.client.get('basic_auth_view')
        self.assertEqual(r.status_code, 401)

    def test_basic_auth_succeeds(self):
        """Test that HTTP Basic Auth succeeds"""

        r = self.client.get('basic_auth_view', extra={
            'HTTP_AUTHORIZATION': 'Basic ' +
                base64.b64encode(b'foo:bar').decode('ascii'),
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['id'], self.user.id)

    def test_basic_auth_invalid_auth_payload(self):
        """Test that invalid Basic Auth payload doesn't crash the pasrser"""

        r = self.client.get('basic_auth_view', extra={
            'HTTP_AUTHORIZATION': 'Basic xyz',
        })
        self.assertEqual(r.status_code, 401)

    def test_custom_auth_fn_returning_none_allows_request(self):
        r = self.client.get('custom_auth_method', data={'user': 'friend'})
        self.assertEqual(r.status_code, 200)

    def test_custom_auth_fn_returning_httpresponse_shortcuts_request(self):
        r = self.client.get('custom_auth_method', data={'user': 'foe'})
        self.assertEqual(r.status_code, 403)

    def test_custom_auth_fn_raising_exception_shortcuts_request(self):
        r = self.client.get('custom_auth_method',
            data={'user': 'exceptional-foe'})
        self.assertEqual(r.status_code, 403)

    def test_custom_auth_fn_with_invalid_return_value_is_a_bug(self):
        ex = None
        try:
            self.client.get('custom_auth_method')
        except TypeError as e:
            ex = e

        self.assertIsNotNone(ex)


class TestModelViews(TestCase):

    def setUp(self):
        self.client = TestClient()
        self.publisher = Publisher.objects.create(name='User Foo')
        self.author = Author.objects.create(name='User Foo')
        self.book = self.author.books.create(author=self.author, title='Book',
            isbn='1234',  price=Decimal('10.0'), publisher=self.publisher)

    def test_publisher_list(self):
        """Excercise listing objects via ListEndpoint"""

        r = self.client.get('publisher_list')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json), 1)
        self.assertEqual(r.json[0]['id'], self.publisher.id)

    def test_publisher_create(self):
        """Excercise creating objects via ListEndpoint"""

        r = self.client.post('publisher_list', data=json.dumps({
            'name': 'Another Publisher'
            }), content_type='application/json')
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Publisher.objects.filter(pk=r.json['id']).exists())

    def test_publisher_details(self):
        """Excercise getting a single object details via DetailEndpoint"""

        r = self.client.get('publisher_detail', pk=self.publisher.id)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['id'], self.publisher.id)

    def test_publisher_update(self):
        """Excercise updating an object via POST via DetailEndpoint"""

        r = self.client.put('publisher_detail', pk=self.publisher.id,
            content_type='application/json', data=json.dumps({
                'name': 'Changed Name'
            }))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['id'], self.publisher.id)
        p = Publisher.objects.get(id=self.publisher.id)
        self.assertEqual(p.name, 'Changed Name')

    def test_publisher_delete(self):
        """Excercise deleting an object via DetailEndpoint"""

        r = self.client.delete('publisher_detail', pk=self.publisher.id)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Publisher.objects.exists())

    def test_redonly_publisher_list_denies_creation(self):
        """Excercise method whitelist in ListEndpoint"""

        r = self.client.post('readonly_publisher_list', data=json.dumps({
            'name': 'Another Publisher'
            }), content_type='application/json')
        self.assertEqual(r.status_code, 405)

    def test_publisher_action(self):
        """Excercise RPC-style actions via ActionEndpoint"""

        r = self.client.post('publisher_action', pk=self.publisher.id,
            content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, {'result': 'done'})

    def test_book_details(self):
        """Excercise using custom lookup_field on a DetailEndpoint"""

        r = self.client.get('book_detail', isbn=self.book.isbn)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['id'], self.book.id)
