`include "inc.sv"

module incTop;
    wire a, b, c;
    `MODULE_NAME I0 (
        .a(a),
        .b(b),
        .c(c)
    );
endmodule
