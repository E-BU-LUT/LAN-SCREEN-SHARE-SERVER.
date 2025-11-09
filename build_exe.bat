@echo off
echo PyInstaller yukleniyor...
pip install pyinstaller

echo.
echo EXE dosyasi olusturuluyor...
pyinstaller --onefile --console --name "EkranPaylasimSunucusu" yerelsunucu.py

echo.
echo Tamamlandi! EXE dosyasi 'dist' klasorunde bulunuyor.
pause

