#!/usr/bin/env Rscript

# Build the first species taxonomy crosswalk from local MRNF species codes and
# the versioned VASCAN Darwin Core Archive. An automatic exact match is kept
# distinct from the documented review of the four teaching species.

required_packages <- c(
  "cli", "data.table", "digest", "dplyr", "fs", "readr", "stringi", "stringr",
  "tibble", "tidyr"
)

source(file.path("R", "helpers_io.R"))
assert_packages(required_packages)
ensure_project_dirs(".")

suppressPackageStartupMessages({
  library(cli)
  library(data.table)
  library(digest)
  library(dplyr)
  library(fs)
  library(readr)
  library(stringi)
  library(stringr)
  library(tibble)
  library(tidyr)
})

vascan_version <- "37.16"
vascan_zip <- file.path("data_raw", "VASCAN", "vascan_dwca_v37.16.zip")
vascan_dir <- file.path("data_intermediate", "VASCAN")
required_vascan_files <- c(
  "taxon.txt", "vernacularname.txt", "distribution.txt", "description.txt"
)

if (!file.exists(vascan_zip)) {
  stop(
    "Archive VASCAN absente : ", vascan_zip,
    ". La télécharger depuis le manifeste avant de construire le crosswalk.",
    call. = FALSE
  )
}

dir_create(vascan_dir, recurse = TRUE)
missing_vascan_files <- required_vascan_files[
  !file.exists(file.path(vascan_dir, required_vascan_files))
]
if (length(missing_vascan_files) > 0L) {
  utils::unzip(
    vascan_zip,
    files = missing_vascan_files,
    exdir = vascan_dir,
    overwrite = TRUE
  )
}

read_dwc_table <- function(path) {
  data.table::fread(
    path,
    sep = "\t",
    quote = "",
    na.strings = c("", "NA"),
    encoding = "UTF-8",
    showProgress = FALSE
  ) |>
    as_tibble()
}

normalize_name <- function(x) {
  x |>
    str_replace_all(" *[(][^)]*[)]", "") |>
    str_replace_all("[’`´]", "'") |>
    str_replace_all("[[:punct:]]+", " ") |>
    str_squish() |>
    str_to_lower(locale = "fr") |>
    stringi::stri_trans_general("Latin-ASCII")
}

taxonomy_path <- file.path("references", "species_taxonomy_crosswalk.csv")
species_path <- file.path("references", "mrnf_species_codes.csv")

species_codes <- read_csv(species_path, show_col_types = FALSE) |>
  transmute(
    species_code = str_to_upper(str_trim(as.character(species_code))),
    species_fr_source = str_squish(as.character(species_fr_source)),
    species_source_key = normalize_name(species_fr_source)
  ) |>
  filter(!is.na(species_code), species_code != "") |>
  distinct(species_code, .keep_all = TRUE)

taxon <- read_dwc_table(file.path(vascan_dir, "taxon.txt"))
vernacular <- read_dwc_table(file.path(vascan_dir, "vernacularname.txt"))
distribution <- read_dwc_table(file.path(vascan_dir, "distribution.txt"))
description <- read_dwc_table(file.path(vascan_dir, "description.txt"))

accepted_species <- taxon |>
  filter(taxonRank == "species", taxonomicStatus == "accepted") |>
  mutate(
    id = as.character(id),
    accepted_species_id = id,
    accepted_binomial = str_squish(paste(genus, specificEpithet)),
    accepted_name_with_authorship = scientificName
  ) |>
  select(
    accepted_species_id, accepted_binomial, accepted_name_with_authorship,
    genus, family, references
  )

habit_lookup <- description |>
  filter(type == "habit") |>
  mutate(id = as.character(id)) |>
  group_by(accepted_species_id = id) |>
  summarise(
    habit = paste(sort(unique(description)), collapse = ";"),
    .groups = "drop"
  )

quebec_distribution <- distribution |>
  filter(locationID == "ISO3166-2:CA-QC" | locality == "Quebec") |>
  mutate(id = as.character(id)) |>
  group_by(accepted_species_id = id) |>
  summarise(
    quebec_status = paste(
      sort(unique(str_squish(paste(occurrenceStatus, establishmentMeans)))),
      collapse = "; "
    ),
    .groups = "drop"
  )

species_meta <- accepted_species |>
  left_join(habit_lookup, by = "accepted_species_id") |>
  left_join(quebec_distribution, by = "accepted_species_id") |>
  mutate(
    species_group = case_when(
      family %in% c("Cupressaceae", "Pinaceae", "Taxaceae") ~ "conifer",
      str_detect(dplyr::coalesce(habit, ""), regex("\\btree\\b", TRUE)) ~
        "deciduous",
      TRUE ~ "other"
    ),
    is_conifer = species_group == "conifer",
    is_deciduous = species_group == "deciduous"
  )

unique_by_key <- function(data, key_col) {
  data |>
    group_by(.data[[key_col]]) |>
    summarise(
      candidate_taxon_ids = paste(
        sort(unique(accepted_species_id)),
        collapse = ";"
      ),
      n_taxa = n_distinct(accepted_species_id),
      accepted_species_id = if_else(n_taxa == 1L, candidate_taxon_ids, NA_character_),
      ambiguous_taxon_ids = if_else(n_taxa > 1L, candidate_taxon_ids, NA_character_),
      .groups = "drop"
    )
}

vernacular_keys <- vernacular |>
  filter(language == "FR") |>
  mutate(
    id = as.character(id),
    match_key = normalize_name(vernacularName)
  ) |>
  inner_join(
    species_meta |> select(accepted_species_id),
    by = c("id" = "accepted_species_id")
  ) |>
  transmute(match_key, accepted_species_id = id) |>
  unique_by_key("match_key")

taxon_scientific_keys <- taxon |>
  filter(taxonRank == "species") |>
  mutate(
    accepted_species_id = as.character(acceptedNameUsageID),
    accepted_species_id = if_else(
      is.na(accepted_species_id) | accepted_species_id == "",
      as.character(id),
      accepted_species_id
    ),
    match_key = normalize_name(str_squish(paste(genus, specificEpithet)))
  ) |>
  inner_join(
    species_meta |> select(accepted_species_id),
    by = "accepted_species_id"
  ) |>
  select(match_key, accepted_species_id) |>
  unique_by_key("match_key")

source_review <- species_codes |>
  left_join(
    taxon_scientific_keys |>
      rename(
        scientific_match_id = accepted_species_id,
        scientific_n_taxa = n_taxa,
        scientific_ambiguous_taxon_ids = ambiguous_taxon_ids
      ),
    by = c("species_source_key" = "match_key")
  ) |>
  left_join(
    vernacular_keys |>
      rename(
        vernacular_match_id = accepted_species_id,
        vernacular_n_taxa = n_taxa,
        vernacular_ambiguous_taxon_ids = ambiguous_taxon_ids
      ),
    by = c("species_source_key" = "match_key")
  ) |>
  mutate(
    accepted_species_id = coalesce(scientific_match_id, vernacular_match_id),
    taxonomy_match_method = case_when(
      !is.na(scientific_match_id) ~ "exact_scientific_name_vascan",
      !is.na(vernacular_match_id) ~ "exact_vernacular_vascan",
      !is.na(scientific_ambiguous_taxon_ids) |
        !is.na(vernacular_ambiguous_taxon_ids) ~ "ambiguous_reference",
      TRUE ~ "unmatched_reference"
    ),
    taxonomy_match_status = if_else(
      !is.na(accepted_species_id),
      "exact_code",
      "needs_review"
    ),
    notes = case_when(
      !is.na(accepted_species_id) ~
        "Automatic unique species-rank match in VASCAN; no documentary review asserted.",
      !is.na(scientific_ambiguous_taxon_ids) |
        !is.na(vernacular_ambiguous_taxon_ids) ~ paste(
          "Ambiguous exact VASCAN match; candidate taxon ids:",
          coalesce(scientific_ambiguous_taxon_ids, vernacular_ambiguous_taxon_ids)
        ),
      str_detect(
        species_source_key,
        regex(
          "absence|inconnu|indifferenciee|non commerciale|feuillu|resineux|sp$|spp$",
          TRUE
        )
      ) ~ "Non-specific MRNF label; human confirmation required.",
      TRUE ~
        "No unique species-rank exact match in VASCAN; human confirmation required."
    )
  ) |>
  left_join(species_meta, by = "accepted_species_id")

crosswalk <- source_review |>
  transmute(
    species_code,
    species_fr_source,
    scientific_name_accepted = accepted_binomial,
    genus,
    family,
    vascan_taxon_id = accepted_species_id,
    quebec_status,
    habit,
    species_group,
    is_conifer,
    is_deciduous,
    taxonomy_match_method,
    taxonomy_match_status,
    taxonomy_source_version = paste0(
      "VASCAN ", vascan_version,
      "; archive_sha256=", sha256_file(vascan_zip)
    ),
    reviewer = NA_character_,
    review_date = NA_character_,
    notes
  ) |>
  arrange(species_code)

review <- read_csv("references/pedagogical_taxonomy_review.csv",
                   col_types = cols(.default = col_character()))
stopifnot(!anyDuplicated(review$species_code))
for (i in seq_len(nrow(review))) {
  j <- match(review$species_code[i], crosswalk$species_code)
  stopifnot(!is.na(j),
            crosswalk$scientific_name_accepted[j] == review$species_latin[i],
            crosswalk$genus[j] == review$genus[i],
            crosswalk$family[j] == review$family[i],
            crosswalk$vascan_taxon_id[j] == review$vascan_taxon_id[i])
  crosswalk$taxonomy_match_status[j] <- "reviewed"
  crosswalk$reviewer[j] <- "documentary_crosscheck"
  crosswalk$review_date[j] <- review$review_date[i]
  crosswalk$notes[j] <- paste("MRNF label, VASCAN accepted name, genus and family checked against", review$source_url[i])
}

readr::write_csv(crosswalk, taxonomy_path, na = "")

review_counts <- crosswalk |>
  count(taxonomy_match_status, name = "n")
needs_review <- crosswalk |>
  filter(taxonomy_match_status == "needs_review") |>
  pull(species_code)

cli_inform(c(
  "v" = paste0("Crosswalk écrit : ", taxonomy_path),
  "i" = paste(
    paste(review_counts$taxonomy_match_status, review_counts$n, sep = "="),
    collapse = "; "
  ),
  "!" = paste0(
    "Codes à confirmer humainement : ",
    if (length(needs_review) == 0L) "aucun" else paste(needs_review, collapse = ", ")
  )
))
