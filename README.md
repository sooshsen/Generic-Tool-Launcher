# Generic Tool Launcher

##### This GUI aims to systematically access the tools required for a pipeline via one platform. It is customizable for different pipelines, as per one's needs.

After Download via git or zip:


## Installation
### WINDOWS Setup:

- Double click on **setup.bat**
##### setup.bat checks if installations are working correctly for the current project
##### If all OK, the GUI starts.


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

