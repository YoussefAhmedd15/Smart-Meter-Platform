# Smart Meter Intelligence Platform - Testing & Validation Guide

## Overview
The platform features an automated testing framework covering meter configuration, address calculation, OBIS parsing, DLMS exception handling, mock simulation, database models, failure similarity, and API endpoints.

## Executing Unit Tests
To run meter package tests:
```bash
python -m unittest meter/tests/test_meter.py
```

To execute pytest suite across backend and meter engine:
```bash
pytest backend/app/tests meter/tests
```

## Running CLI Meter Verification
Inspect available COM ports:
```bash
python -m meter.cli ports
```

Inspect connection status & settings:
```bash
python -m meter.cli status
```

Connect and discover Association View:
```bash
python -m meter.cli discover
```

Read Active Energy Import (+A):
```bash
python -m meter.cli read --obis 1.0.1.8.0.255 --attribute 2
```

Read all telemetry registers:
```bash
python -m meter.cli read-all
```
