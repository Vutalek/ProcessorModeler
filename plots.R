library(ggplot2)
library(grid)
library(gridExtra)
library(rmarkdown)
library(tinytex)
Sys.setenv(RSTUDIO_PANDOC = "D:/Programming/R/BASE/RStudio/resources/app/bin/quarto/bin/tools")

#### Парсер логов ####

read_log_file <- function(fileName) {
  con <- file(fileName, open = "r")
  df <- data.frame(
    id = as.numeric(),
    type = character(),
    task = character(),
    to_core = character(),
    time = numeric()
  )
  counter <-  1
  while (TRUE) {
    line = readLines(con, n = 1)
    if (length(line) == 0) {
      break
    }
    splitted <- unlist(strsplit(line, " "))
    t <- NA
    if (splitted[1] == "Sended") {
      t <- as.numeric(splitted[7])
    } else if (splitted[1] == "Done") {
      t <- as.numeric(splitted[4])
    }
    line_df <- data.frame(
      id = counter,
      type = splitted[1],
      task = splitted[2],
      to_core = if(splitted[1] == "Sended") splitted[4] else NA,
      time = t
    )
    df <- rbind(df, line_df)
    counter <- counter + 1
  }
  close(con)
  return(df)
}

#### Чтение файла с временем работы ####

read_general_file <- function() {
  con <- file("logs/General.txt", open = "r")
  lines <- readLines(con)
  close(con)
  return(lines)
}

#### Исследование частично заполненных Ethernet фреймов ####

ethernet_analyze <- function() {
  con <- file("temp/stream0_0.txt", open = "r")
  data = data.frame(
    type = c("full", "partial"),
    count = c(0, 0)
  )
  while (TRUE) {
    line = readLines(con, n = 1)
    if (length(line) == 0) {
      break
    }
    splitted <- unlist(strsplit(line, ','))
    if (splitted[2] == "1530") {
      data[1, 2] = data[1, 2] + as.numeric(splitted[1])
    } else {
      data[2, 2] = data[2, 2] + as.numeric(splitted[1])
    }
  }
  close(con)

  plt <- ggplot(data = data, aes(x = type, y = count)) +
    geom_col(color = "purple", fill = "purple", alpha = 0.4, linewidth = 1) + 
    geom_text(aes(label = count), vjust = -1) + 
    scale_y_continuous(expand = c(0.1, 0)) +
    theme_minimal()
  return(plt)
}

#### Исследование выполнения/пропуска задач ####

overall_done_timeout_skipped <- function(data) {
  result <- c(
    nrow(data[data$type == "Done",]),
    nrow(data[data$type == "TTL_timeout",]),
    nrow(data[data$type == "Skipped",])
  )
  return(result)
}

done_timeout_analyze <- function(df) {
  done_timeouts <- lapply(df, overall_done_timeout_skipped)
  done <- sum(unlist(done_timeouts)[c(TRUE, FALSE, FALSE)])
  timeouts <- sum(unlist(done_timeouts)[c(FALSE, TRUE, FALSE)])
  skipped <- sum(unlist(done_timeouts)[c(FALSE, FALSE, TRUE)])
  data = data.frame(
    type = c("done", "timeout", "skipped"),
    count = c(done, timeouts, skipped)
  )
  plt <- ggplot(data = data, aes(x = type, y = count)) +
    geom_col(color = "purple", fill = "purple", alpha = 0.4, linewidth = 1) + 
    geom_text(aes(label = count), vjust = -1) + 
    scale_y_continuous(expand = c(0.1, 0)) +
    theme_minimal()
  return(plt)
}

#### Исследование распределения задач по ядрам внутри процессора ####

core_dist <- function(data) {
  seq <- ggplot(data = na.omit(data), aes(x = id, y = to_core, group = "whatever")) +
    geom_point(color = "purple") +
    geom_line(color = "purple") +
    theme_minimal() +
    xlab("time") +
    ylab("core")
  dist <- ggplot(data = na.omit(data), aes(x = to_core)) +
    geom_bar(color = "purple", fill = "purple", alpha = 0.4, linewidth = 1) +
    geom_text(stat = "count", aes(label = after_stat(count)), hjust = -0.5) +
    coord_flip() +
    scale_y_discrete(expand = c(0.1, 0)) +
    theme_minimal() +
    xlab("core")
  plt <- grid.arrange(seq, dist, nrow = 2)
  return(plt)
}

#### Исследование распределения задач по процессорам ####

not_sended <- function(data) {
  return(nrow(data[data$type != "Sended",]))
}

proc_dist <- function(df) {
  ns <- unlist(lapply(df[c(FALSE, TRUE, TRUE, TRUE)], not_sended))
  thirds <- split(ns, ceiling(seq_along(ns)/3))
  count <- unlist(lapply(thirds, sum))
  data = data.frame(
    processor = seq_along(count),
    count = count
  )
  plt <- ggplot(data = data, aes(x = processor, y = count)) +
    geom_col(color = "purple", fill = "purple", alpha = 0.4, linewidth = 1) + 
    geom_text(aes(label = count), vjust = -1) + 
    scale_y_continuous(expand = c(0.1, 0)) +
    theme_minimal()
  return(plt)
}

#### Анализ ####

# Чтение файлов
filenames <- list.files("logs", full.names = TRUE)
filenames <- filenames[-length(filenames)]
df <- lapply(filenames, read_log_file)

# Анализ
gen <- read_general_file()
ethernet <- ethernet_analyze()
dts <- done_timeout_analyze(df)
procs <- proc_dist(df)
cores <- lapply(df[c(TRUE, FALSE, FALSE, FALSE)], core_dist)

# Построение отчёта
render("doc.Rmd", output_file = "output/report.pdf")
