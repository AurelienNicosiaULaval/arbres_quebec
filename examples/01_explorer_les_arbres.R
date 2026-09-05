# Run from the project root. The small CSV is included in the downloaded ZIP.
library(readr)
library(dplyr)
library(ggplot2)

arbres <- read_csv(
  "data_clean/arbres_quebec_small.csv",
  col_types = cols(.default = col_guess(), plot_id = col_character(),
                   tree_id = col_character(), record_id = col_character())
)

portrait <- arbres |>
  group_by(species) |>
  summarise(
    nombre = n(),
    diametre_moyen_cm = mean(diameter_cm),
    hauteur_moyenne_m = mean(height_m),
    ages_manquants = sum(is.na(age_years)),
    .groups = "drop"
  )
print(portrait)

graphique <- ggplot(arbres, aes(diameter_cm, height_m, colour = species)) +
  geom_point(size = 2, alpha = 0.8) +
  scale_colour_brewer(palette = "Dark2") +
  labs(x = "Diamètre à hauteur de poitrine (cm)", y = "Hauteur observée (m)",
       colour = "Espèce") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "bottom") +
  guides(colour = guide_legend(nrow = 2))
if (interactive()) print(graphique)

# This is a balanced teaching sample, not an estimate of Quebec forest shares.
# Basal area is determined by diameter and is not an independent measurement.
dir.create("outputs", showWarnings = FALSE)
write_csv(portrait, "outputs/portrait_especes.csv")
ggsave("outputs/diametre_hauteur.png", graphique, width = 8, height = 5, dpi = 160)
