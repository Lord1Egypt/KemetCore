"""SethCore pymodel — 5-stage pipeline (functional + cycle accounting).

Architectural results are produced by reusing the golden CPU semantics (a correct
program's final register state is forwarding-invariant). On top of that, the model
estimates cycles: 1 instr/cycle steady-state + 1 bubble per taken branch + 1 stall
per load-use hazard, matching a classic IF/ID/EX/MEM/WB pipeline with forwarding.
"""
import seth_rv32im as g

STAGES = ["IF", "ID", "EX", "MEM", "WB"]


class Pipeline:
    def __init__(self):
        self.cpu = g.Cpu()
        self.cycles = 0
        self.instructions = 0

    def load(self, words, base=0):
        self.cpu.load(words, base)

    def run(self, max_steps=100000):
        prev_was_load = False
        prev_rd = 0
        while not self.cpu.halted and self.instructions < max_steps:
            ins = self.cpu._ld(self.cpu.pc, 4)
            op = ins & 0x7F
            rs1 = (ins >> 15) & 0x1F
            rs2 = (ins >> 20) & 0x1F
            rd = (ins >> 7) & 0x1F
            pc_before = self.cpu.pc

            # load-use hazard: previous instr was a load whose rd feeds this one
            if prev_was_load and prev_rd != 0 and prev_rd in (rs1, rs2):
                self.cycles += 1  # one stall bubble

            self.cpu.step()
            self.instructions += 1
            self.cycles += 1

            taken_branch = (op == 0x63 and self.cpu.pc != g.u32(pc_before + 4))
            is_jump = op in (0x6F, 0x67)
            if taken_branch or is_jump:
                self.cycles += 1  # control-hazard bubble

            prev_was_load = (op == 0x03)
            prev_rd = rd
        return self.cpu.x

    @property
    def regs(self):
        return self.cpu.x
