"""R-140: a record citing a document this system generated is not provenance for a claim.

R-117 permits such a record. R-140 closes the hole: the record may sit in the store, but
it may not stand behind a claim, because then the document attests itself and every
traceability check downstream passes while nothing outside the system supports the claim.
This is the seam error case written out in pm/03-interfaces.md S-04.

Every test builds its own store under a temporary directory. None reads or writes ./store.

Run: python3 tests/evidence/test_rejects_self_generated_provenance.py
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
)

from evidence.store import EvidenceStore, ProvenanceRefused  # noqa: E402

GENERATED_DOC_ID = "doc_generated_resume_v1"
GENERATED_RENDER_URI = "renders/doc_generated_resume_v1.pdf"


class TemporaryStore(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="career_os_provenance_test_")
        self.store = EvidenceStore(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write_raw(self, collection, doc_id, payload):
        directory = os.path.join(self.root, collection)
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, doc_id + ".json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def plant_generated_document(self):
        self.write_raw(
            "documents",
            GENERATED_DOC_ID,
            {"id": GENERATED_DOC_ID, "render_uri": GENERATED_RENDER_URI},
        )

    def outside_record(self, **overrides):
        base = {
            "id": "ev_outside",
            "claim_text": "Test Role, Test Org, Jan 2020.",
            "kind": "role",
            "source": "self-written 2022 CV",
            "source_kind": "document",
            "date": "2020-01",
        }
        base.update(overrides)
        return base


class TestSelfGeneratedProvenanceIsRefused(TemporaryStore):
    def test_a_record_citing_a_generated_document_by_id_is_refused(self):
        self.plant_generated_document()
        with self.assertRaises(ProvenanceRefused) as caught:
            self.store.write(
                self.outside_record(id="ev_circular", source=GENERATED_DOC_ID)
            )
        self.assertEqual(caught.exception.record_id, "ev_circular")
        self.assertEqual(caught.exception.source, GENERATED_DOC_ID)
        self.assertIsNone(self.store.get("ev_circular"))

    def test_a_record_citing_a_generated_document_by_render_uri_is_refused(self):
        self.plant_generated_document()
        with self.assertRaises(ProvenanceRefused):
            self.store.write(
                self.outside_record(id="ev_circular_uri", source=GENERATED_RENDER_URI)
            )

    def test_a_record_citing_a_source_outside_the_system_is_accepted(self):
        self.plant_generated_document()
        status, identifier = self.store.write(self.outside_record())
        self.assertEqual(status, "stored")
        self.assertEqual(identifier, "ev_outside")

    def test_a_non_document_source_kind_is_not_caught_by_this_rule(self):
        """R-140 is scoped to source_kind document. A person attestation whose text
        happens to equal a document identifier is not circular provenance, and widening
        the rule past what R-140 says would reject sound records."""
        self.plant_generated_document()
        status, _ = self.store.write(
            self.outside_record(
                id="ev_attested",
                source=GENERATED_DOC_ID,
                source_kind="person_attestation",
            )
        )
        self.assertEqual(status, "stored")

    def test_provenance_records_excludes_a_record_planted_behind_the_write_path(self):
        """A circular record that arrived by a hand edit is still excluded on read."""
        self.plant_generated_document()
        self.store.write(self.outside_record())
        self.write_raw(
            "evidence",
            "ev_planted_circular",
            self.outside_record(id="ev_planted_circular", source=GENERATED_DOC_ID),
        )
        self.assertEqual(len(self.store.all_records()), 2)
        provenance = [r["id"] for r in self.store.provenance_records()]
        self.assertEqual(provenance, ["ev_outside"])


class TestTheR140PredicateFiresOnAConstructedViolation(TemporaryStore):
    """The gate is not trusted until it has been seen red.

    Nothing this system generated exists yet, so R-140 is vacuous on the real store: its
    claim denominator is zero. This test constructs the violation the requirement exists
    to catch and runs the acceptance predicate from R-140 in pm/03-requirements.md over
    it, so the predicate is known to be capable of firing.
    """

    def r140(self):
        def load(collection):
            directory = os.path.join(self.root, collection)
            if not os.path.isdir(directory):
                return []
            loaded = []
            for name in sorted(os.listdir(directory)):
                if not name.endswith(".json"):
                    continue
                with open(os.path.join(directory, name), "r", encoding="utf-8") as handle:
                    loaded.append(json.load(handle))
            return loaded

        documents = load("documents")
        generated = {str(d.get("id")) for d in documents}
        generated |= {str(d.get("render_uri")) for d in documents if d.get("render_uri")}
        evidence = {r.get("id"): r for r in load("evidence")}
        cited = [
            c
            for c in load("document_claims")
            if c.get("traceable") and c.get("evidence_record_id") in evidence
        ]
        circular = [
            c.get("id")
            for c in cited
            if evidence[c["evidence_record_id"]].get("source_kind") == "document"
            and str(evidence[c["evidence_record_id"]].get("source")) in generated
        ]
        passed = bool(evidence) and not circular
        return passed, len(cited) - len(circular), len(cited), len(evidence), circular

    def test_red_when_a_traceable_claim_rests_on_a_self_generated_record(self):
        self.plant_generated_document()
        self.write_raw(
            "evidence",
            "ev_circular",
            self.outside_record(id="ev_circular", source=GENERATED_DOC_ID),
        )
        self.write_raw(
            "document_claims",
            "claim_circular",
            {
                "id": "claim_circular",
                "traceable": True,
                "evidence_record_id": "ev_circular",
            },
        )
        passed, clean, total, evidence_count, circular = self.r140()
        self.assertFalse(passed)
        self.assertEqual((clean, total, evidence_count), (0, 1, 1))
        self.assertEqual(circular, ["claim_circular"])

    def test_green_when_the_same_claim_rests_on_an_outside_source(self):
        self.plant_generated_document()
        self.store.write(self.outside_record())
        self.write_raw(
            "document_claims",
            "claim_sound",
            {"id": "claim_sound", "traceable": True, "evidence_record_id": "ev_outside"},
        )
        passed, clean, total, evidence_count, circular = self.r140()
        self.assertTrue(passed)
        self.assertEqual((clean, total, evidence_count, circular), (1, 1, 1, []))

    def test_the_predicate_is_vacuous_not_passing_when_no_evidence_exists(self):
        passed, _, total, evidence_count, _ = self.r140()
        self.assertEqual((total, evidence_count), (0, 0))
        self.assertFalse(passed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
