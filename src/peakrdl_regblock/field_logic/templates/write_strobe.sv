// Register: {{node.get_path()}}
logic [{{width-1}}:0] decoded_reg_{{node.inst_name}};
always_comb begin
    automatic logic [{{width-1}}:0] reg_{{node.inst_name}} = {{content}};
    for(int i_bit=0; i_bit<{{width}}; i_bit+=8) begin
        decoded_reg_{{node.inst_name}}[i_bit+:8] = (axil_wstrb[i_bit>>3]) ? decoded_wr_data[i_bit+:8] : reg_{{node.inst_name}}[i_bit+:8];
    end
end
