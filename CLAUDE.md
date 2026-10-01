# TI-84 Plus program pipeline

Read README.md ("For LLM agents") before doing anything here. It covers the whole
workflow, the test API, the hardware commands and the TI-BASIC gotchas.

Non-negotiables:
- Every program gets emulator tests (`./ti84 test programs/<name>`) that pass before
  `./ti84 flash`.
- "Works on the calculator" means `./ti84 hw run` showed the right output on the real
  LCD (or the user confirmed). A successful transfer is not proof.
- Don't overwrite the user's calculator variables without asking.
- Matrix send/get over `hw` is broken (DUSB error 0x000e); type matrices with remote keys.
