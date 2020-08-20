import sys

sys.path.append("/webthing")
sys.path.append("/example")

import logging
import connect

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

connect.connect_to_ap()
connect.start_ntp()

from action import Action
from property import Property
from thing import Thing
from value import Value
from server import WebThingServer
import logging
import time
import uuid

log = logging.getLogger(__name__)


def make_thing():
    thing = Thing(
        "urn:dev:ops:my-lamp-1234",
        "My Lamp",
        ["OnOffSwitch", "Light"],
        "A web connected lamp",
    )

    on_property = Property(
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

    brightness_property = Property(
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

    thing.add_property(on_property)
    thing.add_property(brightness_property)

    def fade_function(args):
        time.sleep(args["duration"] / 1000)
        brightness_property.set_value(args["brightness"])

    fade_action = Action(
        thing,
        "fade",
        invokeaction=fade_function,
        metadata={
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
    )

    thing.add_action(fade_action)

    return thing


def run_server():
    log.info("run_server")

    thing = make_thing()

    # If adding more than one thing, use MultipleThings() with a name.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(thing)
    try:
        log.info("starting the server")
        server.start()
    except KeyboardInterrupt:
        log.info("stopping the server")
        server.stop()
        log.info("done")


if __name__ == "__main__":
    run_server()
