# rom

Boot ROM with a build-time image.

![maturity](https://img.shields.io/badge/maturity-planned-lightgrey) ![license](https://img.shields.io/badge/license-MulanPSL--2.0-blue)

Part of the [Tape-Out](https://github.com/Tape-Out) IP library: Bluespec IP over the
bus-neutral contracts in [`hwcore`](https://github.com/Tape-Out/hwcore), assembled by
[`xirang`](https://github.com/Tape-Out/xirang). Maturity runs `planned` -> `simulated` ->
`fpga-proven` -> `asic-ready` -> `silicon-proven`.

## Status

Planned, not started. Work starts when a reference SoC boots from on-chip ROM. The Verilog from the picorv32 era that sits here is kept as history only; the implementation will be written from scratch in Bluespec.

## Notes

# boot-rom-mmio

> todo: 之后改为 asic 的 case wire 或者写一个简单的生成脚本

## License

Mulan PSL v2.
