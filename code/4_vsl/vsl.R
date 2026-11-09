# PROJECT: GEP
# PURPOSE: GDP-adjusted VSL
# AUTHOR: Raahil Madhok

# ----------- SET-UP ----------------------------
# Directories
rm(list=ls())
ROOT <- 'data'
setwd(ROOT)

# Load Packages
packages <- c('tidyverse', 'fuzzyjoin')
pacman::p_load(packages, character.only = TRUE, install = FALSE)

#------------------------------------------------
# PREP DATA
#------------------------------------------------

# Read life expectancy
le <- read_csv('./raw/life_expectancy.csv') %>%
  select(slug, years) %>%
  rename(life_expectancy = years)

# read elderly population
elderly <- read_csv('./clean/age_75.csv') %>%
  rename(slug = country)

# Read real GDP
gdp <- read_csv('./raw/real_gdp_pc.csv') %>%
  select(slug, value, date_of_information) %>%
  rename(base_year = date_of_information,
         gdp_real = value) %>%
  mutate(gdp_real = as.numeric(gsub("[\\$,]", "", gdp_real)))

# Merge together
df <- left_join(le, elderly, by='slug') %>%
  inner_join(gdp, by='slug') %>%
  rename(country = slug)

#------------------------------------------------
# VSL CALCULATION
#------------------------------------------------

# Step 1: set USA vsl
vsl_usa <- 9900000

# Step 2: USA life years lost

## using elderly age
lll_usa <- df$life_expectancy[df$country == 'united-states'] - df$age_75[df$country == 'united-states']

# Step 3: USA GDP
gdp_usa <- df$gdp_real[df$country == 'united-states']

# Step 4: USA intermediates
vsl_lll_usa <- vsl_usa / lll_usa # vsl-per-life year lost
vsl_lll_gdp_usa <- vsl_lll_usa / gdp_usa # vsl-per-life year lost to GDP ratio
 
# Step 5: VSL for all countries
df$lll = df$life_expectancy - df$age_75 # median age
df$vsl = df$gdp_real * df$lll * vsl_lll_gdp_usa

# Save
df <- arrange(df, country) %>% select(country, vsl)
write_csv(df, './clean/vsl.csv')



