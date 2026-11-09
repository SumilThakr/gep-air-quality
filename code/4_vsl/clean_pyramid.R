# PROJECT: GEP
# PURPOSE: Clean Population Pyramid Data
# AUTHOR: Raahil Madhok

# ----------- SET-UP ----------------------------
# Directories
rm(list=ls())
ROOT <- 'data'
setwd(ROOT)

# Load Packages
packages <- c('tidyverse')
pacman::p_load(packages, character.only = TRUE, install = FALSE)

#------------------------------------------------
# PREP DATA
#------------------------------------------------

# settings 
threshold <- 75 # percentile of age distribution which we consider "elderly"

# read age structure by country
df <- read_csv('./raw/age_structure_global.csv') %>%
  select('Country/Area Name', 'GROUP', 'Population') %>%
  rename(country = 'Country/Area Name',
          age = 'GROUP',
          population = 'Population')

# add country population
df <- df %>%
  group_by(country) %>%
  mutate(population_total = population[is.na(age)]) %>%
  filter(!is.na(age))

# age at 75th percentile of age distribtion (elderly)
df <- df %>%
  mutate(pop_share = (population / population_total),
         cum_share = cumsum(pop_share)*100) %>%
  filter(cum_share < threshold) %>%
  group_by(country) %>%
  summarize(age_75 = last(age))

# clean country name to match VSL dataset
df <- df %>%
  mutate(country = str_to_lower(str_replace_all(country, "[-,()]", " ")),   # replace special chars with space
         country = str_squish(country),                       # remove extra, leading/trailing spaces
         country = str_replace_all(country, " ", "-"),        # replace spaces with dash
         country = case_when(
           country == 'curaçao' ~ 'curacao',
           country == 'turkey' ~ 'turkey-turkiye',
           country == 'côte-d’ivoire' ~ 'cote-divoire',
           country == 'virgin-islands-u.s.' ~ 'virgin-islands',
           country == 'virgin-islands-british' ~ 'british-virgin-islands',
           country == 'congo-kinshasa' ~ 'congo-democratic-republic-of-the',
           country == 'congo-brazzaville' ~ 'congo-republic-of-the',
    TRUE ~ country))

# Save
write_csv(df, paste('./clean/age_', threshold, '.csv', sep=''))







