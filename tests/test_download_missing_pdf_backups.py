from pathlib import Path


def test_repo_relative_accepts_relative_output_path(monkeypatch, tmp_path: Path):
    from scripts.download_missing_pdf_backups import repo_relative

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    assert repo_relative(Path("artifacts/run/manifest.csv"), repo) == Path(
        "artifacts/run/manifest.csv"
    )
