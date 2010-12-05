# a port of xmlrpclib to json....
#
#
# The JSON-RPC client interface is based on the XML-RPC client
#
# Copyright (c) 1999-2002 by Secret Labs AB
# Copyright (c) 1999-2002 by Fredrik Lundh
# Copyright (c) 2006 by Matt Harrison
# Copyright (c) 2010 by Pierre Tardy 
#                    - moved to httplib 2.4
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
import httplib
import base64
import simplejson
import types
import cache
__version__ = "0.0.2"

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
        else:
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

##
# Standard transport class for JSON-RPC over HTTP.
# <p>
# You can create custom transports by subclassing this method, and
# overriding selected methods.

class Transport:
    """Handles an HTTP transaction to an JSON-RPC server."""

    # client identifier (may be overridden)
    user_agent = "jsonlib.py/%s (by matt harrison)" % __version__
    h = None
    ##
    # Send a complete request, and parse the response.
    #
    # @param host Target host.
    # @param handler Target PRC handler.
    # @param request_body JSON-RPC request body.
    # @param verbose Debugging flag.
    # @return Parsed response.

    def request(self, host, handler, request_body, verbose=1,update_cache=False):
        rsp = cache.load(host+handler+request_body)
        if rsp == None or update_cache:
            # issue JSON-RPC request
            if self.h==None:
                self.h = self.make_connection(host)
            h = self.h # keep alive
            if verbose:
                h.set_debuglevel(1)
            self.send_request(h, handler, request_body)
            self.send_host(h, host)
            self.send_user_agent(h)
            self.send_content(h, request_body)

            rsp = h.getresponse()

            if rsp.status != 200:
                raise Exception(
                    host + handler,
                    rsp.status, rsp.reason,
                    rsp.getheaders()
                    )

            self.verbose = verbose
            rsp = self._parse_response(rsp)
            cache.store(host+handler+request_body,rsp)
        return simplejson.loads(rsp)

    ##
    # Get authorization info from host parameter
    # Host may be a string, or a (host, x509-dict) tuple; if a string,
    # it is checked for a "user:pw@host" format, and a "Basic
    # Authentication" header is added if appropriate.
    #
    # @param host Host descriptor (URL or (URL, x509 info) tuple).
    # @return A 3-tuple containing (actual host, extra headers,
    #     x509 info).  The header and x509 fields may be None.

    def get_host_info(self, host):

        x509 = {}
        if isinstance(host, types.TupleType):
            host, x509 = host

        auth, host = urllib.splituser(host)

        if auth:
            auth = base64.encodestring(urllib.unquote(auth))
            auth = string.join(string.split(auth), "") # get rid of whitespace
            extra_headers = [
                ("Authorization", "Basic " + auth)
                ]
        else:
            extra_headers = None

        return host, extra_headers, x509

    ##
    # Connect to server.
    #
    # @param host Target host.
    # @return A connection handle.

    def make_connection(self, host):
        # create a HTTP connection object from a host descriptor
        host, extra_headers, x509 = self.get_host_info(host)
        return httplib.HTTPConnection(host)

    ##
    # Send request header.
    #
    # @param connection Connection handle.
    # @param handler Target RPC handler.
    # @param request_body JSON-RPC body.

    def send_request(self, connection, handler, request_body):
        connection.putrequest("POST", handler)

    ##
    # Send host name.
    #
    # @param connection Connection handle.
    # @param host Host name.

    def send_host(self, connection, host):
        host, extra_headers, x509 = self.get_host_info(host)
        connection.putheader("Host", host)
        if extra_headers:
            if isinstance(extra_headers, DictType):
                extra_headers = extra_headers.items()
            for key, value in extra_headers:
                connection.putheader(key, value)

    ##
    # Send user-agent identifier.
    #
    # @param connection Connection handle.

    def send_user_agent(self, connection):
        connection.putheader("User-Agent", self.user_agent)

    ##
    # Send request body.
    #
    # @param connection Connection handle.
    # @param request_body JSON-RPC request body.

    def send_content(self, connection, request_body):
        connection.putheader("Accept-Encoding",	"text")
        connection.putheader("Connection","Keep-Alive")
        connection.putheader("Accept",	"application/json,application/json,application/jsonrequest")
        connection.putheader("Content-Type", "application/json; charset=utf-8")
        connection.putheader("Content-Length", str(len(request_body)))
        connection.endheaders()
        if request_body:
            connection.send(request_body)

    ##
    # Parse response feed the response to parser and unmarshaller
    #
    # @param rsp HTTPResponse.
    # @return Response tuple and target method.

    def _parse_response(self, rsp):
        # read response from input file/socket, and parse it

        remain= int(rsp.getheader("Content-Length"))
        data = ""
        while remain:
            sz = min(remain,1024)
            response = rsp.read(sz)
            if not response:
                break
            if self.verbose:
                print "body:", repr(response)
            data+=response
            remain-=len(response)
        return data

##
# Standard transport class for JSON-RPC over HTTPS.

class SafeTransport(Transport):
    """Handles an HTTPS transaction to an JSON-RPC server."""

    # FIXME: mostly untested

    def make_connection(self, host):
        # create a HTTPS connection object from a host descriptor
        # host may be a string, or a (host, x509-dict) tuple
        host, extra_headers, x509 = self.get_host_info(host)
        try:
            HTTPS = httplib.HTTPSConnection
        except AttributeError:
            raise NotImplementedError(
                "your version of httplib doesn't support HTTPS"
                )
        else:
            return HTTPS(host, None, **(x509 or {}))


class ServerProxy(object):

    def __init__(self, uri, transport=None, encoding=None,
                 verbose=None, allow_none=0,update_cache=False):
        utype, uri = urllib.splittype(uri)
        self.update_cache = update_cache
        if utype not in ("http", "https"):
            raise IOError, "Unsupported JSONRPC protocol"
        self.__host, self.__handler = urllib.splithost(uri)
        if not self.__handler:
            self.__handler = "/RPC2"

        if transport is None:
            if utype == "https":
                transport = SafeTransport()
            else:
                transport = Transport()
        self.__transport = transport

        self.__encoding = encoding
        self.__verbose = verbose
        self.__allow_none = allow_none

    def __request(self, methodname, params):
        """call a method on the remote server
        """

        request = dumps(params, methodname, encoding=self.__encoding,
                        allow_none=self.__allow_none)
        response = self.__transport.request(
            self.__host,
            self.__handler,
            request,
            verbose=self.__verbose
            )

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
