import gzip
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bancodeseries_to_trakt_essentials as etl


class FakeResponse:
    def __init__(self, text="", json_data=None, status_code=200):
        self.text = text
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self, response):
        self.response = response

    def get(self, *_args, **_kwargs):
        return self.response


class TestParsingGrades(unittest.TestCase):
    def test_extracts_four_categories_and_ignores_invalid_links(self):
        html = """
        <b>Ativas em dia</b><br><small>
            <a href="index.php?action=ss&serieid=11">Série Um</a>
            <a href="index.php?action=ss&serieid=11">Série Um duplicada</a>
            <a href="index.php?action=home">Início</a>
            <a href="index.php?action=ss&serieid=12">(link inválido)</a>
        </small>
        <b>Finalizadas Completas</b><br><small>
            <a href="index.php?action=ss&serieid=21">Série Dois</a>
        </small>
        <b>Ativas Atrasadas</b><br>
            <a href="index.php?action=ss&serieid=31">Série Três</a><br><b>Finalizadas Atrasadas</b><br>
            <a href="index.php?action=ss&serieid=41">Série Quatro</a><br><b>Fim da página</b>
        """
        grades = etl.extrair_todas_grades(FakeSession(FakeResponse(html)))

        self.assertEqual(set(grades), {
            "Ativas em dia", "Finalizadas Completas",
            "Ativas Atrasadas", "Finalizadas Atrasadas",
        })
        self.assertEqual(grades["Ativas em dia"], [
            {"id": "11", "nome": "Série Um", "categoria": "Ativas em dia"}
        ])
        self.assertEqual(grades["Finalizadas Completas"][0]["id"], "21")
        self.assertEqual(grades["Ativas Atrasadas"][0]["id"], "31")
        self.assertEqual(grades["Finalizadas Atrasadas"][0]["id"], "41")

    def test_http_failure_is_propagated(self):
        with self.assertRaises(RuntimeError):
            etl.extrair_todas_grades(FakeSession(FakeResponse(status_code=500)))


class TestParsingSeries(unittest.TestCase):
    def test_extracts_imdb_id_and_darkchecked_episode(self):
        html = """
        <a href="https://www.imdb.com/title/tt1234567/">IMDb</a>
        <div class="panel-seasons">
          <div class="rate" data-season="1">
            <b>1x05 - Episódio cinco</b>
            <img src="darkchecked.png">
          </div>
          <div class="rate" data-season="2">
            <b>2x02 - Outro episódio</b>
            <img src="lightchecked.png">
          </div>
        </div>
        """
        imdb_id, episodes = etl.extrair_dados_serie_bds(
            FakeSession(FakeResponse(html)), "123", True
        )
        self.assertEqual(imdb_id, "tt1234567")
        self.assertEqual(episodes, {(1, 5)})

    def test_invalid_season_does_not_abort_series_parsing(self):
        html = """
        <a href="https://www.imdb.com/title/tt1234567/">IMDb</a>
        <div class="panel-seasons">
          <div class="rate" data-season="X">
            <b>1x01 - Episódio</b>
            <img src="darkchecked.png">
          </div>
        </div>
        """
        imdb_id, episodes = etl.extrair_dados_serie_bds(
            FakeSession(FakeResponse(html)), "123", True
        )
        self.assertEqual(imdb_id, "tt1234567")
        self.assertEqual(episodes, set())

    def test_does_not_audit_when_disabled(self):
        html = """
        <a href="https://www.imdb.com/title/tt1234567/">IMDb</a>
        <div class="panel-seasons">
          <div class="rate" data-season="1">
            <b>1x05 - Episódio cinco</b>
            <img src="darkchecked.png">
          </div>
        </div>
        """
        imdb_id, episodes = etl.extrair_dados_serie_bds(
            FakeSession(FakeResponse(html)), "123", False
        )
        self.assertEqual(imdb_id, "tt1234567")
        self.assertEqual(episodes, set())


class TestImdbDatasets(unittest.TestCase):
    def test_indexes_ratings_and_episode_relationships_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ratings = root / "ratings.tsv.gz"
            episodes = root / "episodes.tsv.gz"
            with gzip.open(ratings, "wt", encoding="utf-8") as stream:
                stream.write("tconst\taverageRating\tnumVotes\n")
                stream.write("tt0000001\t0\t10\n")
                stream.write("tt0000002\t8.5\t20\n")
                stream.write("invalid\n")
            with gzip.open(episodes, "wt", encoding="utf-8") as stream:
                stream.write("tconst\tparentTconst\tseasonNumber\tepisodeNumber\n")
                stream.write("tt0000003\ttt0000002\t1\t5\n")
                stream.write("tt0000004\ttt0000002\t\\N\t1\n")
                stream.write("tt0000005\ttt0000002\t1\t0\n")

            with patch.object(etl, "RATINGS_FILE", ratings), patch.object(
                etl, "EPISODES_FILE", episodes
            ):
                ratings_index, structure = etl.carregar_datasets_imdb()

            self.assertEqual(ratings_index["tt0000001"]["rating"], 0.0)
            self.assertEqual(ratings_index["tt0000002"]["votes"], 20)
            self.assertEqual(structure["tt0000002"][1][5], "tt0000003")
            self.assertEqual(structure["tt0000002"], {1: {5: "tt0000003"}})


if __name__ == "__main__":
    unittest.main()
