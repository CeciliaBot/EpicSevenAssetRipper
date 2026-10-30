# EpicSevenAssetRipper

> [!TIP]
> This tool supports both Epic Seven (E7) and Chaos Zero Nightamre (CZN)

<img width="900" height="730" alt="image" src="https://github.com/user-attachments/assets/a93be0ba-4a35-4ce0-b10f-9183099587a8" />

# Installation:

## Requirements
Python 3.11+

## How to install

[Download the latest version](https://github.com/CeciliaBot/EpicSevenAssetRipper/releases/latest) and extract all the files in a folder of your choice.

Open the command prompt (hold shift + right click inside the folder -> Power Shell on windows) and type

    pip install -r requirements.txt

This should take care of all the dependencies required

Now you can double click main.py or type py main.py in the command prompt to run the GUI

A folder named data.pack will be created, you can use this folder to organize your files or just ignore it


## SCT to PNG
To use the SCT to PNG 3 additional installations are required

    python3 -m pip install --upgrade Pillow

    python3 -m pip install texture2ddecoder

    python3 -m pip install lz4

# How to Use

After installing all the requirements open run.bat or run_no_console.vbs (if you don't want the console)

<img width="900" height="730" alt="image" src="https://github.com/user-attachments/assets/00d005f6-f7c7-43db-8258-8ce088d7938d" />

1. Select the data.pack to use (this tool supports data.pack, .tar, .zip (No password) and rrsa manifest (make sure the chunks folder is in the same folder as the manifest)
2. Generate file tree or load file tree from json file. After generating this tool will automatically save the result to tree.json in the same folder as the data.pack, this tool will also try to automatically load the "tree.json" file in the same directory as the data.pack
3. All the assets inside the data.pack will now be displayed in the file tree. You can select and right click files to extract or preview. (You can enable automatic preview in the settings tab) Preview is only available for images only as of now.
4. (Optional) You can use the compare function to remove unchanged nodes when comparing to older file trees
5. You can enable and disable plugins/hooks by clicking the name at the bottom right of the window


# What's new in 2.0
SCT to PNG is now included, this hook allows to decode and convert sct and sct2 files to png

Multiselect in the file tree: you can hold CTRL + Left click to select different nodes in the file tree view

Reload hooks: Click the small refresh icon at the bottom left to relaod hooks (hooks dependencies wont be reloaded)

Settings tab: Here you can change some settings

Light and Dark themes: Improvments to the dark theme and new light theme

# Hooks

Hooks can be disabled by clicking the Hook's name at the bottom right of the window

## Custom hooks

You can create your custom hooks to handle different file extensions. This tool provides the SCT to PNG and Webp loop hooks.

To create a hook create a python file named after the extension/file format you want to handle. Inside this file you need to define a main function that takes only one argument

```
_ADDON_NAME_ = 'ATLAS' # The name of this hook, it will be displayed in the bottom right corner of the Asset Ripper
_PREVENT_DEFAULT_ICON_ = True # Optional: default False. If set to True the icons in the bottom toolbar for this hook won't be created and displayed.


from app.util.misc import FileDescriptor # only used for type hinting, you can skip this import

# This is the main function and only thing required for the hooks to work. It will be called everytime a file extension matches this files name for example 'sct.py'
def main(file: FileDescriptor):
  # the file argument is a class object
  content = file.bytes # -> This is a ByteArray which is a bytearray subclass with additional methods like seek, tell, read
  path = file.path # -> Destination path, set this to None if you want to prevent the default save function and handle it in your hook
  info = file.tree_file # -> The tree data
  thread = file.thread # -> You can check is_stopping() to check if the proccess was interrupted by the user or call progress((int, str)) NOTE: progress requires a tuple
  written = file.written # -> Check if the file has been written, this should be true if the hook is in the after_write folder

# Optional
def onEnabled():
  # Do something to update the ui...
  # this will be called only when switching from disabled to enabled, this function won't be called when the script is loaded

# Optional
def onDisabled():
  # Called when this hook has been disabled by clicking the hook's name in the bottom toolbar of the tool
  # it can be used to update the ui or the previewer

# Optional
def destroy():
  # This function is only called if the refresh hooks button has been clicked and this script is no longer available in the hooks folder

```

## Update UI

If you need to update the ui you should first check if the ui is loaded:
```
if 'PyQt6' in sys.modules:
  # The ui was initialized
  from PyQt6.QtWidgets import QApplication, QWidget
  app = QApplication.instance()
  add_setting = app.property('CreateSetting')
  add_setting(title=f'[<b>My Hook</b>] Setting Title', description='', value=False, type='checkbox', options=[], onchanged=lambda v: print(v))
else:
  # No ui
```

For example the code above will create a new option in the settings tab

`if 'PyQt6' in sys.modules:` is used to check if this tool is running as a GUI or not. `app = QApplication.instance()` returns None if the ui is not initialized.

## Adding a preview type for a file extension
You can add a preview type from the supported components [image, csv (tab), text] for a specific file type by calling the following function
```
from gui.components.preview import FileContentPreview
FileContentPreview.setPreviewType('stc', 'image')
```

You can do the same to remove a preview type
```
from gui.components.preview import FileContentPreview
FileContentPreview.deletePreviewType('stc')
```
