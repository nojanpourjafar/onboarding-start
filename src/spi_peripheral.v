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
    reg [2:0] sclk_sync;   // 3 flip-flops
    reg [2:0] ncs_sync;    // 3 flip-flops
    reg [1:0] copi_sync;   // 2 flip-flop

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sclk_sync <= 3'b000;
            ncs_sync <= 3'b111; // inactive high
            copi_sync <= 2'b00;
        end else begin
            sclk_sync <= {sclk_sync[1:0], sclk};
            ncs_sync <= {ncs_sync[1:0], ncs};
            copi_sync <= {copi_sync[0], copi};
        end
    end

    wire sclk_rise = sclk_sync[1] && ~sclk_sync[2];   // 1 for one tick when SCLK goes 0 -> 1
    wire ncs_rise  = ncs_sync[1] && ~ncs_sync[2];   // 1 for one tick when nCS goes 0 -> 1 (message ended)

    reg [15:0] shift_reg;   // holds the 16 bits as they arrive
    reg [4:0] bit_count;   // how many bits have arrived so far
    localparam max_address = 7'h04;   // highest valid register address

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // reset: everything starts at 0
            shift_reg       <= 0;
            bit_count       <= 0;
            en_reg_out_7_0  <= 0;
            en_reg_out_15_8 <= 0;
            en_reg_pwm_7_0  <= 0;
            en_reg_pwm_15_8 <= 0;
            pwm_duty_cycle  <= 0;

        end else if (ncs_sync[1] == 1'b0) begin          // nCS is low = message in progress
            if (sclk_rise) begin                          // SCLK just went up
                shift_reg <= { shift_reg[14:0], copi_sync[1] };
                bit_count <= bit_count + 1;
            end
        end else if (ncs_rise) begin                  // nCS just went high = message ended
            if (bit_count == 16 && shift_reg[15] == 1'b1 && shift_reg[14:8] <= max_address) begin
                case (shift_reg[14:8])                         // find which register
                    7'h00: en_reg_out_7_0  <= shift_reg[7:0];
                    7'h01: en_reg_out_15_8 <= shift_reg[7:0];
                    7'h02: en_reg_pwm_7_0  <= shift_reg[7:0];

                    7'h03: en_reg_pwm_15_8 <= shift_reg[7:0];
                    7'h04: pwm_duty_cycle  <= shift_reg[7:0];
                    default: ;                            // anything else: do nothing
                endcase
            end
            bit_count <= 0;                               // ready for the next message to eb sent
        end
    end
endmodule