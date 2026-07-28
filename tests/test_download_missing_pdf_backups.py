from pathlib import Path


def test_repo_relative_accepts_relative_output_path(monkeypatch, tmp_path: Path):
    from scripts.download_missing_pdf_backups import repo_relative

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    assert repo_relative(Path("artifacts/run/manifest.csv"), repo) == Path(
        "artifacts/run/manifest.csv"
    )


def test_wayback_replay_url_preserves_the_original_url():
    from scripts.download_missing_pdf_backups import wayback_replay_url

    source = "https://example.org/manuals/Safety%20Manual.pdf"
    assert wayback_replay_url(source) == (
        "https://web.archive.org/web/2id_/"
        "https://example.org/manuals/Safety%20Manual.pdf"
    )
