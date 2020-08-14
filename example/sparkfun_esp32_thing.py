from property import Property
from action import Action
from thing import Thing
from value import Value
from server import MultipleThings, WebThingServer
import logging
import time
import machine

log = logging.getLogger(__name__)


class Led(Thing):
    def __init__(self, ledPin, buttonPin):
        Thing.__init__(
            self,
            "urn:dev:ops:blue-led-1234",
            "Blue LED",
            ["OnOffSwitch", "Light"],
            "Blue LED on SparkFun ESP32 Thing",
        )
        # LED setup
        self.pinLed = machine.Pin(ledPin, machine.Pin.OUT)
        self.pwmLed = machine.PWM(self.pinLed)
        self.ledBrightness = 50
        self.on = False
        self.updateLed()

        # Button setup
        self.pinButton = machine.Pin(buttonPin, machine.Pin.IN)

        self.add_property(
            Property(
                self,
                "on",
                readproperty=self.getOnOff,
                writeproperty=self.setOnOff,
                metadata={
                    "@type": "OnOffProperty",
                    "title": "On/Off",
                    "type": "boolean",
                    "description": "Whether the LED is turned on",
                },
            )
        )
        self.add_property(
            Property(
                self,
                "brightness",
                readproperty=self.getBrightness,
                writeproperty=self.setBrightness,
                metadata={
                    "@type": "BrightnessProperty",
                    "title": "Brightness",
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "unit": "percent",
                    "description": "The brightness of the LED",
                },
            )
        )
        self.add_property(
            Property(
                self,
                "pressed",
                readproperty=self.getPressed,
                metadata={
                    "type": "boolean",
                    "description": "Button 0 pressed",
                    "readOnly": True,
                },
            )
        )
        self.add_action(
            Action(
                self,
                "fade",
                invokeaction=fadeBrightness,
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
        )

    def setOnOff(self, onOff):
        log.info("setOnOff: onOff = " + str(onOff))
        self.on = onOff
        self.updateLed()

    def getOnOff(self):
        return self.on

    def setBrightness(self, brightness):
        log.info("setBrightness: brightness = " + str(brightness))
        self.ledBrightness = brightness
        self.updateLed()

    def getBrightness(self):
        return self.ledBrightness

    def fadeBrightness(self, args):
        time.sleep(args["duration"] / 1000)
        setBrightness(args["brightness"])

    def updateLed(self):
        log.debug(
            "updateLed: on = "
            + str(self.on)
            + " brightness = "
            + str(self.ledBrightness)
        )
        if self.on:
            self.pwmLed.duty(self.ledBrightness)
        else:
            self.pwmLed.duty(0)

    def getPressed(self):
        return self.pin.value() == 0


def run_server():
    log.info("run_server")

    led = Led(5, 0)

    server = WebThingServer(led, "SparkFun-ESP32-Thing", port=80)
    try:
        log.info("starting the server")
        server.start()
    except KeyboardInterrupt:
        log.info("stopping the server")
        server.stop()
        log.info("done")

    while True:
        time.sleep(0.1)
        button.process()
