After Download via git or zip


WINDOWS SETUP (in command prompt):

```
if conda env list | findstr /I "tool-launcher"; then
    echo "Environment already exists"
else
    echo "Creating environment..."
    conda create -n generic-tool-launcher python=3.13 -y
fi

cd ..\Generic-Tool-Launcher-master
conda activate tool-launcher
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
Check if the installations are correct:
```
python -c "from PySide6 import QtCore; print(QtCore.__version__)"
python -c "from PySide6 import QtWidgets; print('QtWidgets OK')"
```
If all OK, start the GUI
```
python -m app.main
```


MacOS SETUP (in terminal):
