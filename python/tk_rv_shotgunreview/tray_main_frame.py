# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore, QtGui
from .tray_delegate import RvTrayDelegate

class TrayMainFrame(QtGui.QWidget):

    def __init__(self, parent):
        """
        Constructor
        """
        QtGui.QWidget.__init__(self, parent)

        # make sure this widget isn't shown
        self.setVisible(True)
        self.tray_dock = parent
        self.tray_model = None
        self.tray_list = None
        self.tray_delegate = None
        self.tray_proxyModel = None
        
        # set up the UI
        self.init_ui()
    
    def init_ui(self):
        self.setMinimumSize(QtCore.QSize(1255,140))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)

        self.tray_frame_vlayout = QtGui.QVBoxLayout(self)

        # tray button bar
        self.tray_button_bar = QtGui.QFrame(self.tray_dock)
        self.tray_button_bar.setStyleSheet('QFrame { border: 1px solid #ff0000; padding: 1px; } QPushButton { margin: 0px; }')
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)

        self.tray_button_bar.setSizePolicy(sizePolicy)

        self.tray_button_bar_hlayout = QtGui.QHBoxLayout(self.tray_button_bar)
        self.tray_button_bar_hlayout.setContentsMargins(0, 0, 0, 0)
        
        self.tray_button_one = QtGui.QPushButton()
        self.tray_button_one.setStyleSheet('QPushButton { border: 1px solid #00ff00; margin: 0px;}')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_one)

        self.tray_button_two = QtGui.QPushButton()
        self.tray_button_two.setStyleSheet('QPushButton { border: 1px solid #00fff0; }')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_two)

        self.tray_button_bar_hlayout.addStretch(1)

        self.tray_button_entire_cut = QtGui.QPushButton()
        self.tray_button_entire_cut.setText('Entire Cut')
        #self.tray_button_three.setStyleSheet('QPushButton { border: 1px solid #000ff0; }')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_entire_cut)
        

        self.tray_button_mini_cut = QtGui.QPushButton()
        self.tray_button_mini_cut.setText('Mini Cut')
        #self.tray_button_four.setStyleSheet('QPushButton { border: 1px solid #f00ff0; }')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_mini_cut)

        # move this above
        # self.tray_button_entire_cut.clicked.connect(self.on_entire_cut)
        # move this above?
        # self.tray_button_mini_cut.clicked.connect(self.on_mini_cut)

        self.tray_button_bar_hlayout.addStretch(1)

        self.tray_button_five = QtGui.QPushButton()
        self.tray_button_five.setStyleSheet('QPushButton { border: 1px solid #f0f000; }')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_five)

        self.tray_frame_vlayout.addWidget(self.tray_button_bar)
        self.tray_frame_vlayout.setStretchFactor(self.tray_button_bar, 1)
        

        # QListView ##########################
        #####################################################################
        self.tray_list = QtGui.QListView()
        #self.tray_list.setSizePolicy(sizePolicy)
        self.tray_frame_vlayout.addWidget(self.tray_list)
        self.tray_frame_vlayout.setStretchFactor(self.tray_list, 1)
        
        from .tray_model import TrayModel
        self.tray_model = TrayModel(self.tray_list)
        from .tray_sort_filter import TraySortFilter
        self.tray_proxyModel =  TraySortFilter(self.tray_list)
        self.tray_proxyModel.setSourceModel(self.tray_model)
        self.tray_proxyModel.setDynamicSortFilter(True)

        self.tray_proxyModel.playhead_moved.connect( lambda rv_data: self.playhead_moved.emit(rv_data) )
        
        self.tray_list.setModel(self.tray_proxyModel)

        self.tray_delegate = RvTrayDelegate(self.tray_list)
        self.tray_list.setItemDelegate(self.tray_delegate)

        #self.tray_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        #self.tray_list.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.tray_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tray_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tray_list.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tray_list.setFlow(QtGui.QListView.LeftToRight)
        self.tray_list.setUniformItemSizes(True)
        
        self.tray_list.setMinimumSize(QtCore.QSize(1000,80))
        
        self.tray_list.setObjectName("tray_list")

        
        # move above
        #self.tray_model.data_refreshed.connect(self.on_data_refreshed)
        #self.tray_model.cache_loaded.connect(self.on_cache_loaded)
        #self.tray_list.clicked.connect(self.tray_clicked)
        #self.tray_list.activated.connect(self.tray_activated)
        #self.tray_list.doubleClicked.connect(self.tray_double_clicked)

        st = "QListView { border: none;}"
        self.setStyleSheet(st)


