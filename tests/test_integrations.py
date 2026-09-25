import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import bancodeseries_to_trakt_essentials as etl


class TestStartupOffline(unittest.TestCase):
    def test_entrypoint_exists_and_bootstraps_without_network(self):
        self.assertTrue(callable(getattr(etl, "main")))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tmdb_api.txt").write_text("fake-tmdb-key", encoding="utf-8")
            (root / "phpsessid.txt").write_text("fake-sessid", encoding="utf-8")
            session = MagicMock()
            previous = Path.cwd()
            os.chdir(root)
            try:
                with patch.object(etl, "console"), \
                     patch.object(etl, "limpar_tela"), \
                     patch.object(etl, "carregar_datasets_imdb", return_value=({}, {})) as datasets, \
                     patch.object(etl, "exibir_menu_e_obter_selecao", side_effect=SystemExit(0)) as menu, \
                     patch.object(etl.requests, "Session", return_value=session) as session_class:
                    with self.assertRaises(SystemExit) as context:
                        etl.main()
            finally:
                os.chdir(previous)

            self.assertEqual(context.exception.code, 0)
            self.assertEqual(etl.TMDB_API_KEY, "fake-tmdb-key")
            datasets.assert_called_once_with()
            menu.assert_called_once_with()
            session_class.assert_called_once_with()
            session.mount.assert_any_call("https://", unittest.mock.ANY)
            session.mount.assert_any_call("http://", unittest.mock.ANY)
            session.cookies.set.assert_called_once_with(
                "PHPSESSID", "fake-sessid", domain="bancodeseries.com.br"
            )
            self.assertIn("User-Agent", session.headers.update.call_args[0][0])

    def test_existing_credential_is_reused_without_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tmdb_api.txt"
            path.write_text("  fake-key \n", encoding="utf-8")
            modified = path.stat().st_mtime_ns
            with patch.object(etl, "console"), patch("builtins.input") as prompt:
                self.assertEqual(etl.carregar_credencial(str(path), "prompt"), "fake-key")
            prompt.assert_not_called()
            self.assertEqual(path.stat().st_mtime_ns, modified)


if __name__ == "__main__":
    unittest.main()
