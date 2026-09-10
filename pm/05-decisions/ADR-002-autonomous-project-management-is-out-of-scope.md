ACCEPTED

# ADR-002: Autonomous project management is out of scope for this project

CONTEXT
The canonical register holds 143 requirements. Rows R-001 to R-116 are the verbatim import of the
legacy Career OS register, and 113 of them govern autonomy, delegation, drift, truthfulness,
coordinator behaviour and control-plane process rather than the product. Lane D1 measured that split:
3 of the 116 are product-facing (S-76, S-77, S-78). The repository also carries a control plane that
serves those requirements and not the product: 741 lines of tracked coordination code under
ops/herdr-coordinator and tools/herdr-coordinator, six CONTROL mission files under how/missions, and
STATE.md. The owner ruled this session that autonomous project management is being completed by a
different project.

DECISION
This project builds the job application product only. Requirements R-001 to R-116 are OUT OF SCOPE
here and are owned by the autonomous project management project. R-117 onward are in scope. The
delivery ladder, the task plan and every status report count product requirements only.

ALTERNATIVES
- Delete rows R-001 to R-116 from the register. Rejected: it destroys the traceability chain back to the legacy register, which the owner committed as authority on 2026-09-09, and a deletion cannot be undone by reading the file.
- Split the register into two files. Rejected: step 3 permits exactly one file carrying the canonical-register marker, and two registers is the failure mode that makes every downstream disagreement unresolvable. The rows stay in one file, marked. This ADR deliberately does not quote that marker string, because a document that quotes it becomes a second match for the repo-wide check that counts registers.
- Leave the scope as it was and continue reporting 143 rows. Rejected by the owner in her own words this session: "remove the autonomous project management, that is being completed by another project. Focus on the job-application product."

CONSEQUENCES
Makes easy: an honest ladder. Progress is now measured against 27 product requirements rather than
diluted across 143, and no control-plane row can be reported as product delivery.
Makes hard: nothing in the product build. The 112 rows previously reading "judged by Ally Haire" leave
the owner's judgement queue, which was the largest single demand on the constraint named in
pm/01-discovery.md.
Forecloses: nothing. The rows remain in place, verbatim, with their source column intact, so the other
project can adopt them by reference.
Does NOT decide: whether the control plane code and mission files are deleted from this repository.
Descoping does not require deletion, deletion is not reversible, and the owner has not asked for it.
They stay until she says otherwise.

DATE
2026-09-10, decided by Ally Haire.
