@echo off
copy /B /Y test_project.fla test_project.zip
mkdir test_project
cd test_project
"C:\Program Files\7-Zip\7z.exe" x ../test_project.zip -aoa
cd ..