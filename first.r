# Clear environment variables
rm(list=ls())

# CHeck for installed package:
# any(grepl("<name of your package>",
# installed.packages()))


# Handle working directory
getwd()
setwd("D:/Aktual/Youtube_stat")

# Import data
input_file <- "all_data.csv"

lowko <- read.csv(file=input_file,head=TRUE,sep=",")

# Convert to numeric
vid_len = as.numeric(unlist(lowko["length"]))
#lowko["length"] <- replace(lowko["length"], TRUE, as.numeric(lowko["length"]))

hist(vid_len, freq=FALSE)
hist(vid_len)
curve(dnorm(x, mean=mean(vid_len), sd=sd(vid_len)), add=T, col="darkblue", lwd=2)
lines(density(vid_len), col="red", lwd=2)
#max(density(vid_len))
mean(vid_len)/60
sd(vid_len)/60
# leghosszabb video: 2 ora 7 perc
# legrovidebb video: fel perc
min(vid_len)

# csv import creates a dataframe, with name() we can list all the collumn names of it
names(lowko)

# with this command we can create a 10 element list of zeros
# numeric(10)

# Make histogram about video length


# Make histgram about video likes

# Make correlation about likes and length

# Make bar chart about released videos per month

# Make histogram about pauses between video releases

# Make graph about likes/video as time goes

# Make graph about dislikes/video as time goes

# Make chart about most used words in titles

# Make chart about most used words in titles per playlist

# Order words used in video titles, which received the most like

# Order words used in video titles, which received the most dislike

# Make chart about playlist lifecycle as time goes.
# A playlist is active, when a new video is released in it

