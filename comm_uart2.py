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


myuart = CommUART("/dev/ttyUSB1")

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

    
"""
Command register:

[31:14] reserved
[13:8] command index
[7] reserved
[6:5] 00 no data transfer
      01 trigger read data transaction after command
      10 trigger write data after command
[4]   check reponse for correct command index
[3]   check crc
[2]   check for busy signal after command
[1:0] 00 don't wait for response
      01 wait for short response (48bit)
      10 wait for long response (136)

"""


def  command(cmd_id, data_xfer=0, chk_id=0, chk_crc=0, chk_busy=0, wait_resp=0):
    ret = (cmd_id << 8) | (data_xfer << 5) | (chk_id << 4) | (chk_crc << 3) | (chk_busy << 2) | wait_resp
    print("--------------")
    print("command {0:08x}".format(ret))
    print("CMD_ID: {0}".format(cmd_id))
    print("Data: {0}".format(data_xfer))
    print("CHK_ID:{0}".format(chk_id))
    print("CRCE:{0}".format(chk_crc))
    print("BUSY:{0}".format(chk_busy))
    print("RESP:{0}".format(wait_resp))
    print("--------------")
    return ret

def setup_core(cmd_timeout, data_timeout):
    #assert reset high
    mywrite(0x28, 0x1)
    #cmd_timeout
    mywrite(0x18, cmd_timeout)
    #data_timeout
    mywrite(0x20, data_timeout)    
    # DMA address
    mywrite(0x60, 0x40000000)
    #clock devider
    mywrite(0x24, 0)
    #assert reset low
    mywrite(0x28, 0x0)
    #cmd irq
    mywrite(0x38, 0x1f)
    #data irq
    mywrite(0x40, 0x7)
    # 1: 4 bit mode (0: 1 bit mode)
    mywrite(0x1c, 1)

    
    mywrite(0x44, 512)
    



def init_card():
    perform(command(0), 0)
    perform(command(8, wait_resp=1), 0x155)
    
    resp = 0
    while resp & 0x80000000 == 0:
        #send command 55
        perform(command(55, 0, 1, 1, 0, 1), 0)

        #send command 41 and wait for ready
        ## 0101 0000 1111 1111 1000 0000 0000 0000
              
        #perform(command(41, wait_resp=1), 0x41ff8000)
        perform(command(41, wait_resp=1), 0x50ff8000)
        resp = myread(8)

        #answers c0ff8000
        #1 1 0 0000 0 1111 1111 1000 0000 0000 0000
        #busy =1, ccs = 1, uhs2=0, s18a=0 <- no switch
        
        #Voltage switch
        #perform(command(11, chk_crc=1, wait_resp=1), 0)

    
    #Asks any card to send the CID numbers    on the CMD line (any card that is connected to the host will respond)
    perform(command(2, chk_crc=1, wait_resp=2), 0)
    
    #Ask the card to publish a new relative  address (RCA) <- we expect 0x1234
    perform(command(3, chk_crc=1, wait_resp=1), 0)

    

def setup_card_to_transfer():

    
    perform(command(7, chk_crc=1, wait_resp=1), 0x12340000)

    perform(command(16, 0, 1, 1, 0, 1), 512)
    #send command 42
    #perform(command(42, 0, 1, 1, 0, 1), 0)
    #send command 42


    #perform(command(55, 0, 1, 1, 0, 1), 0)
    #perform(command(6, 0, 1, 1, 0, 1), 2)
    



    

setup_core(0xffff, 0xffff)
init_card()
setup_card_to_transfer()
perform(command(17, 1,  1, 1, 0, 1), 0)




            

"""

print("-------")
for i in range(0x200//4):
    val = myuart.read(0x40000000   + i*4)
    print("{0:02x}: {1:08x}".format(i*4, val))


exit()
"""
