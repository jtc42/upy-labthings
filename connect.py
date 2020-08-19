import machine
import ntptime
import network
import time
import config


def start_ftp():
    print("Starting FTP...")
    network.ftp.start()


def start_ntp():
    print("Syncing to NTP...")
    rtc = machine.RTC()
    ntptime.settime()
    print("Time:")
    print(time.localtime())


def connect_to_ap():
    station = network.WLAN(network.STA_IF)
    if not station.active():
        station.active(True)
        if not station.isconnected():
            print("Connecting....")
            station.connect(config.SSID, config.PASSWORD)
            while not station.isconnected():
                time.sleep(1)
                print(".", end="")
            print("")
    print("ifconfig =", station.ifconfig())

