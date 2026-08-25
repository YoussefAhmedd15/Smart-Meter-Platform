from GXDLMSReader import GXDLMSReader
from GXDLMSSecureClient2 import GXDLMSSecureClient2

from gurux_dlms.enums import InterfaceType, Authentication
from gurux_common.io import Parity, StopBits
from gurux_serial.GXSerial import GXSerial
from gurux_dlms.objects import GXDLMSClock


# -------------------------------------------------
# DLMS client
# -------------------------------------------------

client = GXDLMSSecureClient2(True)

client.clientAddress = 1

# Physical server 17 + logical server 1
client.serverAddress = 0x91

client.authentication = Authentication.LOW
client.password = "12345678"

client.interfaceType = InterfaceType.HDLC_WITH_MODE_E


# -------------------------------------------------
# Serial connection
# -------------------------------------------------

media = GXSerial(None)

media.port = "COM6"
media.baudRate = 300
media.dataBits = 7
media.parity = Parity.EVEN
media.stopbits = StopBits.ONE


# -------------------------------------------------
# Reader
# -------------------------------------------------

reader = GXDLMSReader(
    client,
    media,
    3,
    None
)


# -------------------------------------------------
# Clock object
# -------------------------------------------------

clock = GXDLMSClock("0.0.1.0.0.255")


try:

    media.open()

    print("Connecting to meter...")

    reader.initializeConnection()

    # -------------------------------------------------
    # READ CURRENT TIME
    # -------------------------------------------------

    print("Reading current meter time...")

    current = reader.read(clock, 2)

    print("Current meter time:", current)

    # -------------------------------------------------
    # SET TIME TO 04:00:00
    # -------------------------------------------------

    print("Setting meter time to 04:00:00...")

    # GXDateTime has a Python datetime representation.
    dt = current.value

    print("Current Python datetime:", dt)

    new_time = dt.replace(
        hour=4,
        minute=0,
        second=0,
        microsecond=0
    )

    print("New time:", new_time)

    # Create a new GXDateTime from the new datetime.
    from gurux_dlms.GXDateTime import GXDateTime

    clock.time = GXDateTime(new_time)

    # -------------------------------------------------
    # WRITE ATTRIBUTE 2
    # -------------------------------------------------

    print("Writing clock...")

    reader.write(clock, 2)

    print("Clock written successfully.")

    # -------------------------------------------------
    # VERIFY
    # -------------------------------------------------

    print("Reading clock again...")

    verify = reader.read(clock, 2)

    print("Meter time after write:", verify)


finally:

    try:
        reader.close()
    except Exception:
        pass