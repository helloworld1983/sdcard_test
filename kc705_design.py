#!/usr/bin/env python3

import argparse

from litex.gen import *
from litex.gen.genlib.resetsync import AsyncResetSynchronizer
from litex.boards.platforms import kc705

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.uart.bridge import UARTWishboneBridge

import kc705_platform as kc705

import sdcard

class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()

        clk200 = platform.request("clk200")
        clk200_se = Signal()
        self.specials += Instance("IBUFDS", i_I=clk200.p, i_IB=clk200.n, o_O=clk200_se)

        rst = platform.request("cpu_reset")

        pll_locked = Signal()
        pll_fb = Signal()
        self.pll_sys = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                     # VCO @ 1GHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=5.0,
                     p_CLKFBOUT_MULT=5, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=clk200_se, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 125MHz
                     p_CLKOUT0_DIVIDE=8, p_CLKOUT0_PHASE=0.0, o_CLKOUT0=self.pll_sys,

                     p_CLKOUT1_DIVIDE=8, p_CLKOUT1_PHASE=0.0, #o_CLKOUT1=,

                     p_CLKOUT2_DIVIDE=8, p_CLKOUT2_PHASE=0.0, #o_CLKOUT2=,

                     p_CLKOUT3_DIVIDE=8, p_CLKOUT3_PHASE=0.0, #o_CLKOUT3=,

                     p_CLKOUT4_DIVIDE=8, p_CLKOUT4_PHASE=0.0, #o_CLKOUT4=
            ),
            Instance("BUFG", i_I=self.pll_sys, o_O=self.cd_sys.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked | rst)
        ]


class BaseSoC(SoCCore):
    mem_map = {
        "sdcard": 0x50000000,  # (shadow @0xd0000000)
    }
    mem_map.update(SoCCore.mem_map)

    def __init__(self, **kwargs):
        platform = kc705.Platform(toolchain="vivado")
        clk_freq = 125*1000000

        SoCCore.__init__(self, platform, clk_freq,
                          cpu_type=None,
                          csr_data_width=32,
                          with_uart=False,
                          ident="SDCard example design",
                          with_timer=False,
                          integrated_main_ram_size=0x8000,
                          **kwargs)

        # clock/reset generation
        self.submodules.crg = _CRG(platform)

        # uart <--> wishbone bridge
        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), clk_freq, baudrate=115200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)

        # sdcard
        self.submodules.sdcard = sdcard.SDCARD(platform, platform.request("sd_card"))
        self.add_wb_master(self.sdcard.master)

        self.add_wb_slave(mem_decoder(self.mem_map["sdcard"]), self.sdcard.slave)
        self.add_memory_region("sdcard", self.mem_map["sdcard"]+self.shadow_base, 0x2000)

        # led blink
        counter = Signal(32)
        led = platform.request("user_led")
        self.sync += \
            If(counter,
                counter.eq(counter - 1)
            ).Else(
                led.eq(~led),
                counter.eq(40000000)
        )


def main():
    parser = argparse.ArgumentParser(description="LiteX SoC port to the KC705")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(**soc_core_argdict(args))
    builder = Builder(soc, output_dir="build")
    builder.build()


if __name__ == "__main__":
    main()
