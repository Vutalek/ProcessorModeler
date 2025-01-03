echo off
cd ..
mkdir temp
mkdir logs
mkdir output
cls
echo Modeling:
python start.py
echo Graphics:
Rscript plots.R
pause
echo on