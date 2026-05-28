# Pre-render script: install missing R packages
if (!requireNamespace("pak", quietly = TRUE)) install.packages("pak", repos = "https://cran.r-project.org")
pak::pak("tdscience/tartu26")
