#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Miyamoto! Level Editor - New Super Mario Bros. U Level Editor
# Copyright (C) 2009-2021 Treeki, Tempus, angelsl, JasonP27, Kinnay,
# MalStar1000, RoadrunnerWMC, MrRean, Grop, AboodXD, Gota7, John10v10,
# mrbengtsson

# This file is part of Miyamoto!.

# Miyamoto! is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Miyamoto! is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Miyamoto!.  If not, see <http://www.gnu.org/licenses/>.


################################################################
################################################################

############ Imports ############

import os

from PyQt5 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt

from bytes import bytes_to_string, to_bytes
import globals
from items import ZoneItem
from misc import HexSpinBox, BGName, setting
from strings import MiyamotoTranslation
from ui import MiyamotoTheme, toQColor, GetIcon, createHorzLine
from widgets import LoadingTab, TilesetsTab
from verifications import SetDirty

#################################


class InputBox(QtWidgets.QDialog):
    Type_TextBox = 1
    Type_SpinBox = 2
    Type_HexSpinBox = 3

    def __init__(self, type=Type_TextBox):
        super().__init__()

        self.label = QtWidgets.QLabel('-')
        self.label.setWordWrap(True)

        if type == InputBox.Type_TextBox:
            self.textbox = QtWidgets.QLineEdit()
            widget = self.textbox
        elif type == InputBox.Type_SpinBox:
            self.spinbox = QtWidgets.QSpinBox()
            widget = self.spinbox
        elif type == InputBox.Type_HexSpinBox:
            self.spinbox = HexSpinBox()
            widget = self.spinbox

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(widget)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)


class AboutDialog(QtWidgets.QDialog):
    """
    The About info for Miyamoto
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('AboutDlg', 0))
        self.setWindowIcon(GetIcon('help'))

        # Open the readme file
        f = open('readme.md', 'r')
        readme = f.read()
        f.close()
        del f

        # Logo
        logo = QtGui.QPixmap('miyamotodata/about.png')
        logoLabel = QtWidgets.QLabel()
        logoLabel.setPixmap(logo)
        logoLabel.setContentsMargins(16, 4, 32, 4)

        # Description
        description = '<html><head><style type=\'text/CSS\'>'
        description += 'body {font-family: Calibri}'
        description += '.main {font-size: 12px}'
        description += '</style></head><body>'
        description += '<center><h1><i>Miyamoto!</i> Level Editor</h1><div class=\'main\'>'
        description += '<i>Miyamoto! Level Editor</i> is a fork of Reggie! Level Editor, an open-source global project started by Treeki in 2010 that aimed to bring New Super Mario Bros. Wii&trade; levels. Now in later years, brings you New Super Mario Bros. U&trade;!<br>'
        description += 'Interested? Check out <a href=\'https://github.com/aboood40091/Miyamoto\'>the Github repository</a> for updates and related downloads, or <a href=\'https://discord.gg/AvFEHpp\'>our Discord group</a> to get in touch with the developers.<br>'
        description += '</div></center></body></html>'

        # Description label
        descLabel = QtWidgets.QLabel()
        descLabel.setText(description)
        descLabel.setMinimumWidth(512)
        descLabel.setWordWrap(True)

        # Readme.md viewer
        readmeView = QtWidgets.QPlainTextEdit()
        readmeView.setPlainText(readme)
        readmeView.setReadOnly(True)

        # Buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)

        # Main layout
        L = QtWidgets.QGridLayout()
        L.addWidget(logoLabel, 0, 0, 2, 1)
        L.addWidget(descLabel, 0, 1)
        L.addWidget(readmeView, 1, 1)
        L.addWidget(buttonBox, 2, 0, 1, 2)
        L.setRowStretch(1, 1)
        L.setColumnStretch(1, 1)
        self.setLayout(L)


class ObjectShiftDialog(QtWidgets.QDialog):
    """
    Lets you pick an amount to shift selected items by
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('ShftItmDlg', 0))
        self.setWindowIcon(GetIcon('move'))

        self.XOffset = QtWidgets.QSpinBox()
        self.XOffset.setRange(-16384, 16383)

        self.YOffset = QtWidgets.QSpinBox()
        self.YOffset.setRange(-8192, 8191)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        moveLayout = QtWidgets.QFormLayout()
        offsetlabel = QtWidgets.QLabel(globals.trans.string('ShftItmDlg', 2))
        offsetlabel.setWordWrap(True)
        moveLayout.addWidget(offsetlabel)
        moveLayout.addRow(globals.trans.string('ShftItmDlg', 3), self.XOffset)
        moveLayout.addRow(globals.trans.string('ShftItmDlg', 4), self.YOffset)

        moveGroupBox = QtWidgets.QGroupBox(globals.trans.string('ShftItmDlg', 1))
        moveGroupBox.setLayout(moveLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(moveGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class ObjectTilesetSwapDialog(QtWidgets.QDialog):
    """
    Lets you pick tilesets to swap objects to
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle('Swap Objects\' Tilesets')
        self.setWindowIcon(GetIcon('swap'))

        # Create widgets
        self.FromTS = QtWidgets.QSpinBox()
        self.FromTS.setRange(1, 4)

        self.ToTS = QtWidgets.QSpinBox()
        self.ToTS.setRange(1, 4)

        # Swap layouts
        swapLayout = QtWidgets.QFormLayout()

        swapLayout.addRow('From tileset:', self.FromTS)
        swapLayout.addRow('To tileset:', self.ToTS)

        self.DoExchange = QtWidgets.QCheckBox('Exchange (perform 2-way conversion)')

        # Buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(swapLayout)
        mainLayout.addWidget(self.DoExchange)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class ObjectTypeSwapDialog(QtWidgets.QDialog):
    """
    Lets you pick object types to swap objects to
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle('Swap Objects\' Types')
        self.setWindowIcon(GetIcon('swap'))

        # Create widgets
        self.FromType = QtWidgets.QSpinBox()
        self.FromType.setRange(0, 255)

        self.ToType = QtWidgets.QSpinBox()
        self.ToType.setRange(0, 255)

        self.FromTileset = QtWidgets.QSpinBox()
        self.FromTileset.setRange(1, 4)

        self.ToTileset = QtWidgets.QSpinBox()
        self.ToTileset.setRange(1, 4)

        self.DoExchange = QtWidgets.QCheckBox('Exchange (perform 2-way conversion)')

        # Swap layout
        swapLayout = QtWidgets.QGridLayout()

        swapLayout.addWidget(QtWidgets.QLabel('From tile type:'), 0, 0)
        swapLayout.addWidget(self.FromType, 0, 1)

        swapLayout.addWidget(QtWidgets.QLabel('From tileset:'), 1, 0)
        swapLayout.addWidget(self.FromTileset, 1, 1)

        swapLayout.addWidget(QtWidgets.QLabel('To tile type:'), 0, 2)
        swapLayout.addWidget(self.ToType, 0, 3)

        swapLayout.addWidget(QtWidgets.QLabel('To tileset:'), 1, 2)
        swapLayout.addWidget(self.ToTileset, 1, 3)

        # Buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(swapLayout)
        mainLayout.addWidget(self.DoExchange)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class MetaInfoDialog(QtWidgets.QDialog):
    """
    Allows the user to enter in various meta-info to be kept in the level for display
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('InfoDlg', 0))
        self.setWindowIcon(GetIcon('info'))

        title = globals.Area.Metadata.strData('Title')
        author = globals.Area.Metadata.strData('Author')
        group = globals.Area.Metadata.strData('Group')
        website = globals.Area.Metadata.strData('Website')
        creator = globals.Area.Metadata.strData('Creator')
        password = globals.Area.Metadata.strData('Password')
        if title is None: title = '-'
        if author is None: author = '-'
        if group is None: group = '-'
        if website is None: website = '-'
        if creator is None: creator = '(unknown)'
        if password is None: password = ''

        self.levelName = QtWidgets.QLineEdit()
        self.levelName.setMaxLength(128)
        self.levelName.setReadOnly(True)
        self.levelName.setMinimumWidth(320)
        self.levelName.setText(title)

        self.Author = QtWidgets.QLineEdit()
        self.Author.setMaxLength(128)
        self.Author.setReadOnly(True)
        self.Author.setMinimumWidth(320)
        self.Author.setText(author)

        self.Group = QtWidgets.QLineEdit()
        self.Group.setMaxLength(128)
        self.Group.setReadOnly(True)
        self.Group.setMinimumWidth(320)
        self.Group.setText(group)

        self.Website = QtWidgets.QLineEdit()
        self.Website.setMaxLength(128)
        self.Website.setReadOnly(True)
        self.Website.setMinimumWidth(320)
        self.Website.setText(website)

        self.Password = QtWidgets.QLineEdit()
        self.Password.setMaxLength(128)
        self.Password.textChanged.connect(self.PasswordEntry)
        self.Password.setMinimumWidth(320)

        self.changepw = QtWidgets.QPushButton(globals.trans.string('InfoDlg', 1))

        if password != '':
            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.addButton(self.changepw, buttonBox.ActionRole)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.changepw.clicked.connect(self.ChangeButton)
        self.changepw.setDisabled(True)

        self.lockedLabel = QtWidgets.QLabel(globals.trans.string('InfoDlg', 2))

        infoLayout = QtWidgets.QFormLayout()
        infoLayout.addWidget(self.lockedLabel)
        infoLayout.addRow(globals.trans.string('InfoDlg', 3), self.Password)
        infoLayout.addRow(globals.trans.string('InfoDlg', 4), self.levelName)
        infoLayout.addRow(globals.trans.string('InfoDlg', 5), self.Author)
        infoLayout.addRow(globals.trans.string('InfoDlg', 6), self.Group)
        infoLayout.addRow(globals.trans.string('InfoDlg', 7), self.Website)

        self.PasswordLabel = infoLayout.labelForField(self.Password)

        levelIsLocked = password != ''
        self.lockedLabel.setVisible(levelIsLocked)
        self.PasswordLabel.setVisible(levelIsLocked)
        self.Password.setVisible(levelIsLocked)

        infoGroupBox = QtWidgets.QGroupBox(globals.trans.string('InfoDlg', 8, '[name]', creator))
        infoGroupBox.setLayout(infoLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(infoGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.PasswordEntry('')

    def PasswordEntry(self, text):
        pswd = globals.Area.Metadata.strData('Password')
        if pswd is None: pswd = ''
        if text == pswd:
            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)
        else:
            self.levelName.setReadOnly(True)
            self.Author.setReadOnly(True)
            self.Group.setReadOnly(True)
            self.Website.setReadOnly(True)
            self.changepw.setDisabled(True)

    # To all would be crackers who are smart enough to reach here:
    #
    #   Make your own levels.
    #
    #
    #
    #       - The management
    #


    def ChangeButton(self):
        """
        Allows the changing of a given password
        """

        class ChangePWDialog(QtWidgets.QDialog):
            """
            Dialog
            """

            def __init__(self):
                super().__init__()
                self.setWindowTitle(globals.trans.string('InfoDlg', 9))
                self.setWindowIcon(GetIcon('info'))

                self.New = QtWidgets.QLineEdit()
                self.New.setMaxLength(64)
                self.New.textChanged.connect(self.PasswordMatch)
                self.New.setMinimumWidth(320)

                self.Verify = QtWidgets.QLineEdit()
                self.Verify.setMaxLength(64)
                self.Verify.textChanged.connect(self.PasswordMatch)
                self.Verify.setMinimumWidth(320)

                self.Ok = QtWidgets.QPushButton('OK')
                self.Cancel = QtWidgets.QDialogButtonBox.Cancel

                buttonBox = QtWidgets.QDialogButtonBox()
                buttonBox.addButton(self.Ok, buttonBox.AcceptRole)
                buttonBox.addButton(self.Cancel)

                buttonBox.accepted.connect(self.accept)
                buttonBox.rejected.connect(self.reject)
                self.Ok.setDisabled(True)

                infoLayout = QtWidgets.QFormLayout()
                infoLayout.addRow(globals.trans.string('InfoDlg', 10), self.New)
                infoLayout.addRow(globals.trans.string('InfoDlg', 11), self.Verify)

                infoGroupBox = QtWidgets.QGroupBox(globals.trans.string('InfoDlg', 12))

                infoLabel = QtWidgets.QVBoxLayout()
                infoLabel.addWidget(QtWidgets.QLabel(globals.trans.string('InfoDlg', 13)), 0, Qt.AlignCenter)
                infoLabel.addLayout(infoLayout)
                infoGroupBox.setLayout(infoLabel)

                mainLayout = QtWidgets.QVBoxLayout()
                mainLayout.addWidget(infoGroupBox)
                mainLayout.addWidget(buttonBox)
                self.setLayout(mainLayout)

            def PasswordMatch(self, text):
                self.Ok.setDisabled(self.New.text() != self.Verify.text() and self.New.text() != '')

        dlg = ChangePWDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.lockedLabel.setVisible(True)
            self.Password.setVisible(True)
            self.PasswordLabel.setVisible(True)
            pswd = str(dlg.Verify.text())
            globals.Area.Metadata.setStrData('Password', pswd)
            self.Password.setText(pswd)
            SetDirty()

            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)


class AreaOptionsDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose among various area options from tabs
    """

    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('AreaDlg', 0))
        self.setWindowIcon(GetIcon('area'))

        self.tabWidget = QtWidgets.QTabWidget()
        self.LoadingTab = LoadingTab()
        self.TilesetsTab = TilesetsTab()
        self.tabWidget.addTab(self.TilesetsTab, globals.trans.string('AreaDlg', 1))
        self.tabWidget.addTab(self.LoadingTab, globals.trans.string('AreaDlg', 2))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class ZonesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose among various from tabs
    """

    class ScrollArea(QtWidgets.QScrollArea):
        def __init__(self, widget=None, initialWidth=-1, initialHeight=-1):
            super().__init__()

            self.setWidgetResizable(True)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            deltaWidth = globals.app.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent)

            if widget:
                self.setWidget(widget)

                if initialWidth == -1:
                    initialWidth = widget.sizeHint().width()

                if initialHeight == -1:
                    initialHeight = widget.sizeHint().height()

            if initialWidth == -1:
                initialWidth = super().sizeHint().width()

            else:
                initialWidth += deltaWidth

            if initialHeight == -1:
                initialHeight = super().sizeHint().height()

            else:
                initialHeight += deltaWidth

            self.initialWidth = initialWidth
            self.initialHeight = initialHeight

        def sizeHint(self):
            return QtCore.QSize(self.initialWidth, self.initialHeight)

    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('ZonesDlg', 0))
        self.setWindowIcon(GetIcon('zones'))

        self.tabWidget = QtWidgets.QTabWidget()

        self.zoneTabs = []
        self.BGTabs = []
        for i, z in enumerate(globals.Area.zones):
            ZoneTabName = globals.trans.string('ZonesDlg', 3, '[num]', i + 1)
            tab = ZoneTab(z); tab.adjustSize()
            self.zoneTabs.append(tab)

            bgTab = BGTab(z.background)
            bgTab.adjustSize()
            self.BGTabs.append(bgTab)

            tabWidget = QtWidgets.QTabWidget()
            tabWidget.addTab(tab, 'Options')
            tabWidget.addTab(bgTab, 'Background')
            tabWidget.adjustSize()

            scrollArea = ZonesDialog.ScrollArea(tabWidget)
            self.tabWidget.addTab(scrollArea, ZoneTabName)

        if self.tabWidget.count() > 5:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, str(tab + 1))

        self.NewButton = QtWidgets.QPushButton(globals.trans.string('ZonesDlg', 4))
        self.DeleteButton = QtWidgets.QPushButton(globals.trans.string('ZonesDlg', 5))
        self.CloneButton = QtWidgets.QPushButton(globals.trans.string('ZonesDlg', 82))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.addButton(self.NewButton, buttonBox.ActionRole);
        buttonBox.addButton(self.DeleteButton, buttonBox.ActionRole);
        buttonBox.addButton(self.CloneButton, buttonBox.ActionRole);

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.NewButton.setEnabled(len(self.zoneTabs) < 8)
        self.NewButton.clicked.connect(self.NewZone)
        self.DeleteButton.clicked.connect(self.DeleteZone)
        self.CloneButton.setEnabled(len(self.zoneTabs) < 8)
        self.CloneButton.clicked.connect(self.CloneZone)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.resize(self.sizeHint())
        self.setFixedWidth(self.sizeHint().width())

    def NewZone(self):
        if len(self.zoneTabs) >= 15:
            result = QtWidgets.QMessageBox.warning(self, globals.trans.string('ZonesDlg', 6), globals.trans.string('ZonesDlg', 7),
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return

        id = len(self.zoneTabs)
        z = ZoneItem(256, 256, 448, 224, 0, 0, id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, (0, 0, 0, 0, 0, 0xF, 0, 0), (0, 0, 0, 0, to_bytes('Black', 16), 0))
        ZoneTabName = globals.trans.string('ZonesDlg', 3, '[num]', id + 1)
        tab = ZoneTab(z); tab.adjustSize()
        self.zoneTabs.append(tab)

        bgTab = BGTab(z.background)
        bgTab.adjustSize()
        self.BGTabs.append(bgTab)

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(tab, 'Options')
        tabWidget.addTab(bgTab, 'Background')
        tabWidget.adjustSize()

        scrollArea = ZonesDialog.ScrollArea(tabWidget)
        self.tabWidget.addTab(scrollArea, ZoneTabName)

        if self.tabWidget.count() > 5:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, str(tab + 1))

        self.NewButton.setEnabled(len(self.zoneTabs) < 8)
        self.CloneButton.setEnabled(len(self.zoneTabs) < 8)

        self.resize(self.sizeHint())
        self.setFixedWidth(self.sizeHint().width())

    def DeleteZone(self):
        curindex = self.tabWidget.currentIndex()
        tabamount = self.tabWidget.count()
        if tabamount == 0: return
        self.tabWidget.removeTab(curindex)

        for tab in range(curindex, tabamount):
            if self.tabWidget.count() < 6:
                self.tabWidget.setTabText(tab, globals.trans.string('ZonesDlg', 3, '[num]', tab + 1))
            else:
                self.tabWidget.setTabText(tab, str(tab + 1))

        self.zoneTabs.pop(curindex)
        self.BGTabs.pop(curindex)
        if self.tabWidget.count() < 6:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, globals.trans.string('ZonesDlg', 3, '[num]', tab + 1))

                # self.NewButton.setEnabled(len(self.zoneTabs) < 8)

        self.resize(self.sizeHint())
        self.setFixedWidth(self.sizeHint().width())

    def CloneZone(self):
        if len(self.zoneTabs) >= 15:
            result = QtWidgets.QMessageBox.warning(self, globals.trans.string('ZonesDlg', 6), globals.trans.string('ZonesDlg', 7),
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return
        
        z0 = self.zoneTabs[self.tabWidget.currentIndex()].zoneObj

        id = len(self.zoneTabs)
        z = ZoneItem(
            z0.objx, z0.objy, z0.width, z0.height, z0.modeldark, z0.terraindark, id, 0,
            z0.cammode, z0.camzoom, z0.unk1, z0.visibility, 0, z0.unk2, z0.camtrack, z0.unk3, z0.music, z0.sfxmod, 0, z0.type,
            (z0.yupperbound, z0.ylowerbound, z0.yupperbound2, z0.ylowerbound2, z0.entryid, z0.mpcamzoomadjust, z0.yupperbound3, z0.ylowerbound3),
            z0.background,
        )
        ZoneTabName = globals.trans.string('ZonesDlg', 3, '[num]', id + 1)
        tab = ZoneTab(z); tab.adjustSize()
        self.zoneTabs.append(tab)

        bgTab = BGTab(z.background)
        bgTab.adjustSize()
        self.BGTabs.append(bgTab)

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(tab, 'Options')
        tabWidget.addTab(bgTab, 'Background')
        tabWidget.adjustSize()

        scrollArea = ZonesDialog.ScrollArea(tabWidget)
        self.tabWidget.addTab(scrollArea, ZoneTabName)

        if self.tabWidget.count() > 5:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, str(tab + 1))

        self.NewButton.setEnabled(len(self.zoneTabs) < 8)
        self.CloneButton.setEnabled(len(self.zoneTabs) < 8)

        self.resize(self.sizeHint())
        self.setFixedWidth(self.sizeHint().width())


class ZoneTab(QtWidgets.QWidget):
    def __init__(self, z):
        super().__init__()

        self.zoneObj = z
        self.AutoChangingSize = False

        self.createDimensions(z)
        self.createVisibility(z)
        self.createBounds(z)
        self.createAudio(z)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.Dimensions)
        mainLayout.addWidget(self.Visibility)
        mainLayout.addWidget(self.Bounds)
        mainLayout.addWidget(self.Audio)
        self.setLayout(mainLayout)

    def createDimensions(self, z):
        self.Dimensions = QtWidgets.QGroupBox(globals.trans.string('ZonesDlg', 8))

        self.Zone_xpos = QtWidgets.QSpinBox()
        self.Zone_xpos.setRange(16, 65535)
        self.Zone_xpos.setToolTip(globals.trans.string('ZonesDlg', 10))
        self.Zone_xpos.setValue(z.objx)

        self.Zone_ypos = QtWidgets.QSpinBox()
        self.Zone_ypos.setRange(16, 65535)
        self.Zone_ypos.setToolTip(globals.trans.string('ZonesDlg', 12))
        self.Zone_ypos.setValue(z.objy)

        self.snapButton8 = QtWidgets.QPushButton(globals.trans.string('ZonesDlg', 78))
        self.snapButton8.clicked.connect(lambda: self.HandleSnapTo8x8Grid(z))

        self.snapButton16 = QtWidgets.QPushButton(globals.trans.string('ZonesDlg', 79))
        self.snapButton16.clicked.connect(lambda: self.HandleSnapTo16x16Grid(z))

        self.Zone_width = QtWidgets.QSpinBox()
        self.Zone_width.setRange(80, 65535)
        self.Zone_width.setToolTip(globals.trans.string('ZonesDlg', 14))
        self.Zone_width.setValue(z.width)
        self.Zone_width.valueChanged.connect(self.PresetDeselected)

        self.Zone_height = QtWidgets.QSpinBox()
        self.Zone_height.setRange(16, 65535)
        self.Zone_height.setToolTip(globals.trans.string('ZonesDlg', 16))
        self.Zone_height.setValue(z.height)
        self.Zone_height.valueChanged.connect(self.PresetDeselected)

        # Common retail zone presets
        # 416 x 224; Zoom Level 0 (used with minigames)
        # 448 x 224; Zoom Level 0 (used with boss battles)
        # 512 x 272; Zoom Level 0 (used in many, many places)
        # 560 x 304; Zoom Level 2
        # 608 x 320; Zoom Level 2 (actually 609x320; rounded it down myself)
        # 784 x 320; Zoom Level 2 (not added to list because it's just an expansion of 608x320)
        # 704 x 384; Zoom Level 3 (used multiple times; therefore it's important)
        # 944 x 448; Zoom Level 4 (used in 9-3 zone 3)
        self.Zone_presets_values = (
        '0: 416x224', '0: 448x224', '0: 512x272', '2: 560x304', '2: 608x320', '3: 704x384', '4: 944x448')

        self.Zone_presets = QtWidgets.QComboBox()
        self.Zone_presets.addItems(self.Zone_presets_values)
        self.Zone_presets.setToolTip(globals.trans.string('ZonesDlg', 18))
        self.Zone_presets.currentIndexChanged.connect(self.PresetSelected)
        self.PresetDeselected()  # can serve as an initializer for self.Zone_presets

        ZonePositionLayout = QtWidgets.QFormLayout()
        ZonePositionLayout.addRow(globals.trans.string('ZonesDlg', 9), self.Zone_xpos)
        ZonePositionLayout.addRow(globals.trans.string('ZonesDlg', 11), self.Zone_ypos)

        ZoneSizeLayout = QtWidgets.QFormLayout()
        ZoneSizeLayout.addRow(globals.trans.string('ZonesDlg', 13), self.Zone_width)
        ZoneSizeLayout.addRow(globals.trans.string('ZonesDlg', 15), self.Zone_height)
        ZoneSizeLayout.addRow(globals.trans.string('ZonesDlg', 17), self.Zone_presets)

        snapLayout = QtWidgets.QHBoxLayout()

        snapLayout.addWidget(self.snapButton8)
        snapLayout.addWidget(self.snapButton16)

        innerLayout = QtWidgets.QHBoxLayout()

        innerLayout.addLayout(ZonePositionLayout)
        innerLayout.addLayout(ZoneSizeLayout)

        verticalLayout = QtWidgets.QVBoxLayout()

        verticalLayout.addLayout(innerLayout)
        verticalLayout.addLayout(snapLayout)

        self.Dimensions.setLayout(verticalLayout)

    def HandleSnapTo8x8Grid(self, z):
        """
        Snaps the current zone to an 8x8 grid
        """
        left = self.Zone_xpos.value()
        top = self.Zone_ypos.value()
        right = left + self.Zone_width.value()
        bottom = top + self.Zone_height.value()

        if left % 8 < 4:
            left -= (left % 8)
        else:
            left += 8 - (left % 8)

        if top % 8 < 4:
            top -= (top % 8)
        else:
            top += 8 - (top % 8)

        if right % 8 < 4:
            right -= (right % 8)
        else:
            right += 8 - (right % 8)

        if bottom % 8 < 4:
            bottom -= (bottom % 8)
        else:
            bottom += 8 - (bottom % 8)

        if right <= left: right += 8
        if bottom <= top: bottom += 8

        right -= left
        bottom -= top

        if left < 16: left = 16
        if top < 16: top = 16
        if right < 80: right = 80
        if bottom < 16: bottom = 16

        if left > 65528: left = 65528
        if top > 65528: top = 65528
        if right > 65528: right = 65528
        if bottom > 65528: bottom = 65528

        self.Zone_xpos.setValue(left)
        self.Zone_ypos.setValue(top)
        self.Zone_width.setValue(right)
        self.Zone_height.setValue(bottom)

    def HandleSnapTo16x16Grid(self, z):
        """
        Snaps the current zone to a 16x16 grid
        """
        left = self.Zone_xpos.value()
        top = self.Zone_ypos.value()
        right = left + self.Zone_width.value()
        bottom = top + self.Zone_height.value()

        if left % 16 < 8:
            left -= (left % 16)
        else:
            left += 16 - (left % 16)

        if top % 16 < 8:
            top -= (top % 16)
        else:
            top += 16 - (top % 16)

        if right % 16 < 8:
            right -= (right % 16)
        else:
            right += 16 - (right % 16)

        if bottom % 16 < 8:
            bottom -= (bottom % 16)
        else:
            bottom += 16 - (bottom % 16)

        if right <= left: right += 16
        if bottom <= top: bottom += 16

        right -= left
        bottom -= top

        if left < 16: left = 16
        if top < 16: top = 16
        if right < 80: right = 80
        if bottom < 16: bottom = 16

        if left > 65520: left = 65520
        if top > 65520: top = 65520
        if right > 65520: right = 65520
        if bottom > 65520: bottom = 65520

        self.Zone_xpos.setValue(left)
        self.Zone_ypos.setValue(top)
        self.Zone_width.setValue(right)
        self.Zone_height.setValue(bottom)

    def createVisibility(self, z):
        self.Visibility = QtWidgets.QGroupBox(globals.trans.string('ZonesDlg', 19))

        self.Zone_vspotlight = QtWidgets.QCheckBox(globals.trans.string('ZonesDlg', 26))
        self.Zone_vspotlight.setToolTip(globals.trans.string('ZonesDlg', 27))

        self.Zone_vfulldark = QtWidgets.QCheckBox(globals.trans.string('ZonesDlg', 28))
        self.Zone_vfulldark.setToolTip(globals.trans.string('ZonesDlg', 29))

        self.Zone_visibility = QtWidgets.QComboBox()
        self.zv = z.visibility

        if self.zv & 0x10:
            self.Zone_vspotlight.setChecked(True)
        if self.zv & 0x20:
            self.Zone_vfulldark.setChecked(True)

        self.ChangeVisibilityList()
        self.Zone_vspotlight.clicked.connect(self.ChangeVisibilityList)
        self.Zone_vfulldark.clicked.connect(self.ChangeVisibilityList)

        self.zm = -1
        cammode = z.cammode
        if cammode > 7:
            cammode = 3

        camzoom = z.camzoom
        if cammode == 2:
            if camzoom > 9-1:
                camzoom = 0

        elif 1 < cammode < 6:
            if camzoom > 10-1:
                camzoom = 0

        else:
            if camzoom > 12-1:
                camzoom = 0

        self.Zone_cammodebuttongroup = QtWidgets.QButtonGroup()
        cammodebuttons = []
        for i, name, tooltip in [
                    (0, 'Normal', 'The standard camera mode, appropriate for most situations.'),
                    (3, 'Static Zoom', 'In this mode, the camera will not zoom out during multiplayer.'),
                    (4, 'Static Zoom, Y Tracking Only', 'In this mode, the camera will not zoom out during multiplayer, and will be centered horizontally in the zone.'),
                    (5, 'Static Zoom, Event-Controlled*', 'In this mode, the camera will not zoom out during multiplayer, and will use event-controlled camera settings.<br>' \
                        '*Event-controlled camera settings were removed in NSMBU and therefore this option is not usable.'),
                    (6, 'X Tracking Only', 'In this mode, the camera will only move horizontally. It will be aligned to the bottom edge of the zone.'),
                    (7, 'X Expanding Only', 'In this mode, the camera will only zoom out during multiplayer if the players are far apart horizontally.'),
                    (1, 'Y Tracking Only', 'In this mode, the camera will only move vertically. It will be centered horizontally in the zone.'),
                    (2, 'Y Expanding Only', 'In this mode, the camera will zoom out during multiplayer if the players are far apart vertically.'),
                ]:

            rb = QtWidgets.QRadioButton('%d: %s' % (i, name))
            rb.setToolTip('<b>' + name + ':</b><br>' + tooltip)
            self.Zone_cammodebuttongroup.addButton(rb, i)
            cammodebuttons.append(rb)

            if i == cammode:
                rb.setChecked(True)

            rb.clicked.connect(self.ChangeCamModeList)

        self.Zone_screenheights = QtWidgets.QComboBox()
        self.Zone_screenheights.setToolTip("<b>Screen Heights:</b><br>Selects screen heights (in blocks) the camera can use during multiplayer. " \
                                           "The camera will zoom out if the players are too far apart, and zoom back in when they get closer together.<br>" \
                                           "If the screen height specified is larger than the zone height (in blocks), the zone height will be used as the screen height instead.<br><br>" \
                                           "In single-player, only the smallest height will be used.<br><br>" \
                                           "Value of 00.0 means the actual value is not known and needs further testing.<br><br>" \
                                           "Options marked with * or ** are glitchy if zone bounds are set to 0; see the Upper/Lower Bounds tooltips for more info.<br>" \
                                           "Options marked with ** are also unplayably glitchy in multiplayer.")

        self.ChangeCamModeList()
        self.Zone_screenheights.setCurrentIndex(camzoom)

        directionmodeValues = globals.trans.stringList('ZonesDlg', 38)
        self.Zone_directionmode = QtWidgets.QComboBox()
        self.Zone_directionmode.addItems(directionmodeValues)
        self.Zone_directionmode.setToolTip(globals.trans.string('ZonesDlg', 40))
        self.Zone_directionmode.setCurrentIndex(z.camtrack if z.camtrack < 9 else 0)

        self.Zone_camunk1 = QtWidgets.QSpinBox()
        self.Zone_camunk1.setRange(0, 255)
        self.Zone_camunk1.setToolTip("It is unknown what this value does.")
        self.Zone_camunk1.setValue(z.unk1)

        self.Zone_camunk2 = QtWidgets.QSpinBox()
        self.Zone_camunk2.setRange(0, 255)
        self.Zone_camunk2.setToolTip("Value looks to be unused in the game code.")
        self.Zone_camunk2.setValue(z.unk2)

        self.Zone_camunk3 = QtWidgets.QSpinBox()
        self.Zone_camunk3.setRange(0, 255)
        self.Zone_camunk3.setToolTip("This is used as \"Progress Path ID\" in NSMB2.")
        self.Zone_camunk3.setValue(z.unk3)

        self.Zone_settings = []

        # Layouts
        ZoneCameraModesLayout = QtWidgets.QGridLayout()
        for i, b in enumerate(cammodebuttons):
            ZoneCameraModesLayout.addWidget(b, i % 4, i // 4)
        ZoneCameraLayout = QtWidgets.QFormLayout()
        ZoneCameraLayout.addRow('Camera Mode:', ZoneCameraModesLayout)
        ZoneCameraLayout.addRow('Screen Heights:', self.Zone_screenheights)

        ZoneVisibilityLayout = QtWidgets.QHBoxLayout()
        ZoneVisibilityLayout.addWidget(self.Zone_vspotlight)
        ZoneVisibilityLayout.addWidget(self.Zone_vfulldark)

        ZoneDirectionLayout = QtWidgets.QFormLayout()
        ZoneDirectionLayout.addRow(globals.trans.string('ZonesDlg', 39), self.Zone_directionmode)

        ZoneCameraUnknownsLayoutA = QtWidgets.QFormLayout()
        ZoneCameraUnknownsLayoutA.addRow('Unknown Value 1:', self.Zone_camunk1)
        ZoneCameraUnknownsLayoutA.addRow('Unknown Value 2:', self.Zone_camunk2)
        ZoneCameraUnknownsLayoutB = QtWidgets.QFormLayout()
        ZoneCameraUnknownsLayoutB.addRow('Unknown Value 3:', self.Zone_camunk3)

        ZoneCameraUnknownsLayout = QtWidgets.QHBoxLayout()
        ZoneCameraUnknownsLayout.addLayout(ZoneCameraUnknownsLayoutA)
        ZoneCameraUnknownsLayout.addLayout(ZoneCameraUnknownsLayoutB)
        
        ZoneSettingsLeft = QtWidgets.QFormLayout()
        ZoneSettingsRight = QtWidgets.QFormLayout()
        settingsNames = globals.trans.stringList('ZonesDlg', 77)
        
        for i in range(0, 8):
            self.Zone_settings.append(QtWidgets.QCheckBox())
            self.Zone_settings[i].setChecked(z.type & 1 << i)
            self.Zone_settings[i].setStyleSheet("margin-left:100%;");

            if i < 4:
                ZoneSettingsLeft.addRow(settingsNames[i], self.Zone_settings[i])
            else:
                ZoneSettingsRight.addRow(settingsNames[i], self.Zone_settings[i])
            
        ZoneSettingsLayout = QtWidgets.QHBoxLayout()
        ZoneSettingsLayout.addLayout(ZoneSettingsLeft)
        ZoneSettingsLayout.addStretch()
        ZoneSettingsLayout.addLayout(ZoneSettingsRight)

        InnerLayout = QtWidgets.QVBoxLayout()
        InnerLayout.addLayout(ZoneCameraLayout)
        InnerLayout.addWidget(createHorzLine())
        InnerLayout.addLayout(ZoneVisibilityLayout)
        InnerLayout.addWidget(self.Zone_visibility)
        InnerLayout.addWidget(createHorzLine())
        InnerLayout.addLayout(ZoneDirectionLayout)
        InnerLayout.addWidget(createHorzLine())
        InnerLayout.addLayout(ZoneCameraUnknownsLayout)
        InnerLayout.addWidget(createHorzLine())
        InnerLayout.addLayout(ZoneSettingsLayout)
        self.Visibility.setLayout(InnerLayout)

    def ChangeVisibilityList(self):
        SelectedIndex = self.zv & 0x0F
        self.Zone_visibility.clear()

        if not self.Zone_vspotlight.isChecked() and not self.Zone_vfulldark.isChecked():
            self.Zone_visibility.addItem(globals.trans.string('ZonesDlg', 41))
            self.Zone_visibility.setToolTip(globals.trans.string('ZonesDlg', 42))
            SelectedIndex = 0
        elif self.Zone_vspotlight.isChecked() and self.Zone_vfulldark.isChecked():
            self.Zone_visibility.addItem(globals.trans.string('ZonesDlg', 80))
            self.Zone_visibility.setToolTip(globals.trans.string('ZonesDlg', 81))
            SelectedIndex = 0
        elif self.Zone_vspotlight.isChecked():
            self.Zone_visibility.addItems(globals.trans.stringList('ZonesDlg', 43))
            self.Zone_visibility.setToolTip(globals.trans.string('ZonesDlg', 44))
            if SelectedIndex > 2: SelectedIndex = 0
        elif self.Zone_vfulldark.isChecked():
            self.Zone_visibility.addItems(globals.trans.stringList('ZonesDlg', 45))
            self.Zone_visibility.setToolTip(globals.trans.string('ZonesDlg', 46))
            if SelectedIndex > 5: SelectedIndex = 5
        
        self.Zone_visibility.setCurrentIndex(SelectedIndex)

    def ChangeCamModeList(self):
        mode = self.Zone_cammodebuttongroup.checkedId()

        oldListChoice = [1, 1, 2, 3, 3, 3, 1, 1][self.zm]
        newListChoice = [1, 1, 2, 3, 3, 3, 1, 1][mode]

        if self.zm == -1 or oldListChoice != newListChoice:

            if newListChoice == 1:
                heights = [
                    ([14, 19  ]    , ''),
                    ([14, 19  , 24], ''),
                    ([14, 19  , 28], ''),
                    ([20, 24  ]    , ''),
                    ([19, 24  , 28], ''),
                    ([17, 24  ]    , ''),
                    ([17, 24  , 28], ''),
                    ([17, 20  ]    , ''),
                    ([ 7, 11  , 28], '**'),
                    ([17, 20.5, 24], ''),
                    ([17, 20  , 28], ''),
                    ([20,  0  ,  0], ''),  # Needs further testing
                ]
            elif newListChoice == 2:
                heights = [
                    ([14, 19  ]    , ''),
                    ([14, 19  , 24], ''),
                    ([14, 19  , 28], ''),
                    ([19, 19  , 24], ''),
                    ([19, 24  , 28], ''),
                    ([19, 24  , 28], ''),
                    ([17, 24  , 28], ''),
                    ([17, 20.5, 24], ''),
                    ([17,  0  ,  0], ''),  # Needs further testing
                ]
            else:
                heights = [
                    ([14  ], ''),
                    ([19  ], ''),
                    ([24  ], ''),
                    ([28  ], ''),
                    ([17  ], ''),
                    ([20  ], ''),
                    ([16  ], ''),
                    ([28  ], ''),
                    ([ 7  ], '*'),
                    ([10.5], '*'),
                ]

            items = []
            for i, (options, asterisk) in enumerate(heights):
                items.append('%d: ' % i + ' -> '.join(('%s blocks' % str(o)) for o in options) + asterisk)

            self.Zone_screenheights.clear()
            self.Zone_screenheights.addItems(items)
            self.Zone_screenheights.setCurrentIndex(0)
            self.zm = mode

    def createBounds(self, z):
        self.Bounds = QtWidgets.QGroupBox(globals.trans.string('ZonesDlg', 47))

        self.Zone_yboundup = QtWidgets.QSpinBox()
        self.Zone_yboundup.setRange(-32688, 32847)
        self.Zone_yboundup.setToolTip(globals.trans.string('ZonesDlg', 49))
        self.Zone_yboundup.setValue(80 + z.yupperbound)

        self.Zone_ybounddown = QtWidgets.QSpinBox()
        self.Zone_ybounddown.setRange(-32695, 32840)
        self.Zone_ybounddown.setToolTip(globals.trans.string('ZonesDlg', 51))
        self.Zone_ybounddown.setValue(72 - z.ylowerbound)

        self.Zone_yboundup2 = QtWidgets.QSpinBox()
        self.Zone_yboundup2.setRange(-32680, 32855)
        self.Zone_yboundup2.setToolTip(globals.trans.string('ZonesDlg', 71))
        self.Zone_yboundup2.setValue(88 + z.yupperbound2)

        self.Zone_ybounddown2 = QtWidgets.QSpinBox()
        self.Zone_ybounddown2.setRange(-32679, 32856)
        self.Zone_ybounddown2.setToolTip(globals.trans.string('ZonesDlg', 73))
        self.Zone_ybounddown2.setValue(88 - z.ylowerbound2)

        self.Zone_yboundup3 = QtWidgets.QSpinBox()
        self.Zone_yboundup3.setRange(-32768, 32767)
        self.Zone_yboundup3.setToolTip('<b>Multiplayer Upper Bounds Adjust:</b><br>Added to the upper bounds value (regular or Lakitu) during multiplayer mode, ' \
                                       'and during the transition back to normal camera behavior after an Auto-Scrolling Controller reaches the end of its path.')
        self.Zone_yboundup3.setValue(z.yupperbound3)

        self.Zone_ybounddown3 = QtWidgets.QSpinBox()
        self.Zone_ybounddown3.setRange(-32767, 32768)
        self.Zone_ybounddown3.setToolTip('<b>Multiplayer Lower Bounds Adjust:</b><br>Added to the lower bounds value (regular or Lakitu) during multiplayer mode, ' \
                                         'and during the transition back to normal camera behavior after an Auto-Scrolling Controller reaches the end of its path.')
        self.Zone_ybounddown3.setValue(-z.ylowerbound3)

        self.Zone_boundflg = QtWidgets.QCheckBox()
        self.Zone_boundflg.setToolTip(globals.trans.string('ZonesDlg', 75))
        self.Zone_boundflg.setChecked(z.mpcamzoomadjust == 0xF)
        self.Zone_boundflg.stateChanged.connect(lambda: self.Zone_mpzoomadjust.setEnabled(not self.Zone_boundflg.isChecked()))

        self.Zone_mpzoomadjust = QtWidgets.QSpinBox()
        self.Zone_mpzoomadjust.setRange(0, 14)
        self.Zone_mpzoomadjust.setToolTip('<b>Multiplayer Screen Height Adjust:</b><br>Increases the height of the screen during multiplayer mode. ' \
                                          'Requires "Enable Upward Scrolling" to be unchecked.<br><br>This causes very glitchy behavior when ' \
                                          'the zone is much taller than the adjusted screen height, the screen becomes more than 28 blocks tall ' \
                                          'or the camera zooms in during the end-of-level celebration.')
        self.Zone_mpzoomadjust.setEnabled(not self.Zone_boundflg.isChecked())
        if z.mpcamzoomadjust < 0xF:
            self.Zone_mpzoomadjust.setValue(z.mpcamzoomadjust)

        LA = QtWidgets.QFormLayout()
        LA.addRow(globals.trans.string('ZonesDlg', 48), self.Zone_yboundup)
        LA.addRow(globals.trans.string('ZonesDlg', 50), self.Zone_ybounddown)
        LA.addRow(globals.trans.string('ZonesDlg', 74), self.Zone_boundflg)
        LA.addRow('Multiplayer Screen Height Adjust:', self.Zone_mpzoomadjust)
        LB = QtWidgets.QFormLayout()
        LB.addRow(globals.trans.string('ZonesDlg', 70), self.Zone_yboundup2)
        LB.addRow(globals.trans.string('ZonesDlg', 72), self.Zone_ybounddown2)
        LB.addRow('Multiplayer Upper Bounds Adjust:', self.Zone_yboundup3)
        LB.addRow('Multiplayer Lower Bounds Adjust:', self.Zone_ybounddown3)
        LC = QtWidgets.QGridLayout()
        LC.addLayout(LA, 0, 0)
        LC.addLayout(LB, 0, 1)

        self.Bounds.setLayout(LC)

    def createAudio(self, z):
        self.Audio = QtWidgets.QGroupBox(globals.trans.string('ZonesDlg', 52))
        self.AutoEditMusic = False

        self.Zone_music = QtWidgets.QComboBox()
        self.Zone_music.setToolTip(globals.trans.string('ZonesDlg', 54))

        import gamedefs
        newItems = gamedefs.getMusic()
        del gamedefs

        for a, b in newItems:
            self.Zone_music.addItem(b, a)  # text, songid
        self.Zone_music.setCurrentIndex(self.Zone_music.findData(z.music))
        self.Zone_music.currentIndexChanged.connect(self.handleMusicListSelect)

        self.Zone_musicid = QtWidgets.QSpinBox()
        self.Zone_musicid.setToolTip(globals.trans.string('ZonesDlg', 69))
        self.Zone_musicid.setMaximum(255)
        self.Zone_musicid.setValue(z.music)
        self.Zone_musicid.valueChanged.connect(self.handleMusicIDChange)

        self.Zone_sfx = QtWidgets.QComboBox()
        self.Zone_sfx.setToolTip(globals.trans.string('ZonesDlg', 56))
        newItems3 = globals.trans.stringList('ZonesDlg', 57)
        self.Zone_sfx.addItems(newItems3)
        self.Zone_sfx.setCurrentIndex(z.sfxmod >> 4)

        self.Zone_boss = QtWidgets.QCheckBox()
        self.Zone_boss.setToolTip(globals.trans.string('ZonesDlg', 59))
        self.Zone_boss.setChecked(z.sfxmod & 0x0F)

        ZoneAudioLayout = QtWidgets.QFormLayout()
        ZoneAudioLayout.addRow(globals.trans.string('ZonesDlg', 53), self.Zone_music)
        ZoneAudioLayout.addRow(globals.trans.string('ZonesDlg', 68), self.Zone_musicid)
        ZoneAudioLayout.addRow(globals.trans.string('ZonesDlg', 55), self.Zone_sfx)
        ZoneAudioLayout.addRow(globals.trans.string('ZonesDlg', 58), self.Zone_boss)

        self.Audio.setLayout(ZoneAudioLayout)

    def handleMusicListSelect(self):
        """
        Handles the user selecting an entry from the music list
        """
        if self.AutoEditMusic: return
        id = self.Zone_music.itemData(self.Zone_music.currentIndex())
        id = int(str(id))  # id starts out as a QString

        self.AutoEditMusic = True
        self.Zone_musicid.setValue(id)
        self.AutoEditMusic = False

    def handleMusicIDChange(self):
        """
        Handles the user selecting a custom music ID
        """
        if self.AutoEditMusic: return
        id = self.Zone_musicid.value()

        # BUG: The music entries are out of order

        self.AutoEditMusic = True
        self.Zone_music.setCurrentIndex(self.Zone_music.findData(id))
        self.AutoEditMusic = False

    def PresetSelected(self, info=None):
        """
        Handles a zone size preset being selected
        """
        if self.AutoChangingSize: return

        if self.Zone_presets.currentText() == globals.trans.string('ZonesDlg', 60): return
        w, h = self.Zone_presets.currentText()[3:].split('x')

        self.AutoChangingSize = True
        self.Zone_width.setValue(int(w))
        self.Zone_height.setValue(int(h))
        self.AutoChangingSize = False

        if self.Zone_presets.itemText(0) == globals.trans.string('ZonesDlg', 60): self.Zone_presets.removeItem(0)

    def PresetDeselected(self, info=None):
        """
        Handles the zone height or width boxes being changed
        """
        if self.AutoChangingSize: return

        self.AutoChangingSize = True
        w = self.Zone_width.value()
        h = self.Zone_height.value()
        check = str(w) + 'x' + str(h)

        found = None
        for preset in self.Zone_presets_values:
            if check == preset[3:]: found = preset

        if found is not None:
            self.Zone_presets.setCurrentIndex(self.Zone_presets.findText(found))
            if self.Zone_presets.itemText(0) == globals.trans.string('ZonesDlg', 60): self.Zone_presets.removeItem(0)
        else:
            if self.Zone_presets.itemText(0) != globals.trans.string('ZonesDlg', 60): self.Zone_presets.insertItem(0,
                                                                                                           globals.trans.string(
                                                                                                               'ZonesDlg',
                                                                                                               60))
            self.Zone_presets.setCurrentIndex(0)
        self.AutoChangingSize = False


class BGTab(QtWidgets.QWidget):
    def __init__(self, background):
        super().__init__()

        self.createBGViewers()

        self.bgFname = QtWidgets.QLineEdit()
        self.bgFname.setText(bytes_to_string(background[4]))

        self.bgName = QtWidgets.QComboBox()
        self.bgName.addItems(BGName.getTransAll())
        self.bgName.setCurrentIndex(BGName.index(self.bgFname.text()))
        self.bgName.activated.connect(self.handleNameBox)

        self.bgFname.setEnabled(self.bgName.currentText() == 'Custom filename...')

        self.xPos = QtWidgets.QSpinBox()
        self.xPos.setRange(-32768, 32767)
        self.xPos.setToolTip("X offset to be applied to the center of the background.\nThis option is no longer valid in the original game.")
        self.xPos.setValue(background[1])

        self.yPos = QtWidgets.QSpinBox()
        self.yPos.setRange(-32768, 32767)
        self.yPos.setToolTip("Y offset to be applied to the center of the background.\nThis option is no longer valid in the original game.")
        self.yPos.setValue(background[2])

        self.zPos = QtWidgets.QSpinBox()
        self.zPos.setRange(-32768, 32767)
        self.zPos.setToolTip("Z offset to be applied to the center of the background.\nThis option is no longer valid in the original game.")
        self.zPos.setValue(background[3])

        self.parallaxMode = QtWidgets.QComboBox()
        self.parallaxMode.addItems(("Y Offset Off, All Parallax On",
                                    "Y Offset On, All Parallax On",
                                    "Y Offset On, All Parallax Off",
                                    "Y Offset On, Y Parallax Off",
                                    "Y Offset On, X Parallax Off"))
        self.parallaxMode.setToolTip("Parallax Mode from NSMB2.\nThis option is no longer valid in the original game.")
        self.parallaxMode.setCurrentIndex(background[5])

        nameLayout = QtWidgets.QFormLayout()
        nameLayout.addRow('Background:', self.bgName)
        nameLayout.addRow('Filename:', self.bgFname)

        settingsLayout = QtWidgets.QFormLayout()
        settingsLayout.addRow('X Offset:', self.xPos)
        settingsLayout.addRow('Y Offset:', self.yPos)
        settingsLayout.addRow('Z Offset:', self.zPos)
        settingsLayout.addRow('Parallax Mode:', self.parallaxMode)

        BGSettingsLayout = QtWidgets.QVBoxLayout()
        BGSettingsLayout.addLayout(nameLayout)
        BGSettingsLayout.addWidget(createHorzLine())
        BGSettingsLayout.addLayout(settingsLayout)

        self.BGSettings = QtWidgets.QGroupBox('Settings')
        self.BGSettings.setLayout(BGSettingsLayout)

        Layout = QtWidgets.QVBoxLayout()
        Layout.addWidget(self.BGViewer)
        Layout.addWidget(self.BGSettings)
        self.setLayout(Layout)

        self.updatePreview()

    def createBGViewers(self):
        self.BGViewer = QtWidgets.QGroupBox(globals.trans.string('BGDlg', 16))

        self.preview = QtWidgets.QLabel()

        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(self.preview, 0, 0)
        self.BGViewer.setLayout(mainLayout)

    def handleNameBox(self):
        """
        Handles any name box changing
        """
        if self.bgName.currentText() == 'Custom filename...':
            self.bgFname.setText('')
            self.bgFname.setEnabled(True)

        else:
            self.bgFname.setText(BGName.getNameForTrans(self.bgName.currentText()))
            self.bgFname.setEnabled(False)

        self.updatePreview()

    def updatePreview(self):
        """
        Updates the preview label
        """
        if self.bgName.currentText() == 'Custom filename...':
            filename = globals.miyamoto_path + '/miyamotodata/bg/no_preview.png'

        else:
            folders = globals.gamedef.recursiveFiles('bg', False, True)
            folders.append(os.path.join(globals.miyamoto_path, 'miyamotodata/bg'))

            for folder in folders:
                filename = os.path.join(folder, self.bgName.currentText() + '.png')
                if os.path.isfile(filename):
                    break

            else:
                filename = globals.miyamoto_path + '/miyamotodata/bg/no_preview.png'

        pix = QtGui.QPixmap(filename)
        self.preview.setPixmap(pix)


class ScreenCapChoiceDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose which zone to take a pic of
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('ScrShtDlg', 0))
        self.setWindowIcon(GetIcon('screenshot'))

        self.zoneCombo = QtWidgets.QComboBox()
        self.zoneCombo.addItem(globals.trans.string('ScrShtDlg', 1))

        zonecount = len(globals.Area.zones)
        if zonecount:
            self.zoneCombo.addItem(globals.trans.string('ScrShtDlg', 2))
            for i in range(zonecount):
                self.zoneCombo.addItem(globals.trans.string('ScrShtDlg', 3, '[zone]', i + 1))

        self.hideBackground = QtWidgets.QCheckBox()
        self.hideBackground.setChecked(True)

        self.saveImage = QtWidgets.QCheckBox()
        self.saveImage.setChecked(True)
        self.saveImage.stateChanged.connect(self.saveImageChanged)

        self.saveClip = QtWidgets.QCheckBox()
        self.saveClip.stateChanged.connect(self.saveClipChanged)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QFormLayout()
        mainLayout.setLabelAlignment(QtCore.Qt.AlignRight)
        mainLayout.addRow("Target:", self.zoneCombo)
        mainLayout.addRow("Hide background:", self.hideBackground)
        mainLayout.addRow(createHorzLine())
        mainLayout.addRow("Save image to file:", self.saveImage)
        mainLayout.addRow("Copy image to clipboard:", self.saveClip)
        mainLayout.addRow(buttonBox)
        self.setLayout(mainLayout)

    def saveImageChanged(self, checked):
        if not (checked or self.saveClip.isChecked()):
            self.saveClip.setChecked(True)

    def saveClipChanged(self, checked):
        if not (checked or self.saveImage.isChecked()):
            self.saveImage.setChecked(True)


class AutoSavedInfoDialog(QtWidgets.QDialog):
    """
    Dialog which lets you know that an auto saved level exists
    """

    def __init__(self, filename):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('AutoSaveDlg', 0))
        self.setWindowIcon(GetIcon('save'))

        mainlayout = QtWidgets.QVBoxLayout(self)

        hlayout = QtWidgets.QHBoxLayout()

        icon = QtWidgets.QLabel()
        hlayout.addWidget(icon)

        label = QtWidgets.QLabel(globals.trans.string('AutoSaveDlg', 1, '[path]', filename))
        label.setWordWrap(True)
        hlayout.addWidget(label)
        hlayout.setStretch(1, 1)

        buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        mainlayout.addLayout(hlayout)
        mainlayout.addWidget(buttonbox)


class AreaChoiceDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose an area
    """

    def __init__(self, areacount):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('AreaChoiceDlg', 0))
        self.setWindowIcon(GetIcon('areas'))

        self.areaCombo = QtWidgets.QComboBox()
        for i in range(areacount):
            self.areaCombo.addItem(globals.trans.string('AreaChoiceDlg', 1, '[num]', i + 1))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.areaCombo)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class PreferencesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you customize Miyamoto
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('PrefsDlg', 0))
        self.setWindowIcon(GetIcon('settings'))

        # Create the tab widget
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.currentChanged.connect(self.tabChanged)

        # Create other widgets
        self.infoLabel = QtWidgets.QLabel()
        self.generalTab = self.getGeneralTab()
        self.toolbarTab = self.getToolbarTab()
        self.themesTab = self.getThemesTab(QtWidgets.QWidget)()
        self.tabWidget.addTab(self.generalTab, globals.trans.string('PrefsDlg', 1))
        self.tabWidget.addTab(self.toolbarTab, globals.trans.string('PrefsDlg', 2))
        self.tabWidget.addTab(self.themesTab, globals.trans.string('PrefsDlg', 3))

        # Create the buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Create a main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.infoLabel)
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        # Update it
        self.tabChanged()

    def tabChanged(self):
        """
        Handles the current tab being changed
        """
        self.infoLabel.setText(self.tabWidget.currentWidget().info)

    def getGeneralTab(self):
        """
        Returns the General Tab
        """

        class GeneralTab(QtWidgets.QWidget):
            """
            General Tab
            """
            info = globals.trans.string('PrefsDlg', 4)

            def __init__(self):
                """
                Initializes the General Tab
                """
                super().__init__()

                # Add the Clear Recent Files button
                ClearRecentBtn = QtWidgets.QPushButton(globals.trans.string('PrefsDlg', 16))
                ClearRecentBtn.setMaximumWidth(ClearRecentBtn.minimumSizeHint().width())
                ClearRecentBtn.clicked.connect(self.ClearRecent)

                # Add the Translation Language setting
                self.Trans = QtWidgets.QComboBox()
                self.Trans.setMaximumWidth(256)

                # Add the compression level setting
                self.compLevel = QtWidgets.QComboBox()
                self.compLevel.setMaximumWidth(256)

                if globals.libyaz0_available:
                    for i in range(33, 43):
                        self.compLevel.addItem(globals.trans.string('PrefsDlg', i))

                    self.compLevel.setCurrentIndex(globals.CompLevel)

                else:
                    self.compLevel.addItem(globals.trans.string('PrefsDlg', 42))
                    self.compLevel.setCurrentIndex(0)

                # Add the Embedded tab type determiner
                self.separate = QtWidgets.QCheckBox()
                self.separate.setChecked(globals.isEmbeddedSeparate)

                from spritelib import RotationFPS

                # Add the pivotal rotation animation FPS specifier
                self.rotationFPS = QtWidgets.QSpinBox()
                self.rotationFPS.setMaximumWidth(256)
                self.rotationFPS.setRange(1, 60)
                self.rotationFPS.setValue(RotationFPS)

                del RotationFPS

                # Add the option to modify the inner sarc name
                self.modifyInnerName = QtWidgets.QCheckBox()
                self.modifyInnerName.setChecked(globals.modifyInnerName)

                # Create the main layout
                L = QtWidgets.QFormLayout()
                L.addRow(globals.trans.string('PrefsDlg', 14), self.Trans)
                L.addRow(globals.trans.string('PrefsDlg', 15), ClearRecentBtn)
                L.addRow(globals.trans.string('PrefsDlg', 32), self.compLevel)
                L.addRow(globals.trans.string('PrefsDlg', 43), self.separate)
                L.addRow(globals.trans.string('PrefsDlg', 45), self.rotationFPS)
                L.addRow(globals.trans.string('PrefsDlg', 44), self.modifyInnerName)
                self.setLayout(L)

                # Set the buttons
                self.Reset()

            def Reset(self):
                """
                Read the preferences and check the respective boxes
                """
                self.Trans.addItem('English')
                self.Trans.setItemData(0, None, Qt.UserRole)
                self.Trans.setCurrentIndex(0)
                i = 1
                for trans in os.listdir('miyamotodata/translations'):
                    if trans.lower() == 'english': continue

                    fp = 'miyamotodata/translations/' + trans + '/main.xml'
                    if not os.path.isfile(fp): continue

                    transobj = MiyamotoTranslation(trans)
                    name = transobj.name
                    self.Trans.addItem(name)
                    self.Trans.setItemData(i, trans, Qt.UserRole)
                    if trans == str(setting('Translation')):
                        self.Trans.setCurrentIndex(i)
                    i += 1

            def ClearRecent(self):
                """
                Handle the Clear Recent Files button being clicked
                """
                ans = QtWidgets.QMessageBox.question(None, globals.trans.string('PrefsDlg', 17), globals.trans.string('PrefsDlg', 18), QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                if ans != QtWidgets.QMessageBox.Yes: return
                globals.mainWindow.RecentMenu.clearAll()

        return GeneralTab()

    def getToolbarTab(self):
        """
        Returns the Toolbar Tab
        """

        class ToolbarTab(QtWidgets.QWidget):
            """
            Toolbar Tab
            """
            info = globals.trans.string('PrefsDlg', 5)

            def __init__(self):
                """
                Initializes the Toolbar Tab
                """
                super().__init__()

                # Determine which keys are activated
                if setting('ToolbarActs') in (None, 'None', 'none', '', 0):
                    # Get the default settings
                    toggled = {}
                    for List in (globals.FileActions, globals.EditActions, globals.ViewActions, globals.SettingsActions, globals.HelpActions):
                        for name, activated, key in List:
                            toggled[key] = activated
                else:  # Get the registry settings
                    toggled = setting('ToolbarActs')
                    newToggled = {}  # here, I'm replacing QStrings w/ python strings
                    for key in toggled:
                        newToggled[str(key)] = toggled[key]
                    toggled = newToggled

                # Create some data
                self.FileBoxes = []
                self.EditBoxes = []
                self.ViewBoxes = []
                self.SettingsBoxes = []
                self.HelpBoxes = []
                FL = QtWidgets.QVBoxLayout()
                EL = QtWidgets.QVBoxLayout()
                VL = QtWidgets.QVBoxLayout()
                SL = QtWidgets.QVBoxLayout()
                HL = QtWidgets.QVBoxLayout()
                FB = QtWidgets.QGroupBox(globals.trans.string('Menubar', 0))
                EB = QtWidgets.QGroupBox(globals.trans.string('Menubar', 1))
                VB = QtWidgets.QGroupBox(globals.trans.string('Menubar', 2))
                SB = QtWidgets.QGroupBox(globals.trans.string('Menubar', 3))
                HB = QtWidgets.QGroupBox(globals.trans.string('Menubar', 5))

                # Arrange this data so it can be iterated over
                menuItems = (
                    (globals.FileActions, self.FileBoxes, FL, FB),
                    (globals.EditActions, self.EditBoxes, EL, EB),
                    (globals.ViewActions, self.ViewBoxes, VL, VB),
                    (globals.SettingsActions, self.SettingsBoxes, SL, SB),
                    (globals.HelpActions, self.HelpBoxes, HL, HB),
                )

                # Set up the menus by iterating over the above data
                for defaults, boxes, layout, group in menuItems:
                    for L, C, I in defaults:
                        box = QtWidgets.QCheckBox(L)
                        boxes.append(box)
                        layout.addWidget(box)
                        try:
                            box.setChecked(toggled[I])
                        except KeyError:
                            pass
                        box.InternalName = I  # to save settings later
                    group.setLayout(layout)

                # Create the always-enabled Current Area checkbox
                CurrentArea = QtWidgets.QCheckBox(globals.trans.string('PrefsDlg', 19))
                CurrentArea.setChecked(True)
                CurrentArea.setEnabled(False)

                # Create the Reset button
                reset = QtWidgets.QPushButton(globals.trans.string('PrefsDlg', 20))
                reset.clicked.connect(self.reset)

                # Create the main layout
                L = QtWidgets.QGridLayout()
                L.addWidget(reset, 0, 0, 1, 1)
                L.addWidget(FB, 1, 0, 3, 1)
                L.addWidget(EB, 1, 1, 3, 1)
                L.addWidget(VB, 1, 2, 3, 1)
                L.addWidget(SB, 1, 3, 1, 1)
                L.addWidget(HB, 3, 3, 1, 1)
                L.addWidget(CurrentArea, 4, 3, 1, 1)
                self.setLayout(L)

            def reset(self):
                """
                This is called when the Reset button is clicked
                """
                items = (
                    (self.FileBoxes, globals.FileActions),
                    (self.EditBoxes, globals.EditActions),
                    (self.ViewBoxes, globals.ViewActions),
                    (self.SettingsBoxes, globals.SettingsActions),
                    (self.HelpBoxes, globals.HelpActions)
                )

                for boxes, defaults in items:
                    for box, default in zip(boxes, defaults):
                        box.setChecked(default[1])

        return ToolbarTab()

    @staticmethod
    def getThemesTab(parent):
        """
        Returns the Themes Tab
        """

        class ThemesTab(parent):
            """
            Themes Tab
            """
            info = globals.trans.string('PrefsDlg', 6)

            def __init__(self):
                """
                Initializes the Themes Tab
                """
                super().__init__()

                # Get the current and available themes
                self.themeID = globals.theme.themeName
                self.themes = self.getAvailableThemes

                # Create the theme box
                self.themeBox = QtWidgets.QComboBox()
                for name, themeObj in self.themes:
                    self.themeBox.addItem(name)

                index = self.themeBox.findText(setting('Theme'), Qt.MatchFixedString)
                if index >= 0:
                     self.themeBox.setCurrentIndex(index)

                self.themeBox.currentIndexChanged.connect(self.UpdatePreview)

                boxGB = QtWidgets.QGroupBox('Themes')
                L = QtWidgets.QFormLayout()
                L.addRow('Theme:', self.themeBox)
                L2 = QtWidgets.QGridLayout()
                L2.addLayout(L, 0, 0)
                boxGB.setLayout(L2)

                # Create the preview labels and groupbox
                self.preview = QtWidgets.QLabel()
                self.description = QtWidgets.QLabel()
                L = QtWidgets.QVBoxLayout()
                L.addWidget(self.preview)
                L.addWidget(self.description)
                L.addStretch(1)
                previewGB = QtWidgets.QGroupBox(globals.trans.string('PrefsDlg', 22))
                previewGB.setLayout(L)

                # Create the options box options
                keys = QtWidgets.QStyleFactory().keys()
                self.NonWinStyle = QtWidgets.QComboBox()
                self.NonWinStyle.setToolTip(globals.trans.string('PrefsDlg', 24))
                self.NonWinStyle.addItems(keys)
                uistyle = setting('uiStyle', "Fusion")
                if uistyle is not None:
                    self.NonWinStyle.setCurrentIndex(keys.index(setting('uiStyle', "Fusion")))

                # Create the options groupbox
                L = QtWidgets.QVBoxLayout()
                L.addWidget(self.NonWinStyle)
                optionsGB = QtWidgets.QGroupBox(globals.trans.string('PrefsDlg', 25))
                optionsGB.setLayout(L)

                # Create a main layout
                Layout = QtWidgets.QGridLayout()
                Layout.addWidget(boxGB, 0, 0)
                Layout.addWidget(optionsGB, 0, 1)
                Layout.addWidget(previewGB, 1, 1)
                Layout.setRowStretch(1, 1)
                self.setLayout(Layout)

                # Update the preview things
                self.UpdatePreview()

            @property
            def getAvailableThemes(self):
                """Searches the Themes folder and returns a list of theme filepaths.
                Automatically adds 'Classic' to the list."""
                themes = os.listdir(globals.miyamoto_path + '/miyamotodata/themes')
                themeList = [('Classic', MiyamotoTheme())]
                for themeName in themes:
                    if os.path.isdir(globals.miyamoto_path + '/miyamotodata/themes/' + themeName):
                        try:
                            theme = MiyamotoTheme(themeName)
                            themeList.append((themeName, theme))
                        except Exception:
                            pass

                return tuple(themeList)

            def UpdatePreview(self):
                """
                Updates the preview and theme box
                """
                theme = self.themeBox.currentText()
                style = self.NonWinStyle.currentText()

                themeObj = MiyamotoTheme(theme)
                keys = QtWidgets.QStyleFactory().keys()

                if themeObj.color('ui') is not None and not themeObj.forceStyleSheet:
                    styles = ["WindowsXP", "WindowsVista"]
                    for _style in styles:
                        for key in _style, _style.lower():
                            if key in keys:
                                keys.remove(key)

                    if style in styles + [_style.lower() for _style in styles]:
                        style = "Fusion"

                self.NonWinStyle.clear()
                self.NonWinStyle.addItems(keys)
                self.NonWinStyle.setCurrentIndex(keys.index(style))

                for name, themeObj in self.themes:
                    if name == self.themeBox.currentText():
                        t = themeObj
                        self.preview.setPixmap(self.drawPreview(t))
                        text = globals.trans.string('PrefsDlg', 26, '[name]', t.themeName, '[creator]', t.creator,
                                            '[description]', t.description)
                        self.description.setText(text)

            def drawPreview(self, theme):
                """
                Returns a preview pixmap for the given theme
                """

                tilewidth = 24
                width = int(21.875 * tilewidth)
                height = int(11.5625 * tilewidth)

                # Set up some things
                px = QtGui.QPixmap(width, height)
                px.fill(theme.color('bg'))

                paint = QtGui.QPainter(px)

                font = QtGui.QFont(globals.NumberFont) # need to make a new instance to avoid changing global settings
                font.setPointSize(6)
                paint.setFont(font)

                # Draw the spriteboxes
                paint.setPen(QtGui.QPen(theme.color('spritebox_lines'), 1))
                paint.setBrush(QtGui.QBrush(theme.color('spritebox_fill')))

                paint.drawRoundedRect(11 * tilewidth, 4 * tilewidth, tilewidth, tilewidth, 5, 5)
                paint.drawText(QtCore.QPointF(11.25 * tilewidth, 4.6875 * tilewidth), '38')

                paint.drawRoundedRect(tilewidth, 6 * tilewidth, tilewidth, tilewidth, 5, 5)
                paint.drawText(QtCore.QPointF(1.25 * tilewidth, 6.6875 * tilewidth), '53')

                # Draw the entrance
                paint.setPen(QtGui.QPen(theme.color('entrance_lines'), 1))
                paint.setBrush(QtGui.QBrush(theme.color('entrance_fill')))

                paint.drawRoundedRect(13 * tilewidth, 8 * tilewidth, tilewidth, tilewidth, 5, 5)
                paint.drawText(QtCore.QPointF(13.25 * tilewidth, 8.625 * tilewidth), '0')

                # Draw the location
                paint.setPen(QtGui.QPen(theme.color('location_lines'), 1))
                paint.setBrush(QtGui.QBrush(theme.color('location_fill')))

                paint.drawRect(tilewidth, 9 * tilewidth, 6 * tilewidth, 2 * tilewidth)
                paint.setPen(QtGui.QPen(theme.color('location_text'), 1))
                paint.drawText(QtCore.QPointF(1.25 * tilewidth, 9.625 * tilewidth), '1')

                # Draw the zone
                paint.setPen(QtGui.QPen(theme.color('zone_lines'), 3))
                paint.setBrush(QtGui.QBrush(toQColor(0, 0, 0, 0)))
                paint.drawRect(8.5 * tilewidth, 3.25 * tilewidth, 16 * tilewidth, 7.5 * tilewidth)
                paint.setPen(QtGui.QPen(theme.color('zone_corner'), 3))
                paint.setBrush(QtGui.QBrush(theme.color('zone_corner'), 3))
                paint.drawRect(8.4375 * tilewidth, 3.1875 * tilewidth, 0.125 * tilewidth, 0.125 * tilewidth)
                paint.drawRect(8.4375 * tilewidth, 10.6875 * tilewidth, 0.125 * tilewidth, 0.125 * tilewidth)
                paint.setPen(QtGui.QPen(theme.color('zone_text'), 1))
                font = QtGui.QFont(globals.NumberFont)
                font.setPointSize(5 / 16 * tilewidth)
                paint.setFont(font)
                paint.drawText(QtCore.QPointF(8.75 * tilewidth, 3.875 * tilewidth), 'Zone 1')

                # Draw the grid
                paint.setPen(QtGui.QPen(theme.color('grid'), 1, Qt.DotLine))
                gridcoords = [i for i in range(0, width, tilewidth)]
                for i in gridcoords:
                    paint.setPen(QtGui.QPen(theme.color('grid'), 0.75, Qt.DotLine))
                    paint.drawLine(i, 0, i, height)
                    paint.drawLine(0, i, width, i)
                    if not (i / tilewidth) % (tilewidth / 4):
                        paint.setPen(QtGui.QPen(theme.color('grid'), 1.5, Qt.DotLine))
                        paint.drawLine(i, 0, i, height)
                        paint.drawLine(0, i, width, i)

                    if not (i / tilewidth) % (tilewidth / 2):
                        paint.setPen(QtGui.QPen(theme.color('grid'), 2.25, Qt.DotLine))
                        paint.drawLine(i, 0, i, height)
                        paint.drawLine(0, i, width, i)

                # Delete the painter and return the pixmap
                paint.end()
                return px

        return ThemesTab


class ChooseLevelNameDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose a level from a list
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals.trans.string('OpenFromNameDlg', 0))
        self.setWindowIcon(GetIcon('open'))

        self.currentlevel = None

        # create the tree
        tree = QtWidgets.QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        tree.setIndentation(16)
        tree.currentItemChanged.connect(self.HandleItemChange)
        tree.itemActivated.connect(self.HandleItemActivated)

        # add items (globals.LevelNames is effectively a big category)
        tree.addTopLevelItems(self.ParseCategory(globals.LevelNames))

        # assign it to self.leveltree
        self.leveltree = tree

        # create the buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # create the layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.leveltree)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        self.layout = layout

        self.setMinimumWidth(320)  # big enough to fit "World 5: Freezeflame Volcano/Freezeflame Glacier"
        self.setMinimumHeight(384)

    def ParseCategory(self, items):
        """
        Parses a XML category
        """
        nodes = []
        for item in items:
            node = QtWidgets.QTreeWidgetItem()
            node.setText(0, item[0])
            # see if it's a category or a level
            if isinstance(item[1], str):
                # it's a level
                node.setData(0, Qt.UserRole, item[1])
                node.setToolTip(0, item[1])
            else:
                # it's a category
                children = self.ParseCategory(item[1])
                for cnode in children:
                    node.addChild(cnode)
                node.setToolTip(0, item[0])
            nodes.append(node)
        return tuple(nodes)

    def HandleItemChange(self, current, previous):
        """
        Catch the selected level and enable/disable OK button as needed
        """
        self.currentlevel = current.data(0, Qt.UserRole)
        if self.currentlevel is None:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            self.currentlevel = str(self.currentlevel)

    def HandleItemActivated(self, item, column):
        """
        Handle a doubleclick on a level
        """
        self.currentlevel = item.data(0, Qt.UserRole)
        if self.currentlevel is not None:
            self.currentlevel = str(self.currentlevel)
            self.accept()
