from PyQt6.QtWidgets             import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QProgressBar, QFileDialog, QMessageBox, QMenu
from PyQt6.QtCore                import QSize, Qt, QThread
from PyQt6.QtGui                 import QAction
from app.constants               import IMG_FORMATS
from app.strings                 import translate
from app.settings                import getDefaultFilePromptPath, getAutomaticFilePreview
from app.util.file               import convert_size
from app.util.thread             import ThreadData
from app.util.exceptions         import OperationAbortedByUser
from app.pack                    import DataPack, NotDataPackZip
from app.extract                 import get_file
from gui.components.search_bar   import SearchBar
from gui.components.button       import Button
from gui.components.tree_view    import TreeViewTable, CustomQTreeWidgetItem
from gui.components.preview      import FileContentPreview
from gui.components.error_dialog import ErrorWindow
from gui.util.svg_icon           import QIcon_from_svg
from gui.components.progress_bar.ProgressBar import ProgressBar
from gui.util.thread_process     import QtThreadedProcess
import json

class CreateTab(QWidget):
    name: str = ''
    order: int = -99

    pack: DataPack = None
    toolbar: QToolBar = None
    tree: TreeViewTable = None
    is_generating_tree: bool = False

    disable_if_no_pack: list[QWidget] = []
    disable_if_no_tree: list[QWidget] = []
    disable_if_tree_gen: list[QWidget] = []
    
    search_bar: SearchBar = None
    progressbar: QProgressBar = None
    compare_btn: QAction = None


    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.name = translate('file_tree')
        self.setObjectName('FileTreeTab')
        APP = QApplication.instance()

        main_view = QMainWindow(parent)
        vertical_box = QVBoxLayout()
        buttons_line = QHBoxLayout()
        progressbar_layout = QHBoxLayout()

        self.setLayout(vertical_box)
        vertical_box.addLayout(buttons_line)
        vertical_box.addLayout(progressbar_layout)
        vertical_box.addWidget(main_view)

        main_widget = QWidget()
        main_widget.setLayout(QHBoxLayout())
        main_widget.layout().setSpacing(5)
        main_widget.layout().setContentsMargins(0,4,0,0)


        tree = TreeViewTable()
        self.tree = tree
        tree.setColumns([translate('name'), translate('type'), translate('size'), f'{translate("files_in_folder")} / {translate("offset")}'])
        tree.setDictToColumn( self.tree_file_to_column )
        tree.dargdrop.connect(self._extract_sync)
        tree.widget().customContextMenuRequested.connect(self.tree_context_menu)
        tree.widget().itemDoubleClicked.connect(self.doubleClickTreeItemToPreview)
        tree.widget().currentItemChanged.connect(self.automaticFilePreview)
        main_widget.layout().addWidget(tree.widget(), stretch=1)

        preview = FileContentPreview()
        preview.setVisible(False)
        self.previewWidget = preview
        main_widget.layout().addWidget(preview, stretch=1)

        
        toolbar = QToolBar(self)
        toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(32,32))
        toolbar.setBaseSize(0, 32)
        toolbar.setDisabled(False)
        self.toolbar = toolbar

        main_view.addToolBar(toolbar)
        # main_view.setCentralWidget(tree.widget())
        main_view.setCentralWidget(main_widget)

        button_action = QAction(QIcon_from_svg('content-save-outline.svg', APP.ThemeColors.TOOLBAR_ICON_COLOR), translate('btn_save'), toolbar)
        button_action.setToolTip( translate('tooltip_save_tree') )
        button_action.triggered.connect(self.prompt_select_save_tree_path)
        button_action.setShortcut('Ctrl+S')
        button_action.setDisabled(True)
        self.disable_if_no_tree.append(button_action)
        toolbar.addAction(button_action)

        button_action = QAction(QIcon_from_svg('file-compare.svg', APP.ThemeColors.TOOLBAR_ICON_COLOR), translate('btn_compare_tree'), toolbar)
        button_action.setToolTip( translate('tooltip_compare_tree') )
        button_action.triggered.connect(self.prompt_select_compare_tree_path)
        button_action.setDisabled(True)
        self.disable_if_no_tree.append(button_action)
        toolbar.addAction(button_action)
        self.compare_btn = button_action
    
        toolbar.addSeparator()

        button_action = QAction(QIcon_from_svg('checkbox-multiple-marked-outline.svg', APP.ThemeColors.TOOLBAR_ICON_COLOR), translate('btn_extract_selected'), toolbar)
        button_action.setToolTip( translate('tooltip_extract_selected') )
        button_action.triggered.connect(self.extract_selected_only)
        button_action.setDisabled(True)
        self.disable_if_no_tree.append(button_action)
        toolbar.addAction(button_action)

        button_action = QAction(QIcon_from_svg('file-image-outline.svg', APP.ThemeColors.TOOLBAR_ICON_COLOR), translate('btn_img_only'), toolbar)
        button_action.setToolTip( translate('tooltip_img_only').format(', '.join(IMG_FORMATS)) )
        button_action.triggered.connect(self.extract_all_images)
        button_action.setDisabled(True)
        self.disable_if_no_tree.append(button_action)
        toolbar.addAction(button_action)

        button_action = QAction(QIcon_from_svg('package-variant.svg', APP.ThemeColors.TOOLBAR_ICON_COLOR), translate('btn_all'), toolbar)
        button_action.setToolTip( translate('tooltip_extract_all') )
        button_action.triggered.connect(self.extract_all)
        button_action.setDisabled(True)
        button_action.setCheckable(True)
        self.disable_if_no_tree.append(button_action)
        toolbar.addAction(button_action)


        self.progressbar = QProgressBar(self)
        self.progressbar.setValue(0)
        self.progressbar.setFormat("%p%")
        self.progressbar.setTextVisible(False)
        self.progressbar.setObjectName("progressbar")
        self.progressbar.setHidden(True)
        progressbar_layout.addWidget(self.progressbar)


        button = Button(self, text=translate('select_pack'), pointer=True, minimum_width=150)
        button.clicked.connect(self.select_data_pack)
        # button.clicked.connect(self.parent().get_progress_bar_window().new)
        buttons_line.addWidget(button)
        self.disable_if_tree_gen.append(button)

        button = Button(self, text=translate('generate_file_tree'), pointer=True, minimum_width=150, disabled=True)
        button.clicked.connect(self.start_tree_generating)
        buttons_line.addWidget(button)
        self.disable_if_no_pack.append(button)
        self.disable_if_tree_gen.append(button)

        button = Button(self, text=translate('load_file_tree'), pointer=True, minimum_width=150, disabled=True)
        button.clicked.connect(self.select_tree_json)
        # button.clicked.connect(self.parent().get_progress_bar_window().new)
        button.setProperty('class', 'red-button')
        buttons_line.addWidget(button)
        self.disable_if_no_pack.append(button)
        self.disable_if_tree_gen.append(button)

        buttons_line.addStretch()

        self.search_bar = SearchBar(self, placeholder=translate('search'))
        self.search_bar.search.connect( self.search_bar_value_changed )
        self.search_bar.setMaximumWidth(350)
        self.disable_if_no_tree.append(self.search_bar)
        buttons_line.addWidget(self.search_bar)

    def doubleClickTreeItemToPreview(self, item: CustomQTreeWidgetItem):
        if item.childCount() == 0:
            self.showTreeItemPreview(item)

    def automaticFilePreview(self):
        if getAutomaticFilePreview() == True:
            self.showTreeItemPreview(self.tree.tree.currentItem())

    def showTreeItemPreview(self, item:CustomQTreeWidgetItem, windowed=False):
        if item:
            file = item.getJSONData()
            is_supported = self.previewWidget.is_preview_supported( file.get('format') )

            if not is_supported:
                return self.previewWidget.setHidden(True)

            self.previewWidget.display(
                file,
                lambda: get_file(file, pack=self.pack),
                windowed=windowed
            )


    def errorWindow(self, title, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(message)
        msg.resize(400, 300)
        msg.setWindowTitle(title)
        msg.exec()

    @staticmethod
    def tree_file_to_column(data):
        if data["type"] == 'folder':
            return [data["name"], translate('folder'), convert_size(data["size"]), str(data["files"]) + ' files']
        else:
            return [data["name"], data["format"].upper(), convert_size(data["size"]), str(data["offset"])]

    def search_bar_value_changed(self, value):
        self.tree.setQuery(value)

    def update_btn_state(self):
        for widget in self.disable_if_no_pack:
            widget.setDisabled( not self.pack )

        for widget in self.disable_if_no_tree:
            widget.setDisabled( not self.pack or not self.pack.tree() )

        for widget in self.disable_if_tree_gen:
            widget.setDisabled( self.is_generating_tree )


    @staticmethod
    def tree_drag_and_drop(pack, files, path):
        thread_data = ThreadData()
        progwindow = ProgressBar()
        Qthread = QThread(progwindow)
        progwindow.moveToThread(Qthread)
        Qthread.run()
        p = progwindow.new()
        p.destroyed.connect(lambda: thread_data.stop())
        thread_data.onprogress(lambda v: p.setValue(v[0]))
        thread_data.onfinished(lambda: p.setLabel('Done'))
        # progwindow.moveToThread(QThread)
        pack.extract(files, path, thread_data)
        progwindow.close()
        Qthread.quit()

    def tree_context_menu(self, position):
        options = [
            [translate('extract'), self.extract_selected_only]
        ]
        currItem: CustomQTreeWidgetItem = self.tree.tree.currentItem()

        if currItem:
            data = currItem.getJSONData()

            file_extension = data.get('format', None)

            if self.previewWidget.is_preview_supported(file_extension):
                options.append(['Preview', lambda: self.showTreeItemPreview(currItem)])
                options.append(['Preview (Windowed)', lambda: self.showTreeItemPreview(currItem, windowed=True)])

            if file_extension in IMG_FORMATS:
                options.append(['View Image', lambda: self.view_image(data)])

            menu = QMenu(self.tree.tree)
            menu.setLayout(QVBoxLayout())
            for option in options:
                menu.addAction(option[0], option[1])

            menu.exec(self.tree.tree.viewport().mapToGlobal(position))

    def view_image(self, file):
        try:
            from PIL import Image
            _bytes = get_file(file, self.pack)
            img = Image.open( _bytes ) # _bytes should be a custom ByteArray with seek and tell, no need to wrap in BytesIO
            img.show()
        except ImportError:
            self.errorWindow('Missing Optional Module', 'PIL Module is missing!\nIf you want to use this function please run "pip install pillow" first!')
        except Exception as e:
            print(f'[View Image] {e}')

    def select_data_pack(self):
        fname, ext = QFileDialog.getOpenFileName(
            self,
            translate('select_decrypted_pack'),
            getDefaultFilePromptPath(),
            "Pack (*.pack *.zip *.tar *.ssra);;", # ;; to allow all files
        )
        if fname:
            try:
                pack = DataPack(fname)
                tree_data = pack.tree()
                # self.tree.write_temp_files = pack.extract # lambda *args: self.tree_drag_and_drop(pack, *args) # use this for the drag and drop
                if self.tree:
                    self.tree.clearTree()
                    self.tree.showTree(tree_data)
                    self.update_compare_icon()
                if self.pack: # Clean up previous patch
                    self.pack.destroy()
                self.pack = pack
            except NotDataPackZip:
                ErrorWindow('Error', 'Unknown data.pack type.\nMake sure it\'s a valid E7 data.pack')
            except Exception as e:
                print(e)
            self.update_btn_state()
        
    def select_tree_json(self):
        fname, ext = QFileDialog.getOpenFileName(
            self,
            translate('select_decrypted_pack'),
            getDefaultFilePromptPath(),
            "Epic Seven data pack (*.json);;",
        )

        if fname:
            try:
                self.pack.load_json_tree_from_path(fname)
                self.tree.clearTree()
                self.update_compare_icon()
                tree = self.pack.tree()
                if tree:
                    self.tree.showTree(tree)
            except Exception as e:
                ErrorWindow('Error', str(e))
            self.update_btn_state()

    def prompt_select_save_tree_path(self):
        if not self.pack or not self.pack.tree():
            return ErrorWindow('Error', 'No tree to save')
        
        fname, ext = QFileDialog.getSaveFileName(
            self,
            translate('select_decrypted_pack'),
            getDefaultFilePromptPath(),
            "JSON file (*.json);;",
        )

        if fname:
            with open(fname, 'w') as f:
                f.write(json.dumps(self.pack.tree()))

    def prompt_select_compare_tree_path(self):
        if self.tree.isComparing():
            self.tree.stopComparing()
        else:
            fname, ext = QFileDialog.getOpenFileName(
                self,
                translate('select_decrypted_pack'),
                getDefaultFilePromptPath(),
                "File Tree (*.json);;", #;; to allow *.*
            )
            if fname:
                f = open(fname)
                tree=json.loads(f.read())
                self.tree.setCompare(tree)

        self.update_compare_icon()

    def update_compare_icon(self):
        APP = QApplication.instance()
        if self.tree.isComparing():
            self.compare_btn.setIcon(QIcon_from_svg('close.svg', APP.ThemeColors.TOOLBAR_ICON_COLOR))
            self.compare_btn.setText(translate('btn_compare_tree_stop'))
            self.compare_btn.setChecked(True)
        else:
            self.compare_btn.setIcon(QIcon_from_svg('file-compare.svg', APP.ThemeColors.TOOLBAR_ICON_COLOR))
            self.compare_btn.setText(translate('btn_compare_tree'))
            self.compare_btn.setChecked(False)


    def thread_process_error(self, tuple_data, tuple_error):
        a,b,c = tuple_error
        if a == OperationAbortedByUser:
            pass
        else:
            self.errorWindow('Error', str(b))

    def extract_selected_only(self):
        selected = self.tree.fileTreeJsonFromSelection()
        if len(selected) == 0:
            return ErrorWindow('Error', 'No files selected!\nPlease select at least one file from the tree view.')
        
        dest_path = QFileDialog.getExistingDirectory(
            self,
            translate('select_decrypted_pack'),
            getDefaultFilePromptPath()
        )

        if dest_path:
            self._extract( dest_path, selected )

    def extract_all_images(self):
        dest_path = QFileDialog.getExistingDirectory(
            self,
            translate('select_decrypted_pack'),
            getDefaultFilePromptPath()
        )

        if dest_path:
            self._extract( dest_path, self.tree.fileTreeJsonFromTreeItemsWithFormatFilter(formats=IMG_FORMATS) )

    def extract_all(self):
        dest_path = QFileDialog.getExistingDirectory(
            self,
            translate('select_decrypted_pack'),
            getDefaultFilePromptPath()
        )

        if dest_path:
            self._extract(dest_path, self.tree.fileTreeJsonFromView(), translate('extracting_all'))

    def _extract_sync(self, files, path):
        '''
            This will freeze the ui until it's done
        '''
        t = ThreadData()
        t.onprogress = lambda a: print(a) # Show the percentage update in the console
        self.pack.extract(files, path, thread=t)

    def _extract(self, dest_path, files, label = None):
        '''
            Threaded extract process
        '''
        worker = QtThreadedProcess(self.pack, self.pack.extract, files, dest_path)
        # worker = QtThreadedProcess(self.pack, self.extract_from_tree_view, self.pack, self.tree, dest_path)
        bar: ProgressBar = self.nativeParentWidget().get_progress_bar_window().new(0, label)
        bar.destroyed.connect( worker.stop )
        # Stop if window is closed
        # c = self.destroyed.connect( bar.remove ) # This works but sometimes it triggers "RuntimeError: wrapped C/C++ object of type WorkerSignals has been deleted"
        worker.onprogress = (lambda v: (bar.setValue(v[0]), bar.setLabel(v[1]))) if not label else (lambda v: bar.setValue(v[0]))
        worker.onfinished = lambda: (bar.remove())#, self.disconnect(c))
        worker.onerror = self.thread_process_error
        worker.run()

    def start_tree_generating(self):
        if not self.pack:
            return ErrorWindow('Error', 'No data.pack loaded')

        self.progressbar.setValue(0)
        self.pack.set_tree(None)
        self.tree.clearTree()
        self.update_compare_icon()
        self.is_generating_tree = True
        self.update_btn_state()
        self.progressbar.setHidden(False)
        worker = QtThreadedProcess(self.pack, self.pack.build_tree)
        QApplication.instance().property('MainWindow').closed.connect(worker.stop) # Stop running as soon as the main window is closed
        worker.onprogress = self.generation_update
        worker.onfinished = self.generation_finish
        worker.onerror = self.thread_process_error
        worker.onresult = self.generation_complete
        # p: ProgressBar = self.nativeParentWidget().get_progress_bar_window()
        # progress = p.new()
        # progress.setLabel('Generate tree')
        # progress.destroyed.connect(lambda *args: worker.stop())
        worker.run()
        # self.is_generating_tree = not self.is_generating_tree

    def generation_update(self, value: tuple):
        self.progressbar.setValue(*value)

    def generation_finish(self, tuple_data):
        self.is_generating_tree = False
        self.progressbar.setHidden(True)
        self.update_btn_state()

    def generation_complete(self, tuple_data, result):
        self.tree.showTree(self.pack.tree())














    # This works but changing the file tree view will also change the result of this method while it's running 
    # @pyqtSlot()
    # def extract_from_tree_view(self, pack: DataPack, treeWidget: TreeViewTable, path, thread = None):
    #     import os
    #     file_size = 1000000000000
    #     processed_files = 0
    #     progress_percentage = -1
    #     mmap = pack.mmap()

    #     def recursive(item: CustomQTreeWidgetItem, path):
    #         nonlocal file_size, processed_files, progress_percentage, thread

    #         if item.isHidden():
    #             return
    #         else:
    #             if thread.is_stopping():
    #                 raise Exception()

    #             childCount = item.childCount()
    #             if childCount > 0:
    #                 # Folder
    #                 rel_path = os.path.join(path, item.getJSONData()['name'])
    #                 os.makedirs( rel_path, exist_ok=True )
    #                 for i in range( childCount ):
    #                     recursive( item.child(i), rel_path )
    #             else:
    #                 file = item.getJSONData()
    #                 _pfiles = processed_files + file['size']
    #                 _percentage = round( _pfiles / file_size *100)
    #                 processed_files = _pfiles
    #                 if _percentage > progress_percentage:
    #                     thread.progress((progress_percentage,file['full_path'])) # keep the comma 
    #                     progress_percentage = _percentage
    #                     print(f'Still running {_percentage}')

    #                 mmap.seek(file['offset'])
    #                 data = pack.read_bytes(mmap, file['offset'], file['size'])
    #                 file_path = os.path.join(path, file['name'])

    #                 file = FileDescriptor(data=data, path=file_path, tree_file=file, pack=pack, thread=thread)

    #                 call_hooks('before', file)

    #                 if file.path:
    #                     with open(file.path, 'wb') as f:
    #                         f.write(file.bytes)
    #                         file.written = True

    #                 call_hooks('after', file)

    #     for i in range(treeWidget.tree.topLevelItemCount()):
    #         recursive(treeWidget.tree.topLevelItem(i), path)

    #     mmap.close()