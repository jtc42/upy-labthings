"""Python Web Thing server implementation."""

from MicroWebSrv2 import MicroWebSrv2, RegisterRoute
import _thread
import upy.logging
import sys
import network
from time import sleep

import gc

from errors import PropertyError
from utils import get_addresses
from thing import Thing

log = logging.getLogger(__name__)

# set to True to print WebSocket messages
WS_messages = True

# =================================================
# Recommended configuration:
#   - run microWebServer in thread
#   - do NOT run MicroWebSocket in thread
# =================================================
# Run microWebServer in thread
srv_run_in_thread = True
# Run microWebSocket in thread
ws_run_in_thread = False

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept",
    "Access-Control-Allow-Methods": "GET, HEAD, PUT, POST, DELETE",
}


def print_exc(func):
    """Wrap a function and print an exception, if encountered."""

    def wrapper(*args, **kwargs):
        try:
            # log.debug('Calling {}'.format(func.__name__))
            ret = func(*args, **kwargs)
            # log.debug('Back from {}'.format(func.__name__))
            return ret
        except Exception as err:
            sys.print_exception(err)

    return wrapper


class WebThingServer:
    """Server to represent a Web Thing over HTTP."""

    def __init__(
        self,
        thing: Thing,
        port: int = 80,
        hostname: str = None,
        ssl_options=None,
        additional_routes=None,
    ):
        """
        Initialize the WebThingServer.

        things -- list of Things managed by this server
        port -- port to listen on (defaults to 80)
        hostname -- Optional host name, i.e. mything.com
        ssl_options -- dict of SSL options to pass to the tornado server
        additional_routes -- list of additional routes to add to the server
        """
        self.ssl_suffix = "" if ssl_options is None else "s"

        self.thing = thing
        self.name = thing.title
        self.port = port
        self.hostname = hostname

        station = network.WLAN()
        mac = station.config("mac")
        self.system_hostname = "esp32-upy-{:02x}{:02x}{:02x}".format(
            mac[3], mac[4], mac[5]
        )

        self.hosts = [
            "localhost",
            "localhost:{}".format(self.port),
            "{}.local".format(self.system_hostname),
            "{}.local:{}".format(self.system_hostname, self.port),
        ]

        for address in get_addresses():
            self.hosts.extend(
                [address, "{}:{}".format(address, self.port),]
            )

        if self.hostname is not None:
            self.hostname = self.hostname.lower()
            self.hosts.extend(
                [self.hostname, "{}:{}".format(self.hostname, self.port),]
            )

        log.info("Registering a single thing")
        handlers = [
            ("/.*", "OPTIONS", self.optionsHandler),
            ("/", "GET", self.thingGetHandler),
            ("/properties", "GET", self.propertiesGetHandler),
            ("/properties/<property_name>", "GET", self.propertyGetHandler),
            ("/properties/<property_name>", "PUT", self.propertyPutHandler),
        ]

        if isinstance(additional_routes, list):
            handlers = additional_routes + handlers

        self.server = MicroWebSrv2()
        self.server.SetEmbeddedConfig()
        self.server.BindAddress = ("0.0.0.0", self.port)

        for handler in handlers:
            print((handler[2], handler[1], handler[0]))
            RegisterRoute(handler[2], handler[1], handler[0])

        wsMod = self.server.LoadModule("WebSockets")
        wsMod.OnWebSocketAccepted = self._OnWebSocketAcceptedCallback

    def start(self):
        """Start listening for incoming connections."""
        # If WebSocketS used and NOT running in thread, and WebServer IS
        # running in thread make shure WebServer has enough stack size to
        # handle also the WebSocket requests.
        log.info("Starting Web Server on port {}".format(self.port))
        self.server.StartManaged(procStackSize=12 * 1024)

        if hasattr(network, "mDNS"):
            mdns = network.mDNS()
            mdns.start(self.system_hostname, "MicroPython with mDNS")
            mdns.addService(
                "_labthing",
                "_tcp",
                80,
                self.system_hostname,
                {"board": "ESP32", "path": "/",},
            )

        try:
            while self.server.IsRunning:
                sleep(1)
        except KeyboardInterrupt:
            pass

    def stop(self):
        """Stop listening."""
        self.server.Stop()

    def getProperty(self, routeArgs):
        """Get the property name based on the route."""
        thing = self.thing
        if thing:
            property_name = routeArgs["property_name"]
            if thing.has_property(property_name):
                return thing, thing.find_property(property_name)
        return None, None

    def getHeader(self, headers, key, default=None):
        standardized = {k.lower(): v for k, v in headers.items()}
        return standardized.get(key, default)

    def validateHost(self, headers):
        """Validate the Host header in the request."""
        host = httpRequest.GetHeader(headers, "host")
        if host is not None and host.lower() in self.hosts:
            return True

        return False

    @print_exc
    def optionsHandler(self, microWebSrv2, request):
        """Handle an OPTIONS request to any path."""
        request.Response.Return(204)

    @print_exc
    def thingGetHandler(self, microWebSrv2, request):
        """Handle a GET request for an individual thing."""

        thing = self.thing
        if thing is None:
            request.Response.ReturnNotFound()
            return

        base_href = "http{}://{}".format(self.ssl_suffix, request.GetHeader("host"))
        ws_href = "ws{}://{}".format(self.ssl_suffix, request.GetHeader("host"))

        description = thing.as_thing_description()
        description["links"].append(
            {"rel": "alternate", "href": "{}{}".format(ws_href, thing.get_href()),}
        )
        description["base"] = "{}{}".format(base_href, thing.get_href())
        description["securityDefinitions"] = {
            "nosec_sc": {"scheme": "nosec",},
        }
        description["security"] = "nosec_sc"
        request.Response.ReturnOkJSON(description)

    @print_exc
    def propertiesGetHandler(self, microWebSrv2, request):
        """Handle a GET request for a property."""
        thing = self.thing
        if thing is None:
            request.Response.ReturnNotFound()
            return
        request.Response.ReturnOkJSON(thing.get_properties())

    @print_exc
    def propertyGetHandler(self, microWebSrv2, request, routeArgs):
        """Handle a GET request for a property."""
        thing, prop = self.getProperty(routeArgs)
        if thing is None:
            request.Response.ReturnNotFound()
            return

        request.Response.ReturnOkJSON(prop.get_value())

    @print_exc
    def propertyPutHandler(self, microWebSrv2, request, routeArgs):
        """Handle a PUT request for a property."""
        thing, prop = self.getProperty(routeArgs)
        if thing is None:
            request.Response.ReturnNotFound()
            return

        args = request.GetPostedJSONObject()
        content = request.Content
        print(content)
        if args is None:
            request.Response.ReturnBadRequest()
            return
        try:
            prop.set_value(args)
        except PropertyError:
            request.Response.ReturnBadRequest()
            return

        request.Response.ReturnOkJSON(prop.get_value())

    # === MicroWebSocket callbacks ===

    @print_exc
    def _OnWebSocketAcceptedCallback(self, microWebSrv2, webSocket):
        if WS_messages:
            if ws_run_in_thread or srv_run_in_thread:
                # Print thread list so that we can monitor maximum stack size
                # of WebServer thread and WebSocket thread if any is used
                _thread.list()
        webSocket.OnTextMessage = self._OnTextMessageCallback
        webSocket.OnBinaryMessage = self._OnBinaryMessageCallback
        webSocket.OnClosed = self._OnClosedCallback
        webSocket.thing = self.thing
        self.thing.add_subscriber(webSocket)

    @print_exc
    def _OnTextMessageCallback(self, webSocket, msg):
        if WS_messages:
            print("WS RECV TEXT : %s" % msg)

    @print_exc
    def _OnBinaryMessageCallback(self, webSocket, data):
        if WS_messages:
            print("WS RECV DATA : %s" % data)

    @print_exc
    def _OnClosedCallback(self, webSocket):
        if WS_messages:
            if ws_run_in_thread or srv_run_in_thread:
                _thread.list()
            print("WS CLOSED")
