# Current State
- `racore_lite.sv` successfully synthesized with 0 latches alongside `seth_pipeline_csr`. PR #245 is merged!
- Hardened `seth_branch` to ASAP7 7nm via ORFS. WNS 0.00, area 46 um^2. PR #246 is ready to be merged once CI is green.
- Hardened `seth_imm` to ASAP7 7nm via ORFS. WNS 0.00, area 43 um^2. PR #247 is ready to be merged once CI is green.
- Hardened `seth_aluctl` to ASAP7 7nm via ORFS. WNS 0.00, area 14 um^2. PR #248 is ready to be merged once CI is green.
- Hardened `seth_decode` to ASAP7 7nm via ORFS. WNS 0.00, area 16 um^2. PR #249 is ready to be merged once CI is green.
- Hardened `seth_trap` to ASAP7 7nm via ORFS. WNS 0.00, area 212 um^2. PR #250 is ready to be merged once CI is green.
- Hardened `seth_lsu` to ASAP7 7nm via ORFS. WNS 0.00, area 99 um^2. PR #251 is ready to be merged once CI is green.
- Hardened `seth_mcsr` to ASAP7 7nm via ORFS. WNS 0.00, area 228 um^2.
- Tracking and WORKLOG updated for all.

# Next Step
- Open a PR for `seth_mcsr`. Wait for PRs CI to pass and merge them. Proceed to the next core in Phase 3/4 based on `PROGRESS.md`.
