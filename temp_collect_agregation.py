#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import time
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 Chrome/126 Safari/537.36 "
    "Academic-public-resource-archiver/1.0"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/pdf,application/octet-stream,*/*;q=0.7",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
}
DOWNLOAD_EXTENSIONS = {
    ".pdf", ".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".bz2", ".xz",
    ".ipynb", ".py", ".sage", ".sagews", ".tex", ".sty", ".cls",
    ".r", ".rmd", ".qmd", ".jl", ".m", ".nb", ".mlx",
    ".doc", ".docx", ".odt", ".ppt", ".pptx", ".odp",
    ".txt", ".md", ".csv",
}
SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".css", ".js", ".map", ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".avi", ".mov", ".webm", ".ogg",
}
RELEVANT = re.compile(
    r"agreg|agrég|le[cç]on|develop|dévelop|cours|poly|fascicule|td\b|tp\b|"
    r"exerc|corrig|oral|option|model|modél|math|algeb|algèb|analys|probab|"
    r"geometr|géom|topolog|groupe|anneau|corps|galois|matric|fourier|"
    r"integr|intégr|equation|équation|edo|edp|numer|numér|optim|convex|"
    r"stoch|markov|sage|python|calcul|mesure|represent|représent|biline|"
    r"forme|sujet|rapport|jury|admiss|concours|mod\d{2}|mg\d{2}|ap\d{2}",
    re.I,
)
EXCLUDE = re.compile(
    r"login|logout|connexion|inscription|compte|panier|checkout|facebook|twitter|linkedin|"
    r"instagram|youtube|mailto:|javascript:|calendar|ical|print=|action=edit|historique|"
    r"spécial:|special:|discussion:|utilisateur:|user:|favicon|rss|atom",
    re.I,
)


@dataclass(frozen=True)
class Seed:
    label: str
    url: str
    max_depth: int = 3
    max_pages: int = 700
    crawl_all_same_host: bool = False


LOTS: dict[str, list[Seed]] = {
    "officiel": [
        Seed("Jury officiel - archives", "https://agreg.org/index.php?id=archives", 3, 700, True),
        Seed("Jury officiel - modelisation", "https://agreg.org/index.php?id=modelisation", 3, 700, True),
        Seed("Ancien site du jury - sujets", "https://old.agreg.org/sujets.html", 3, 700, True),
        Seed("Ancien site du jury - accueil", "https://old.agreg.org/", 3, 700, True),
        Seed("Ministere - programmes 2027", "https://www.devenirenseignant.gouv.fr/les-programmes-des-concours-d-enseignants-du-second-degre-de-la-session-2027-1662", 2, 150, False),
        Seed("Ministere - sujets 2026", "https://www.devenirenseignant.gouv.fr/sujets-et-rapports-des-jurys-concours-de-l-agregation-de-2026-1659", 2, 150, False),
    ],
    "universites": [
        Seed("ENS Rennes - Le Borgne", "https://perso.ens-rennes.fr/math/people/jeremy.leborgne/agreg.html", 3, 500, False),
        Seed("Sorbonne - Option B", "https://mdupuy.pages.math.cnrs.fr/agreg-option-B-website/", 4, 1200, True),
        Seed("Nantes - preparation", "https://www.math.sciences.univ-nantes.fr/~agreg/", 4, 1200, True),
        Seed("Nantes - geometrie projective", "https://www.math.sciences.univ-nantes.fr/~franjou/Agregation.html", 3, 400, False),
        Seed("Bordeaux - Fresnel Matignon", "https://www.math.u-bordeaux.fr/~mmatigno/agregation.html", 4, 1200, False),
        Seed("Bordeaux - Brinon", "https://www.math.u-bordeaux.fr/~obrinon/enseignement.htm", 3, 700, False),
        Seed("Bordeaux - Option C Belabas", "https://www.math.u-bordeaux.fr/~kbelabas/teach/Agreg/", 5, 1600, True),
        Seed("Toulouse - portail", "https://agreg.math.univ-toulouse.fr/", 4, 1000, True),
        Seed("Toulouse - Boyer option B", "https://www.math.univ-toulouse.fr/~fboyer/enseignements/cours_agreg", 4, 1000, False),
        Seed("Toulouse - Sablik", "https://www.math.univ-toulouse.fr/~msablik/enseignement.html", 3, 500, False),
        Seed("Lyon 1 - wiki", "https://math.univ-lyon1.fr/wikis/agregation/doku.php", 4, 1200, True),
        Seed("Lyon 1 - ecrit MG", "https://math.univ-lyon1.fr/wikis/agregation/doku.php?id=ecrit-mg", 4, 1200, True),
        Seed("Paris Saclay - probabilites", "https://www.imo.universite-paris-saclay.fr/~ruette/agreg/", 4, 900, True),
        Seed("Tours - agregation", "https://math.univ-tours.fr/agreg", 3, 500, False),
        Seed("Tours - bibliotheque", "https://math.univ-tours.fr/bibliotheque", 3, 500, False),
        Seed("Rouen - Mourragui", "https://lmrs.univ-rouen.fr/fr/persopage/enseignement-mustapha-mourragui", 3, 500, False),
        Seed("Rouen - bibliotheque", "https://lmrs.univ-rouen.fr/fr/content/bibliotheque", 3, 500, False),
        Seed("IREM Lorraine - brochures", "https://irem.univ-lorraine.fr/liste-des-brochures-editees-par-lirem-de-lorraine/", 3, 700, False),
    ],
    "minerve": [
        Seed("Minerve ENS Rennes", "https://minerve.ens-rennes.fr/index.php/Accueil", 5, 5000, True),
        Seed("Jonathan Badin 2025", "https://perso.eleves.ens-rennes.fr/people/jonathan.badin/agreg.html", 4, 800, True),
        Seed("Kylian Prigent 2025", "https://perso.eleves.ens-rennes.fr/people/kylian.prigent/", 4, 800, False),
        Seed("Matthias Hostein 2024", "https://perso.eleves.ens-rennes.fr/people/matthias.hostein/agreg.html", 4, 800, True),
        Seed("Thomas Courant 2024", "https://perso.eleves.ens-rennes.fr/people/thomas.courant/Agr%C3%A9gation.html", 4, 800, True),
        Seed("Matteo Miannay 2024", "https://perso.eleves.ens-rennes.fr/people/matteo.miannay/agregation.html", 4, 800, True),
        Seed("Lucas Toury 2024", "https://perso.eleves.ens-rennes.fr/people/lucas.toury/agreg.html", 4, 800, True),
        Seed("Gael Druez 2024", "https://perso.eleves.ens-rennes.fr/people/gael.druez/agreg.html", 4, 800, True),
        Seed("Eliot Hecky 2023", "https://perso.eleves.ens-rennes.fr/people/eliot.hecky/agreg.html", 4, 800, True),
        Seed("Laurent Montaigu 2023", "https://perso.eleves.ens-rennes.fr/people/laurent.montaigu/agreg.html", 4, 800, True),
        Seed("Sacha Quayle 2023", "https://perso.eleves.ens-rennes.fr/people/sacha.quayle/Agr%C3%A9gation.html", 4, 800, True),
        Seed("Jeremy Bettinger 2023", "https://perso.eleves.ens-rennes.fr/people/jeremy.bettinger/agreg.html", 4, 800, True),
        Seed("Florian Bouguet 2012", "https://florian.bouguet.free.fr", 4, 800, False),
        Seed("Arnaud Girand 2012", "https://math.webgirand.eu", 4, 800, False),
    ],
    "agreg_maths": [
        Seed("Agreg-maths - accueil", "https://agreg-maths.fr/", 5, 12000, True),
        Seed("Agreg-maths - lecons 2026", "https://agreg-maths.fr/lecons/annee/2026", 5, 12000, True),
    ],
}


class PoliteSession:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.last_request: dict[str, float] = defaultdict(float)

    def get(self, url: str, **kwargs):
        host = urlparse(url).netloc.lower()
        wait = 0.20 - (time.monotonic() - self.last_request[host])
        if wait > 0:
            time.sleep(wait)
        response = self.session.get(url, **kwargs)
        self.last_request[host] = time.monotonic()
        return response


def strip_fragment(url: str) -> str:
    p = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if k.lower() not in {"utm_source", "utm_medium", "utm_campaign", "fbclid", "gclid"}]
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path, p.params, urlencode(query), ""))


def clean_name(text: str, fallback: str = "document") -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", " - ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-_")
    return (text or fallback)[:180]


def ext_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.endswith(".tar.gz"):
        return ".tar.gz"
    return Path(path).suffix.lower()


def is_download_candidate(url: str) -> bool:
    ext = ext_from_url(url)
    return ext in DOWNLOAD_EXTENSIONS


def is_skip_asset(url: str) -> bool:
    return ext_from_url(url) in SKIP_EXTENSIONS


def is_html_type(content_type: str) -> bool:
    content_type = (content_type or "").lower()
    return "text/html" in content_type or "application/xhtml" in content_type


def content_disposition_name(header: str | None) -> str | None:
    if not header:
        return None
    match = re.search(r"filename\*=UTF-8''([^;]+)", header, re.I)
    if match:
        from urllib.parse import unquote
        return unquote(match.group(1))
    match = re.search(r'filename="?([^";]+)', header, re.I)
    return match.group(1).strip() if match else None


def should_follow_html(seed: Seed, current_url: str, target_url: str, anchor_text: str, depth: int) -> bool:
    if depth > seed.max_depth:
        return False
    p_seed = urlparse(seed.url)
    p_target = urlparse(target_url)
    if p_target.scheme not in {"http", "https"}:
        return False
    if EXCLUDE.search(target_url):
        return False
    same_host = p_target.netloc.lower() == p_seed.netloc.lower()
    if not same_host:
        return False
    if seed.crawl_all_same_host:
        return True
    seed_dir = str(Path(p_seed.path).parent).rstrip("/")
    target_path = p_target.path
    close_path = bool(seed_dir and seed_dir != "." and target_path.startswith(seed_dir))
    return close_path or bool(RELEVANT.search(target_url + " " + anchor_text))


def likely_relevant_file(url: str, anchor_text: str, source_url: str) -> bool:
    if EXCLUDE.search(url):
        return False
    ext = ext_from_url(url)
    if ext == ".pdf":
        # Direct PDF links from a relevant source page are retained, even when the filename is opaque.
        return True
    return bool(RELEVANT.search(url + " " + anchor_text + " " + source_url))


def validate_pdf(data: bytes) -> tuple[int, str]:
    pos = data.find(b"%PDF-")
    if pos < 0 or pos > 4096:
        raise ValueError("signature PDF absente")
    data2 = data[pos:]
    reader = PdfReader(io.BytesIO(data2), strict=False)
    pages = len(reader.pages)
    if pages < 1:
        raise ValueError("PDF sans page")
    title = ""
    try:
        title = str((reader.metadata or {}).get("/Title") or "").strip()
    except Exception:
        pass
    return pages, title


def unique_destination(base: Path, proposed: Path, digest: str) -> Path:
    destination = base / proposed
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        return destination
    return destination.with_name(f"{destination.stem} [{digest[:8]}]{destination.suffix}")


def archive_name_from_url(url: str, response: requests.Response, pdf_title: str = "") -> str:
    cd_name = content_disposition_name(response.headers.get("content-disposition"))
    raw = cd_name or Path(urlparse(response.url).path).name or Path(urlparse(url).path).name
    raw = clean_name(raw, "document")
    content_type = response.headers.get("content-type", "").lower()
    ext = ext_from_url(raw)
    if "application/pdf" in content_type or raw.lower().endswith(".pdf"):
        if pdf_title and (not raw or raw.lower() in {"document.pdf", "download.pdf", "fichier.pdf"}):
            raw = clean_name(pdf_title) + ".pdf"
        elif not raw.lower().endswith(".pdf"):
            raw += ".pdf"
    return raw


def crawl_seed(seed: Seed, lot_root: Path, session: PoliteSession, global_hashes: dict[str, str], records: list[dict]) -> None:
    queue = deque([(strip_fragment(seed.url), 0, "")])
    visited: set[str] = set()
    pages_seen = 0
    site_dir = lot_root / clean_name(seed.label)
    site_dir.mkdir(parents=True, exist_ok=True)

    while queue and pages_seen < seed.max_pages:
        url, depth, source_page = queue.popleft()
        url = strip_fragment(url)
        if url in visited or is_skip_asset(url):
            continue
        visited.add(url)
        try:
            response = session.get(url, timeout=(12, 90), allow_redirects=True, stream=True)
            status = response.status_code
            final_url = strip_fragment(response.url)
            content_type = response.headers.get("content-type", "").lower()
            if status >= 400:
                records.append({
                    "lot": lot_root.name, "source": seed.label, "source_page": source_page,
                    "url": url, "final_url": final_url, "status": f"http_{status}",
                    "filename": "", "bytes": 0, "pages": 0, "sha256": "", "duplicate_of": "",
                    "detail": response.reason or "",
                })
                response.close()
                continue

            # Read with a hard ceiling of 120 MiB per file.
            chunks: list[bytes] = []
            total = 0
            limit = 120 * 1024 * 1024
            for chunk in response.iter_content(256 * 1024):
                if not chunk:
                    continue
                chunks.append(chunk)
                total += len(chunk)
                if total > limit:
                    raise ValueError("fichier > 120 Mio")
                if is_html_type(content_type) and total > 12 * 1024 * 1024:
                    raise ValueError("page HTML anormalement volumineuse")
            data = b"".join(chunks)
            response.close()

            looks_pdf = data.find(b"%PDF-") in range(0, 4097)
            downloadable = is_download_candidate(final_url) or is_download_candidate(url) or looks_pdf
            if downloadable and not is_html_type(content_type):
                pages = 0
                pdf_title = ""
                if looks_pdf or "application/pdf" in content_type:
                    pages, pdf_title = validate_pdf(data)
                digest = hashlib.sha256(data).hexdigest()
                filename = archive_name_from_url(url, response, pdf_title)
                if digest in global_hashes:
                    records.append({
                        "lot": lot_root.name, "source": seed.label, "source_page": source_page,
                        "url": url, "final_url": final_url, "status": "duplicate",
                        "filename": filename, "bytes": len(data), "pages": pages, "sha256": digest,
                        "duplicate_of": global_hashes[digest], "detail": "",
                    })
                    continue
                destination = unique_destination(site_dir, Path(filename), digest)
                destination.write_bytes(data)
                relative = str(destination.relative_to(lot_root))
                global_hashes[digest] = relative
                records.append({
                    "lot": lot_root.name, "source": seed.label, "source_page": source_page,
                    "url": url, "final_url": final_url, "status": "ok",
                    "filename": relative, "bytes": len(data), "pages": pages, "sha256": digest,
                    "duplicate_of": "", "detail": "",
                })
                continue

            if not is_html_type(content_type) and not (data.lstrip().startswith(b"<!DOCTYPE") or data.lstrip().startswith(b"<html")):
                # Some servers use generic octet-stream without an extension.
                if likely_relevant_file(url, "", source_page):
                    digest = hashlib.sha256(data).hexdigest()
                    filename = archive_name_from_url(url, response)
                    if not Path(filename).suffix:
                        filename += ".bin"
                    if digest not in global_hashes:
                        destination = unique_destination(site_dir, Path(filename), digest)
                        destination.write_bytes(data)
                        relative = str(destination.relative_to(lot_root))
                        global_hashes[digest] = relative
                        records.append({
                            "lot": lot_root.name, "source": seed.label, "source_page": source_page,
                            "url": url, "final_url": final_url, "status": "ok_non_pdf",
                            "filename": relative, "bytes": len(data), "pages": 0, "sha256": digest,
                            "duplicate_of": "", "detail": content_type,
                        })
                continue

            pages_seen += 1
            html = data.decode(response.encoding or "utf-8", errors="replace")
            soup = BeautifulSoup(html, "lxml")
            for anchor in soup.find_all("a", href=True):
                href = anchor.get("href", "").strip()
                text = " ".join(anchor.get_text(" ", strip=True).split())
                if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
                    continue
                target = strip_fragment(urljoin(final_url, href))
                if is_skip_asset(target) or EXCLUDE.search(target):
                    continue
                if is_download_candidate(target):
                    if likely_relevant_file(target, text, final_url):
                        queue.append((target, depth + 1, final_url))
                    continue
                if should_follow_html(seed, final_url, target, text, depth + 1):
                    queue.append((target, depth + 1, final_url))
        except Exception as exc:
            records.append({
                "lot": lot_root.name, "source": seed.label, "source_page": source_page,
                "url": url, "final_url": "", "status": "error", "filename": "",
                "bytes": 0, "pages": 0, "sha256": "", "duplicate_of": "",
                "detail": f"{type(exc).__name__}: {exc}",
            })


def write_manifests(root: Path, records: list[dict]) -> None:
    fields = [
        "lot", "source", "source_page", "url", "final_url", "status", "filename",
        "bytes", "pages", "sha256", "duplicate_of", "detail",
    ]
    with (root / "MANIFEST.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    (root / "MANIFEST.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = defaultdict(int)
    total_bytes = 0
    total_pages = 0
    for row in records:
        counts[row["status"]] += 1
        if row["status"].startswith("ok"):
            total_bytes += int(row["bytes"] or 0)
            total_pages += int(row["pages"] or 0)
    summary = {
        "records": len(records),
        "downloaded_files": counts["ok"] + counts["ok_non_pdf"],
        "validated_pdfs": counts["ok"],
        "duplicates": counts["duplicate"],
        "errors": counts["error"] + sum(v for k, v in counts.items() if k.startswith("http_")),
        "bytes": total_bytes,
        "pdf_pages": total_pages,
        "status_counts": dict(counts),
    }
    (root / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    readme = f"""# Agrégation externe de mathématiques — lot {root.name}\n\n"
    readme += f"- Fichiers téléchargés : {summary['downloaded_files']}\n"
    readme += f"- PDF validés : {summary['validated_pdfs']}\n"
    readme += f"- Pages PDF : {summary['pdf_pages']}\n"
    readme += f"- Doublons retirés : {summary['duplicates']}\n"
    readme += f"- Échecs consignés : {summary['errors']}\n\n"
    readme += "Tous les documents proviennent de pages publiquement accessibles. Les ressources nécessitant une connexion, les livres commerciaux et les fichiers privés ne sont pas inclus.\n"
    (root / "README.md").write_text(readme, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lot", choices=sorted(LOTS), required=True)
    args = parser.parse_args()
    output = Path(f"agregation_externe_{args.lot}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    session = PoliteSession()
    hashes: dict[str, str] = {}
    records: list[dict] = []
    for index, seed in enumerate(LOTS[args.lot], 1):
        print(f"[{index}/{len(LOTS[args.lot])}] {seed.label}: {seed.url}", flush=True)
        crawl_seed(seed, output, session, hashes, records)
        ok = sum(1 for row in records if row["status"].startswith("ok"))
        print(f"  total téléchargé: {ok}", flush=True)
    write_manifests(output, records)
    shutil.make_archive(output.name, "zip", output)
    summary = json.loads((output / "SUMMARY.json").read_text(encoding="utf-8"))
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
