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
        self._write(list((addr).to_bytes(4, byteorder="big")))
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
            self._write(list(((addr+offset)).to_bytes(4, byteorder="big")))
            for i, value in enumerate(data[offset:offset+size]):
                self._write(list(value.to_bytes(4, byteorder="big")))
                if self.debug:
                    print("write {:08x} @ {:08x}".format(value, addr + offset, 4*i))
            offset += size
            length -= size


myuart = CommUART("/dev/ttyUSB0")






#for i in range(0x60):
#    myuart.write( 0x50000000 + i, 0xdead0000+i)
myuart.write(0x80000000 + (0x28 ), 0x1)
myuart.write(0x80000000 + (0x28 ), 0x0)
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))
    
myuart.write(0x80000000 + (0x18 ), 0xfff)
myuart.write(0x80000000 + (0x20 ), 0xfff)
#devider
myuart.write(0x80000000 + (0x24 ), 0)
#4bit mode
myuart.write(0x80000000 + (0x1c ), 1)

myuart.write(0x80000000 + (0x60 ), 0x40000000)
myuart.write(0x80000000 + (0x48 ), 0x1)

myuart.write(0x80000004, 0x0)
myuart.write(0x80000000, 0x0)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))




myuart.write(0x80000004, 0x0801)
myuart.write(0x80000000, 0x155)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))



#3701
#110111 0 00 0 0 0 01
#0011 0111 0000 0001






myuart.write(0x80000004, 0x3719)
myuart.write(0x80000000, 0x0)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))

        
myuart.write(0x80000004, 0x2901)
myuart.write(0x80000000, 0x00000000)
resp = myuart.read(0x80000000   + 8)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))


resp = 0
while resp & 0x80000000 == 0:
    myuart.write(0x80000004, 0x3719)
    myuart.write(0x80000000, 0x0)
    print("---")
    for i in range(0x64//4):
        val = myuart.read(0x80000000   + i*4)
        print("{0:02x}: {1:08x}".format(i*4, val))

        
    myuart.write(0x80000004, 0x2901)
    myuart.write(0x80000000, 0x41ff8000)
    resp = myuart.read(0x80000000   + 8)
    print("---")
    for i in range(0x64//4):
        val = myuart.read(0x80000000   + i*4)
        print("{0:02x}: {1:08x}".format(i*4, val))


    
myuart.write(0x80000004, 0x020a)
myuart.write(0x80000000, 0x00000000)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))



myuart.write(0x80000004, 0x0319)
myuart.write(0x80000000, 0x00000000)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))



myuart.write(0x80000004, 0x0719)
myuart.write(0x80000000, 0x00000000)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))

    
myuart.write(0x80000004, 0x0719)
myuart.write(0x80000000, 0x12340000)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))



myuart.write(0x80000004, 0x1159)
myuart.write(0x80000000, 0x12340000)
print("---")
for i in range(0x64//4):
    val = myuart.read(0x80000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))

print("-------")
for i in range(0x64//4):
    val = myuart.read(0x00000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))





