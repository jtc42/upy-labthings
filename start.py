import sys
import logging
import connect

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

sys.path.append("/flash/upy")
sys.path.append("/flash/webthing")
sys.path.append("/flash/example")

connect.connect_to_ap()
connect.start_ntp()


def rgb():
    print("importing esp32_wrover_kit_rgb...")
    import esp32_wrover_kit_rgb

    print("Starting esp32_wrover_kit_rgb server...")
    esp32_wrover_kit_rgb.run_server()


def single():
    print("importing single_thing...")
    import single_thing

    print("Starting single_thing server...")
    single_thing.run_server()


def thing():
    print("importing sparkfun_esp32_thing...")
    import sparkfun_esp32_thing

    print("Starting sparkfun_esp32_thing server...")
    sparkfun_esp32_thing.run_server()
