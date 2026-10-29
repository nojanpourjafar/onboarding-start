# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    
    Parameters:
    - r_w: boolean, True for write, False for read
    - address: int, 7-bit address (0-127)
    - data: LogicArray or int, 8-bit data
    """
    # Convert data to int if it's a LogicArray
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Validate inputs
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # Combine RW and address into first byte
    first_byte = (int(r_w) << 7) | address
    # Start transaction - pull CS low
    sclk = 0
    ncs = 0
    bit = 0
    # Set initial state with CS low
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send first byte (RW + Address)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send second byte (Data)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End transaction - return CS high
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")

@cocotb.test()
async def test_pwm_freq(dut):
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    await send_spi_transaction(dut, 1, 0x00, 0x01)  # turn on pin 0
    await send_spi_transaction(dut, 1, 0x02, 0x01)  # make pin 0 do PWM
    await send_spi_transaction(dut, 1, 0x04, 0x80)  # duty = 128/256 = 50% test

    # find two rising edges (0 -> 1) on pin 0
    last = int(dut.uo_out.value) & 1
    t1 = 0
    t2 = 0
    for i in range(100000):
        await ClockCycles(dut.clk, 1)
        now = int(dut.uo_out.value) & 1
        if last == 0 and now == 1:
            if t1 == 0:
                t1 = cocotb.utils.get_sim_time(units="ns")
            else:
                t2 = cocotb.utils.get_sim_time(units="ns")
                break
        last = now

    assert t2 != 0, "timed out, never saw two rising edges"

    period = t2 - t1
    freq = 1e9 / period
    dut._log.info(f"Frequency: {freq} Hz")
    assert 2970 <= freq <= 3030, f"Frequency is {freq} Hz, should be 2970-3030"

    dut._log.info("PWM Frequency test completed successfully")


@cocotb.test()
async def test_pwm_duty(dut):
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    await send_spi_transaction(dut, 1, 0x00, 0x01)  # turn on pin 0
    await send_spi_transaction(dut, 1, 0x02, 0x01)  # make pin 0 do PWM

    # 0% duty: pin 0 should stay low the whole time
    await send_spi_transaction(dut, 1, 0x04, 0x00)
    for i in range(4000):
        await ClockCycles(dut.clk, 1)
        pin = int(dut.uo_out.value) & 1
        assert pin == 0, "0% duty: pin 0 went high"

    # 100% duty: pin 0 should stay high the whole time
    await send_spi_transaction(dut, 1, 0x04, 0xFF)
    for i in range(4000):
        await ClockCycles(dut.clk, 1)
        pin = int(dut.uo_out.value) & 1
        assert pin == 1, "100% duty: pin 0 went low"

    # 50% duty: time rising edge -> falling edge -> next rising edge
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    last = int(dut.uo_out.value) & 1
    rise1 = 0
    fall = 0
    rise2 = 0
    for i in range(100000):
        await ClockCycles(dut.clk, 1)
        now = int(dut.uo_out.value) & 1
        if last == 0 and now == 1:
            if rise1 == 0:
                rise1 = cocotb.utils.get_sim_time(units="ns")
            elif fall != 0:
                rise2 = cocotb.utils.get_sim_time(units="ns")
                break
        if last == 1 and now == 0 and rise1 != 0:
            fall = cocotb.utils.get_sim_time(units="ns")
        last = now
    assert rise2 != 0, "timed out"
    duty = (fall - rise1) / (rise2 - rise1) * 100
    dut._log.info(f"Duty: {duty}%")
    assert 49 <= duty <= 51, f"duty is {duty}%, should be 49-51"

    dut._log.info("PWM Duty Cycle test completed successfully")