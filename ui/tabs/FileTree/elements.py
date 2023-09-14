import json
import re
import copy
from PyQt5                                    import QtWidgets, QtCore, QtGui
from tkinter.filedialog                       import askopenfilename, askdirectory, asksaveasfile
from ui.components.filetree                   import TreeTable
from ui.threads                               import Worker, ThreadPool
#from .threads                                import GenerateTreeThread, ExtractFilesThread
from app.utils                                import convert_size, checkValidDataPack, treeToList, listToTree
from app.utils_generate_file_tree_pack        import generate_pack_tree
from app.utils_extract_pack                   import ExtractFiles
from ui.components.progress_bar.ProgressBar   import ProgressBar


class TreeTab(QtWidgets.QWidget):
    pack_file = None
    pack_decrypted = False
    tree_map = None
    compare_tree_map = None
    is_generating_tree = False
    disable_if_extracting = []
    disable_if_no_map = []
    disable_if_cant_extract = []

    def __init__(self):
        QtCore.QObject.__init__(self)

        pagelayout = QtWidgets.QVBoxLayout()
        button_layout = QtWidgets.QHBoxLayout()
        progressbar_layout = QtWidgets.QHBoxLayout()
        toolbar_layout = QtWidgets.QHBoxLayout()
        self.stacklayout = QtWidgets.QStackedLayout()

        pagelayout.addLayout(button_layout)
        pagelayout.addLayout(progressbar_layout)
        pagelayout.addLayout(toolbar_layout)
        pagelayout.addLayout(self.stacklayout)

        btn = QtWidgets.QPushButton("Select data.pack")
        btn.clicked.connect(lambda: self.selectPackFile())
        button_layout.addWidget(btn)
        self.disable_if_extracting.append(btn)

        btn = QtWidgets.QPushButton("Generate File Tree")
        btn.pressed.connect(self.generateTree)
        button_layout.addWidget(btn)
        self.disable_if_extracting.append(btn)
        self.generate_tree_button = btn

        btn = QtWidgets.QPushButton("Load File Tree JSON")
        btn.pressed.connect(self.selectTreeMapFile)
        button_layout.addWidget(btn)
        self.disable_if_extracting.append(btn)

        button_layout.addStretch()

        self.search_bar = QtWidgets.QLineEdit(self)
        button_layout.addWidget(self.search_bar)
        self.disable_if_extracting.append(self.search_bar)
        self.disable_if_no_map.append(self.search_bar)

        btn = QtWidgets.QPushButton()
        btn.pressed.connect(self.searchTreeMap)
        pixmapi = QtWidgets.QStyle.SP_CommandLink
        icon = self.style().standardIcon(pixmapi)
        btn.setIcon(icon)
        button_layout.addWidget(btn)
        self.disable_if_extracting.append(btn)
        self.disable_if_no_map.append(btn)

        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.setValue(0)
        self.progressbar.setFormat("%p%")
        self.progressbar.setTextVisible(False)
        self.progressbar.setObjectName("progressbar")
        progressbar_layout.addWidget(self.progressbar)

        self.FileTree = TreeTable()
        self.FileTree.setColumns(["File", "Type", "Size", "Files in folder / Offset"])
        self.FileTree.setDictToColumn( self.functionColumnElements )
        self.FileTree.setContextMenu([["Extract", self.extractFile]])
        self.stacklayout.addWidget(self.FileTree.widget())




        toolbar = QtWidgets.QToolBar()
        toolbar_layout.addWidget(toolbar)
        #self.FileTree.widget().addToolBar(toolbar)

        ############################### Save Button ###############################
        pixmapi = QtWidgets.QStyle.SP_DialogSaveButton
        icon = self.style().standardIcon(pixmapi)
        button_action = QtWidgets.QAction(icon, "Save file map (CTRL + S)", toolbar)
        toolbar.addAction(button_action)
        button_action.triggered.connect(self.saveTreeMapFile)
        button_action.setShortcut('Ctrl+S')
        # button_action.setCheckable(True)
        self.disable_if_no_map.append(button_action)

        toolbar.addSeparator()

        ############################### Extract All Button ###############################
        button_action = QtWidgets.QAction(QtGui.QIcon('./ui/assets/archive-extract.png'), "Extract all", toolbar)
        toolbar.addAction(button_action)
        button_action.triggered.connect(self.toolbarExtractAllClick)
        # button_action.setCheckable(True)
        self.disable_if_cant_extract.append(button_action)
        
        ############################### Extract Selected Button ###############################
        button_action = QtWidgets.QAction(QtGui.QIcon('./ui/assets/archive-extract-selected.png'), "Extract selected files", toolbar)
        toolbar.addAction(button_action)
        button_action.triggered.connect(self.toolbarExtractSelectedClick)
        self.disable_if_cant_extract.append(button_action)
        # button_action.setCheckable(True)

        toolbar.addSeparator()

        ############################### Compare ###############################
        button_action = QtWidgets.QAction(QtGui.QIcon('./ui/assets/compare.png'), "Compare to older file tree", toolbar)
        toolbar.addAction(button_action)
        button_action.triggered.connect(self.toolbarCompareClick)
        self.disable_if_no_map.append(button_action)
        # button_action.setCheckable(True)

        toolbar.addSeparator()

        self.checkAndDisable() # Check and disable buttons if needed

        widget = QtWidgets.QWidget()
        widget.setLayout(pagelayout)
        self.treeUI = widget

    def ui(self):
        return self.treeUI

    def checkAndDisable(self):
        canExtract = self.canExtract()

        if self.is_generating_tree:
            for el in self.disable_if_extracting:
                el.setEnabled(False)
        else:
            for el in self.disable_if_extracting:
                el.setEnabled(True)
            if self.pack_file is None:
                self.generate_tree_button.setEnabled(False)
            if self.tree_map is None:
                for el in self.disable_if_no_map:
                    el.setEnabled(False)

        if self.tree_map:
            for el in self.disable_if_no_map:
                el.setEnabled(True)
        else:
            for el in self.disable_if_no_map:
                el.setEnabled(False)

        for el in self.disable_if_cant_extract:
            el.setEnabled(canExtract)

    def canExtract(self):
        if self.tree_map and self.pack_file:
            return True

        return False

    def errorWindow(self, title, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(message)
        msg.resize(400, 300)
        # msg.setInformativeText('More information')
        msg.setWindowTitle(title)
        msg.exec_()

    @staticmethod
    def functionColumnElements(data): # Return the columns for each item in the file tree (function passed to file tree widget)
        if data["type"] == 'folder':
            return [data["name"], "Folder", convert_size(data["size"]), str(data["files"]) + ' files']
        else:
            return [data["name"], data["format"].upper(), convert_size(data["size"]), str(data["offset"])]

    def selectPackFile(self):
        path = askopenfilename(title='Select data.pack')
        if path != '':
            check = checkValidDataPack(path)
            if check == 1:
                self.pack_file = path
                self.pack_decrypted = False
                self.checkAndDisable()
            elif check == 2:
                self.pack_file = path
                self.pack_decrypted = True
                self.checkAndDisable()
            else:
                self.errorWindow('Error', 'Not a valid Epic Seven data.pack.')

    def selectTreeMapFile(self):
        path = askopenfilename(title='Select file map')
        if path != '':
            try:
                f = open(path)
                self.tree_map = json.load(f)
                self.FileTree.showTree(self.tree_map)
                f.close()
                self.checkAndDisable()
            except:
                self.errorWindow('Error', 'Error while parsing your file map.')

    def threadError(self, err):
        a,b,c = err
        self.errorWindow('Error', b)

    ###################### GENERATE TREE
    def generateTree(self):
        if self.pack_file is None:
             return self.errorWindow('Error', 'Please select the data.pack first.')

        self.is_generating_tree = True
        self.FileTree.showTree([])
        self.checkAndDisable()

        # Pass the function to execute
        worker = Worker(generate_pack_tree, self.pack_file, self.pack_decrypted)

        worker.signals.result.connect(self.generate_tree_result)
        worker.signals.finished.connect(self.generate_tree_finished)
        worker.signals.progress.connect(self.generate_tree_progress)
        worker.signals.error.connect(self.threadError)

        # Execute
        ThreadPool.start(worker)


        # Update path and other data on the thread
        # self.worker.updateData()
        # Run the thread
        # self.worker.start()

    def generate_tree_progress(self, val):
        self.progressbar.setValue(val)

    def generate_tree_finished(self):
        self.is_generating_tree = False
        self.checkAndDisable()
        self.progressbar.setValue(0)

    def generate_tree_result(self, result):
        self.tree_map = result
        self.FileTree.showTree(self.tree_map)


    def saveTreeMapFile(self):
        if self.tree_map is None:
            self.errorWindow('Error', 'No file tree map to save.')
            return

        path = asksaveasfile(title='Save file map', initialfile = 'Untitled.json', defaultextension=".json",filetypes=[("All Files","*.*")])

        if path is None:
            return

        try:
           jsonString = json.dumps(self.tree_map)
           path.write(jsonString)
        except:
           self.errorWindow('Error', 'Error while saving.')

        path.close()

    def toolbarExtractAllClick(self):
          self.extractFile( self.FileTree.getCurrentTreeData() )

    def toolbarExtractSelectedClick(self):
          files = self.FileTree.getSelectedItemData()
          print(files)
          if files:
              self.extractFile(files)

    ###################### EXTRACT

    def extractFile(self, file):
        if self.canExtract() is False:
             return self.errorWindow('Error', 'Please select the data.pack and file tree first.')

        # treeToList(files)

        path = askdirectory(title='Select destination folder')

        if path == '':
            # User clicked cancel
            return print('operation aborted')

        self.checkAndDisable()

        # Pass the function to execute
        worker = Worker(ExtractFiles, path, self.pack_file, file, self.pack_decrypted) # Any other args, kwargs are passed to the run function

        pb = ProgressBar("Extracting...")
        pb.setWindowIcon(QtGui.QIcon("./ui/assets/icon.png"))

        # worker.signals.result.connect(self.extractResult)
        worker.signals.finished.connect(lambda: self.extract_finished(pb))
        worker.signals.progress.connect(lambda val: pb.setValue(val))
        worker.signals.error.connect(self.threadError)

        # Execute
        ThreadPool.start(worker)

    def extract_finished(self, pb):
        pb.close()
        self.checkAndDisable()

    def searchTreeMap(self):
        if self.tree_map is None:
            return

        w = self.search_bar.text().lower()

        if w == '':
            self.FileTree.showTree(self.tree_map)
            return

        ## Try and check if the user's regex is valid
        try:
            re.search( w, "")
        except:
            return self.errorWindow('Error', 'Search input is not a valid Regular Expression (RegEx)!')


        def recursive(list):
            for i in range(len(list) - 1, -1, -1):
                 if list[i]["type"] == "folder":
                      recursive(list[i]["children"])
                      if len(list[i]["children"]) == 0:
                          list.pop(i)
                 else:
                      if re.search( w, list[i]["name"]):
                           # pass
                           continue
                      else:
                           list.pop(i)

        list = copy.deepcopy(self.tree_map)
        recursive(list)
        self.FileTree.showTree(list)


    def toolbarCompareClick(self):
        path = askopenfilename(title='Select file map')
        if path != '':
            try:
                f = open(path)
                self.compareFileMaps(self.tree_map, json.load(f))
                self.checkAndDisable()
            except:
                self.errorWindow('Error', 'Error while parsing your file map.')



    def compareFileMaps(self, map1, map2):
        newFiles = 0
        deletedFiles = 0
        modifiedFiles = 0
        result = copy.deepcopy(map1)

        def searchList(list, name):
            res = []
            for index, item in enumerate(list):
                 if item["name"] == name:
                     res.append([item, index])

            if len(res) == 0:
                 return None
           
            return res

        def recursiveCompare1(list1, list2, parentRes):
            res = []
            for i in range(len(list1) - 1, -1, -1):
                item = list1[i]
                inList2 = searchList(list2, item["name"])

                if inList2 is None:
                    item["color"] = "green"
                    res.append(item)
                    continue
                
                if item["type"] == "folder":
                    recursiveCompare(item["children"], inList2[0][0]["children"], [])
                    if len( inList2[0][0]["children"] ) > 0:
                        for it in inList2[0][0]["children"]:
                            it["color"] = "red"
                        res.append( inList2[0][0] )
                    list2.pop( inList2[0][1] )
                else:
                    not_found = True
                    for file in inList2:
                        if file[0]["size"] == item["size"]:
                            not_found = False
                            list2.pop(file[1])
                            break
                    if not_found:
                        list2.pop(inList2[0][1])
                        item["color"] = "yellow"
                        res.append(item)
            
            parentRes = parentRes + res
            return parentRes

        def recursiveCompare(list1, list2, parent = None):
            for i in range(len(list1) - 1, -1, -1):
                    item = list1[i]
                    inList2 = searchList(list2, item["name"])

                    if inList2 is None:
                        # newFiles += 1
                        item["color"] = "green"
                        continue

                    if item["type"] == "folder":
                        beforeSize = item["size"]
                        beforeFiles = item["files"]
                        recursiveCompare(item["children"], inList2[0][0]["children"], item)

                        if parent:
                            parent["size"] -= beforeSize - item["size"]
                            parent["files"] -= beforeFiles - item["files"]

                        for file in inList2[0][0]["children"]:
                            file["color"] = "red"
                            item["children"].append(file)

                        list2.pop(inList2[0][1])
                        if len(item["children"]) == 0:
                            list1.pop(i)
                    else:
                        not_found = True
                        for file in inList2:
                            if file[0]["size"] == item["size"]:
                                not_found = False
                                if parent:
                                    parent["size"] -= item["size"]
                                    parent["files"] -= 1
                                list2.pop(file[1])
                                list1.pop(i)
                                break

                        if not_found:
                            list2.pop(inList2[0][1])
                            # modifiedFiles += 1
                            item["color"] = "yellow"
        
        try:
            recursiveCompare(result, map2)
        except Exception as err:
            print(err)
            return
        
        self.FileTree.showTree( result )
        