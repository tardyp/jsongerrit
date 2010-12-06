# a port of xmlrpclib to json....
#
#
# The JSON-RPC client interface is based on the XML-RPC client
#
# Copyright (c) 1999-2002 by Secret Labs AB
# Copyright (c) 1999-2002 by Fredrik Lundh
# Copyright (c) 2006 by Matt Harrison
# Copyright (c) 2010 by Pierre Tardy
#                    - moved to urlib2
#                    - use keepalive
#                    - return objects instead if dicts
#                    - add some headers to comply with gerrit
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and
# its associated documentation for any purpose and without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# Secret Labs AB or the author not be used in advertising or publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANT-
# ABILITY AND FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
# --------------------------------------------------------------------

import urllib
import urllib2
import httplib
import base64
import simplejson
import types
import traceback
import cache
__version__ = "0.0.3"

ID = 1
def _gen_id():
    global ID
    ID = ID + 1
    return ID



def dumps(params, methodname=None, methodresponse=None, encoding=None,
          allow_none=0):
    if methodname:
        request = {}
        request["jsonrpc"] = "2.0"
        request["method"] = methodname
        request["params"] = params
        request["id"] = _gen_id()
        return simplejson.dumps(request)


class dict2obj:
    def __init__(self,_dict):
        self._dict = _dict
    def __nonzero__(self):
        return True
    def __repr__(self):
        return str(self)
    def __str__(self):
        s = "{"
        for k,v in self._dict.items():
            if type(v)==dict:
                v = dict2obj(v)
            elif type(v) == list:
                v= [ (type(i) == dict) and dict2obj(i) or i for i in v]
            s+= "%s:%s\n"%(repr(k),repr(v).replace("\n","\n\t"))
        return s+"}"
    def __getattr__(self,name):
        v = self._dict[name]
        if type(v) == dict:
            return dict2obj(v)
        if type(v) == list:
            return [ (type(i) == dict) and dict2obj(i) or i for i in v]
        if type(v) == type(""):
            return v.encode("utf-8")
        if type(v) == type(u""):
            return v.encode("utf-8")
        return v
    def has_key(self,name):
        return self._dict.has_key(name)
class _Method(object):
    # some magic to bind an JSON-RPC method to an RPC server.
    # supports "nested" methods (e.g. examples.getStateName)
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args):
        return dict2obj(self.__send(self.__name, args))

from keepalive import HTTPHandler
keepalive_handler = HTTPHandler()
opener = urllib2.build_opener(keepalive_handler)
urllib2.install_opener(opener)

class urllibTransport():
    def __init__(self,uri):
        self.uri = uri
    def request(self, request_body, verbose=1,update_cache=False):
        rsp = cache.load(self.uri+request_body)
        if rsp == None or update_cache:
            req = urllib2.Request(url=self.uri)
            req.add_data(data=request_body)
            headers =  [ ('Content-Type', 'application/json; charset=utf-8'),
            ('Accept-Encoding', 'text'),
            ('Accept', 'application/json,application/json,application/jsonrequest')]
            for t,v in headers:
                req.add_header(t,v)
            rsp = urllib2.urlopen(req).read()
            cache.store(self.uri+request_body,rsp)
        return simplejson.loads(rsp)

class ServerProxy(object):

    def __init__(self, uri, transport=None, encoding=None,
                 verbose=None, allow_none=0,update_cache=False):
        transport=urllibTransport(uri)
        self.__transport = transport

        self.__encoding = encoding
        self.__verbose = verbose
        self.__allow_none = allow_none

    def __request(self, methodname, params):
        """call a method on the remote server
        """

        request = dumps(params, methodname, encoding=self.__encoding,
                        allow_none=self.__allow_none)
        while True:
            try:
                response = self.__transport.request(
                    request,
                    verbose=self.__verbose
                    )
                break
            except KeyboardInterrupt:
                raise Exception ("stop")
            except:
                traceback.print_exc()
                continue

        if len(response) == 1:
            response = response[0]

        return response

    def __repr__(self):
        return ("<JSONProxy for %s%s>" %
                (self.__host, self.__handler)
                )

    __str__ = __repr__

    def __getattr__(self, name):
        #dispatch
        return _Method(self.__request, name)

    # note: to call a remote object with an non-standard name, use
    # result getattr(server, "strange-python-name")(args)


if __name__ == "__main__":
    s = ServerProxy("http://localhost:8080/foo/", verbose = 1)
    c = s.echo("foo bar")
    print c
    d = s.bad("other")
    print d
    e = s.echo("foo bar", "baz")
    print e
    f = s.echo(5)
    print f
