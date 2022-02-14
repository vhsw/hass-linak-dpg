"""
Wrapper for bluetoothctl
"""

import sys
import time

import pexpect


class BTctl:
    """A wrapper for bluetoothctl utility."""

    def __init__(self):
        """Initalize shell."""
        self.process = pexpect.spawnu("bluetoothctl", echo=False)

    def convertHexStr(self, hexStr):
        """Convert Hex string to human readable."""
        value = int(hexStr[:2], 16) + (int(hexStr[3:5], 16) << 8)

        if (value & 0x8000) == 0x8000:
            value = -((value ^ 0xFFFF) + 1)

        return value

    def run(self, command, expectations=None, timeout=1):
        """Run command in shell."""
        if expectations is None:
            expectations = []
        self.process.send(f"{command}\n")
        time.sleep(timeout)

        expectations.append(pexpect.EOF)

        result = self.process.expect_exact(expectations, 3)
        if result == len(expectations) - 1:
            raise Exception("Unexpected response")

        return result

    def get_output(self, command, expectations=None, timeout=1):
        """Run command and get output from shell."""
        if expectations is None:
            expectations = []
        result = self.run(command, expectations, timeout)

        if result != 0:
            raise Exception("Failed to receive info.")

        output = self.process.before.strip() if self.process.before else ""
        return self.clean_output(output)

    def clean_output(self, input):
        """Remove unwanted characters from output."""
        formatting = ["\x1b[?2004h\x1b", "\x1b[0m", "\x1b[?2004l", "[0;94m", "\n"]

        for format in formatting:
            input = input.replace(format, "")

        return [substring.strip() for substring in input.split("\r")]

    def scan_start(self):
        """Start scanning for devices."""
        result = self.run("scan on", ["Discovery started"], 5)
        if result != 0:
            raise Exception("Failed to start scanning")

        return True

    def scan_stop(self):
        """Stop scanning for devices."""
        result = self.run("scan off", ["Discovery stopped"])
        if result != 0:
            raise Exception("Failed to stop scanning")

        return True

    def device_info(self, mac_address):
        """Get device info."""
        result = self.run(f"info {mac_address}", ["Name:", "not available"])

        if result != 0:
            raise Exception("Failed to receive device info")

        return True

    def pair(self, mac_address):
        """Try to pair device."""
        result = self.run(
            f"pair {mac_address}", ["Pairing successful", "Failed to pair"], 5
        )

        if result != 0:
            raise Exception("Failed to pair device")

        return True

    def connect(self, mac_address):
        """Try to connect to device."""
        result = self.run(
            f"connect {mac_address}",
            ["Connection successful", "Failed to connect", "not available"],
            3,
        )

        if result != 0:
            raise Exception("Failed to establish connection")

        return True

    def gatt(self):
        """Try to enter Generic Attribute mode."""
        return self._extracted_from_menu_3(
            "menu gatt", "Failed to enter Generic Attribute mode."
        )

    def menu(self):
        """Try to enter default mode."""
        return self._extracted_from_menu_3("back", "Failed to enter default mode.")

    # TODO Rename this here and in `gatt` and `menu`
    def _extracted_from_menu_3(self, arg0, arg1):
        result = self.run(arg0, ["Print environment variables", "Invalid command"])
        if result != 0:
            raise Exception(arg1)
        return True

    def attribute_info(self, uuid):
        """Try to get attribute info."""
        return self.get_output(f"attribute-info {uuid}", ["Flags:"])

    def attribute_read_value(self, uuid):
        """Try to read value from attribute."""
        self.run(f"select-attribute {uuid}", [":/service"])
        return self.get_output("read", ["..."])
