import csv
import os
import tempfile
import unittest
from pathlib import Path

import bancodeseries_to_trakt_essentials as etl


class TestTraktExportFiles(unittest.TestCase):
    def _rows(self):
        return [
            {"imdb_id": "tt1", "tmdb_id": 1, "type": "show", "rating": 0.0,
             "ignorar_no_historico": True},
            {"imdb_id": "tt2", "tmdb_id": 2, "type": "episode", "rating": 8.0,
             "ignorar_no_historico": False},
        ]

    def test_writes_exact_headers_and_internal_fields_are_omitted(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                history, ratings, history_name, ratings_name = etl.exportar_trakt(
                    self._rows(), "20260925_010203"
                )
                self.assertEqual(history, [self._rows()[1]])
                self.assertEqual(ratings, self._rows())
                with open(history_name, newline="", encoding="utf-8") as stream:
                    self.assertEqual(next(csv.reader(stream)), ["imdb_id", "tmdb_id", "type"])
                with open(ratings_name, newline="", encoding="utf-8") as stream:
                    self.assertEqual(next(csv.reader(stream)), ["imdb_id", "tmdb_id", "type", "rating"])
                self.assertNotIn("ignorar_no_historico", Path(ratings_name).read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)

    def test_uses_same_timestamp_and_preserves_zero_rating(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                _, _, history_name, ratings_name = etl.exportar_trakt(
                    self._rows(), "20260925_010203"
                )
                self.assertIn("20260925_010203", history_name)
                self.assertIn("20260925_010203", ratings_name)
                with open(ratings_name, newline="", encoding="utf-8") as stream:
                    rows = list(csv.DictReader(stream))
                self.assertEqual(rows[0]["rating"], "0.0")
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
