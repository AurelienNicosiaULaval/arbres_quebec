#!/usr/bin/env Rscript

# Validate the teaching dataset. --from-source additionally reads the frozen
# GeoPackage directly, independently of the cleaning joins and conversions.
library(dplyr)
library(readr)
library(tidyr)
library(digest)
library(jsonlite)

dir.create("validation", showWarnings = FALSE)
source("R/helpers_validation.R")
small_path <- "data_clean/arbres_quebec_small.csv"
small <- read_csv(small_path, col_types = cols(
  .default = col_character(), diameter_cm = col_double(), height_m = col_double(),
  age_years = col_double(), basal_area_m2 = col_double(), survey_year = col_integer(),
  small_sampling_seed = col_integer(), small_n_per_species = col_integer()
))
dictionary <- read_csv("data_clean/arbres_quebec_small_dictionary.csv",
                       col_types = cols(.default = col_character()))
review <- read_csv("references/pedagogical_taxonomy_review.csv",
                  col_types = cols(.default = col_character()))
checks <- tibble(check = character(), passed = logical(), detail = character())
check <- function(name, passed, detail = "") {
  checks <<- bind_rows(checks, tibble(check = name, passed = isTRUE(passed),
                                    detail = as.character(detail)))
}
sha <- function(path) digest(file = path, algo = "sha256", serialize = FALSE)
same <- function(x, y, tolerance = 1e-10) {
  identical(is.na(x), is.na(y)) &&
    if (is.numeric(x) && is.numeric(y)) all(abs(x - y) < tolerance, na.rm = TRUE)
    else all(as.character(x) == as.character(y), na.rm = TRUE)
}

check("csv_parsing", nrow(problems(small)) == 0)
check("200_trees", nrow(small) == 200L, nrow(small))
check("four_species_50_each", identical(sort(unique(small$species_code)),
  sort(review$species_code)) && all((small |> count(species_code))$n == 50L))
check("unique_record_ids", !anyNA(small$record_id) && !anyDuplicated(small$record_id))
check("unique_species_plot", !anyNA(small$plot_id) &&
  !anyDuplicated(small[c("species_code", "plot_id")]))
check("positive_measured_diameter_height",
  all(is.finite(small$diameter_cm) & small$diameter_cm > 0 &
      is.finite(small$height_m) & small$height_m > 0))
check("screening_thresholds", all(small$diameter_cm <= 300 & small$height_m <= 70) &&
  all(is.na(small$age_years) | between(small$age_years, 0, 500)))
check("survey_year_present", !anyNA(small$survey_year))
check("no_quality_flags", all(is.na(small$data_quality_flag)))
check("documented_taxonomy", all(small$observation_quality == "A_observed_taxonomy_reviewed"))
check("basal_area_formula", same(small$basal_area_m2, pi * (small$diameter_cm / 200)^2))
check("complete_small_dictionary", identical(dictionary$variable, names(small)) &&
  !anyDuplicated(dictionary$variable))
tax <- small |> distinct(species_code, species_latin, genus, family) |>
  left_join(review, by = "species_code", suffix = c("", "_review"))
check("taxonomy_names_and_families", nrow(tax) == 4L &&
  all(tax$species_latin == tax$species_latin_review & tax$genus == tax$genus_review &
      tax$family == tax$family_review))
check("iso_survey_date_regression", identical(
  safe_date(c("2016-08-17T00:00:00.000Z", "2024-06-21", NA_character_)),
  as.Date(c("2016-08-17", "2024-06-21", NA_character_))))

from_source <- "--from-source" %in% commandArgs(trailingOnly = TRUE)
if (from_source) {
  library(DBI)
  library(RSQLite)
  library(readxl)
  gpkg <- "data_intermediate/PET5_GPKG/PET5.gpkg"
  expected_gpkg_sha <- "a59c96d55cfea48233f6699369f9235f6fe809cc80eb75170201db7345a290da"
  actual_sha <- sha(gpkg)
  check("frozen_geopackage_sha256", actual_sha == expected_gpkg_sha)
  frozen <- read_csv("references/frozen_sources.csv", col_types = cols(.default = col_character()))
  check("frozen_dictionary_and_taxonomy_sha256", all(vapply(seq_len(nrow(frozen)),
    function(i) sha(frozen$local_path[i]) == frozen$sha256[i], logical(1))))
  con <- dbConnect(SQLite(), gpkg, flags = SQLITE_RO)
  ids <- paste(dbQuoteString(con, small$record_id), collapse = ",")
  raw <- dbGetQuery(con, paste0(
    "SELECT a.ID_ARBRE AS record_id, a.ID_PE AS plot_id, a.ESSENCE AS species_code, ",
    "a.DHP AS diameter_mm_raw, a.HAUT_ARBRE AS tree_height_dm_raw, ",
    "e.HAUT_ARBRE AS study_height_dm_raw, a.AGE AS tree_age_raw, ",
    "e.AGE AS study_age_raw, e.SOURCE_AGE AS age_source_code, ",
    "e.NIVLECTAGE AS age_reading_height_cm, p.DATE_SOND AS survey_date_raw, ",
    "e.MET_SELEC AS study_selection_method, a.ETAGE_ARB AS canopy_code_raw, ",
    "c.REG_ECO AS ecological_region_code_raw ",
    "FROM DENDRO_ARBRES a LEFT JOIN DENDRO_ARBRES_ETUDES e ON a.ID_ARBRE=e.ID_ARBRE ",
    "LEFT JOIN PLACETTE p ON a.ID_PE=p.ID_PE ",
    "LEFT JOIN CLASSI_ECO_PE c ON a.ID_PE=c.ID_PE ",
    "WHERE a.ID_ARBRE IN (", ids, ") ORDER BY a.ID_ARBRE"
  )) |> as_tibble()
  total_raw <- dbGetQuery(con, "SELECT COUNT(*) AS n FROM DENDRO_ARBRES")$n
  dbDisconnect(con)
  raw <- raw[match(small$record_id, raw$record_id), ]
  raw$source_file_sha256 <- actual_sha
  check("raw_rows_found_once", nrow(raw) == nrow(small) &&
    !anyNA(raw$record_id) && !anyDuplicated(raw$record_id))
  check("raw_record_ids", same(small$record_id, raw$record_id))
  check("raw_plot_ids", same(small$plot_id, raw$plot_id))
  check("raw_species_codes", same(small$species_code, raw$species_code))
  check("raw_diameter_conversion", same(small$diameter_cm, raw$diameter_mm_raw / 10))
  check("raw_observed_height_conversion", same(small$height_m,
    coalesce(raw$study_height_dm_raw, raw$tree_height_dm_raw) / 10))
  check("raw_age_including_missingness", same(small$age_years,
    coalesce(raw$study_age_raw, raw$tree_age_raw)))
  # Independent year extraction from the literal source timestamp.
  check("raw_survey_year", same(small$survey_year,
    as.integer(substr(raw$survey_date_raw, 1, 4))))
  code_sheet <- function(sheet) {
    x <- read_excel("data_raw/PET5/DICTIONNAIRE_PLACETTE.xlsx", sheet = sheet, skip = 2)
    label_col <- if ("Description" %in% names(x)) "Description" else "Nom"
    tibble(code = as.character(x$Code), label = trimws(as.character(x[[label_col]])))
  }
  for (spec in list(c("ETAGE", "canopy_code_raw", "canopy_stratum"),
                    c("REG_ECO", "ecological_region_code_raw", "ecological_region"),
                    c("ESSENCES", "species_code", "species_fr"))) {
    lookup <- code_sheet(spec[1])
    labels <- lookup$label[match(raw[[spec[2]]], lookup$code)]
    check(paste0("raw_codebook_", spec[1]), same(small[[spec[3]]], labels))
  }
  provenance_path <- "data_clean/arbres_quebec_small_provenance.csv"
  write_csv(raw, provenance_path, na = "")
  write_csv(code_sheet("SOURCE_AGE") |> filter(!is.na(code), grepl("^[0-9]+$", code)),
            "references/age_source_codes.csv")
  library(arrow)
  full <- read_parquet("data_clean/arbres_quebec.parquet", col_select = c(
    "record_id", "plot_id", "survey_year", "measurement_date", "species_code",
    "diameter_cm", "height_observed_m", "height_estimated_m", "height_source",
    "age_years", "species_latin", "taxonomy_match_status", "data_quality_flag"
  ))
  check("full_source_row_count", nrow(full) == total_raw, nrow(full))
  check("full_unique_keys", !anyNA(full$record_id) && !anyDuplicated(full$record_id))
  check("full_plot_ids_present", !anyNA(full$plot_id))
  check("full_survey_dates_present", !anyNA(full$survey_year) && !anyNA(full$measurement_date))
  exclusions <- read_csv("data_clean/exclusion_log.csv", col_types = cols(.default = col_character()))
  check("exclusions_account_for_every_other_tree",
    !anyDuplicated(exclusions$record_id) &&
    nrow(exclusions) + nrow(small) == nrow(full) &&
    length(intersect(exclusions$record_id, small$record_id)) == 0L &&
    setequal(c(exclusions$record_id, small$record_id), full$record_id))
  full |>
    summarise(observations = n(), plots = n_distinct(plot_id),
      species_codes = n_distinct(species_code),
      survey_year_min = min(survey_year), survey_year_max = max(survey_year),
      diameter_missing = sum(is.na(diameter_cm)),
      observed_height_missing = sum(is.na(height_observed_m)),
      estimated_heights_used = sum(height_source == "estimated", na.rm = TRUE),
      scientific_name_missing = sum(is.na(species_latin))) |>
    write_csv("validation/full_profile.csv")
  full |> count(species_code, species_latin, taxonomy_match_status, sort = TRUE) |>
    write_csv("validation/full_species_counts.csv", na = "")
  exclusions |> count(stage, exclusion_reason, sort = TRUE) |>
    write_csv("validation/exclusion_summary.csv", na = "")
  source_checks <- checks
  write_json(list(
    release = readLines("VERSION"), checked_on = as.character(Sys.Date()),
    source_sha256 = actual_sha, source_rows = total_raw,
    full_parquet_sha256 = sha("data_clean/arbres_quebec.parquet"),
    dictionary_sha256 = sha("data_clean/arbres_quebec_small_dictionary.csv"),
    taxonomy_review_sha256 = sha("references/pedagogical_taxonomy_review.csv"),
    small_sha256 = sha(small_path), provenance_sha256 = sha(provenance_path),
    checks = source_checks, all_passed = all(source_checks$passed)
  ), "validation/source_verification.json", pretty = TRUE, auto_unbox = TRUE)
}

audit <- read_json("validation/source_verification.json", simplifyVector = TRUE)
check("source_verification_passed", audit$all_passed)
check("sample_matches_source_verification", audit$small_sha256 == sha(small_path))
check("provenance_integrity", audit$provenance_sha256 ==
  sha("data_clean/arbres_quebec_small_provenance.csv"))
check("dictionary_and_review_integrity",
  audit$dictionary_sha256 == sha("data_clean/arbres_quebec_small_dictionary.csv") &&
  audit$taxonomy_review_sha256 == sha("references/pedagogical_taxonomy_review.csv"))

profile <- small |>
  group_by(species_code, species) |>
  summarise(n = n(), plots = n_distinct(plot_id),
    diameter_min_cm = min(diameter_cm), diameter_mean_cm = mean(diameter_cm),
    diameter_max_cm = max(diameter_cm), height_min_m = min(height_m),
    height_mean_m = mean(height_m), height_max_m = max(height_m),
    age_missing = sum(is.na(age_years)), survey_year_min = min(survey_year),
    survey_year_max = max(survey_year), .groups = "drop")
missingness <- tibble(variable = names(small),
                     missing = vapply(small, function(x) sum(is.na(x)), integer(1)))
write_csv(profile, "validation/sample_profile.csv", na = "")
write_csv(missingness, "validation/small_missingness.csv", na = "")
write_csv(checks, "validation/release_checks.csv", na = "")
if (from_source) writeLines(trimws(capture.output(sessionInfo()), which = "right"),
                            "validation/session_info.txt")
print(checks, n = nrow(checks))
if (!all(checks$passed)) stop("Échec de validation : voir validation/release_checks.csv")
cat("Tous les contrôles de livraison ont réussi.\n")
