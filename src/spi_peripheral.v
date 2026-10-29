`default_nettype none

module spi_peripheral (
    input wire clk,      // 10 MHz system clock
    input wire rst_n,    // reset, active low
    input wire sclk,     // SPI clock
    input wire copi,     // SPI data in (controller out, peripheral in)
    input wire ncs,       // SPI chip select (active low)   

    output reg [7:0] en_reg_out_7_0,  // 0x00: output enable for uo_out[7:0]
    output reg [7:0] en_reg_out_15_8, // 0x01: output enable for uio_out[7:0]
    output reg [7:0] en_reg_pwm_7_0,  // 0x02: PWM enable for uo_out[7:0]
    output reg [7:0] en_reg_pwm_15_8, // 0x03: PWM enable for uio_out[7:0]
    output reg [7:0] pwm_duty_cycle    // 0x04: PWM duty cycle
);

endmodule