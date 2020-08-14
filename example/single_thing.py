from action import ActionObject
from event import Event
from property import Property
from thing import Thing
from value import Value
from server import WebThingServer
import logging
import time
import uuid

log = logging.getLogger(__name__)


class OverheatedEvent(Event):
    def __init__(self, thing, data):
        Event.__init__(self, thing, "overheated", data=data)


class FadeActionObject(ActionObject):
    def __init__(self, thing, input_):
        ActionObject.__init__(self, uuid.uuid4().hex, thing, "fade", input_=input_)

    def invokeaction(self, args):
        time.sleep(args["duration"] / 1000)
        self.thing.set_property("brightness", args["brightness"])
        self.thing.add_event(OverheatedEvent(self.thing, 102))


def make_thing():
    thing = Thing(
        "urn:dev:ops:my-lamp-1234",
        "My Lamp",
        ["OnOffSwitch", "Light"],
        "A web connected lamp",
    )

    thing.add_property(
        Property(
            thing,
            "on",
            writeproperty=lambda v: print(v),
            initial_value=True,
            metadata={
                "@type": "OnOffProperty",
                "title": "On/Off",
                "type": "boolean",
                "description": "Whether the lamp is turned on",
            },
        )
    )
    thing.add_property(
        Property(
            thing,
            "brightness",
            writeproperty=lambda v: print(v),
            initial_value=50,
            metadata={
                "@type": "BrightnessProperty",
                "title": "Brightness",
                "type": "integer",
                "description": "The level of light from 0-100",
                "minimum": 0,
                "maximum": 100,
                "unit": "percent",
            },
        )
    )

    thing.add_available_action(
        "fade",
        {
            "title": "Fade",
            "description": "Fade the lamp to a given level",
            "input": {
                "type": "object",
                "required": ["brightness", "duration",],
                "properties": {
                    "brightness": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "unit": "percent",
                    },
                    "duration": {
                        "type": "integer",
                        "minimum": 1,
                        "unit": "milliseconds",
                    },
                },
            },
        },
        FadeActionObject,
    )

    thing.add_available_event(
        "overheated",
        {
            "description": "The lamp has exceeded its safe operating temperature",
            "type": "number",
            "unit": "degree celsius",
        },
    )

    return thing


def run_server():
    log.info("run_server")

    thing = make_thing()

    # If adding more than one thing, use MultipleThings() with a name.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(thing, port=80)
    try:
        log.info("starting the server")
        server.start()
    except KeyboardInterrupt:
        log.info("stopping the server")
        server.stop()
        log.info("done")


if __name__ == "__main__":
    log.basicConfig(
        level=10, format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )
    run_server()
