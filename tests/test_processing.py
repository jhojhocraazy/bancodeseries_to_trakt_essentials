import unittest
from unittest.mock import patch

import bancodeseries_to_trakt_essentials as etl


class TestProcessingConsumption(unittest.TestCase):
    def setUp(self):
        console_patch = patch.object(etl, "console")
        console_patch.start()
        self.addCleanup(console_patch.stop)

    def _obras(self):
        return [{"id": "123", "nome": "Série Fictícia", "categoria": "Ativas em dia"}]

    def _tmdb_structure(self):
        return "900", {
            1: [
                {"episode": 1, "tmdb_id": 1001, "air_date": "2020-01-01", "lancado": True},
                {"episode": 2, "tmdb_id": 1002, "air_date": "2099-01-01", "lancado": False},
            ]
        }

    @patch.object(etl.time, "sleep", return_value=None)
    @patch.object(etl, "buscar_estrutura_tmdb")
    @patch.object(etl, "extrair_dados_serie_bds")
    def test_progress_indicates_position_and_total(self, extrair, buscar_tmdb, _sleep):
        extrair.return_value = ("tt1234567", set())
        buscar_tmdb.return_value = ("900", {})
        obras = [
            {"id": "1", "nome": "Série Uma", "categoria": "Ativas em dia"},
            {"id": "2", "nome": "Série Dois", "categoria": "Ativas em dia"},
        ]
        with patch.object(etl, "console") as console:
            etl.processar_bloco(object(), obras, True, {}, {}, [])
        messages = [str(call.args[0]) for call in console.print.call_args_list]
        self.assertTrue(any("[1/2] Processando" in message for message in messages))
        self.assertTrue(any("[2/2] Processando" in message for message in messages))

    @patch.object(etl.time, "sleep", return_value=None)
    @patch.object(etl, "buscar_estrutura_tmdb")
    @patch.object(etl, "extrair_dados_serie_bds")
    def test_absolute_confidence_exports_released_episodes_only(
        self, extrair, buscar_tmdb, _sleep
    ):
        extrair.return_value = ("tt1234567", set())
        buscar_tmdb.return_value = self._tmdb_structure()
        lines = []

        metrics = etl.processar_bloco(
            object(), self._obras(), True,
            {"tt1234567": {"rating": 8.0, "votes": 10}},
            {"tt1234567": {1: {1: "tt0000001", 2: "tt0000002"}}},
            lines,
        )

        self.assertEqual(metrics["series"], 1)
        self.assertEqual(metrics["episodios_assistidos"], 1)
        self.assertEqual(metrics["episodios_ignorados"], 1)
        self.assertEqual(lines[0]["type"], "show")
        self.assertEqual(lines[0]["ignorar_no_historico"], False)
        self.assertEqual([line["imdb_id"] for line in lines[1:]], ["tt0000001"])
        self.assertNotIn("tt0000002", [line["imdb_id"] for line in lines])

    @patch.object(etl.time, "sleep", return_value=None)
    @patch.object(etl, "buscar_estrutura_tmdb")
    @patch.object(etl, "extrair_dados_serie_bds")
    def test_delayed_grade_exports_only_audited_episodes(
        self, extrair, buscar_tmdb, _sleep
    ):
        extrair.return_value = ("tt1234567", {(1, 1)})
        buscar_tmdb.return_value = self._tmdb_structure()
        lines = []

        etl.processar_bloco(
            object(), self._obras(), False,
            {}, {"tt1234567": {1: {1: "tt0000001", 2: "tt0000002"}}}, lines
        )

        self.assertEqual(lines[0]["ignorar_no_historico"], True)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1]["imdb_id"], "tt0000001")
        self.assertEqual(lines[1]["type"], "episode")

    @patch.object(etl.time, "sleep", return_value=None)
    @patch.object(etl, "buscar_estrutura_tmdb", side_effect=[(None, {}), ("901", {})])
    @patch.object(etl, "buscar_fallback_tmdb", return_value="tt7654321")
    @patch.object(etl, "resolver_redirecionamento_imdb", return_value=None)
    @patch.object(etl, "extrair_dados_serie_bds", return_value=("tt1234567", set()))
    def test_identity_fallback_retries_tmdb_when_redirect_has_no_result(
        self, _extrair, _redirect, _fallback, _buscar, _sleep
    ):
        lines = []
        etl.processar_bloco(
            object(), self._obras(), True, {}, {}, lines
        )
        self.assertEqual([line["imdb_id"] for line in lines], ["tt7654321"])


class TestIdentityFallback(unittest.TestCase):
    def test_tmdb_requests_use_v3_api_key_parameter(self):
        class Response:
            status_code = 200

            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        class Session:
            def __init__(self):
                self.calls = []

            def get(self, url, **kwargs):
                self.calls.append((url, kwargs))
                if "/find/" in url:
                    return Response({"tv_results": [{"id": 900}]})
                return Response({"number_of_seasons": 0})

        session = Session()
        with patch.object(etl, "TMDB_API_KEY", "SECRETKEY"):
            etl.buscar_estrutura_tmdb(session, "tt1234567")
        self.assertTrue(session.calls)
        for url, kwargs in session.calls:
            self.assertNotIn("api_key=", url)
            self.assertEqual(kwargs["params"]["api_key"], "SECRETKEY")

    @patch.object(etl, "buscar_fallback_tmdb", return_value=None)
    @patch.object(etl.requests, "get")
    def test_imdb_redirect_returns_new_id_from_final_url(self, get, _fallback):
        response = type("Response", (), {
            "status_code": 200,
            "url": "https://www.imdb.com/title/tt7654321/",
            "text": "",
        })()
        get.return_value = response
        self.assertEqual(etl.resolver_redirecionamento_imdb("tt1234567"), "tt7654321")


if __name__ == "__main__":
    unittest.main()
