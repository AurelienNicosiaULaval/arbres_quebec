#!/usr/bin/env Rscript

# Collecte reproductible des sources botaniques et forestières québécoises.
# Les fichiers bruts sont conservés tels quels. Aucun fichier existant n'est
# remplacé. Les grosses archives ne sont téléchargées que sur autorisation.

required_packages <- c(
  "cli", "curl", "digest", "dplyr", "fs", "purrr", "readr",
  "stringr", "tibble"
)

source(file.path("R", "helpers_io.R"))
assert_packages(required_packages)
ensure_project_dirs(".")

suppressPackageStartupMessages({
  library(cli)
  library(dplyr)
  library(fs)
  library(purrr)
  library(readr)
  library(stringr)
  library(tibble)
})

download_large <- as_bool_env("DOWNLOAD_LARGE_FILES", FALSE)
collect_sources <- Sys.getenv("COLLECT_SOURCES", unset = "PET5,PEP") |>
  str_split(",", simplify = FALSE) |>
  unlist() |>
  str_trim() |>
  toupper() |>
  unique()

manifest_path <- file.path("references", "source_manifest.csv")
if (!file.exists(manifest_path)) {
  stop("Manifeste introuvable : ", manifest_path, call. = FALSE)
}

manifest <- read_csv(manifest_path, show_col_types = FALSE) |>
  mutate(
    source_family = str_extract(source_id, "^[A-Z0-9]+"),
    large_file = as.logical(large_file),
    download_by_default = as.logical(download_by_default),
    selected_family = source_family %in% collect_sources,
    should_download = selected_family &
      (download_by_default | (large_file & download_large)),
    manual_reason = case_when(
      !selected_family ~ "source_family_not_selected",
      large_file & !download_large ~ "large_download_disabled",
      !download_by_default ~ "optional_resource_not_selected",
      TRUE ~ NA_character_
    )
  )

if (!any(manifest$selected_family)) {
  stop(
    "Aucune famille de source sélectionnée. Valeurs reçues : ",
    paste(collect_sources, collapse = ", "),
    call. = FALSE
  )
}

safe_download <- function(source_id, url, local_relpath) {
  destination <- path_abs(local_relpath)
  dir_create(path_dir(destination), recurse = TRUE)
  started <- Sys.time()

  if (file.exists(destination)) {
    cli_warn(c(
      "!" = "Fichier brut déjà présent; il ne sera pas remplacé.",
      "i" = destination
    ))
    return(tibble(
      source_id = source_id,
      collection_started_utc = format(started, tz = "UTC", usetz = TRUE),
      collection_finished_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
      status = "exists_not_overwritten",
      url = url,
      local_path = destination,
      size_bytes = file.info(destination)$size,
      sha256 = sha256_file(destination),
      message = "Existing raw file preserved"
    ))
  }

  temporary <- paste0(destination, ".part")
  if (file.exists(temporary)) {
    stop(
      "Un téléchargement incomplet existe : ", temporary,
      ". Le supprimer manuellement après vérification.", call. = FALSE
    )
  }

  result <- tryCatch({
    cli_inform(c("i" = paste("Téléchargement de", source_id)))
    downloaded <- tryCatch({
      curl::curl_download(url, temporary, quiet = FALSE, mode = "wb")
      TRUE
    }, error = function(e) {
      cli_warn(c(
        "!" = paste0("Téléchargement R curl échoué pour ", source_id, "."),
        "i" = paste0("Nouvel essai avec le curl système : ", conditionMessage(e))
      ))
      FALSE
    })
    if (!downloaded) {
      status <- utils::download.file(
        url,
        temporary,
        mode = "wb",
        method = "curl",
        quiet = FALSE
      )
      if (!identical(status, 0L)) {
        stop("Le téléchargement avec curl système a échoué avec le statut ", status, ".")
      }
    }
    if (!file.exists(temporary) || file.info(temporary)$size <= 0) {
      stop("Le fichier temporaire est absent ou vide.")
    }
    if (!file.rename(temporary, destination)) {
      stop("Impossible de déplacer le fichier temporaire vers sa destination.")
    }
    tibble(
      source_id = source_id,
      collection_started_utc = format(started, tz = "UTC", usetz = TRUE),
      collection_finished_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
      status = "downloaded",
      url = url,
      local_path = destination,
      size_bytes = file.info(destination)$size,
      sha256 = sha256_file(destination),
      message = NA_character_
    )
  }, error = function(e) {
    if (file.exists(temporary)) unlink(temporary)
    tibble(
      source_id = source_id,
      collection_started_utc = format(started, tz = "UTC", usetz = TRUE),
      collection_finished_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
      status = "download_failed",
      url = url,
      local_path = destination,
      size_bytes = NA_real_,
      sha256 = NA_character_,
      message = conditionMessage(e)
    )
  })

  result
}

selected <- manifest |>
  filter(should_download)

logs_download <- if (nrow(selected) > 0L) {
  pmap_dfr(
    selected[, c("source_id", "url", "local_relpath")],
    safe_download
  )
} else {
  tibble(
    source_id = character(), collection_started_utc = character(),
    collection_finished_utc = character(), status = character(), url = character(),
    local_path = character(), size_bytes = double(), sha256 = character(),
    message = character()
  )
}

skipped <- manifest |>
  filter(!should_download) |>
  transmute(
    source_id,
    collection_started_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
    collection_finished_utc = collection_started_utc,
    status = "manual_or_optional",
    url,
    local_path = path_abs(local_relpath),
    size_bytes = NA_real_,
    sha256 = NA_character_,
    message = manual_reason
  )

run_log <- bind_rows(logs_download, skipped) |>
  mutate(
    manifest_sha256 = sha256_file(manifest_path),
    collect_sources = paste(collect_sources, collapse = ","),
    download_large_files = download_large
  )

log_path <- file.path("logs", "collection_log.csv")
readr::write_csv(
  run_log,
  log_path,
  append = file.exists(log_path),
  col_names = !file.exists(log_path),
  na = ""
)

stamp <- format(Sys.time(), tz = "UTC", format = "%Y%m%dT%H%M%SZ")
manual_path <- file.path("logs", paste0("manual_download_instructions_", stamp, ".md"))
manual_rows <- manifest |>
  filter(!should_download)

manual_lines <- c(
  "# Ressources non téléchargées automatiquement",
  "",
  paste0("Collecte UTC : ", format(Sys.time(), tz = "UTC", usetz = TRUE)),
  paste0("Familles demandées : ", paste(collect_sources, collapse = ", ")),
  paste0("Gros téléchargements autorisés : ", download_large),
  "",
  "Déposer tout fichier téléchargé manuellement à l'emplacement indiqué sans le modifier.",
  "Relancer ensuite ce script : il conservera le fichier et calculera son empreinte SHA-256.",
  ""
)

if (nrow(manual_rows) == 0L) {
  manual_lines <- c(manual_lines, "Aucune ressource à télécharger manuellement.")
} else {
  for (i in seq_len(nrow(manual_rows))) {
    row <- manual_rows[i, ]
    manual_lines <- c(
      manual_lines,
      paste0("## ", row$source_id),
      "",
      paste0("- Motif : `", row$manual_reason, "`"),
      paste0("- URL : ", row$url),
      paste0("- Destination : `", row$local_relpath, "`"),
      paste0("- Licence annoncée : ", row$license),
      ""
    )
  }
}
writeLines(manual_lines, manual_path, useBytes = TRUE)

failed <- run_log |> filter(status == "download_failed")
cli_inform(c(
  "v" = paste0("Journal écrit : ", log_path),
  "i" = paste0("Instructions manuelles : ", manual_path),
  "i" = paste0("Téléchargements réussis ou déjà présents : ",
                 sum(run_log$status %in% c("downloaded", "exists_not_overwritten"))),
  "i" = paste0("Ressources manuelles ou optionnelles : ",
                 sum(run_log$status == "manual_or_optional"))
))

if (nrow(failed) > 0L) {
  stop(
    "Au moins un téléchargement a échoué. Consulter ", log_path,
    " et utiliser les instructions manuelles.", call. = FALSE
  )
}
