# SPDX-FileCopyrightText: © 2025 XXX Authors
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.runner import get_runner
from cocotb.triggers import Timer, ClockCycles

import random

@cocotb.test()
async def counter_test(dut):
    """Testing the design."""
    
    # Create a clock with a period of 10ns = 100MHz
    clock = Clock(dut.clk, 10, 'ns')
    await cocotb.start(clock.start())

    dut.ena.value    = 1 # always 1
    dut.uio_in.value = 0
    dut.ui_in.value = 0

    # Reset the design for 100ns
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    numbers=[random.randint(0,2**8-1) for i in range(22)]

    for n in numbers:
        dut.ui_in.value  = n
        dut.uio_in.value = 1<<1;
        print ("Inserting number "+str(n))
        await ClockCycles(dut.clk, 1)

    dut.uio_in.value = 0 # not inserting
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = 1 # flush output
    await ClockCycles(dut.clk, 2)

    numbers.sort()
    for n in numbers:
        # Ensure there is output
        #print (n, hex(dut.uio_out.value), int(str(dut.uo_out.value),2))
        print ("Exporting "+str(int(str(dut.uo_out.value),2)))
        assert dut.uio_out.value >>2 == 1, "Expecting output (data_o_v==1)"
        assert int(str(dut.uo_out.value),2) == n, "Correct number order" 
        await ClockCycles(dut.clk, 1)

    # Wait for 10 clock cycles
    await ClockCycles(dut.clk, 10)
    
    
    # cocotb documentation: https://docs.cocotb.org/en/stable/refcard.html
    # cocotb reference card: https://docs.cocotb.org/en/stable/refcard.html

if __name__ == "__main__":

    sim         = os.getenv("SIM", "icarus")
    pdk_root    = os.getenv("PDK_ROOT", "~/.ciel")
    pdk         = os.getenv("PDK", "ihp-sg13g2")
    scl         = os.getenv("SCL", "sg13g2_stdcell")
    gl          = os.getenv("GL", False)

    testbench_path = Path(__file__).resolve().parent
    sources = []#[testbench_path / 'testbench.sv']
    defines = {}

    MACRO_NL = testbench_path / '../macro/nl/heichips25_top_sorter.nl.v'

    if gl:
        if not MACRO_NL.exists():
            print(f"The macro netlist {MACRO_NL} does not exist. Did you implement the macro?")
            sys.exit(0)
    
        sources.append(Path(pdk_root).expanduser() / pdk / "libs.ref" / scl / "verilog" / f"{scl}.v" )
        sources.append(MACRO_NL)
        defines = {'FUNCTIONAL': True, 'UNIT_DELAY': '#0'}
    else:
        sources.extend(list(testbench_path.glob('../src/*')))
        defines = {'RTL': True}

    hdl_toplevel = "heichips25_top_sorter"

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        defines=defines,
        timescale=['1ns', '1ps'],
        waves=True,
        build_args=['--trace', '--trace-fst', '--trace-structs'] if sim == 'verilator' else ['-gno-specify'],
    )

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module='testbench,',
        timescale=['1ns', '1ps'],
        waves=True,
        plusargs=['--trace-file', f'{hdl_toplevel}.fst']  if sim == 'verilator' else [],
    )
