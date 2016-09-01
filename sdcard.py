import os

from litex.gen import *
from litex.soc.interconnect import wishbone


class SDCARD(Module):
    def __init__(self, platform, pads):
        self.master = master = wishbone.Interface()
        self.slave = slave = wishbone.Interface()


        self.int_cmd = Signal()
        self.int_data = Signal()

        self.cmd_o = Signal()
        self.cmd_i = Signal()
        self.cmd_oe = Signal()
        self.dat_o = Signal(4)
        self.dat_i = Signal(4)
        self.dat_oe = Signal()
        self.sd_clk = Signal()

        self.cmd = TSTriple(1)
        self.dat = TSTriple(4)
        self.specials += self.cmd.get_tristate(pads.cmd)
        self.specials += self.dat.get_tristate(pads.d)

        self.comb += [
            self.cmd.o.eq(self.cmd_o),
            self.cmd.oe.eq(self.cmd_oe),
            self.cmd_i.eq(self.cmd.i),

            self.dat.o.eq(self.dat_o),
            If(self.dat_oe,
                self.dat.oe.eq(0xf)
            ).Else(
                self.dat.oe.eq(0x0)
            ),
            self.dat_i.eq(self.dat.i),
            pads.clk.eq(self.sd_clk)
        ]

        # # #

        self.specials += Instance("sdc_controller",
                            i_wb_clk_i=ClockSignal(),
                            i_wb_rst_i=ResetSignal(),

                            # Wishbone slave
                            i_wb_dat_i=slave.dat_w,
                            o_wb_dat_o=slave.dat_r,
                            i_wb_adr_i=slave.adr,
                            i_wb_sel_i=slave.sel,
                            i_wb_we_i=slave.we,
                            i_wb_cyc_i=slave.cyc,
                            i_wb_stb_i=slave.stb,
                            o_wb_ack_o=slave.ack,

                            # Wishbone master
                            o_m_wb_dat_o=master.dat_w,
                            i_m_wb_dat_i=master.dat_r,
                            o_m_wb_adr_o=master.adr,
                            o_m_wb_sel_o=master.sel,
                            o_m_wb_we_o=master.we,
                            o_m_wb_cyc_o=master.cyc,
                            o_m_wb_stb_o=master.stb,
                            i_m_wb_ack_i=master.ack,
                            o_m_wb_cti_o=master.cti,
                            o_m_wb_bte_o=master.bte,

                            # SDCard bus
                            i_sd_cmd_dat_i=self.cmd_i,
                            o_sd_cmd_out_o=self.cmd_o,
                            o_sd_cmd_oe_o=self.cmd_oe,

                            i_sd_dat_dat_i=self.dat_i,
                            o_sd_dat_out_o=self.dat_o,
                            o_sd_dat_oe_o=self.dat_oe,
                            o_sd_clk_o_pad=self.sd_clk,
                            i_sd_clk_i_pad=ClockSignal(),

                            o_int_cmd=self.int_cmd,
                            o_int_data=self.int_data
        )

        sdcard_path = os.path.abspath(os.path.dirname(__file__))
        platform.add_source_dir(os.path.join(sdcard_path, "verilog"))
