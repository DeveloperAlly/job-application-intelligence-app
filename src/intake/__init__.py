"""C-01 Advertisement intake.

Implements seam S-01 of pm/03-interfaces.md over entity E-03 of
pm/03-data-contract.md, per ADR-001 (greenfield, nothing carried in from the
existing estate).

This package stores an advertisement and its source text. It does not extract
employer, role title, seniority, location, work arrangement or skills: those are
R-120 and R-121, seam S-02, and a different task. The extracted fields are
written here only at the defaults the data contract states for them, which is a
contract default and not a reading of the posting.
"""
