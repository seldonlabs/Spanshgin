mkdir Spanshgin
rm pyperclip\*.pyc
cp -recurse spansh.py, load.py, pyperclip Spanshgin/

& "$Env:ProgramFiles\7-Zip\7z.exe" a -sdel Spanshgin-$(git symbolic-ref HEAD --short)-$(git rev-parse --short HEAD)-$(get-date -uformat "%Y.%m.%d").zip Spanshgin
