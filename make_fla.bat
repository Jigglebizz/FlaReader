@echo off
"C:\Program Files\7-Zip\7z.exe" a %1.zip ./%1/*
copy /B /Y %1.zip %1.fla