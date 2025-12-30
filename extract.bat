@echo off
copy /B /Y %1.fla %1.zip
mkdir %1
cd %1
"C:\Program Files\7-Zip\7z.exe" x ../%1.zip -aoa
cd ..