#!/usr/bin/env Rscript

# Assemble the small standalone teaching archive after validation and rendering.
library(readr)
library(digest)
library(jsonlite)

version <- trimws(readLines("VERSION"))
stopifnot(length(version) == 1L, grepl("^[0-9]+[.][0-9]+[.][0-9]+$", version))
audit <- read_json("validation/source_verification.json", simplifyVector = TRUE)
sha <- function(path) digest(file = path, algo = "sha256", serialize = FALSE)
stopifnot(audit$all_passed, audit$small_sha256 == sha("data_clean/arbres_quebec_small.csv"))
stopifnot(audit$full_parquet_sha256 == sha("data_clean/arbres_quebec.parquet"),
  audit$dictionary_sha256 == sha("data_clean/arbres_quebec_small_dictionary.csv"))

top <- c("README.md", "NEWS.md", "CITATION.cff", "DATA_LICENSES.md", "LICENSE",
  "MANUAL_STEPS.md", "VERSION", "_quarto.yml", "arbres_quebec.Rproj",
  "data_dictionary.csv", "renv.lock")
code <- list.files(c("R", "scripts", "examples"), pattern = "[.]R$", full.names = TRUE)
docs <- list.files("docs", pattern = "[.](md|qmd|html)$", full.names = TRUE)
refs <- list.files("references", pattern = "[.](csv|md)$", full.names = TRUE)
data <- c("data_clean/arbres_quebec_small.csv",
  "data_clean/arbres_quebec_small_dictionary.csv",
  "data_clean/arbres_quebec_small_provenance.csv",
  "data_clean/small_sampling_manifest.csv", "data_clean/validation_summary.csv",
  "data_clean/data_dictionary.csv")
validation <- list.files("validation", pattern = "[.](csv|json|txt)$", full.names = TRUE)
files <- sort(unique(c(top, code, docs, refs, data, validation)))
required_html <- c("docs/premiers_pas.html", "docs/validation_report.html")
stopifnot(all(file.exists(files)), all(required_html %in% files))

manifest_files <- files[!grepl("[.]html$", files)]
writeLines(paste(vapply(manifest_files, sha, character(1)), manifest_files, sep = "  "),
           "checksums_repo.txt")
files <- c(files, "checksums_repo.txt")
dir.create("dist", showWarnings = FALSE)
archive <- file.path("dist", paste0("arbres_quebec-v", version, ".zip"))
if (file.exists(archive)) unlink(archive)
status <- utils::zip(archive, files = files, flags = "-q")
if (status != 0L) stop("Échec de création de l'archive")
cat("Archive pédagogique :", archive, "\n")

assets <- c(archive, "data_clean/arbres_quebec.parquet",
  "data_raw/PET5/PET5_GPKG.zip", "data_raw/PET5/DICTIONNAIRE_PLACETTE.xlsx",
  "data_raw/VASCAN/vascan_dwca_v37.16.zip",
  "docs/premiers_pas.html", "docs/validation_report.html")
stopifnot(all(file.exists(assets)))
writeLines(paste(vapply(assets, sha, character(1)), basename(assets), sep = "  "),
           "dist/SHA256SUMS.txt")
cat("Empreintes des fichiers de la release : dist/SHA256SUMS.txt\n")
