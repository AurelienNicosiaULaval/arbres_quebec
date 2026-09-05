#!/usr/bin/env Rscript

# Download the exact source bytes used for version 1.0.0. Existing files are
# verified, never silently replaced. The teaching CSV does not need this step.
library(readr)
library(digest)

sources <- read_csv("references/frozen_sources.csv",
                    col_types = cols(.default = col_character()))
selected <- Sys.getenv("FROZEN_SOURCE_IDS", "")
if (nzchar(selected)) {
  ids <- trimws(strsplit(selected, ",", fixed = TRUE)[[1]])
  stopifnot(all(ids %in% sources$source_id))
  sources <- sources[sources$source_id %in% ids, ]
}
for (i in seq_len(nrow(sources))) {
  path <- sources$local_path[i]
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  if (!file.exists(path)) {
    temporary <- tempfile(tmpdir = dirname(path))
    cat("Téléchargement :", sources$source_id[i], "\n")
    status <- tryCatch(download.file(sources$frozen_url[i], temporary,
      method = "curl", mode = "wb", extra = "--fail --location --retry 2"),
      error = function(e) { unlink(temporary); stop(e) })
    if (status != 0L || !file.exists(temporary)) stop("Échec du téléchargement : ", path)
    actual <- digest(file = temporary, algo = "sha256", serialize = FALSE)
    if (actual != sources$sha256[i]) {
      unlink(temporary)
      stop("Empreinte incorrecte pour ", path)
    }
    if (!file.rename(temporary, path)) stop("Impossible de créer ", path)
  }
  actual <- digest(file = path, algo = "sha256", serialize = FALSE)
  if (actual != sources$sha256[i]) {
    stop("Le fichier existant diffère de la version figée : ", path,
         ". Conserver cette autre version dans un dossier distinct.")
  }
  cat("SHA-256 vérifié :", path, "\n")
}
