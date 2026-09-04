# OBIS Map Reference Guide

## Overview
OBIS (Object Identification System) codes define the identification structure for DLMS/COSEM data objects exposed by Iskraemeco and standard IEC 62056 smart electricity meters.

> [!NOTE]
> All OBIS definitions in the Smart Meter Intelligence Platform are dynamically mapped. If an unknown OBIS code is encountered during Association View discovery, the platform registers it automatically as a vendor-specific object without crashing.

## Electrical Parameters & Standard OBIS Codes

| OBIS Code | COSEM Class ID | Object Name | Description | Default Unit |
| :--- | :---: | :--- | :--- | :---: |
| `1.0.1.8.0.255` | 3 (Register) | Active Energy Import (+A) | Total cumulative active import energy | `kWh` |
| `1.0.2.8.0.255` | 3 (Register) | Active Energy Export (-A) | Total cumulative active export energy | `kWh` |
| `1.0.32.7.0.255` | 3 (Register) | Instantaneous Voltage L1 | RMS voltage on phase 1 | `V` |
| `1.0.52.7.0.255` | 3 (Register) | Instantaneous Voltage L2 | RMS voltage on phase 2 | `V` |
| `1.0.72.7.0.255` | 3 (Register) | Instantaneous Voltage L3 | RMS voltage on phase 3 | `V` |
| `1.0.31.7.0.255` | 3 (Register) | Instantaneous Current L1 | RMS current on phase 1 | `A` |
| `1.0.51.7.0.255` | 3 (Register) | Instantaneous Current L2 | RMS current on phase 2 | `A` |
| `1.0.71.7.0.255` | 3 (Register) | Instantaneous Current L3 | RMS current on phase 3 | `A` |
| `1.0.1.7.0.255` | 3 (Register) | Active Power (+P) | Total active power demand | `W` |
| `1.0.14.7.0.255` | 3 (Register) | Network Frequency | Electrical grid frequency | `Hz` |
| `1.0.13.7.0.255` | 3 (Register) | Power Factor | Displacement power factor | N/A |
| `0.0.1.0.0.255` | 8 (Clock) | Real-Time Clock | Internal device clock & timestamp | N/A |
| `1.0.99.1.0.255` | 7 (Profile Generic) | Load Profile 1 | 15-minute periodic interval data | N/A |
| `0.0.96.1.1.255` | 1 (Data) | Meter Serial Number | Manufacturer hardware serial ID | N/A |
| `0.0.96.1.0.255` | 1 (Data) | Firmware Version | Internal firmware identifier | N/A |

## Attribute Mapping Standard
* **Attribute 1**: Logical Name (OBIS code in bytes).
* **Attribute 2**: Value (Data value or scaled numeric value).
* **Attribute 3**: Scaler and Unit (Multiplier $10^{\text{scaler}}$ and physical unit code).
