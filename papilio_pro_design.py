#!/usr/bin/env python3
import argparse
from fractions import Fraction

from litex.gen import *
from litex.gen.genlib.io import CRG

from litex.gen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.interconnect import wishbone
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores.uart.bridge import UARTWishboneBridge

from litedram.modules import MT48LC4M16
from litedram.phy import GENSDRPHY

import papilio_pro_platform as papilio_pro

import sdcard


class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()

        f0 = 32*1000000
        clk32 = platform.request("clk32")
        clk32a = Signal()
        self.specials += Instance("IBUFG", i_I=clk32, o_O=clk32a)
        clk32b = Signal()
        self.specials += Instance("BUFIO2", p_DIVIDE=1,
                                  p_DIVIDE_BYPASS="TRUE", p_I_INVERT="FALSE",
                                  i_I=clk32a, o_DIVCLK=clk32b)
        f = Fraction(int(clk_freq), int(f0))
        n, m, p = f.denominator, f.numerator, 8
        assert f0/n*m == clk_freq
        pll_lckd = Signal()
        pll_fb = Signal()
        pll = Signal(6)
        self.specials.pll = Instance("PLL_ADV", p_SIM_DEVICE="SPARTAN6",
                                     p_BANDWIDTH="OPTIMIZED", p_COMPENSATION="INTERNAL",
                                     p_REF_JITTER=.01, p_CLK_FEEDBACK="CLKFBOUT",
                                     i_DADDR=0, i_DCLK=0, i_DEN=0, i_DI=0, i_DWE=0, i_RST=0, i_REL=0,
                                     p_DIVCLK_DIVIDE=1, p_CLKFBOUT_MULT=m*p//n, p_CLKFBOUT_PHASE=0.,
                                     i_CLKIN1=clk32b, i_CLKIN2=0, i_CLKINSEL=1,
                                     p_CLKIN1_PERIOD=1000000000/f0, p_CLKIN2_PERIOD=0.,
                                     i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
                                     o_CLKOUT0=pll[0], p_CLKOUT0_DUTY_CYCLE=.5,
                                     o_CLKOUT1=pll[1], p_CLKOUT1_DUTY_CYCLE=.5,
                                     o_CLKOUT2=pll[2], p_CLKOUT2_DUTY_CYCLE=.5,
                                     o_CLKOUT3=pll[3], p_CLKOUT3_DUTY_CYCLE=.5,
                                     o_CLKOUT4=pll[4], p_CLKOUT4_DUTY_CYCLE=.5,
                                     o_CLKOUT5=pll[5], p_CLKOUT5_DUTY_CYCLE=.5,
                                     p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//1,
                                     p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=p//1,
                                     p_CLKOUT2_PHASE=0., p_CLKOUT2_DIVIDE=p//1,
                                     p_CLKOUT3_PHASE=0., p_CLKOUT3_DIVIDE=p//1,
                                     p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=p//1,  # sys
                                     p_CLKOUT5_PHASE=270., p_CLKOUT5_DIVIDE=p//1,  # sys_ps
        )
        self.specials += Instance("BUFG", i_I=pll[4], o_O=self.cd_sys.clk)
        self.specials += Instance("BUFG", i_I=pll[5], o_O=self.cd_sys_ps.clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd)

        self.specials += Instance("ODDR2", p_DDR_ALIGNMENT="NONE",
                                  p_INIT=0, p_SRTYPE="SYNC",
                                  i_D0=0, i_D1=1, i_S=0, i_R=0, i_CE=1,
                                  i_C0=self.cd_sys.clk, i_C1=~self.cd_sys.clk,
                                  o_Q=platform.request("sdram_clock"))


class BaseSoC(SoCSDRAM):
    mem_map = {
        "sdcard": 0x50000000,  # (shadow @0xd0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self, **kwargs):
        platform = papilio_pro.Platform()
        clk_freq = 80*1000000

        SoCSDRAM.__init__(self, platform, clk_freq,
                          cpu_type=None,
                          csr_data_width=32,
                          with_uart=False,
                          ident="LitePCIe example design",
                          with_timer=False,
                          **kwargs)
        # clock/reset generation
        self.submodules.crg = _CRG(platform, clk_freq)

        # sdram
        self.submodules.sdrphy = GENSDRPHY(platform.request("sdram"))
        sdram_module = MT48LC4M16(clk_freq, "1:1")
        self.register_sdram(self.sdrphy,
                            sdram_module.geom_settings, sdram_module.timing_settings)

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
    parser = argparse.ArgumentParser(description="MiSoC port to the Papilio Pro")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(**soc_sdram_argdict(args))
    builder = Builder(soc, **builder_argdict(args))
    builder.build()


if __name__ == "__main__":
    main()
