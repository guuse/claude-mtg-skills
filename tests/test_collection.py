"""Tests for mtg_scryfall.collection — tolerant parsing of txt/csv/json owned-card exports.

Pure file/string parsing, fully offline. Each test writes a small fixture to a tempdir and
checks the normalised {name: count} mapping, merging, and format detection.
"""

import json
import os
import sys
import tempfile
import unittest

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import collection  # noqa: E402


def _write(dirpath, name, text):
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class TxtTests(unittest.TestCase):
    def test_plain_count_name(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.txt", "4 Lightning Bolt\n2 Counterspell\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["format"], "txt")
            self.assertEqual(r["cards"], {"Lightning Bolt": 4, "Counterspell": 2})
            self.assertEqual(r["total"], 6)
            self.assertEqual(r["unique"], 2)

    def test_strips_set_annotation_and_sections(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.txt",
                       "Deck\n4 Lightning Bolt (M21) 159\nSideboard\n3 Negate (DMU) 58\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Lightning Bolt": 4, "Negate": 3})

    def test_merges_duplicates_case_insensitively(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.txt", "4 Lightning Bolt\n2 lightning bolt\n")
            r = collection.parse_collection(p)
            # First-seen display name is kept; counts sum.
            self.assertEqual(r["cards"], {"Lightning Bolt": 6})

    def test_comments_and_blanks_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.txt", "# my collection\n\n4 Llanowar Elves\n// note\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Llanowar Elves": 4})

    def test_bare_name_counts_as_one(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.txt", "Sol Ring\nSol Ring\nMana Crypt\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Sol Ring": 2, "Mana Crypt": 1})

    def test_x_prefix_quantity(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.txt", "4x Opt\n1x Shock\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Opt": 4, "Shock": 1})


class CsvTests(unittest.TestCase):
    def test_header_name_quantity(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", "Name,Quantity\nLightning Bolt,4\nCounterspell,2\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["format"], "csv")
            self.assertEqual(r["cards"], {"Lightning Bolt": 4, "Counterspell": 2})

    def test_moxfield_style_count_first(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv",
                       "Count,Tradelist Count,Name,Edition\n"
                       "3,0,Sheoldred the Apocalypse,DMU\n"
                       "4,1,Llanowar Elves,DMU\n")
            r = collection.parse_collection(p)
            # Prefers exact "count" over "tradelist count"; picks the Name column.
            self.assertEqual(r["cards"],
                             {"Sheoldred the Apocalypse": 3, "Llanowar Elves": 4})

    def test_quoted_name_with_comma(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", 'Name,Quantity\n"Jace, the Mind Sculptor",1\n')
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Jace, the Mind Sculptor": 1})

    def test_merges_same_card_across_rows(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv",
                       "Name,Set,Quantity\nShock,M21,2\nShock,DMU,3\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Shock": 5})

    def test_headerless_positional(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", "4,Lightning Bolt\n2,Counterspell\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Lightning Bolt": 4, "Counterspell": 2})

    def test_header_without_quantity_defaults_one(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", "Name\nLightning Bolt\nLightning Bolt\nShock\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Lightning Bolt": 2, "Shock": 1})


class JsonTests(unittest.TestCase):
    def test_array_of_objects(self):
        with tempfile.TemporaryDirectory() as d:
            data = [{"name": "Lightning Bolt", "quantity": 4},
                    {"name": "Counterspell", "count": 2}]
            p = _write(d, "c.json", json.dumps(data))
            r = collection.parse_collection(p)
            self.assertEqual(r["format"], "json")
            self.assertEqual(r["cards"], {"Lightning Bolt": 4, "Counterspell": 2})

    def test_name_to_count_map(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json", json.dumps({"Sol Ring": 1, "Shock": 3}))
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Sol Ring": 1, "Shock": 3})

    def test_container_key_unwrapped(self):
        with tempfile.TemporaryDirectory() as d:
            data = {"collection": [{"name": "Opt", "quantity": 4}]}
            p = _write(d, "c.json", json.dumps(data))
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Opt": 4})

    def test_array_of_bare_names(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json", json.dumps(["Shock", "Shock", "Opt"]))
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Shock": 2, "Opt": 1})

    def test_arena_id_only_map_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json", json.dumps({"70123": 4, "70124": 2}))
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {})
            self.assertIsNotNone(r["note"])

    def test_invalid_json_raises_valueerror(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json", "{not valid json")
            with self.assertRaises(ValueError):
                collection.parse_collection(p)


class FindAndLoadTests(unittest.TestCase):
    def test_find_prefers_known_stem_and_txt(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "random.json", "[]")
            _write(d, "mtga_collection.csv", "Name,Quantity\nShock,1\n")
            _write(d, "mtga_collection.txt", "1 Shock\n")
            found = collection.find_collection_file(d)
            self.assertEqual(os.path.basename(found), "mtga_collection.txt")

    def test_find_ignores_empty_and_dotfiles(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, ".keep", "")
            _write(d, "empty.txt", "")
            _write(d, "deck.csv", "Name,Quantity\nShock,2\n")
            found = collection.find_collection_file(d)
            self.assertEqual(os.path.basename(found), "deck.csv")

    def test_find_returns_none_when_empty_dir(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(collection.find_collection_file(d))

    def test_load_with_explicit_path(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.txt", "4 Opt\n")
            r = collection.load_collection(p)
            self.assertEqual(r["cards"], {"Opt": 4})

    def test_load_via_mtg_home(self):
        with tempfile.TemporaryDirectory() as home:
            cdir = os.path.join(home, "collection")
            os.makedirs(cdir)
            _write(cdir, "mtga_collection.csv", "Name,Quantity\nShock,3\n")
            old = os.environ.get("MTG_HOME")
            os.environ["MTG_HOME"] = home
            try:
                r = collection.load_collection()
            finally:
                if old is None:
                    os.environ.pop("MTG_HOME", None)
                else:
                    os.environ["MTG_HOME"] = old
            self.assertEqual(r["cards"], {"Shock": 3})

    def test_load_returns_none_when_no_file(self):
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, "collection"))
            old = os.environ.get("MTG_HOME")
            os.environ["MTG_HOME"] = home
            try:
                self.assertIsNone(collection.load_collection())
            finally:
                if old is None:
                    os.environ.pop("MTG_HOME", None)
                else:
                    os.environ["MTG_HOME"] = old


class MergeAndEdgeTests(unittest.TestCase):
    def test_zero_and_negative_and_nonint_counts_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json",
                       json.dumps({"Shock": 0, "Opt": -2, "Bolt": "lots", "Keep": 3}))
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Keep": 3})

    def test_csv_empty_name_cell_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", "Name,Quantity\n,4\nShock,2\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Shock": 2})

    def test_csv_blank_only_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", "\n\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {})
            self.assertEqual(r["total"], 0)

    def test_csv_substring_header_match(self):
        with tempfile.TemporaryDirectory() as d:
            # Neither header is an exact token; both match by substring (amount / card name).
            p = _write(d, "c.csv", "Amount Owned,The Card Name\n4,Shock\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Shock": 4})

    def test_csv_header_no_name_column_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", "Quantity,Edition\n4,Dominaria\n")
            r = collection.parse_collection(p)
            # No name column → positional fallback on data rows; the text cell is the name.
            self.assertEqual(r["cards"], {"Dominaria": 4})

    def test_csv_short_row_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", "Set,Name\nM21,Shock\nDMU\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Shock": 1})

    def test_csv_positional_digits_only_row_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.csv", "4,2\n3,Shock\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Shock": 3})

    def test_json_object_without_quantity_defaults_one(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json", json.dumps([{"name": "Opt"}]))
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Opt": 1})

    def test_json_array_objects_without_names_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json", json.dumps([{"quantity": 4}, {"qty": 2}]))
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {})
            self.assertIsNotNone(r["note"])

    def test_json_map_of_objects(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json",
                       json.dumps({"slot1": {"name": "Shock", "quantity": 3}}))
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {"Shock": 3})

    def test_json_scalar_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.json", "42")
            r = collection.parse_collection(p)
            self.assertEqual(r["cards"], {})

    def test_find_skips_non_collection_extensions(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "notes.md", "hello")
            _write(d, "deck.txt", "1 Shock\n")
            self.assertEqual(os.path.basename(collection.find_collection_file(d)), "deck.txt")

    def test_find_returns_none_for_missing_dir(self):
        self.assertIsNone(collection.find_collection_file("/no/such/dir/xyz"))

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            collection.parse_collection("/no/such/file.txt")


class SniffTests(unittest.TestCase):
    def test_unknown_ext_json_content(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.dat", json.dumps({"Shock": 2}))
            r = collection.parse_collection(p)
            self.assertEqual(r["format"], "json")
            self.assertEqual(r["cards"], {"Shock": 2})

    def test_unknown_ext_csv_content(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.dat", "Name,Quantity\nShock,2\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["format"], "csv")
            self.assertEqual(r["cards"], {"Shock": 2})

    def test_unknown_ext_txt_content(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "c.dat", "4 Shock\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["format"], "txt")
            self.assertEqual(r["cards"], {"Shock": 4})

    def test_unknown_ext_bracket_but_invalid_json_falls_through(self):
        with tempfile.TemporaryDirectory() as d:
            # First char '{' makes JSON get tried (and fail); then it sniffs to the txt grammar.
            p = _write(d, "c.dat", "{\n4 Shock\n")
            r = collection.parse_collection(p)
            self.assertEqual(r["format"], "txt")
            self.assertEqual(r["cards"].get("Shock"), 4)


if __name__ == "__main__":
    unittest.main()
