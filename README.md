# Epic Seven Asset Ripper

Python 3 tool to extract assets from the data.pack without wasting storage on your PC!

![image](https://github.com/CeciliaBot/EpicSevenAssetRipper/assets/62508224/0fb8680e-27d0-426a-8d0f-4c68a7b16062)

# Installation:
Download the code and extract in a folder of your choice

Open the command prompt and type

> py install requirements.txt

This should take care of the dependencies

Now you can double click main.py or type py main.py to run the GUI

A folder named data.pack will be created, you can use this folder to organize your files or just ignore it

## File Tree

![image](https://github.com/CeciliaBot/EpicSevenAssetRipper/assets/62508224/39bf2475-cb0b-42b1-ba13-29b7c05b36c9)

1) Select a valid data.pack to extract files from (data.pack can be the original file or a decrypted data.pack both work)
2) Scan the data.pack to find all available assets to extract
3) Load a file tree you previously saved if you don't want to generate a new one each time to save time. If you use the wrong file tree for the wrong data.pack files will result corrupted!
4) Save file tree, will save the file tree as a JSON file and you can select the output name and directory. Note: will save the original file tree without any filters applied
5) Extract all files from the file tree
6) Extract selected files: you can extract a single file or folder from the file tree. (You can also right click the file/folder and select "Extract" from the contextual menu)
7) Compare: compare the current file tree to an older file tree and find file differences. Note: this tool will compare file size and not actual file content, if a single byte has changed this tool won't detect the change
8) Search for specific files using this search bar. The search bar supports Regex! For example if you want only pngs and jpgs you can type \.(png|jpg)$ this will filter the file tree and you can use extract all to get all the files you need!

# Decrypt

![image](https://github.com/CeciliaBot/EpicSevenAssetRipper/assets/62508224/fd7096f5-d209-40ec-b1a3-fdea96d79856)

This is the classic aproach you can select the original data.pack and the output file name to generate the decrtpted data.pack then you can use the decrypted data.pack to extract all the assets. You need a lot of free space (2x data.pack file size) to use this method.

## Dev stuff
In the app/hooks folder you will find 2 folders "before_write" and "after_write". You can add custom code for each file extension to excute while files are being written to your drive. For example you can create "db.py" in the "before_write" folder to perform some decryption or other logic before writing the data to the hard drive!

In the files you create you must define a "main" method, this will method will be called by the tool

    # db.py file
    def main(data):
        // do some mutation with the data
        print(data)

