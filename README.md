# Generic Tool Launcher

##### The GUI helps access tools required for a pipeline (stored in different Conda environments with differing dependencies) on one platform. It is customizable for different kinds of tools; the current project focuses on DeepLabCut (https://github.com/DeepLabCut/DeepLabCut.git) and SimBA (https://github.com/sgoldenlab/simba.git) for animal pose and behavior estimation.

## Installation
This GitHub repository can be downloaded in zipped format; follow the next steps:

### WINDOWS Setup:

- Double-click on **setup.bat**
##### setup.bat checks if installations are working correctly for the current project. If all is OK, the GUI starts.


### MacOS Setup (in Terminal):
```
cd ../Generic-Tool-Launcher-master/
chmod +x setup.sh
bash setup.sh
```

##### Once the initialization is done, the GUI can be accessed directly by:
```
conda run -n tool-launcher python -m app.main
```

