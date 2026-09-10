"""R-121: an undetermined field is unknown, and nothing is inferred.

R-121, verbatim from pm/03-requirements.md:

    If extraction cannot determine a field, then the system shall mark that field
    unknown and shall not infer a value.

The owner set the concrete test for inference: a skill term that appears in the
extracted fields but nowhere in the source text was invented, not extracted.
That test is here, twice over. Once as a property over every term the extractor
emits, and once as a planted defect, so the check has been seen red against a
real violation and is not trusted merely because it is green.

Run: python3 tests/extract/test_unknown_not_inferred.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from support import (  # noqa: E402
    COMPLETE_POSTING,
    LEAD_VERB_POSTING,
    SPARSE_POSTING,
    TemporaryStore,
)

from extract import fields as fields_module  # noqa: E402
from extract import vocabulary as vocabulary_module  # noqa: E402

STAMP = "2026-09-10T01:00:00Z"

POSTINGS = (COMPLETE_POSTING, SPARSE_POSTING, LEAD_VERB_POSTING)


class UnknownRatherThanInferred(TemporaryStore):
    def stored_for(self, posting):
        identifier = self.ingest(posting)
        extraction = fields_module.extract(posting)
        self.store.apply(identifier, extraction.as_record_fields(), STAMP)
        return self.store.get(identifier)

    # the literal unknown, not an absence and not an empty string

    def test_an_undetermined_scalar_carries_the_literal_unknown(self):
        stored = self.stored_for(SPARSE_POSTING)
        for field in fields_module.SCALAR_FIELDS:
            self.assertEqual(stored[field], "unknown", field + " is not the literal unknown")
            self.assertNotEqual(stored[field], "")

    def test_an_undetermined_skill_list_is_empty_and_flagged_undetermined(self):
        stored = self.stored_for(SPARSE_POSTING)
        self.assertEqual(stored["required_skills"], [])
        self.assertFalse(stored["required_skills_determined"])
        self.assertEqual(stored["preferred_skills"], [])
        self.assertFalse(stored["preferred_skills_determined"])

    def test_every_unknown_field_records_why_it_is_unknown(self):
        stored = self.stored_for(SPARSE_POSTING)
        reasons = stored["extraction_unknown_reasons"]
        unknown = [
            f for f in fields_module.SCALAR_FIELDS if stored[f] == "unknown"
        ] + [f for f in fields_module.LIST_FIELDS if not stored[f + "_determined"]]
        missing = [f for f in unknown if not reasons.get(f)]
        self.assertEqual(
            missing,
            [],
            str(len(unknown) - len(missing))
            + " of "
            + str(len(unknown))
            + " unknown fields carry a reason",
        )

    # the owner's inference test, as a property

    def test_every_emitted_skill_term_occurs_verbatim_in_its_own_source_text(self):
        checked = 0
        for posting in POSTINGS:
            stored = self.stored_for(posting)
            terms = stored["required_skills"] + stored["preferred_skills"]
            for term in terms:
                checked += 1
                self.assertIn(
                    term.lower(),
                    stored["source_text"].lower(),
                    "invented term: " + repr(term),
                )
        self.assertGreater(checked, 0, "VACUOUS: no terms were checked")

    def test_every_emitted_value_is_reproducible_from_its_recorded_span(self):
        checked = 0
        for posting in POSTINGS:
            stored = self.stored_for(posting)
            text = stored["source_text"]
            spans = stored["extraction_spans"]
            for field in fields_module.SCALAR_FIELDS:
                if stored[field] == "unknown":
                    self.assertEqual(spans.get(field), [])
                    continue
                self.assertTrue(spans.get(field), field + " has no span")
                for span in spans[field]:
                    checked += 1
                    self.assertEqual(text[span["start"]:span["end"]], span["text"])
            for field in fields_module.LIST_FIELDS:
                self.assertEqual(len(spans.get(field, [])), len(stored[field]))
                for term, span in zip(stored[field], spans[field]):
                    checked += 1
                    self.assertEqual(text[span["start"]:span["end"]], term)
        self.assertGreater(checked, 0, "VACUOUS: no spans were checked")

    def test_a_scalar_that_is_not_unknown_is_the_exact_substring_it_points_at(self):
        stored = self.stored_for(COMPLETE_POSTING)
        text = stored["source_text"]
        for field in ("employer", "role_title", "seniority", "location"):
            self.assertNotEqual(stored[field], "unknown")
            self.assertIn(stored[field], text)

    def test_work_arrangement_is_an_enum_token_backed_by_a_trigger_span(self):
        """The one field whose stored value is normalised rather than quoted.

        E-03 declares work_arrangement as an enum, so the stored value cannot be
        the posting's wording. The span must therefore carry the wording, and
        that wording must be a phrase the rule accepts for that value.
        """
        stored = self.stored_for(COMPLETE_POSTING)
        self.assertIn(stored["work_arrangement"], ("remote", "hybrid", "onsite"))
        spans = stored["extraction_spans"]["work_arrangement"]
        self.assertEqual(len(spans), 1)
        triggers = dict(fields_module._ARRANGEMENT_TRIGGERS)
        self.assertTrue(
            triggers[stored["work_arrangement"]].fullmatch(spans[0]["text"])
        )
        self.assertIn(spans[0]["text"], stored["source_text"])

    # planted defects, so the checks above have been seen red

    def test_the_verbatim_check_goes_red_on_a_planted_invented_term(self):
        stored = self.stored_for(COMPLETE_POSTING)
        poisoned = list(stored["required_skills"]) + ["Erlang"]
        self.assertNotIn("erlang", stored["source_text"].lower())
        offenders = [
            t for t in poisoned if t.lower() not in stored["source_text"].lower()
        ]
        self.assertEqual(
            offenders,
            ["Erlang"],
            "the check that is supposed to catch an invented term did not",
        )

    def test_a_term_that_cannot_be_located_is_dropped_rather_than_stored(self):
        extraction = fields_module.extract(COMPLETE_POSTING)
        extraction.required_skills.append("Erlang")
        extraction.spans["required_skills"].append(
            {"start": 0, "end": 6, "text": "Erlang", "rule_id": "planted"}
        )
        fields_module._enforce_traceability(extraction, COMPLETE_POSTING)
        self.assertNotIn("Erlang", extraction.required_skills)
        dropped = [d["term"] for d in extraction.dropped_terms]
        self.assertIn("Erlang", dropped)

    def test_a_scalar_whose_span_does_not_reproduce_it_is_forced_to_unknown(self):
        extraction = fields_module.extract(COMPLETE_POSTING)
        extraction.values["employer"] = "Globex"
        extraction.spans["employer"] = [
            {"start": 0, "end": 6, "text": "Globex", "rule_id": "planted"}
        ]
        fields_module._enforce_traceability(extraction, COMPLETE_POSTING)
        self.assertEqual(extraction.values["employer"], "unknown")
        self.assertIn(
            "Globex", [d["term"] for d in extraction.dropped_terms]
        )

    # the trap: a plausible token that means something else

    def test_a_seniority_word_used_as_a_verb_does_not_become_the_seniority(self):
        self.assertIn("Lead technical discovery", LEAD_VERB_POSTING)
        stored = self.stored_for(LEAD_VERB_POSTING)
        self.assertEqual(
            stored["seniority"],
            "unknown",
            "the verb 'Lead' was read as a seniority, which would put a level on "
            "a resume the posting never stated",
        )
        self.assertEqual(stored["role_title"], "Customer Engineer")

    def test_a_single_weak_possessive_does_not_become_the_employer(self):
        posting = "As a Data Engineer, you will improve Acme's pipeline.\n"
        stored = self.stored_for(posting)
        self.assertEqual(stored["employer"], "unknown")
        self.assertIn("occurs once", stored["extraction_unknown_reasons"]["employer"])

    # the vocabulary is a filter, never a source of content

    def test_no_vocabulary_entry_absent_from_the_posting_is_ever_emitted(self):
        stored = self.stored_for(COMPLETE_POSTING)
        text = stored["source_text"].lower()
        emitted = set(
            t.lower() for t in stored["required_skills"] + stored["preferred_skills"]
        )
        absent = [t for t in vocabulary_module.TERMS if t.lower() not in text]
        leaked = [t for t in absent if t.lower() in emitted]
        self.assertEqual(
            leaked,
            [],
            str(len(absent) - len(leaked))
            + " of "
            + str(len(absent))
            + " vocabulary entries absent from this posting stayed out of it",
        )
        self.assertGreater(len(absent), 0, "VACUOUS: no absent entries to check")

    def test_a_posting_with_no_vocabulary_term_yields_no_skills(self):
        posting = (
            "As a Gardener, you will tend the beds.\n\nWhat You Bring\n\n"
            " - A steady hand and an early start\n"
        )
        stored = self.stored_for(posting)
        self.assertEqual(stored["required_skills"], [])
        self.assertFalse(stored["required_skills_determined"])
        self.assertIn("required_skills", stored["extraction_unknown_reasons"])

    def test_duties_outside_a_requirements_section_are_not_required_skills(self):
        posting = (
            "As a Customer Engineer, you will help customers.\n\n"
            "What You'll Do\n\n - Build demos with Kubernetes and Terraform\n\n"
            "What You Bring\n\n - Experience with APIs\n"
        )
        stored = self.stored_for(posting)
        self.assertEqual(stored["required_skills"], ["APIs"])
        self.assertNotIn("Kubernetes", stored["required_skills"])

    def test_a_plus_marker_moves_a_term_out_of_required(self):
        posting = (
            "What You Bring\n\n - Experience with APIs\n\n"
            " - Exposure to Kubernetes is a plus\n"
        )
        stored = self.stored_for(posting)
        self.assertEqual(stored["required_skills"], ["APIs"])
        self.assertEqual(stored["preferred_skills"], ["Kubernetes"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
