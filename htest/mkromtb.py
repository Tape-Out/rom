"""rom 的行为测试台，两件事。

一、表作为值传进 mkRomOf：测试台装一张不对称的图案（第 i 个字是 0x9E3779B9 × (i + 1)，截成 32 位），
每个下标都读一遍，地址少移两位、下标错一位都读不对。另查：答复不在请求那一拍（宏的形状）·
紧挨着最后一个字的地址与窗口顶端的地址回错 · 写回错，写完再读原值不变 · 一个请求只有一个答复
（发起方在答复那一拍还顶着请求，目标不许再收一次）。
二、mkRom 装的是烧进去的镜像：每个字等于 image/boot.hex，镜像之后的第一个字读 0。
"""
import json
import pathlib
import sys

out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
out.mkdir(parents=True, exist_ok=True)
cfg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
label = cfg.get("label", "")
words = int(cfg.get("knobs", {}).get("words", 64))

here = pathlib.Path(__file__).resolve().parent.parent
image = []
for line in (here / "image" / "boot.hex").read_text(encoding="utf-8").splitlines():
    s = line.split("#", 1)[0].strip()
    if s:
        image.append(int(s, 16))
if len(image) > words:
    raise SystemExit(f"镜像 {len(image)} 个字，这一点的 ROM 只有 {words} 个字，不生成测试台")

boot = [f"""    xfer(True, 16'h{i * 4:04X}, False, 0);
    action if (rsp.rdata != 32'h{w:08X} || rsp.err) begin $display("FAIL image word {i} reads %08h (err %0d), want {w:08x}", rsp.rdata, rsp.err); bad <= True; end endaction"""
        for i, w in enumerate(image)]
if len(image) < words:
    boot.append(f"""    xfer(True, 16'h{len(image) * 4:04X}, False, 0);
    action if (rsp.rdata != 0 || rsp.err) begin $display("FAIL the word after the image reads %08h (err %0d), want 0", rsp.rdata, rsp.err); bad <= True; end endaction""")

verdict = (f"every word of a {words}-word pattern reads back one cycle after its request, the address past the end "
           f"and a write answer with an error, each request gets exactly one answer counted on the wire, and the built image reads as image/boot.hex")

TEMPLATE = r'''package Rom@L@Tb;

// 由 htest/mkromtb.py 生成，勿手改。这一点：words=@WORDS@

import Vector::*;
import StmtFSM::*;
import RegIf::*;
import Rom::*;

(* synthesize *)
module mkRom@L@Tb(Empty);
  function Bit#(32) pat(Integer i) = 32'h9E3779B9 * fromInteger(i + 1);
  Vector#(@WORDS@, Bit#(32)) patTbl = genWith(pat);
  RegTarget#(16, 32)       a <- mkRomOf(patTbl);
  RomIfc#(16, 32, @WORDS@) b <- mkRom(RomCfg { none: ? });

  Reg#(UInt#(32))       cyc     <- mkReg(0);
  Reg#(Bool)            toB     <- mkReg(False);
  Reg#(Bool)            hold[2] <- mkCReg(2, False);
  Reg#(Bool)            got[2]  <- mkCReg(2, False);
  Reg#(Bool)            pres[2] <- mkCReg(2, False);
  Wire#(Bool)           firstNow <- mkDWire(False);
  Reg#(RegReq#(16, 32)) q       <- mkReg(unpack(0));
  Reg#(RegRsp#(32))     rsp     <- mkReg(unpack(0));
  Reg#(UInt#(32))       issued  <- mkReg(0);
  Reg#(UInt#(32))       answers <- mkReg(0);
  // take 只数顶着请求时收下的答复；目标在答复那一拍又收一次的话，多出来的那一拍 rspValid 落在 hold 清掉之后，
  // take 看不见。这里不看 hold，线上每一拍都数
  Reg#(UInt#(32))       onWire  <- mkReg(0);
  Reg#(Bool)            same    <- mkReg(False);
  Reg#(Bool)            bad     <- mkReg(False);
  Reg#(Bit#(16))        i       <- mkReg(0);

  Bool rv = toB ? b.mem.rspValid : a.rspValid;

  // 请求一直顶到收下答复的下一拍：答复那一拍目标还看得见这个请求，不许再收一次
  rule drive;
    a.req(hold[0] && !toB, q);
    b.mem.req(hold[0] && toB, q);
    if (hold[0] && !pres[0]) begin
      pres[0] <= True;
      firstNow <= True;
    end
  endrule

  rule watch;
    onWire <= onWire + (a.rspValid ? 1 : 0) + (b.mem.rspValid ? 1 : 0);
  endrule

  rule take (hold[0] && rv);
    rsp <= toB ? b.mem.rsp : a.rsp;
    hold[0] <= False;
    got[0] <= True;
    pres[1] <= False;
    answers <= answers + 1;
    if (firstNow) same <= True;
  endrule

  function Stmt xfer(Bool toRom, Bit#(16) addr, Bool w, Bit#(32) v) = seq
    action
      toB <= toRom;
      q <= RegReq { addr: addr, write: w, wdata: v, wstrb: 4'hF };
      hold[1] <= True;
      got[1] <= False;
      issued <= issued + 1;
    endaction
    await(got[1]);
  endseq;

  Stmt test = seq
    i <= 0;
    while (i < @WORDS@) seq
      xfer(False, i << 2, False, 0);
      action if (rsp.rdata != 32'h9E3779B9 * (zeroExtend(i) + 1) || rsp.err) begin $display("FAIL word %0d reads %08h (err %0d), want %08h", i, rsp.rdata, rsp.err, 32'h9E3779B9 * (zeroExtend(i) + 1)); bad <= True; end endaction
      i <= i + 1;
    endseq

    xfer(False, 16'h@PAST@, False, 0);
    action if (!rsp.err || rsp.rdata != 0) begin $display("FAIL the first address past the ROM reads %08h with err %0d, want 0 and 1", rsp.rdata, rsp.err); bad <= True; end endaction
    xfer(False, 16'hFFFC, False, 0);
    action if (!rsp.err) begin $display("FAIL the top of the address window reads without an error"); bad <= True; end endaction
    xfer(False, 16'h0004, True, 32'h12345678);
    action if (!rsp.err) begin $display("FAIL a write to the ROM gives no error"); bad <= True; end endaction
    xfer(False, 16'h0004, False, 0);
    action if (rsp.rdata != 32'h9E3779B9 * 2) begin $display("FAIL word 1 reads %08h after a write, want it unchanged", rsp.rdata); bad <= True; end endaction

@BOOT@

    action
      Bool wrong = False;
      if (same) begin $display("FAIL an answer came in the same cycle as its request"); wrong = True; end
      if (answers != issued) begin $display("FAIL %0d requests got %0d answers", issued, answers); wrong = True; end
      if (onWire != issued) begin $display("FAIL %0d requests but %0d cycles with an answer on the wire", issued, onWire); wrong = True; end
      if (wrong) bad <= True;
    endaction
  endseq;

  FSM fsm <- mkFSM(test);
  Reg#(Bool) started <- mkReg(False);

  rule go (!started);
    started <= True;
    fsm.start;
  endrule

  rule count;
    cyc <= cyc + 1;
    if (cyc > 50000) begin
      $display("TIMEOUT");
      $finish(1);
    end
  endrule

  rule fin (started && fsm.done);
    if (bad) $display("FAILED");
    else $display("PASS rom: @VERDICT@");
    $finish(bad ? 1 : 0);
  endrule
endmodule

endpackage
'''

txt = (TEMPLATE.replace("@L@", label).replace("@WORDS@", str(words))
       .replace("@PAST@", f"{words * 4:04X}").replace("@BOOT@", "\n".join(boot))
       .replace("@VERDICT@", verdict))

(out / f"Rom{label}Tb.bsv").write_text(txt, encoding="utf-8")
print(f"  rom 行为测试台就位：words={words}，镜像 {len(image)} 个字")
