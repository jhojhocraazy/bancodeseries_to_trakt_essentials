import gzip
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bancodeseries_to_trakt_essentials as etl


class FakeResponse:
    def __init__(self, payload=b"", error=None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def iter_content(self, chunk_size=8192):
        yield self.payload


class TestHardening(unittest.TestCase):
    @patch("builtins.input", return_value="valor-secreto")
    def test_credential_is_persisted_after_visible_prompt(self, _input):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credencial.txt"
            valor = etl.carregar_credencial(str(path), "Credencial")
            self.assertEqual(valor, "valor-secreto")
            self.assertEqual(path.read_text(encoding="utf-8"), "valor-secreto")

    @patch.object(etl.requests, "get")
    def test_dataset_download_is_atomic_and_validated(self, get):
        get.return_value = FakeResponse(b"conteudo-gzip-valido")
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "dataset.gz"
            with self.assertRaises(gzip.BadGzipFile):
                etl._baixar_dataset_imdb("https://example.invalid", destination)
            self.assertFalse(destination.exists())
            self.assertFalse(destination.with_name("dataset.gz.part").exists())

    @patch.object(etl.requests, "get")
    def test_truncated_gzip_is_rejected(self, get):
        source = io.BytesIO()
        with gzip.GzipFile(fileobj=source, mode="wb") as stream:
            stream.write(b"conteudo")
        payload = source.getvalue()[:-4]
        get.return_value = FakeResponse(payload)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "dataset.gz"
            with self.assertRaises((EOFError, OSError)):
                etl._baixar_dataset_imdb("https://example.invalid", destination)
            self.assertFalse(destination.exists())

    @patch.object(etl.requests, "get")
    def test_dataset_download_replaces_only_after_gzip_validation(self, get):
        source = io.BytesIO()
        with gzip.GzipFile(fileobj=source, mode="wb") as stream:
            stream.write(b"conteudo")
        get.return_value = FakeResponse(source.getvalue())
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "dataset.gz"
            etl._baixar_dataset_imdb("https://example.invalid", destination)
            self.assertTrue(destination.exists())
            with gzip.open(destination, "rb") as stream:
                self.assertEqual(stream.read(), b"conteudo")


if __name__ == "__main__":
    unittest.main()
