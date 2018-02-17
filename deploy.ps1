if (Test-Path "$Env:localappdata\EDMarketConnector\plugins\Spanshgin") {
   rm -recurse "$Env:localappdata\EDMarketConnector\plugins\Spanshgin"
}

mkdir "$Env:localappdata\EDMarketConnector\plugins\Spanshgin"
cp -recurse spansh.py, load.py, pyperclip "$Env:localappdata\EDMarketConnector\plugins\Spanshgin\"
