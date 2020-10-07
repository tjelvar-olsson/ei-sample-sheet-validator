"Validate sample sheet."

import os
import sys
from dataclasses import dataclass

HEADERS = [
    "Sample ID",
    "Submitter Library Name",
    "Index 1 ID",
    "Index 1 (i7) Sequence in 5' to 3' orientation",
    "Index 2 ID",
    "Index 2 (i5) Sequence in 5' to 3' orientation",
    "Index ID",
    "Index Tag"
]

REQUIRED_HEADERS = [
    "Sample ID",
    "Submitter Library Name",
    "Index 1 ID",
    "Index 1 (i7) Sequence in 5' to 3' orientation",
]

@dataclass
class SampleRow:
    sample_id: str
    submitter_library_name: str
    index_1_id: str
    index_1_seq: str
    index_2_id: str = None
    index_2_seq: str = None
    index_id: str = None
    index_tag: str = None


def test_SampleRow_init():
    sample_row = SampleRow(
        "A35376",
        "BC003BRHSC1",
        "HSC_A1",
        "TAAGGCGA",
        "HSC_A1",
        "CTCTCTAT"
    )
    assert sample_row.sample_id == "A35376"
    assert sample_row.index_2_id == "HSC_A1"
    assert sample_row.index_id is None


def find_duplicates(l):
    unique_counts = {}
    duplicates = []
    for i in l:
        unique_counts[i] = unique_counts.get(i, 0) + 1
    for key, value in unique_counts.items():
        if value > 1:
            duplicates.append((key, value))
    return duplicates


def test_find_duplicates():
    l = [("a", "1"), ("a", "2"), ("b", "1"), ("a", "2")]
    assert find_duplicates(l) == [(("a", "2"), 2)]


def all_unique(l, message):
    duplicates = find_duplicates(l)
    for d in duplicates:
        ids, count = d
        print(message.format(ids))
    return len(duplicates) == 0


class SampleSheet:

    def __init__(self):
        self._headers = []
        self._rows = []
        self._is_okay = True

    @classmethod
    def parse_line(cls, line):
        return line.strip().split(",")

    @classmethod
    def from_csv(cls, fhandle):
        sample_sheet = cls()
        sample_sheet._headers = cls.parse_line(next(fhandle))
        for line in fhandle:
            sample_row = SampleRow(*cls.parse_line(line))
            sample_sheet._rows.append(sample_row)
        return sample_sheet

    @property
    def is_okay(self):
        return self._is_okay

    def _validate_required_headers(self):
        for h in REQUIRED_HEADERS:
            if h not in self._headers:
                print(f"Missing required header: {h}")
                print(self._headers)
                self._is_okay = False

    def _validate_sample_id_and_submitter_libarary_name_unique(self):
        ids = [
            (s.sample_id,  s.submitter_library_name)
            for s in self._rows
        ]
        okay = all_unique(ids, "'Sample ID' and 'Submitter Library ID' not unique: {}")
        if not okay:
            self._is_okay = False

    def _validate_sample_id_and_index1seq_unique_if_no_index2seq(self):
        ids = [
            (s.sample_id, s.index_1_seq)
            for s in self._rows
            if s.index_2_seq == ""
        ]
        okay = all_unique(ids, "'Sample ID' and 'Index 1 Sequence' not unique: {}")
        if not okay:
            self._is_okay = False

    def _validate_sample_id_and_index_tag_unique_if_index2seq(self):
        ids = [
            (s.sample_id, s.index_tag)
            for s in self._rows
            if s.index_2_seq != ""
        ]
        okay = all_unique(ids, "'Sample ID' and 'Index Tag' not unique: {}")
        if not okay:
            self._is_okay = False

    def _validate_index_tag_matches_tag1_seq_tag2_seq(self):
        for i, s in enumerate(self._rows):
            if s.index_tag != "":
                expected_index_tag = f"{s.index_1_seq}-{s.index_2_seq}"
                if expected_index_tag != s.index_tag:
                    self._is_okay = False
                    row = i + 2
                    print(f"Expected and actual index tags do not match on row {row}")
                    print(f"Expected: {expected_index_tag}")
                    print(f"Actual  : {s.index_tag}")


    def validate(self):
        self._validate_required_headers()
        self._validate_sample_id_and_submitter_libarary_name_unique()
        self._validate_sample_id_and_index1seq_unique_if_no_index2seq()
        self._validate_sample_id_and_index_tag_unique_if_index2seq()
        self._validate_index_tag_matches_tag1_seq_tag2_seq()




if __name__ == "__main__":

    fpath = os.path.abspath(sys.argv[1])
    with open(fpath) as fh:
        sample_sheet = SampleSheet.from_csv(fh)
    sample_sheet.validate()
    if sample_sheet.is_okay:
        print("All good!  :)")
    else:
        sys.exit(2)
