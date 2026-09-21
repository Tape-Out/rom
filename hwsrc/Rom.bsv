package Rom;

// 片上只读存储。控制口照 ICS55 ROM 宏的形状做成会停顿的 RegTarget：宏在时钟沿采样地址，
// 下一拍才出数（宏手册 Read Cycle），逻辑实现也晚一拍答，换成宏时接口与时序都不动。
// 内容是构建时的镜像（RomImage，由 tools/romimage.py 生成），查表逻辑在 RomTable（BH）里。

import Vector::*;
import RegIf::*;
import RomImage::*;
import RomTable::*;

typedef struct {
  Bit#(0) none;
} RomCfg;

interface RomIfc#(numeric type aw, numeric type dw, numeric type words);
  interface RegTarget#(aw, dw) mem;
endinterface

// 表作为值传进来：同一个模块既能装烧进去的镜像，也能让测试台装一张不对称的图案，
// 把每个下标都读一遍
module mkRomOf#(Vector#(words, Bit#(32)) tbl)(RegTarget#(aw, dw))
    provisos (Add#(0, dw, 32), Add#(_a, TLog#(words), aw));

  Reg#(Bool)        ans  <- mkReg(False);
  Reg#(RegRsp#(dw)) rspR <- mkReg(RegRsp { rdata: 0, err: False });

  Wire#(Bool)            takeV <- mkDWire(False);
  Wire#(RegReq#(aw, dw)) takeR <- mkDWire(unpack(0));

  Integer n = valueOf(words);

  // 状态只有这一条规则写，方法只发线
  rule step;
    if (takeV) begin
      Bit#(aw) idx = takeR.addr >> 2;
      // 下标比较在地址全宽上做：截成 TLog 位再比，超出的地址会绕回来读到别的字
      Bool oob = idx >= fromInteger(n);
      Bit#(TLog#(words)) i = truncate(idx);
      Bool bad = takeR.write || oob;
      rspR <= RegRsp { rdata: bad ? 0 : tbl[i], err: bad };
      ans  <= True;
    end else
      ans <= False;
  endrule

  method Action req(Bool valid, RegReq#(aw, dw) r);
    if (valid && !ans) begin
      takeV <= True;
      takeR <= r;
    end
  endmethod
  method Bool ready = !ans;
  method Bool rspValid = ans;
  method RegRsp#(dw) rsp = rspR;
endmodule

module mkRom#(RomCfg cfg)(RomIfc#(aw, dw, words))
    provisos (Add#(0, dw, 32), Add#(_a, TLog#(words), aw));
  Vector#(words, Bit#(32)) tbl = fill(image);
  RegTarget#(aw, dw) t <- mkRomOf(tbl);
  interface mem = t;
endmodule

endpackage
