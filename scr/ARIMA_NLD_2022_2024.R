## @author: Roberto Mendoza

# clean environment variables
rm(list = ls())

# clean plots
graphics.off()

# clean console

cat("\014")

# additional options
options(scipen = 999)      # No scientific notation


library(pacman)


p_load(tidyverse,
       haven,
       stringi,
       stringdist, 
       readxl,
       foreign,
       labelled,
       openxlsx,
       forecast)


# Change working directory

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# Load data harmonized nightlight data 1992-2021 at municipio level

nld_data <- read_dta(
"data/raw/Nightlight/colombia_nl_harmonized_1992_2021.dta") 


nld_data <- nld_data |>
  select(adm2_pcode, nl_mean, year ) |>
  rename(light_mean_y=nl_mean) |>
  arrange(adm2_pcode, year)

# Load data nightlight data from VIIRS satellite 2022-2024 at municipio level

nld_data_viirs <- read_dta(
  "data/raw/Gold_data/PEP_NLD_municipio_2013_2024_viirs.dta") 

nld_data_viirs <- nld_data_viirs |>
  select(adm2_pcode, light_mean, year, idyear) |>
  rename(light_mean_x=light_mean) |>
  arrange(adm2_pcode, year)



nld_data_merge <- left_join(nld_data_viirs,
                            nld_data,
                             by =c("adm2_pcode","year")
                             )

# Calculate the first difference of nightlight data for both series harmonized and VIIRS NLD

nld_diff <- nld_data_merge |>
  group_by(adm2_pcode) |>
  mutate(nld_diff_x =c(NA,diff(light_mean_x)),
         nld_diff_y =c(NA,diff(light_mean_y)) ) |>
  ungroup() |>
  filter(year>2013)



##########################################################


nld_diff_training <- nld_diff |> filter(between(year, 2014,2021))

nld_diff_predict <- nld_diff |> filter(between(year, 2022,2024))


############################  Fit Arimax model per Municipio  ##############################


p_load(forecast,
       tibble,
       purrr)


# Function to set the optimal order of MA and AR procees in the Arimax Model 

mejor_arimax_d0 <- function(ts_y, xreg) {
  mejor_aic <- Inf
  mejor_modelo <- NULL
  
  for (p in 0:3) {
    for (q in 0:3) {
      modelo <- try(Arima(ts_y, order = c(p, 0, q), xreg = xreg), silent = TRUE)
      if (!inherits(modelo, "try-error")) {
        if (AIC(modelo) < mejor_aic) {
          mejor_aic <- AIC(modelo)
          mejor_modelo <- modelo
        }
      }
    }
  }
  return(mejor_modelo)
}


id_actual <- sort(unique(nld_diff_training$adm2_pcode))
list_dataframes <- list()

print(length(id_actual))


i<-0

# Loop to fit the Arimax model per municipio and predict the nightlight values for 2022-2024,
# then reconstruct the nightlight values for 2022-2024 and append them to the original dataset 1992-2021

for ( muni in id_actual ) {
  
  
  i<-i+1
  
  
  tryCatch({
    
  data_filter <- nld_diff_training |> filter( adm2_pcode == muni )
  data_filter_predict <- nld_diff_predict |> filter( adm2_pcode == muni )
  
  
  ts_y <-   ts(data_filter$nld_diff_y, start = as.numeric(min(data_filter$year)),
               frequency = 1)

  
  xreg_train <- as.matrix(data_filter$nld_diff_x)  # exogenous variable

  # Fit the ARIMAX model and select the best one based on AIC

  modelo <-   mejor_arimax_d0(ts_y, xreg_train)
  
  
  xreg_future <- as.matrix(data_filter_predict$nld_diff_x)

  # Predict the first difference of nightlight values for 2022-2024 using the fitted model
  pred <- forecast(modelo, xreg = xreg_future, h = 3)


   df_pred <- tibble(
    adm2_pcode = data_filter_predict$adm2_pcode,
    year = data_filter_predict$year,
    nld_diff_y = as.numeric(pred$mean),
    tipo = "predicción"
  ) 
  
    
  data_filter$tipo <- "observado"
  
  nld_data_1 <- nld_data_merge |> filter(year==2021 & adm2_pcode==muni)

  # Create a new dataframe with the predicted values for 2022-2024
  # and the observed value for 2021 to reconstruct the nightlight values for 2022-2024

  data_2022_2024 <- bind_rows(nld_data_1,df_pred ) |> 
    select(adm2_pcode, year, light_mean_y, nld_diff_y)
  
  # Fill in the reconstructed values
  
  data_2022_2024$light_mean <- NA
  data_2022_2024$light_mean[1] <- data_2022_2024$light_mean_y[1]
  data_2022_2024$light_mean[-1] <- data_2022_2024$light_mean[1] + cumsum(data_2022_2024$nld_diff_y[-1])
  
  
  data_2022_2024 <- data_2022_2024 |> filter(year>2021) |> 
    select(adm2_pcode, year, light_mean)
  
  # Append the predicted values for 2022-2024 to the original dataset 1992-2021
  
  nld_data_2000_2021 <- read_dta(
    "data/raw/Nightlight/colombia_nl_harmonized_1992_2021.dta") |>
    arrange(adm2_pcode, year) |>
    select(adm2_pcode, year, nl_mean) |>
    rename(light_mean=nl_mean) |>
    filter(adm2_pcode==muni) 
  
  
  data_2000_2024 <- bind_rows(nld_data_2000_2021,data_2022_2024 )

  
  list_dataframes[[as.character(muni)]] <-data_2000_2024
  
  
  }, error = function(e) {
    message(paste("Error con municipio:", muni, "-", e$message))
  })
  
  
}


print(i)


## Append datasets 1992-2021 and 2022-2024 (predicted Nightlight values)

data_muni_2000_2024 <- do.call(rbind, list_dataframes) |>
  arrange(adm2_pcode, year)

sapply(data_muni_2000_2024, class) ## class variables

## replace negative values by NA

sum(data_muni_2000_2024$light_mean==0)

data_muni_2000_2024$light_mean[data_muni_2000_2024$light_mean<0] <- 0

summary(data_muni_2000_2024$light_mean)

sum(data_muni_2000_2024$light_mean==0)

## Export dataset 

write_dta(data_muni_2000_2024, 
          "data/processed/Nightlight/Colombia/PEP_NLD_municipio_1992_2021_harmonization_extension_arimax.dta")


