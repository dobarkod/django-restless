# Django Restless

[![Build Status](https://secure.travis-ci.org/senko/DjangoRestless.png?branch=master)](http://travis-ci.org/senko/DjangoRestless)

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

Here's a simple view implementing an API endpoint greeting the caller:

    from restless.views import Endpoint

    class HelloWorld(Endpoint):
        def get(self, request):
            name = request.params.get('name', 'World')
            return {'message': 'Hello, %s!' % name}


## Installation

Django Restless is available from cheeseshop, so you can install it via pip:

    pip install DjangoRestless

For the latest and the greatest, you can also get it directly from git master:

    pip install -e git+ssh://github.com/senko/DjangoRestless/tree/master

## Documentation

Documentation is graciously hosted by ReadTheDocs: http://django-restless.rtfd.org/

## License

Copyright (C) 2012. by Senko Rašić and Django Restless contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
