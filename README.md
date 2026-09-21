# rom

Boot ROM with a build-time image.

![maturity](https://img.shields.io/badge/maturity-simulated-yellow) ![license](https://img.shields.io/badge/license-MulanPSL--2.0-blue)

Part of the [Tape-Out](https://github.com/Tape-Out) IP library: Bluespec IP over the
bus-neutral contracts in [`hwcore`](https://github.com/Tape-Out/hwcore), assembled by
[`xirang`](https://github.com/Tape-Out/xirang). Maturity runs `planned` -> `simulated` ->
`fpga-proven` -> `asic-ready` -> `silicon-proven`.

## Status

Simulated. A read-only memory of `words` 32-bit words whose contents are fixed at build time. It answers one cycle after each request, which is the read timing of the ICS55 ROM macro (address and chip enable clocked, data out after the edge), so replacing the logic with the macro later changes neither the interface nor the timing. Writes and addresses past the last word answer with an error.

The image is `image/boot.hex`, one 32-bit word per line. `tools/romimage.py` turns it into `hwsrc/RomImage.bs`, a Bluespec Haskell list. `RomTable.bs` pads the list with zeros to the ROM size, which is a numeric type, and stops the build if the image does not fit. `Rom.bsv` is the stalling target. It takes the table as a value, so the testbench can load a pattern of its own. The default image is two instructions that jump to 0x8000_0000.

The testbench loads an asymmetric pattern and reads every word back. It checks that no answer comes in the cycle of its request, that the address just past the end and the top of the window answer with an error, that a write answers with an error and changes nothing, and that each request gets exactly one answer even though the requester still holds the request in the answer cycle. It then reads the built image and checks it against `image/boot.hex`.

To change the image, edit `image/boot.hex` and run `python3 tools/romimage.py image/boot.hex > hwsrc/RomImage.bs`. The generated logic changes, so the area table has to be measured again.

## Parameters

| Parameter | Range | Meaning |
| :--: | :--: | :-- |
| `words` | 4 to 256 | ROM size in 32-bit words |

The Verilog from the picorv32 era, `mrom_mmio.v`, stays in the repository as history only and is not part of the build.

The ICS55 ROM macro implementation is not provided yet: its Verilog model cannot run in Bluesim, and the macro starts at 256 words. Booting a reference SoC from the ROM needs a reset vector parameter on `hart` as well.

## Specification sources

The specifications this IP is implemented against, with their links, digests and the clause-by-clause comparison, are kept on the [`spec` branch](https://github.com/Tape-Out/rom/tree/spec).

## License

Mulan PSL v2.
