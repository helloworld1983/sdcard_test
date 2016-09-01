#!/usr/bin/python3
import logging
import serial


class CommUART:
    msg_type = {
        "write": 0x01,
        "read":  0x02
    }
    def __init__(self, port, baudrate=115200, debug=False):
        self.port = port
        self.baudrate = str(baudrate)
        self.debug = debug
        self.port = serial.serial_for_url(port, baudrate)

    def open(self):
        if hasattr(self, "port"):
            return
        self.port.open()

    def close(self):
        if not hasattr(self, "port"):
            return
        self.port.close()
        del self.port

    def _read(self, length):
        r = bytes()
        while len(r) < length:
            r += self.port.read(length - len(r))
        return r

    def _write(self, data):
        remaining = len(data)
        pos = 0
        while remaining:
            written = self.port.write(data[pos:])
            remaining -= written
            pos += written

    def read(self, addr, length=None):
        data = []
        length_int = 1 if length is None else length
        self._write([self.msg_type["read"], length_int])
        self._write(list((addr//4).to_bytes(4, byteorder="big")))
        for i in range(length_int):
            value = int.from_bytes(self._read(4), "big")
            if self.debug:
                print("read {:08x} @ {:08x}".format(value, addr + 4*i))
            if length is None:
                return value
            data.append(value)
        return data

    def write(self, addr, data):
        data = data if isinstance(data, list) else [data]
        length = len(data)
        offset = 0
        while length:
            size = min(length, 8)
            self._write([self.msg_type["write"], size])
            self._write(list(((addr+offset)//4).to_bytes(4, byteorder="big")))
            for i, value in enumerate(data[offset:offset+size]):
                self._write(list(value.to_bytes(4, byteorder="big")))
                if self.debug:
                    print("write {:08x} @ {:08x}".format(value, addr + offset, 4*i))
            offset += size
            length -= size


myuart = CommUART("/dev/ttyUSB0")

def mywrite(offset, val):
    myuart.write(0x50000000 + (offset*4 ), val)
    
def myread(offset):
    return myuart.read(0x50000000 + (4*offset))


def myprint():
    print("---")
    for i in range(0x64//4):
        val = myread( i*4)
        print("{0:02x}: {1:08x}".format(i*4, val))

def perform( dat, arg):
    mywrite(4, dat)
    mywrite(0, arg)
    myprint()
#for i in range(0x60):
#    myuart.write( 0x50000000 + i, 0xdead0000+i)

mywrite(0x28, 0x1)
mywrite(0x28, 0x0)
myprint()

mywrite(0x18, 0xfff)
mywrite(0x20, 0xfff)
mywrite(0x24, 0)
mywrite(0x1c, 1)
mywrite(0x60, 0x20000000)
mywrite(0x48, 1)


perform(0, 0)
perform(0x0801, 0x155)
perform(0x2719, 0)
perform(0x2901, 0)

resp = 0
while resp & 0x80000000 == 0:
    perform(0x3719, 0)
    perform(0x2901, 0x41ff8000)
    resp = myread(8)

perform(0x20a, 0)
perform (0x319, 0)
perform(0x719, 0)
perform(0x719, 0x12340000)
print("DONE1")
perform(0x1159, 0x12340000)
print("DONE2")

myuart.write(0x40000000, 0xdeadbeef)
myuart.write(0x40000004, 0xcafebabe)

print("-------")
for i in range(0x200//4):
    val = myuart.read(0x40000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))


exit()
