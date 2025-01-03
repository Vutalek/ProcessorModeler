library(ggplot2)
library(rmarkdown)
library(tinytex)
Sys.setenv(RSTUDIO_PANDOC = "D:/Programming/R/BASE/RStudio/resources/app/bin/quarto/bin/tools")

# парсер файлов логов ядер
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

# чтение файла с общими выводами
read_general_file <- function() {
  con <- file("logs/General.txt", open = "r")
  lines <- readLines(con)
  close(con)
  return(lines)
}

# график отображает последовательностьь выполненных действий
seq_plot <- function(data) {
  plt <- ggplot(data = data, aes(x = id, y = task, group = type, color = type)) +
    geom_point() +
    geom_line() +
    theme_minimal() +
    xlab("time")
  return(plt)
}

# график показывает соотнешение количества заданий по типу операции
type_plot <- function(data) {
  plt <- ggplot(data = data, aes(x = type)) +
    geom_bar(color = "purple", fill = "purple", alpha = 0.4, linewidth = 1) +
    geom_text(stat = "count", aes(label = after_stat(count)), vjust = -1) +
    scale_y_continuous(expand = c(0.1, 0)) +
    theme_minimal()
  return(plt)
}

# график показывает соотнешение количества заданий по типу
task_plot <- function(data) {
  plt <- ggplot(data = data, aes(x = task)) +
    geom_bar(color = "purple", fill = "purple", alpha = 0.4, linewidth = 1) +
    geom_text(stat = "count", aes(label = after_stat(count)), vjust = -1) +
    scale_y_continuous(expand = c(0.1, 0)) +
    theme_minimal()
  return(plt)
}

# отображает распределение времени исполнения
time_plot <- function(data) {
  plt <- ggplot(data = data, aes(x = time)) +
    geom_density(color = "purple", fill = "purple", alpha = 0.4, linewidth = 1, kernel = "epanechnikov") +
    theme_minimal()
  return(plt)
}

# расчёт статистик
statistic <- function(data) {
  count <- nrow(data)
  mt <- mean(na.omit(data$time))
  std <- sd(na.omit(data$time))
  return(c(count, mt, std))
}

# чтение файлов
filenames <- list.files("logs", full.names = TRUE)
filenames <- filenames[-length(filenames)]
df <- lapply(filenames, read_log_file)
gen <- read_general_file()

# построение графиков
seq_plots <- lapply(df, seq_plot)
type_plots <- lapply(df, type_plot)
task_plots <- lapply(df, task_plot)
time_plots <- lapply(df, time_plot)
stats <- lapply(df, statistic)

invisible(render("doc.Rmd", output_file = "output/report.pdf"))
