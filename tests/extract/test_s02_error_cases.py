"""Every error case S-02 lists for advertisement field extraction, one test each.

The error cases, verbatim from pm/03-interfaces.md S-02:

1. The model returns a value for a field that cannot be located in source_text.
   The field is forced to unknown and the proposed value is recorded in
   dropped_terms, because R-121 forbids inference. What is observable is a field
   the model answered and the system refused, visible as a dropped term with no
   source_span.
2. The model returns prose, a partial object, or a shape that does not carry one
   entry per field. No extraction is recorded, the advertisement is left with
   extraction not attempted, and the raw model output is retained so the
   malformed response can be read back rather than described from memory.
3. The model omits a field rather than marking it unknown. The field is treated
   as unknown, and the record keeps the difference between "the model said
   unknown" and "the model did not answer", because those two point at different
   fixes.
4. The model paraphrases a term the advertisement writes differently, returning
   an expanded name where the posting used an abbreviation. The occurrence check
   fails, the term lands in dropped_terms, and what is observable is a required
   skill visible to a human reader in source_text that is absent from
   required_skills.
5. The model files a preferred skill under required skills, or the reverse. Both
   terms occur in source_text, so the occurrence check passes and the misfiling
   is invisible to it. It is observable only by reading each source_span back
   against the section it came from, and nothing in the requirements makes that
   automatic.
6. Every field comes back unknown while source_text plainly names the employer.
   This is indistinguishable at this seam from the login wall case in S-01, and
   both surface as an advertisement with full source text and no extracted
   fields.

Six cases, six test classes. Case 5 asserts that the misfiling is NOT detected,
because F-02 of pm/05-architecture.md records it as the one T1 correctness check
with no command behind it. A test that claimed otherwise would be a false green.

This build calls no model. The producer on the other side of the boundary is the
deterministic rule set in src/extract/fields.py, and every case is exercised
through fields.ingest_proposal, which is the single point any producer's answer
passes through.

Run: python3 tests/extract/test_s02_error_cases.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from support import COMPLETE_POSTING, TemporaryStore  # noqa: E402

from extract import fields as fields_module  # noqa: E402

STAMP = "2026-09-10T01:00:00Z"

POSTING = (
    "Company: Northwind Analytics\n"
    "Title: Platform Engineer\n"
    "Location: Melbourne, Australia\n\n"
    "We work remote.\n\n"
    "What You Bring\n\n"
    " - Strong experience with APIs and Kubernetes\n\n"
    "Nice to have\n\n"
    " - Exposure to Terraform\n"
)

FULL_PROPOSAL = {
    "employer": "Northwind Analytics",
    "role_title": "Platform Engineer",
    "seniority": "unknown",
    "location": "Melbourne, Australia",
    "work_arrangement": "remote",
    "required_skills": ["APIs", "Kubernetes"],
    "preferred_skills": ["Terraform"],
}


class Case1ValueNotInSourceText(TemporaryStore):
    def test_the_field_is_forced_to_unknown(self):
        proposal = dict(FULL_PROPOSAL, employer="Globex Corporation")
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        self.assertEqual(extraction.values["employer"], "unknown")

    def test_the_proposed_value_is_recorded_in_dropped_terms(self):
        proposal = dict(FULL_PROPOSAL, employer="Globex Corporation")
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        dropped = [d["term"] for d in extraction.dropped_terms]
        self.assertIn("Globex Corporation", dropped)

    def test_the_refused_field_carries_no_source_span(self):
        proposal = dict(FULL_PROPOSAL, employer="Globex Corporation")
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        self.assertEqual(extraction.spans["employer"], [])

    def test_the_refusal_is_observable_on_the_stored_record(self):
        identifier = self.ingest(POSTING)
        proposal = dict(FULL_PROPOSAL, employer="Globex Corporation")
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        self.store.apply(identifier, extraction.as_record_fields(), STAMP)
        stored = self.store.get(identifier)
        self.assertEqual(stored["employer"], "unknown")
        self.assertIn(
            "Globex Corporation", [d["term"] for d in stored["dropped_terms"]]
        )
        self.assertEqual(stored["extraction_spans"]["employer"], [])


class Case2MalformedResponse(TemporaryStore):
    def test_prose_records_no_extraction(self):
        extraction = fields_module.ingest_proposal(
            "The employer appears to be Northwind Analytics.", POSTING
        )
        self.assertIsNotNone(extraction.malformed)
        self.assertEqual(extraction.status, "not_attempted")

    def test_the_raw_response_is_retained_for_reading_back(self):
        raw = ["employer", "Northwind Analytics"]
        extraction = fields_module.ingest_proposal(raw, POSTING)
        self.assertEqual(extraction.raw_proposal, raw)

    def test_the_advertisement_is_left_with_extraction_not_attempted(self):
        identifier = self.ingest(POSTING)
        before = self.store.get(identifier)
        extraction = fields_module.ingest_proposal("not an object", POSTING)
        self.assertIsNotNone(extraction.malformed)
        after = self.store.get(identifier)
        self.assertEqual(after, before)
        self.assertNotIn("model_id", after)
        self.assertNotIn("extracted_at", after)

    def test_an_empty_source_text_is_also_a_not_attempted_state(self):
        extraction = fields_module.extract("")
        self.assertIsNotNone(extraction.malformed)
        self.assertEqual(extraction.status, "not_attempted")


class Case3FieldOmittedRatherThanMarkedUnknown(TemporaryStore):
    def test_an_omitted_field_is_treated_as_unknown(self):
        proposal = dict(FULL_PROPOSAL)
        del proposal["location"]
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        self.assertEqual(extraction.values["location"], "unknown")

    def test_said_unknown_and_did_not_answer_are_kept_apart(self):
        proposal = dict(FULL_PROPOSAL)
        del proposal["location"]
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        self.assertIn("location", extraction.unanswered_fields)
        self.assertNotIn("seniority", extraction.unanswered_fields)
        self.assertNotEqual(
            extraction.unknown_reasons["location"],
            extraction.unknown_reasons["seniority"],
        )

    def test_the_difference_survives_onto_the_stored_record(self):
        identifier = self.ingest(POSTING)
        proposal = dict(FULL_PROPOSAL)
        del proposal["location"]
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        self.store.apply(identifier, extraction.as_record_fields(), STAMP)
        stored = self.store.get(identifier)
        self.assertEqual(stored["location"], "unknown")
        self.assertEqual(stored["seniority"], "unknown")
        self.assertEqual(stored["extraction_unanswered_fields"], ["location"])


class Case4ParaphrasedTerm(TemporaryStore):
    def test_an_expanded_name_for_an_abbreviation_is_dropped(self):
        proposal = dict(
            FULL_PROPOSAL,
            required_skills=["Application Programming Interfaces", "Kubernetes"],
        )
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        self.assertEqual(extraction.required_skills, ["Kubernetes"])
        self.assertIn(
            "Application Programming Interfaces",
            [d["term"] for d in extraction.dropped_terms],
        )

    def test_the_observable_is_a_skill_in_the_text_and_absent_from_the_list(self):
        proposal = dict(
            FULL_PROPOSAL,
            required_skills=["Application Programming Interfaces", "Kubernetes"],
        )
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        self.assertIn("APIs", POSTING)
        self.assertNotIn("APIs", extraction.required_skills)


class Case5MisfiledBetweenRequiredAndPreferred(TemporaryStore):
    """The gap, asserted as a gap.

    Nothing here fixes the misfiling. The tests record that the occurrence check
    cannot see it, and that the spans needed for a person to see it are stored.
    """

    def swapped(self):
        return fields_module.ingest_proposal(
            dict(
                FULL_PROPOSAL,
                required_skills=["Terraform"],
                preferred_skills=["APIs", "Kubernetes"],
            ),
            POSTING,
        )

    def test_the_occurrence_check_passes_on_a_misfiled_term(self):
        extraction = self.swapped()
        terms = extraction.required_skills + extraction.preferred_skills
        offenders = [t for t in terms if t.lower() not in POSTING.lower()]
        self.assertEqual(
            offenders,
            [],
            "the occurrence check is supposed to be blind to misfiling, and is",
        )
        self.assertEqual(extraction.required_skills, ["Terraform"])

    def test_the_span_needed_to_catch_it_by_reading_is_stored(self):
        extraction = self.swapped()
        spans = extraction.spans["required_skills"]
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(POSTING[span["start"]:span["end"]], "Terraform")
        heading = POSTING.rfind("Nice to have", 0, span["start"])
        self.assertGreater(
            heading,
            -1,
            "the stored span sits under a preferred heading, which is the only "
            "way this misfiling can be seen, and it is a person who must look",
        )


class Case6EverythingUnknownWhileTheEmployerIsNamed(TemporaryStore):
    LOGIN_WALL = "Sign in to continue.\n\nPlease log in to view this job at Northwind.\n"

    def test_all_fields_unknown_while_the_text_names_the_employer(self):
        proposal = {
            "employer": "unknown",
            "role_title": "unknown",
            "seniority": "unknown",
            "location": "unknown",
            "work_arrangement": "unknown",
            "required_skills": [],
            "preferred_skills": [],
        }
        extraction = fields_module.ingest_proposal(proposal, POSTING)
        for field in fields_module.SCALAR_FIELDS:
            self.assertEqual(extraction.values[field], "unknown")
        self.assertIn("Northwind Analytics", POSTING)
        self.assertEqual(extraction.status, "partial")

    def test_a_login_wall_produces_the_same_observable(self):
        wall = fields_module.extract(self.LOGIN_WALL)
        posting = fields_module.ingest_proposal(
            {f: "unknown" for f in fields_module.SCALAR_FIELDS}, POSTING
        )
        wall_shape = [wall.values[f] for f in fields_module.SCALAR_FIELDS]
        posting_shape = [posting.values[f] for f in fields_module.SCALAR_FIELDS]
        self.assertEqual(
            wall_shape,
            posting_shape,
            "S-02 says these two are indistinguishable at this seam, and they are",
        )

    def test_both_still_retain_the_full_source_text(self):
        identifier = self.ingest(self.LOGIN_WALL)
        extraction = fields_module.extract(self.LOGIN_WALL)
        self.store.apply(identifier, extraction.as_record_fields(), STAMP)
        stored = self.store.get(identifier)
        self.assertEqual(stored["source_text"], self.LOGIN_WALL)


class ProposalBoundaryDoesNotLeakContent(TemporaryStore):
    def test_a_proposal_cannot_introduce_a_term_that_is_not_in_the_posting(self):
        vocabulary_free = "Company: Acme\nTitle: Gardener\n\nWhat You Bring\n\n - Patience\n"
        extraction = fields_module.ingest_proposal(
            dict(FULL_PROPOSAL, required_skills=["Kubernetes", "Rust", "Patience"]),
            vocabulary_free,
        )
        self.assertEqual(extraction.required_skills, ["Patience"])
        self.assertEqual(
            sorted(d["term"] for d in extraction.dropped_terms if d["proposed_for"] == "required_skills"),
            ["Kubernetes", "Rust"],
        )

    def test_the_deterministic_rules_and_a_proposal_agree_on_the_same_posting(self):
        rules = fields_module.extract(COMPLETE_POSTING)
        proposal = fields_module.ingest_proposal(
            {
                "employer": rules.values["employer"],
                "role_title": rules.values["role_title"],
                "seniority": rules.values["seniority"],
                "location": rules.values["location"],
                "work_arrangement": rules.values["work_arrangement"],
                "required_skills": rules.required_skills,
                "preferred_skills": rules.preferred_skills,
            },
            COMPLETE_POSTING,
        )
        self.assertEqual(proposal.values, rules.values)
        self.assertEqual(proposal.required_skills, rules.required_skills)
        self.assertEqual(proposal.preferred_skills, rules.preferred_skills)


if __name__ == "__main__":
    unittest.main(verbosity=2)
