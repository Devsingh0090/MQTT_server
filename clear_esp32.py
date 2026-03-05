#!/usr/bin/env python3
"""Publish a CLEAR command to the ESP32 control topic to remove stored IDs.

Usage: python clear_esp32.py [--broker BROKER] [--port PORT] [--topic TOPIC]
"""
import argparse
import time
import paho.mqtt.client as mqtt


def publish_clear(broker, port, topic, timeout=10):
    client = mqtt.Client()
    client.connect(broker, port, 60)
    # give the broker a moment
    client.loop_start()
    client.publish(topic, payload="CLEAR")
    # wait briefly to ensure delivery
    time.sleep(0.5)
    client.loop_stop()
    client.disconnect()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--broker", default="test.mosquitto.org")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--topic", default="server18/ctrl")
    args = p.parse_args()
    print(f"Publishing CLEAR to {args.topic} @ {args.broker}:{args.port}")
    publish_clear(args.broker, args.port, args.topic)
    print("Done")


if __name__ == '__main__':
    main()
