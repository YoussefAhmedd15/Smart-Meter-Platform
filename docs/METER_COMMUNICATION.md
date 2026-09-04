# Smart Meter DLMS/COSEM Communication Architecture

## Overview
This document details the hardware communication flow between the **Smart Meter Intelligence Platform** and Iskraemeco smart meters over serial optical probes, HDLC, and IEC 62056-21 Mode E protocol handshakes using the integrated **Gurux DLMS Python** library.

## Supported Protocols & Media
1. **HDLC_WITH_MODE_E**: Used for optical head serial communication on `COM6` (or standard serial interfaces). Starts at 300 baud rate (7E1), sends standard IEC 62056-21 identification request `/?!`, reads target meter identification response, executes baud rate switching to target baud rate (e.g., 9600), switches to HDLC framing, and executes DLMS SNRM/AARQ.
2. **HDLC**: Standard HDLC framing directly at target baud rate without Mode E optical handshake.
3. **WRAPPER**: TCP/IP socket encapsulation over port `4059` or ethernet media.

## DLMS/COSEM Connection Sequence

```text
+-------------------+                      +-------------------+
|  Platform Reader  |                      | Iskraemeco Meter  |
+---------+---------+                      +---------+---------+
          |                                          |
          |  1. Open Serial (300 Baud 7E1)           |
          |----------------------------------------->|
          |  2. Send Identification Request "/?!"    |
          |----------------------------------------->|
          |  3. Identification Response "/ISK5..."   |
          |<-----------------------------------------|
          |  4. ACK / Baudrate switch (9600 8N1)     |
          |----------------------------------------->|
          |  5. Send SNRM (Set Normal Response Mode) |
          |----------------------------------------->|
          |  6. Receive UA (Unnumbered Ack)          |
          |<-----------------------------------------|
          |  7. Send AARQ (Application Assoc Req)    |
          |----------------------------------------->|
          |  8. Receive AARE (Application Assoc Resp)|
          |<-----------------------------------------|
          |  9. Fetch Association View (GET-Request) |
          |----------------------------------------->|
          | 10. Read OBIS Attribute (e.g. 1.0.32.7.255)|
          |----------------------------------------->|
          | 11. Decoded Response (230.2 V)           |
          |<-----------------------------------------|
          | 12. Disconnect                           |
          |----------------------------------------->|
```

## Addressing Calculation
HDLC server addressing combines logical address and physical address:
$$\text{Server Address} = (\text{Logical Address} \ll 7) \mid (\text{Physical Address} \& \text{0x7F})$$

* Default Iskraemeco setup: Client Address = `1`, Logical Address = `0`, Physical Address = `11` $\rightarrow$ Server Address = `11`.

## Hardware Safety & Read-Only Policy
> [!IMPORTANT]
> To protect smart meter calibration, tariffs, and firmware integrity during testing, all communication mechanisms in the platform are strictly **READ-ONLY**. No `SET` or `ACTION` primitives are executed against hardware.
