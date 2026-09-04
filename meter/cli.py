import argparse
import json
import sys
import os

# Ensure meter workspace is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meter.config import MeterConfig, AppMode
from meter.reader import DLMSMeterReader
from meter.obis import COMMON_OBIS_CODES


def main():
    parser = argparse.ArgumentParser(
        description="Smart Meter Intelligence Platform - DLMS/COSEM CLI Tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: ports
    subparsers.add_parser("ports", help="List available serial COM ports")

    # Command: status
    subparsers.add_parser("status", help="Get meter connection status and config")

    # Command: connect
    subparsers.add_parser("connect", help="Initialize and connect to the smart meter")

    # Command: discover
    subparsers.add_parser("discover", help="Fetch association view and COSEM objects")

    # Command: read
    read_parser = subparsers.add_parser("read", help="Read specific OBIS code attribute")
    read_parser.add_argument(
        "--obis",
        type=str,
        default="1.0.1.8.0.255",
        help="OBIS code (e.g. 1.0.1.8.0.255)",
    )
    read_parser.add_argument(
        "--attribute",
        type=int,
        default=2,
        help="Attribute index (default: 2)",
    )

    # Command: read-all
    subparsers.add_parser("read-all", help="Read all registered OBIS telemetry registers")

    # Command: disconnect
    subparsers.add_parser("disconnect", help="Disconnect from meter")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    config = MeterConfig()
    reader = DLMSMeterReader(config)

    if args.command == "ports":
        try:
            from gurux_serial import GXSerial
            ports = GXSerial.getPortNames()
            print(json.dumps({"available_ports": list(ports)}, indent=2))
        except Exception:
            print(json.dumps({"available_ports": ["COM6 (Configured)"], "note": "Gurux serial check"}, indent=2))

    elif args.command == "status":
        info = reader.get_meter_information()
        print(json.dumps({
            "mode": config.app_mode.value,
            "config": config.sanitized_dict(),
            "meter_info": info,
        }, indent=2, default=str))

    elif args.command == "connect":
        connected = reader.connect()
        init_res = reader.initialize()
        print(json.dumps({
            "connected": connected,
            "handshake": init_res,
        }, indent=2))

    elif args.command == "discover":
        reader.connect()
        assoc = reader.get_association_view()
        print(json.dumps(assoc.model_dump(), indent=2, default=str))

    elif args.command == "read":
        reader.connect()
        res = reader.read_obis(args.obis, args.attribute)
        print(json.dumps(res.model_dump(), indent=2, default=str))

    elif args.command == "read-all":
        reader.connect()
        results = reader.read_all()
        output = [r.model_dump() for r in results]
        print(json.dumps(output, indent=2, default=str))

    elif args.command == "disconnect":
        disc = reader.disconnect()
        print(json.dumps({"disconnected": disc}, indent=2))


if __name__ == "__main__":
    main()
