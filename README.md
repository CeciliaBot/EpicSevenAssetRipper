# Epic Seven Asset Ripper

Python 3 tool to extract assets from the data.pack without wasting storage on your PC!

![image](https://github.com/CeciliaBot/EpicSevenAssetRipper/assets/62508224/0fb8680e-27d0-426a-8d0f-4c68a7b16062)

# Todo

- Add support for audio bank files (python's FSB5 package doesn't support E7 (0F) wav mode?)

# Help

If you find a bug or have improvments to make feel free to open a Pull Request or open an Issue!

# Installation:

## Requirements
Python 3.7+

## How to install

[Download the latest version](https://github.com/CeciliaBot/EpicSevenAssetRipper/releases/latest) and extract all the files in a folder of your choice.

Open the command prompt (hold shift + right click inside the folder -> Power Shell on windows) and type

    pip install requirements.txt

This should take care of all the dependencies required

Now you can double click main.py or type py main.py in the command prompt to run the GUI

A folder named data.pack will be created, you can use this folder to organize your files or just ignore it

# File Tree

![image](https://github.com/CeciliaBot/EpicSevenAssetRipper/assets/62508224/39bf2475-cb0b-42b1-ba13-29b7c05b36c9)

1) Select a valid data.pack to extract files from (data.pack can be the original file or a decrypted data.pack both work)
2) Scan the data.pack to find all available assets to extract
3) Load a file tree you previously saved if you don't want to generate a new one each time to save time. Each data.pack is different, you must use the correct file tree map file or you will get corrupted files when extracting!
4) Save file tree, will save the file tree as a JSON file and you can select the output name and directory. Note: will save the original file tree without any filters applied
5) Extract all files from the file tree
6) Extract selected files: you can extract a single file or folder from the file tree. (You can also right click the file/folder and select "Extract" from the contextual menu)
7) Compare: compare the current file tree to an older file tree and find file differences. Note: this tool will compare file size and not actual file content, if a single byte has changed this tool won't detect the change
8) Search for specific files using this search bar. The search bar supports Regex! For example if you want only pngs and jpgs you can type \.(png|jpg)$ this will filter the file tree and you can use extract all to get all the files you need!

# Decrypt

![image](https://github.com/CeciliaBot/EpicSevenAssetRipper/assets/62508224/fd7096f5-d209-40ec-b1a3-fdea96d79856)

This is the classic aproach you can select the original data.pack and the output file name to generate the decrtpted data.pack then you can use the decrypted data.pack to extract all the assets. You need a lot of free space (2x data.pack file size) to use this method.

# Dev stuff
In the app/hooks folder you will find 2 folders "before_write" and "after_write". You can add custom code for each file extension to excute while files are being written to your drive. For example you can create "db.py" in the "before_write" folder to perform some decryption or other logic before writing the data to the hard drive!

In the files you have created you must define a "main" method, this method will be called by the tool

    # for example "hooks/after_write/db.py" file
    def main(file_path, data_bytes, tree_file):
        # file_path: string => path where to write the file (or were it's written if after -> the file il closed, you need to open it again if you want to edit)
        # data_bytes: bytes => the content of the file
        # tree_info: dictionary => file info contains: name, full_path (in the data.pack header), offset, size
        print(file_path)