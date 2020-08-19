# These should be edited to reflect your actual SSID and password

SSID = "FRITZ!Box 3490"
PASSWORD = "happyelephantpeanutbucket!"

if SSID == "":
    print("Please edit config.py and set the SSID and password")
    raise ValueError("SSID not set")
