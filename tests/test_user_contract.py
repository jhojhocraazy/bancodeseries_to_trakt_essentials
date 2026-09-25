import unittest
from unittest.mock import patch

import bancodeseries_to_trakt_essentials as etl


class TestUserContract(unittest.TestCase):
    @patch.object(etl, "console")
    @patch("builtins.input", side_effect=["9", "2"])
    def test_invalid_menu_option_keeps_user_in_menu(self, _input, _console):
        self.assertEqual(etl.exibir_menu_e_obter_selecao(), ["Finalizadas Completas"])
        self.assertEqual(_input.call_count, 2)

    @patch.object(etl, "console")
    @patch.object(etl.Panel, "fit", side_effect=lambda *args, **kwargs: args[0])
    @patch("builtins.input", side_effect=["1"])
    def test_confirmation_exposes_columns_and_rules(self, _input, _panel, console):
        self.assertTrue(etl.confirmar_exportacao(["Finalizadas Completas"]))
        rendered = " ".join(str(call.args[0]) for call in console.print.call_args_list)
        self.assertIn("imdb_id, tmdb_id, type", rendered)
        self.assertIn("imdb_id, tmdb_id, type, rating", rendered)
        self.assertIn("futuros", rendered.lower())

    @patch.object(etl, "console")
    @patch.object(etl.Panel, "fit", side_effect=lambda *args, **kwargs: args[0])
    @patch("builtins.input", side_effect=["H"])
    def test_menu_is_compact_and_help_uses_same_white_style(self, _input, _panel, console):
        etl.exibir_menu_e_obter_selecao()
        rendered = " ".join(str(call.args[0]) for call in console.print.call_args_list)
        self.assertIn("Ativas em dia (imdb_id, tmdb_id, type)", rendered)
        self.assertIn("[bold white]H.[/bold white] Ajuda", rendered)
        self.assertNotIn("[bold green]H", rendered)

    @patch.object(etl, "console")
    @patch("builtins.input", side_effect=["H"])
    def test_help_is_official_option_and_six_remains_compatible(self, _input, _console):
        self.assertEqual(etl.exibir_menu_e_obter_selecao(), "DOC")
        _input.reset_mock()
        with patch("builtins.input", side_effect=["6"]):
            self.assertEqual(etl.exibir_menu_e_obter_selecao(), "DOC")

    @patch.object(etl, "console")
    @patch("builtins.input", side_effect=["0"])
    def test_exit_menu_option_stops_without_selection(self, _input, _console):
        with self.assertRaises(SystemExit) as context:
            etl.exibir_menu_e_obter_selecao()
        self.assertEqual(context.exception.code, 0)

    def test_history_excludes_internal_flag_and_ratings_preserves_zero(self):
        lines = [
            {"imdb_id": "tt1", "tmdb_id": 1, "type": "show", "rating": 0.0,
             "ignorar_no_historico": True},
            {"imdb_id": "tt2", "tmdb_id": 2, "type": "episode", "rating": "",
             "ignorar_no_historico": False},
        ]
        self.assertEqual(etl._linhas_history(lines), [lines[1]])
        self.assertEqual(etl._linhas_com_nota(lines), [lines[0]])


if __name__ == "__main__":
    unittest.main()
