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

import json
from math import sqrt
import os
import re
import struct
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt

import globals

from items import ObjectItem, ZoneItem, LocationItem, SpriteItem
from items import EntranceItem, PathItem, NabbitPathItem
from items import PathEditorLineItem, NabbitPathEditorLineItem
from items import CommentItem

# from loading import LoadSpriteData, LoadSpriteListData
# from loading import LoadSpriteCategories, LoadEntranceNames

from misc import clipStr, setting, setSetting, drawForegroundGrid
from stamp import StampListModel

from tileset import TilesetTile, ObjectDef, objFitsInTileset
from tileset import addObjToTilesetImpl, addObjToTileset, exportObject
from tileset import HandleTilesetEdited, DeleteObject, RenderObject
from tileset import RenderObjectAll, ProcessOverrides, SimpleTilesetNames

from ui import createHorzLine, createVertLine, GetIcon
from verifications import SetDirty

#################################


class LevelOverviewWidget(QtWidgets.QWidget):
    """
    Widget that shows an overview of the level and can be clicked to move the view
    """
    moveIt = QtCore.pyqtSignal(int, int)

    def __init__(self):
        """
        Constructor for the level overview widget
        """
        super().__init__()
        self.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding))

        self.bgbrush = QtGui.QBrush(globals.theme.color('bg'))
        self.objbrush = QtGui.QBrush(globals.theme.color('overview_object'))
        self.viewbrush = QtGui.QBrush(globals.theme.color('overview_zone_fill'))
        self.view = QtCore.QRectF(0, 0, 0, 0)
        self.spritebrush = QtGui.QBrush(globals.theme.color('overview_sprite'))
        self.entrancebrush = QtGui.QBrush(globals.theme.color('overview_entrance'))
        self.locationbrush = QtGui.QBrush(globals.theme.color('overview_location_fill'))

        self.Reset()

        self.Xposlocator = 0
        self.Yposlocator = 0
        self.Hlocator = 50
        self.Wlocator = 80
        self.mainWindowScale = 1

    def Reset(self):
        """
        Resets the max and scale variables
        """
        self.CalcSize()
        self.Rescale()

    def mouseMoveEvent(self, event):
        """
        Handles mouse movement over the widget
        """
        QtWidgets.QWidget.mouseMoveEvent(self, event)

        if event.buttons() == Qt.LeftButton:
            self.moveIt.emit(event.pos().x() * self.posmult, event.pos().y() * self.posmult)

    def mousePressEvent(self, event):
        """
        Handles mouse pressing events over the widget
        """
        QtWidgets.QWidget.mousePressEvent(self, event)

        if event.button() == Qt.LeftButton:
            self.moveIt.emit(event.pos().x() * self.posmult, event.pos().y() * self.posmult)

    def paintEvent(self, event):
        """
        Paints the level overview widget
        """
        if not hasattr(globals.Area, 'layers'):
            # fixes race condition where this widget is painted after
            # the level is created, but before it's loaded
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        self.Reset()
        painter.scale(self.scale, self.scale)
        painter.fillRect(0, 0, 1024, 512, self.bgbrush)

        dr = painter.drawRect
        fr = painter.fillRect
        transform = QtGui.QTransform() / globals.TileWidth

        b = self.viewbrush
        painter.setPen(QtGui.QPen(globals.theme.color('overview_zone_lines'), 1))

        for zone in globals.Area.zones:
            r = transform.mapRect(zone.sceneBoundingRect())
            fr(r, b)
            dr(r)

        b = self.objbrush

        for layer in globals.Area.layers:
            for obj in layer:
                fr(obj.LevelRect, b)

        b = self.spritebrush

        for sprite in globals.Area.sprites:
            fr(sprite.LevelRect, b)

        b = self.entrancebrush

        for ent in globals.Area.entrances:
            fr(ent.LevelRect, b)

        b = self.locationbrush
        painter.setPen(QtGui.QPen(globals.theme.color('overview_location_lines'), 1))

        for location in globals.Area.locations:
            r = transform.mapRect(location.sceneBoundingRect())
            fr(r, b)
            dr(r)

        painter.setPen(QtGui.QPen(globals.theme.color('overview_viewbox'), 1))
        painter.drawRect(self.Xposlocator / globals.TileWidth / self.mainWindowScale,
                         self.Yposlocator / globals.TileWidth / self.mainWindowScale,
                         self.Wlocator / globals.TileWidth / self.mainWindowScale,
                         self.Hlocator / globals.TileWidth / self.mainWindowScale)

    def CalcSize(self):
        """
        Calculates all the required sizes for this scale
        """
        if not globals.Area:
            self.maxX = 0
            self.maxY = 0
            return

        transform = QtGui.QTransform() / globals.TileWidth
        rect = QtCore.QRectF()

        for zone in globals.Area.zones:
            rect |= transform.mapRect(zone.sceneBoundingRect())

        for layer in globals.Area.layers:
            for obj in layer:
                rect |= obj.LevelRect

        for sprite in globals.Area.sprites:
            rect |= sprite.LevelRect

        for ent in globals.Area.entrances:
            rect |= ent.LevelRect

        for location in globals.Area.locations:
            rect |= transform.mapRect(location.sceneBoundingRect())

        self.maxX = rect.right()
        self.maxY = rect.bottom()

    def Rescale(self):
        """
        Calculates self.scale and self.posmult
        """
        self.scale = max(0.002, min(self.width() / (self.maxX + 45), self.height() / (self.maxY + 25)))
        self.posmult = globals.TileWidth / self.scale

class ObjectPickerWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available objects
    """

    def __init__(self):
        """
        Initializes the widget
        """

        super().__init__()
        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setLayoutMode(QtWidgets.QListView.SinglePass)
        self.setMovement(QtWidgets.QListView.Static)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setWrapping(True)

        self.objTS123Tab = globals.mainWindow.objTS123Tab

        self.m0 = self.ObjectListModel()
        self.mall = self.ObjectListModel()
        self.m123 = self.objTS123Tab.getModels()
        self.setModel(self.m0)

        self.setItemDelegate(self.ObjectItemDelegate())

        self.clicked.connect(self.HandleObjReplace)

    def contextMenuEvent(self, event):
        """
        Creates and shows the right-click menu
        """
        if globals.CurrentPaintType in [0, 10]:
            return QtWidgets.QListView.contextMenuEvent(self, event)

        self.menu = QtWidgets.QMenu(self)

        export = QtWidgets.QAction('Export', self)
        export.triggered.connect(self.HandleObjExport)

        replace = QtWidgets.QAction('Replace', self)
        replace.triggered.connect(self.HandleObjImportReplace)

        delete = QtWidgets.QAction('Delete', self)
        delete.triggered.connect(self.HandleObjDelete)

        delIns = QtWidgets.QAction('Delete instances', self)
        delIns.triggered.connect(self.HandleObjDeleteInstances)

        self.menu.addAction(export)
        self.menu.addAction(replace)
        self.menu.addAction(delete)
        self.menu.addAction(delIns)

        self.menu.popup(QtGui.QCursor.pos())

    def LoadFromTilesets(self):
        """
        Renders all the object previews
        """
        self.m0.LoadFromTileset(0)
        self.objTS123Tab.LoadFromTilesets()

    def ShowTileset(self, id):
        """
        Shows a specific tileset in the picker
        """
        sel = self.currentIndex().row()
        if id == 0: self.setModel(self.m0)
        elif id == 1: self.setModel(self.mall)
        else: self.setModel(self.objTS123Tab.getActiveModel())

        globals.CurrentObject = -1
        self.clearSelection()

    def currentChanged(self, current, previous):
        """
        Throws a signal when the selected object changed
        """
        self.ObjChanged.emit(current.row())

    def HandleObjReplace(self, index):
        """
        Throws a signal when the selected object is used as a replacement
        """
        if QtWidgets.QApplication.keyboardModifiers() == Qt.AltModifier:
            self.ObjReplace.emit(index.row())

    def HandleObjExport(self, index):
        """
        Exports an object from the tileset
        """
        file = QtWidgets.QFileDialog.getSaveFileName(None, "Save Objects", "", "Object files (*.json)")[0]
        if not file:
            return

        name = os.path.splitext(file)[0]
        baseName = os.path.basename(name)

        idx = globals.CurrentPaintType
        objNum = globals.CurrentObject

        exportObject(name, baseName, idx, objNum)

    def HandleObjImportReplace(self, index):
        """
        Imports a replacement for the selected object
        """
        idx = globals.CurrentPaintType
        objNum = globals.CurrentObject

        if objNum == -1: return

        # Get the json file
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open Object", '',
                    "Object files (*.json)")[0]

        if not file: return

        with open(file) as inf:
            jsonData = json.load(inf)

        dir = os.path.dirname(file)

        # Read the other files
        with open(dir + "/" + jsonData["meta"], "rb") as inf:
            indexfile = inf.read()

        with open(dir + "/" + jsonData["objlyt"], "rb") as inf:
            deffile = inf.read()

        with open(dir + "/" + jsonData["colls"], "rb") as inf:
            colls = inf.read()

        # Get the object's definition
        indexstruct = struct.Struct('>HBBH')

        data = indexstruct.unpack_from(indexfile, 0)
        obj = ObjectDef()
        obj.width = data[1]
        obj.height = data[2]

        if "randLen" in jsonData:
            obj.randByte = data[3]

        else:
            obj.randByte = 0

        obj.load(deffile, 0)

        # Get the image and normal map
        img = QtGui.QPixmap(dir + "/" + jsonData["img"])
        nml = QtGui.QPixmap(dir + "/" + jsonData["nml"])

        # Temporarily remove the selected object
        oObj = globals.ObjectDefinitions[idx].pop(objNum)
        globals.ObjectDefinitions[idx].append(None)

        # Check if the replacement fits
        fits = objFitsInTileset(obj, idx)

        # Restore the selected object
        del globals.ObjectDefinitions[idx][-1]
        globals.ObjectDefinitions[idx][objNum:objNum] = [oObj]

        # Throw warning and return if the replacement doesn't fit
        if not fits:
            QtWidgets.QMessageBox.critical(self, 'Cannot Delete', 'Replacement doesn\'t fit ' \
                                                                  'in the tileset')
            return

        # Delete the selected object (using soft deletion)
        DeleteObject(idx, objNum, True)

        # Add the replacement in place of the previously deleted object
        obj = addObjToTilesetImpl(obj, colls, img, nml, idx, fits)
        globals.ObjectDefinitions[idx][objNum] = obj

        # Update all instances of the replaced object in the scene
        for obj in globals.mainWindow.scene.items():
            if isinstance(obj, ObjectItem) and obj.tileset == idx and obj.type == objNum:
                obj.update()

        # Set related flags
        HandleTilesetEdited()
        SetDirty()

        # Clear selection in the palette to avoid a bug
        globals.CurrentObject = -1
        self.clearSelection()

    def HandleObjDelete(self, index):
        """
        Deletes an object from the tileset
        """
        idx = globals.CurrentPaintType
        objNum = globals.CurrentObject

        if objNum == -1: return

        # Check if the object is deletable
        matchingObjs = []

        ## Check if the object is in the scene
        for layer in globals.Area.layers:
            for obj in layer:
                if obj.tileset == idx and obj.type == objNum:
                    matchingObjs.append(obj)

        if matchingObjs:
            where = [('(%d, %d)' % (obj.objx, obj.objy)) for obj in matchingObjs]
            dlgTxt = "You can't delete this object because there are instances of it at the following coordinates:\n"
            dlgTxt += ', '.join(where)
            dlgTxt += '\nPlease remove or replace them before deleting this object.'

            QtWidgets.QMessageBox.critical(self, 'Cannot Delete', dlgTxt)
            return

        ## Check if the object is used as a stamp
        usedAsStamp = False
        for stamp in globals.mainWindow.stampChooser.model.items:
            layers, _ = globals.mainWindow.getEncodedObjects(stamp.MiyamotoClip, False)
            for layer in layers:
                for obj in layer:
                    if obj.tileset == idx and obj.type == objNum:
                        usedAsStamp = True
                        break
                if usedAsStamp: break
            if usedAsStamp: break

        if usedAsStamp:
            dlgTxt = "You can't delete this object because it is used as a stamp."
            dlgTxt += '\nPlease remove the stamp before deleting this object.'

            QtWidgets.QMessageBox.critical(self, 'Cannot Delete', dlgTxt)
            return

        ## Check if the object is in the clipboard
        inClipboard = False
        if globals.mainWindow.clipboard is not None:
            if globals.mainWindow.clipboard.startswith('MiyamotoClip|') and globals.mainWindow.clipboard.endswith('|%'):
                layers, _ = globals.mainWindow.getEncodedObjects(globals.mainWindow.clipboard, False)
                for layer in layers:
                    for obj in layer:
                        if obj.tileset == idx and obj.type == objNum:
                            inClipboard = True
                            break
                    if inClipboard:
                        break

        if inClipboard:
            dlgTxt = "You can't delete this object because it is in the clipboard."
            dlgTxt += '\nDo you want to empty the clipboard?.'

            result = QtWidgets.QMessageBox.warning(self, 'Cannot Delete', dlgTxt,
                                                   QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if result != QtWidgets.QMessageBox.Yes:
                return

            # Empty the clipboard
            globals.mainWindow.clipboard = None
            globals.mainWindow.actions['paste'].setEnabled(False)

            dlgTxt = "The clipboard has been emptied."
            dlgTxt += '\nDo you want to proceed with deleting the object?'

            result = QtWidgets.QMessageBox.warning(self, 'Cannot Delete', dlgTxt,
                                                   QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if result != QtWidgets.QMessageBox.Yes:
                return

        DeleteObject(idx, objNum)
        HandleTilesetEdited()

        if not (globals.Area.tileset1 or globals.Area.tileset2 or globals.Area.tileset3):
            globals.CurrentObject = -1

        globals.mainWindow.scene.update()
        SetDirty()

    def HandleObjDeleteInstances(self, index):
        """
        Deletes all instances of an object from the level scene
        """
        idx = globals.CurrentPaintType
        objNum = globals.CurrentObject

        if objNum == -1: return

        # Check if the object is in the scene
        matchingObjs = []
        for i, layer in enumerate(globals.Area.layers):
            for j, obj in enumerate(layer):
                if obj.tileset == idx and obj.type == objNum:
                    matchingObjs.append(obj)

        if not matchingObjs:
            return

        dlgTxt = "Are you sure you want to remove all instances of this object from the scene?"
        dlgTxt += '\nThis cannot be undone!'

        result = QtWidgets.QMessageBox.warning(self, 'Confirm', dlgTxt,
                                               QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if result != QtWidgets.QMessageBox.Yes:
            return

        for obj in matchingObjs:
            obj.delete()
            obj.setSelected(False)
            globals.mainWindow.scene.removeItem(obj)
            globals.mainWindow.levelOverview.update()
            del obj

        globals.mainWindow.scene.update()
        SetDirty()
        globals.mainWindow.SelectionUpdateFlag = False
        globals.mainWindow.ChangeSelectionHandler()

    ObjChanged = QtCore.pyqtSignal(int)
    ObjReplace = QtCore.pyqtSignal(int)

    class ObjectItemDelegate(QtWidgets.QAbstractItemDelegate):
        """
        Handles tileset objects and their rendering
        """

        def paint(self, painter, option, index):
            """
            Paints an object
            """
            if option.state & QtWidgets.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            p = index.model().data(index, Qt.DecorationRole)
            painter.drawPixmap(option.rect.x() + 2, option.rect.y() + 2, p)
            # painter.drawText(option.rect, str(index.row()))

        def sizeHint(self, option, index):
            """
            Returns the size for the object
            """
            p = index.model().data(index, Qt.UserRole)
            return p or QtCore.QSize(globals.TileWidth, globals.TileWidth)
            # return QtCore.QSize(76,76)

    class ObjectListModel(QtCore.QAbstractListModel):
        """
        Model containing all the objects in a tileset
        """

        def __init__(self):
            """
            Initializes the model
            """
            super().__init__()
            self.items = []
            self.ritems = []
            self.itemsize = []

            for i in range(256):
                self.items.append(None)
                self.ritems.append(None)

        def rowCount(self, parent=None):
            """
            Required by Qt
            """
            return len(self.items)

        def data(self, index, role=Qt.DisplayRole):
            """
            Get what we have for a specific row
            """
            if not index.isValid(): return None
            n = index.row()
            if n < 0: return None
            if n >= len(self.items): return None

            if role == Qt.DecorationRole and n < len(self.ritems):
                return self.ritems[n]

            if role == Qt.BackgroundRole:
                return QtWidgets.qApp.palette().base()

            if role == Qt.UserRole and n < len(self.itemsize):
                return self.itemsize[n]

            if role == Qt.ToolTipRole and n < len(self.tooltips):
                return self.tooltips[n]

            return None

        def LoadFromTileset(self, idx):
            """
            Renders all the object previews for the model
            """
            self.items = []
            self.ritems = []
            self.itemsize = []
            self.tooltips = []

            self.beginResetModel()

            globals.numObj = []

            z = 0

            if idx == 4:
                numTileset = range(1, 4)
            else:
                numTileset = [idx]

            for idx in numTileset:
                if globals.ObjectDefinitions[idx] is None:
                    globals.numObj.append(z)
                    continue

                defs = globals.ObjectDefinitions[idx]

                for i in range(256):
                    if defs[i] is None:
                        break

                    obj = RenderObject(idx, i, defs[i].width, defs[i].height, True)
                    self.items.append(obj)

                    pm = QtGui.QPixmap(defs[i].width * globals.TileWidth, defs[i].height * globals.TileWidth)
                    pm.fill(Qt.transparent)
                    p = QtGui.QPainter()
                    p.begin(pm)
                    y = 0
                    isAnim = False

                    for row in obj:
                        x = 0
                        for tile in row:
                            if tile != -1:
                                try:
                                    if isinstance(globals.Tiles[tile].main, QtGui.QImage):
                                        p.drawImage(x, y, globals.Tiles[tile].main)
                                    else:
                                        p.drawPixmap(x, y, globals.Tiles[tile].main)
                                except AttributeError:
                                    break
                                if isinstance(globals.Tiles[tile], TilesetTile) and globals.Tiles[tile].isAnimated: isAnim = True
                            x += globals.TileWidth
                        y += globals.TileWidth
                    p.end()

                    pm = pm.scaledToWidth(pm.width() * 32 / globals.TileWidth, Qt.SmoothTransformation)
                    if pm.width() > 256:
                        pm = pm.scaledToWidth(256, Qt.SmoothTransformation)
                    if pm.height() > 256:
                        pm = pm.scaledToHeight(256, Qt.SmoothTransformation)

                    self.ritems.append(pm)
                    self.itemsize.append(QtCore.QSize(pm.width() + 4, pm.height() + 4))
                    if (idx == 0) and (i in globals.ObjDesc) and isAnim:
                        self.tooltips.append(globals.trans.string('Objects', 4, '[tileset]', idx+1, '[id]', i, '[desc]', globals.ObjDesc[i]))
                    elif (idx == 0) and (i in globals.ObjDesc):
                        self.tooltips.append(globals.trans.string('Objects', 3, '[tileset]', idx+1, '[id]', i, '[desc]', globals.ObjDesc[i]))
                    elif isAnim:
                        self.tooltips.append(globals.trans.string('Objects', 2, '[tileset]', idx+1, '[id]', i))
                    else:
                        self.tooltips.append(globals.trans.string('Objects', 1, '[tileset]', idx+1, '[id]', i))

                    z += 1

                globals.numObj.append(z)

            self.endResetModel()

        def LoadFromFolder(self):
            """
            Renders all the object previews for the model from a folder
            """
            globals.ObjectAllDefinitions = []
            globals.ObjectAllCollisions = []
            globals.ObjectAllImages = []

            self.items = []
            self.ritems = []
            self.itemsize = []
            self.tooltips = []

            self.beginResetModel()

            # Fixes issues if the user selects the wrong Objects Folder
            if not globals.mainWindow.folderPicker.currentText():
                self.endResetModel()
                return

            z = 0
            top_folder = os.path.join(setting('ObjPath'), globals.mainWindow.folderPicker.currentText())

            # Get the list of files in the folder
            files = os.listdir(top_folder)
            ## Sort the files through "Natural sorting" (opposite of "Lexicographic sorting")
            files.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)])

            # Discard files not enging with ".json" from the list
            files_ = [file for file in files if file[-5:] == ".json"]
            del files

            for file in files_:
                dir = top_folder + "/"

                with open(dir + file) as inf:
                    jsonData = json.load(inf)

                if not ("colls" in jsonData and "meta" in jsonData and "objlyt" in jsonData
                        and "img" in jsonData and "nml" in jsonData):

                    # Invalid object JSON
                    continue

                # Check for the required files
                found = True
                for f in ["colls", "meta", "objlyt", "img", "nml"]:
                    if not os.path.isfile(dir + jsonData[f]):
                        print("%s not found!" % (dir + jsonData[f]))
                        found = False
                        break

                if not found:
                    # One of the required files is missing
                    continue

                with open(dir + jsonData["colls"], "rb") as inf:
                    globals.ObjectAllCollisions.append(inf.read())

                with open(dir + jsonData["meta"], "rb") as inf:
                    indexfile = inf.read()

                with open(dir + jsonData["objlyt"], "rb") as inf:
                    deffile = inf.read()

                # Read the object definition file into Object instances
                indexstruct = struct.Struct('>HBBH')

                data = indexstruct.unpack_from(indexfile, 0)
                def_ = ObjectDef()
                def_.width = data[1]
                def_.height = data[2]
                def_.folderIndex = globals.mainWindow.folderPicker.currentIndex()
                def_.objAllIndex = z

                if "randLen" in jsonData:
                    def_.randByte = data[3]

                else:
                    def_.randByte = 0

                def_.load(deffile, 0)

                globals.ObjectAllDefinitions.append(def_)

                # Get the properly rendered object definition
                obj = RenderObjectAll(def_, def_.width, def_.height, True)
                self.items.append(obj)

                globals.ObjectAllImages.append([QtGui.QPixmap(dir + jsonData["img"]),
                                        QtGui.QPixmap(dir + jsonData["nml"])])

                img, nml = globals.ObjectAllImages[-1]

                # Render said object definition for the preview
                tilesUsed = {}
                tiles = [None] * def_.width * def_.height

                # Load the tiles of the object for the preview
                ## Start by creating a TilesetTile instance for each tile
                if def_.reversed:
                    for crow, row in enumerate(def_.rows):
                        if def_.subPartAt != -1:
                            if crow >= def_.subPartAt:
                                crow -= def_.subPartAt

                            else:
                                crow += def_.height - def_.subPartAt

                        x = 0
                        y = crow

                        for tile in row:
                            if len(tile) == 3:
                                if tile != [0, 0, 0]:
                                    tilesUsed[tile[1] & 0x3FF] = y * def_.width + x
                                    tiles[y * def_.width + x] = TilesetTile(img.copy(x * 60, y * 60, 60, 60), nml.copy(x * 60, y * 60, 60, 60))

                                x += 1

                else:
                    for crow, row in enumerate(def_.rows):
                        x = 0
                        y = crow

                        for tile in row:
                            if len(tile) == 3:
                                if tile != [0, 0, 0]:
                                    tilesUsed[tile[1] & 0x3FF] = y * def_.width + x
                                    tiles[y * def_.width + x] = TilesetTile(img.copy(x * 60, y * 60, 60, 60), nml.copy(x * 60, y * 60, 60, 60))

                                x += 1

                # Start painting the preview
                pm = QtGui.QPixmap(def_.width * 60, def_.height * 60)
                pm.fill(Qt.transparent)
                p = QtGui.QPainter()
                p.begin(pm)
                y = 0

                for row in obj:
                    x = 0
                    for tile in row:
                        if tile != -1:
                            if tile in tilesUsed:
                                p.drawPixmap(x, y, tiles[tilesUsed[tile]].main)
                            else:
                                try:
                                    if isinstance(globals.Tiles[tile].main, QtGui.QImage):
                                        p.drawImage(x, y, globals.Tiles[tile].main)
                                    else:
                                        p.drawPixmap(x, y, globals.Tiles[tile].main)
                                except AttributeError:
                                    break
                        x += 60
                    y += 60
                p.end()

                # Resize the preview for a good looking layout
                pm = pm.scaledToWidth(pm.width() * 32 / globals.TileWidth, Qt.SmoothTransformation)
                if pm.width() > 256:
                    pm = pm.scaledToWidth(256, Qt.SmoothTransformation)
                if pm.height() > 256:
                    pm = pm.scaledToHeight(256, Qt.SmoothTransformation)

                self.ritems.append(pm)
                self.itemsize.append(QtCore.QSize(pm.width() + 4, pm.height() + 4))
                self.tooltips.append(globals.trans.string('Objects', 5, '[id]', z))

                z += 1

            self.endResetModel()


class StampChooserWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available stamps
    """
    selectionChangedSignal = QtCore.pyqtSignal()

    def __init__(self):
        """
        Initializes the widget
        """
        super().__init__()

        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setLayoutMode(QtWidgets.QListView.SinglePass)
        self.setMovement(QtWidgets.QListView.Static)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setWrapping(True)

        self.model = StampListModel()
        self.setModel(self.model)

        self.setItemDelegate(StampChooserWidget.StampItemDelegate())

    class StampItemDelegate(QtWidgets.QStyledItemDelegate):
        """
        Handles stamp rendering
        """

        def __init__(self):
            """
            Initializes the delegate
            """
            super().__init__()

        def createEditor(self, parent, option, index):
            """
            Creates a stamp name editor
            """
            return QtWidgets.QLineEdit(parent)

        def setEditorData(self, editor, index):
            """
            Sets the data for the stamp name editor from the data at index
            """
            editor.setText(index.model().data(index, Qt.UserRole + 1))

        def setModelData(self, editor, model, index):
            """
            Set the data in the model for the data at index
            """
            index.model().setData(index, editor.text())

        def paint(self, painter, option, index):
            """
            Paints a stamp
            """

            if option.state & QtWidgets.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            painter.drawPixmap(option.rect.x() + 2, option.rect.y() + 2, index.model().data(index, Qt.DecorationRole))

        def sizeHint(self, option, index):
            """
            Returns the size for the stamp
            """
            return index.model().data(index, Qt.DecorationRole).size() + QtCore.QSize(4, 4)

    def addStamp(self, stamp):
        """
        Adds a stamp
        """
        self.model.addStamp(stamp)

    def removeStamp(self, stamp):
        """
        Removes a stamp
        """
        self.model.removeStamp(stamp)

    def currentlySelectedStamp(self):
        """
        Returns the currently selected stamp
        """
        idxobj = self.currentIndex()
        if idxobj.row() == -1: return
        return self.model.items[idxobj.row()]

    def selectionChanged(self, selected, deselected):
        """
        Called when the selection changes.
        """
        val = super().selectionChanged(selected, deselected)
        self.selectionChangedSignal.emit()
        return val


class SpritePickerWidget(QtWidgets.QTreeWidget):
    """
    Widget that shows a list of available sprites
    """

    def __init__(self):
        """
        Initializes the widget
        """
        super().__init__()
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.currentItemChanged.connect(self.HandleItemChange)

        import loading
        loading.LoadSpriteData()
        loading.LoadSpriteListData()
        loading.LoadSpriteCategories()
        del loading

        self.LoadItems()

    def LoadItems(self):
        """
        Loads tree widget items
        """
        self.clear()

        for viewname, view, nodelist in globals.SpriteCategories:
            for n in nodelist: nodelist.remove(n)
            for catname, category in view:
                cnode = QtWidgets.QTreeWidgetItem()
                cnode.setText(0, catname)
                cnode.setData(0, Qt.UserRole, -1)

                isSearch = (catname == globals.trans.string('Sprites', 16))
                if isSearch:
                    self.SearchResultsCategory = cnode
                    SearchableItems = []

                for id in category:
                    snode = QtWidgets.QTreeWidgetItem()
                    if id == 9999:
                        snode.setText(0, globals.trans.string('Sprites', 17))
                        snode.setData(0, Qt.UserRole, -2)
                        self.NoSpritesFound = snode
                    else:
                        sdef = globals.Sprites[id] if 0 <= id < globals.NumSprites else None
                        snode.setText(0, globals.trans.string('Sprites', 18, '[id]', id, '[name]', "UNKNOWN" if sdef is None else sdef.name))
                        snode.setData(0, Qt.UserRole, id)

                    if isSearch:
                        SearchableItems.append(snode)

                    cnode.addChild(snode)

                self.addTopLevelItem(cnode)
                cnode.setHidden(True)
                nodelist.append(cnode)

        self.ShownSearchResults = SearchableItems
        self.NoSpritesFound.setHidden(True)

        self.itemClicked.connect(self.HandleSprReplace)

        self.SwitchView(globals.SpriteCategories[0])

    def SwitchView(self, view):
        """
        Changes the selected sprite view
        """
        for i in range(0, self.topLevelItemCount()):
            self.topLevelItem(i).setHidden(True)

        for node in view[2]:
            node.setHidden(False)

    def HandleItemChange(self, current, previous):
        """
        Throws a signal when the selected object changed
        """
        if current is None: return
        id = current.data(0, Qt.UserRole)
        if id != -1:
            self.SpriteChanged.emit(id)

    def SetSearchString(self, searchfor):
        """
        Shows the items containing that string
        """
        check = self.SearchResultsCategory

        rawresults = self.findItems(searchfor, Qt.MatchContains | Qt.MatchRecursive)
        results = list(filter((lambda x: x.parent() == check), rawresults))

        for x in self.ShownSearchResults: x.setHidden(True)
        for x in results: x.setHidden(False)
        self.ShownSearchResults = results

        self.NoSpritesFound.setHidden((len(results) != 0))
        self.SearchResultsCategory.setExpanded(True)

    def HandleSprReplace(self, item, column):
        """
        Throws a signal when the selected sprite is used as a replacement
        """
        if QtWidgets.QApplication.keyboardModifiers() == Qt.AltModifier:
            id = item.data(0, Qt.UserRole)
            if id != -1:
                self.SpriteReplace.emit(id)

    SpriteChanged = QtCore.pyqtSignal(int)
    SpriteReplace = QtCore.pyqtSignal(int)


class SpriteEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing sprite data
    """
    DataUpdate = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create the raw editor
        font = QtGui.QFont()
        font.setPointSize(8)
        editbox = QtWidgets.QLabel(globals.trans.string('SpriteDataEditor', 3))
        editbox.setFont(font)
        edit = QtWidgets.QLineEdit()
        edit.textEdited.connect(self.HandleRawDataEdited)
        self.raweditor = edit

        editboxlayout = QtWidgets.QHBoxLayout()
        editboxlayout.addWidget(editbox)
        editboxlayout.addWidget(edit)
        editboxlayout.setStretch(1, 1)

        # 'Editing Sprite #' label
        self.spriteLabel = QtWidgets.QLabel('-')
        self.spriteLabel.setWordWrap(True)

        self.noteButton = QtWidgets.QToolButton()
        self.noteButton.setIcon(GetIcon('note'))
        self.noteButton.setText(globals.trans.string('SpriteDataEditor', 4))
        self.noteButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.noteButton.setAutoRaise(True)
        self.noteButton.clicked.connect(self.ShowNoteTooltip)

        self.relatedObjFilesButton = QtWidgets.QToolButton()
        self.relatedObjFilesButton.setIcon(GetIcon('data'))
        self.relatedObjFilesButton.setText(globals.trans.string('SpriteDataEditor', 7))
        self.relatedObjFilesButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.relatedObjFilesButton.setAutoRaise(True)
        self.relatedObjFilesButton.clicked.connect(self.ShowRelatedObjFilesTooltip)

        toplayout = QtWidgets.QHBoxLayout()
        toplayout.addWidget(self.spriteLabel)
        toplayout.addStretch(1)
        toplayout.addWidget(self.relatedObjFilesButton)
        toplayout.addWidget(self.noteButton)

        subLayout = QtWidgets.QVBoxLayout()
        subLayout.setContentsMargins(0, 0, 0, 0)

        # create a layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(toplayout)
        mainLayout.addLayout(subLayout)

        layout = QtWidgets.QGridLayout()
        self.editorlayout = layout
        subLayout.addLayout(layout)
        subLayout.addLayout(editboxlayout)

        self.setLayout(mainLayout)

        self.activeLayer = QtWidgets.QComboBox()
        self.activeLayer.addItems(globals.trans.stringList('SpriteDataEditor', 10))
        self.activeLayer.setToolTip(globals.trans.string('SpriteDataEditor', 11))
        self.activeLayer.activated.connect(globals.mainWindow.SpriteLayerUpdated)

        self.initialState = QtWidgets.QSpinBox()
        self.initialState.setRange(0, 255)
        self.initialState.setToolTip(globals.trans.string('SpriteDataEditor', 13))
        self.initialState.valueChanged.connect(globals.mainWindow.SpriteInitialStateUpdated)

        self.spritetype = -1
        self.data = b'\0' * 12
        self.fields = []
        self.UpdateFlag = False
        self.DefaultMode = defaultmode

        self.notes = None
        self.relatedObjFiles = None

    class PropertyDecoder(QtCore.QObject):
        """
        Base class for all the sprite data decoder/encoders
        """
        updateData = QtCore.pyqtSignal('PyQt_PyObject')

        def retrieve(self, data):
            """
            Extracts the value from the specified bit(s). Bit numbering is ltr BE
            and starts at 1.
            """
            bit = self.bit

            if isinstance(bit, tuple):
                if bit[1] == bit[0] + 7 and bit[0] & 1 == 1:
                    # optimise if it's just one byte
                    return data[bit[0] >> 3]

                else:
                    # we have to calculate it sadly
                    # just do it by looping, shouldn't be that bad

                    value = 0
                    for n in range(bit[0], bit[1]):
                        n -= 1
                        value = (value << 1) | ((data[n >> 3] >> (7 - (n & 7))) & 1)

                    return value

            else:
                # we just want one bit
                bit -= 1

                if (bit >> 3) >= len(data):
                    return 0

                return (data[bit >> 3] >> (7 - (bit & 7))) & 1

        def insertvalue(self, data, value):
            """
            Assigns a value to the specified bit(s)
            """
            bit = self.bit
            sdata = list(data)

            if isinstance(bit, tuple):
                if bit[1] == bit[0] + 7 and bit[0] & 1 == 1:
                    # just one byte, this is easier
                    sdata[(bit[0] - 1) >> 3] = value & 0xFF

                else:
                    # complicated stuff
                    for n in reversed(range(bit[0], bit[1])):
                        off = 1 << (7 - ((n - 1) & 7))

                        if value & 1:
                            # set the bit
                            sdata[(n - 1) >> 3] |= off

                        else:
                            # mask the bit out
                            sdata[(n - 1) >> 3] &= 0xFF ^ off

                        value >>= 1

            else:
                # only overwrite one bit
                byte = (bit - 1) >> 3
                if byte >= len(data):
                    return 0

                off = 1 << (7 - ((bit - 1) & 7))

                if value & 1:
                    # set the bit
                    sdata[byte] |= off

                else:
                    # mask the bit out
                    sdata[byte] &= 0xFF ^ off

            return bytes(sdata)

    class CheckboxPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a checkbox
        """

        def __init__(self, title, bit, mask, comment, layout, row):
            """
            Creates the widget
            """
            super().__init__()

            self.widget = QtWidgets.QCheckBox(title)

            if comment is not None:
                self.widget.setToolTip(comment)

            self.widget.clicked.connect(self.HandleClick)

            if isinstance(bit, tuple):
                length = bit[1] - bit[0] + 1

            else:
                length = 1

            xormask = 0
            for i in range(length):
                xormask |= 1 << i

            self.bit = bit
            self.mask = mask
            self.xormask = xormask
            layout.addWidget(self.widget, row, 0, 1, 2)

        def update(self, data):
            """
            Updates the value shown by the widget
            """
            value = ((self.retrieve(data) & self.mask) == self.mask)
            self.widget.setChecked(value)

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            value = self.retrieve(data) & (self.mask ^ self.xormask)

            if self.widget.isChecked():
                value |= self.mask

            return self.insertvalue(data, value)

        def HandleClick(self, clicked=False):
            """
            Handles clicks on the checkbox
            """
            self.updateData.emit(self)

    class ListPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a combobox
        """

        def __init__(self, title, bit, model, comment, layout, row):
            """
            Creates the widget
            """
            super().__init__()

            self.model = model
            self.widget = QtWidgets.QComboBox()
            self.widget.setModel(model)

            if comment is not None:
                self.widget.setToolTip(comment)

            self.widget.currentIndexChanged.connect(self.HandleIndexChanged)

            self.bit = bit
            layout.addWidget(QtWidgets.QLabel(title + ':'), row, 0, Qt.AlignRight)
            layout.addWidget(self.widget, row, 1)

        def update(self, data):
            """
            Updates the value shown by the widget
            """
            value = self.retrieve(data)
            if not self.model.existingLookup[value]:
                self.widget.setCurrentIndex(-1)
                return

            for i, x in enumerate(self.model.entries):
                if x[0] == value:
                    self.widget.setCurrentIndex(i)
                    break

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            return self.insertvalue(data, self.model.entries[self.widget.currentIndex()][0])

        def HandleIndexChanged(self, index):
            """
            Handle the current index changing in the combobox
            """
            if index < 0:
                return

            self.updateData.emit(self)

    class ValuePropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a spinbox
        """

        def __init__(self, title, bit, max, comment, layout, row):
            """
            Creates the widget
            """
            super().__init__()

            self.widget = QtWidgets.QSpinBox()
            self.widget.setRange(0, max - 1)

            if comment is not None:
                self.widget.setToolTip(comment)

            self.widget.valueChanged.connect(self.HandleValueChanged)

            self.bit = bit
            layout.addWidget(QtWidgets.QLabel(title + ':'), row, 0, Qt.AlignRight)
            layout.addWidget(self.widget, row, 1)

        def update(self, data):
            """
            Updates the value shown by the widget
            """
            value = self.retrieve(data)
            self.widget.setValue(value)

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            return self.insertvalue(data, self.widget.value())

        def HandleValueChanged(self, value):
            """
            Handle the value changing in the spinbox
            """
            self.updateData.emit(self)

    class BitfieldPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a bitfield
        """

        def __init__(self, title, startbit, bitnum, comment, layout, row):
            """
            Creates the widget
            """
            super().__init__()

            self.startbit = startbit
            self.bitnum = bitnum

            self.widgets = []

            CheckboxLayout = QtWidgets.QGridLayout()
            CheckboxLayout.setContentsMargins(0, 0, 0, 0)

            for i in range(bitnum):
                c = QtWidgets.QCheckBox()
                self.widgets.append(c)
                CheckboxLayout.addWidget(c, 0, i)

                if comment is not None:
                    c.setToolTip(comment)

                c.toggled.connect(self.HandleValueChanged)

                L = QtWidgets.QLabel(str(i + 1))
                CheckboxLayout.addWidget(L, 1, i)
                CheckboxLayout.setAlignment(L, Qt.AlignHCenter)

            w = QtWidgets.QWidget()
            w.setLayout(CheckboxLayout)

            layout.addWidget(QtWidgets.QLabel(title + ':'), row, 0, Qt.AlignRight)
            layout.addWidget(w, row, 1)

        def update(self, data):
            """
            Updates the value shown by the widget
            """
            for bitIdx in range(self.bitnum):
                checkbox = self.widgets[bitIdx]

                adjustedIdx = bitIdx + self.startbit
                byteNum = adjustedIdx // 8
                bitNum = adjustedIdx % 8
                checkbox.setChecked((data[byteNum] >> (7 - bitNum) & 1))

        def assign(self, data):
            """
            Assigns the checkbox states to the data
            """
            data = bytearray(data)

            for idx in range(self.bitnum):
                checkbox = self.widgets[idx]

                adjustedIdx = idx + self.startbit
                byteIdx = adjustedIdx // 8
                bitIdx = adjustedIdx % 8

                origByte = data[byteIdx]
                origBit = (origByte >> (7 - bitIdx)) & 1
                newBit = 1 if checkbox.isChecked() else 0

                if origBit == newBit:
                    continue

                if origBit == 0 and newBit == 1:
                    # Turn the byte on by OR-ing it in
                    newByte = (origByte | (1 << (7 - bitIdx))) & 0xFF

                else:
                    # Turn it off by:
                    # inverting it
                    # OR-ing in the new byte
                    # inverting it back
                    newByte = ~origByte & 0xFF
                    newByte = newByte | (1 << (7 - bitIdx))
                    newByte = ~newByte & 0xFF

                data[byteIdx] = newByte

            return bytes(data)

        def HandleValueChanged(self, value):
            """
            Handle any checkbox being changed
            """
            self.updateData.emit(self)

    def setSprite(self, type, reset=False):
        """
        Change the sprite type used by the data editor
        """
        if (self.spritetype == type) and not reset: return

        self.spritetype = type
        if type != 1000 and 0 <= type < globals.NumSprites:
            sprite = globals.Sprites[type]

        else:
            sprite = None

        # remove all the existing widgets in the layout
        layout = self.editorlayout
        for row in range(2, layout.rowCount()):
            for column in range(0, layout.columnCount()):
                w = layout.itemAtPosition(row, column)
                if w is not None:
                    widget = w.widget()
                    layout.removeWidget(widget)
                    widget.setParent(None)

        if sprite is None:
            self.spriteLabel.setText(globals.trans.string('SpriteDataEditor', 5, '[id]', type))
            self.noteButton.setVisible(False)

            # use the raw editor if nothing is there
            self.raweditor.setVisible(True)
            if len(self.fields) > 0:
                self.fields = []

        else:
            self.spriteLabel.setText(globals.trans.string('SpriteDataEditor', 6, '[id]', type, '[name]', sprite.name))

            self.noteButton.setVisible(sprite.notes is not None)
            self.notes = sprite.notes

            self.relatedObjFilesButton.setVisible(sprite.relatedObjFiles is not None)
            self.relatedObjFiles = sprite.relatedObjFiles

            # create all the new fields
            fields = []
            row = 2

            for f in sprite.fields:
                if f[0] == 0:
                    nf = SpriteEditorWidget.CheckboxPropertyDecoder(f[1], f[2], f[3], f[4], layout, row)

                elif f[0] == 1:
                    nf = SpriteEditorWidget.ListPropertyDecoder(f[1], f[2], f[3], f[4], layout, row)

                elif f[0] == 2:
                    nf = SpriteEditorWidget.ValuePropertyDecoder(f[1], f[2], f[3], f[4], layout, row)

                elif f[0] == 3:
                    nf = SpriteEditorWidget.BitfieldPropertyDecoder(f[1], f[2], f[3], f[4], layout, row)

                nf.updateData.connect(self.HandleFieldUpdate)
                fields.append(nf)
                row += 1

            self.fields = fields
            layout.addWidget(createHorzLine(), row, 0, 1, 2); row += 1

            layout.addWidget(QtWidgets.QLabel(globals.trans.string('SpriteDataEditor', 9)), row, 0, Qt.AlignRight)
            layout.addWidget(self.activeLayer, row, 1); row += 1

            layout.addWidget(QtWidgets.QLabel(globals.trans.string('SpriteDataEditor', 12)), row, 0, Qt.AlignRight)
            layout.addWidget(self.initialState, row, 1)

    def update(self):
        """
        Updates all the fields to display the appropriate info
        """
        self.UpdateFlag = True

        data = self.data

        self.raweditor.setText('%02x%02x %02x%02x %02x%02x %02x%02x %02x%02x %02x%02x' % (
            data[0], data[1], data[2], data[3],
            data[4], data[5], data[6], data[7],
            data[8], data[9], data[10], data[11],
        ))

        self.raweditor.setStyleSheet('')

        # Go through all the data
        for f in self.fields:
            f.update(data)

        self.UpdateFlag = False

    def ShowNoteTooltip(self):
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self.notes, self)

    def ShowRelatedObjFilesTooltip(self):
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self.relatedObjFiles, self)

    def HandleFieldUpdate(self, field):
        """
        Triggered when a field's data is updated
        """
        if self.UpdateFlag: return

        data = field.assign(self.data)
        self.data = data

        self.raweditor.setText('%02x%02x %02x%02x %02x%02x %02x%02x %02x%02x %02x%02x' % (
            data[0], data[1], data[2], data[3],
            data[4], data[5], data[6], data[7],
            data[8], data[9], data[10], data[11],
        ))

        self.raweditor.setStyleSheet('')

        for f in self.fields:
            if f != field:
                f.update(data)

        self.DataUpdate.emit(data)

    def HandleRawDataEdited(self, text):
        """
        Triggered when the raw data textbox is edited
        """

        raw = text.replace(' ', '')
        valid = False

        if len(raw) == 24:
            try:
                data = bytes.fromhex(text)
                valid = True

            except ValueError:
                pass

        # if it's invalid, colour the editor
        if not valid:
            self.raweditor.setStyleSheet('QLineEdit { background-color: #ffd2d2; }')
            return

        self.raweditor.setStyleSheet('')
        self.data = data

        self.UpdateFlag = True

        for f in self.fields:
            f.update(data)

        self.UpdateFlag = False
        self.DataUpdate.emit(data)

class EntranceEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing entrance properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        self.cameraX = QtWidgets.QSpinBox()
        self.cameraX.setRange(-32768, 32767)
        self.cameraX.setToolTip(globals.trans.string('EntranceDataEditor', 30))
        self.cameraX.valueChanged.connect(self.HandleCameraXChanged)

        self.cameraY = QtWidgets.QSpinBox()
        self.cameraY.setRange(-32768, 32767)
        self.cameraY.setToolTip(globals.trans.string('EntranceDataEditor', 31))
        self.cameraY.valueChanged.connect(self.HandleCameraYChanged)

        self.entranceID = QtWidgets.QSpinBox()
        self.entranceID.setRange(0, 255)
        self.entranceID.setToolTip(globals.trans.string('EntranceDataEditor', 1))
        self.entranceID.valueChanged.connect(self.HandleEntranceIDChanged)

        self.entranceType = QtWidgets.QComboBox()

        import loading
        loading.LoadEntranceNames()
        del loading

        self.entranceType.addItems(globals.EntranceTypeNames)
        self.entranceType.setToolTip(globals.trans.string('EntranceDataEditor', 3))
        self.entranceType.activated.connect(self.HandleEntranceTypeChanged)

        self.destArea = QtWidgets.QSpinBox()
        self.destArea.setRange(0, 4)
        self.destArea.setToolTip(globals.trans.string('EntranceDataEditor', 7))
        self.destArea.valueChanged.connect(self.HandleDestAreaChanged)

        self.destEntrance = QtWidgets.QSpinBox()
        self.destEntrance.setRange(0, 255)
        self.destEntrance.setToolTip(globals.trans.string('EntranceDataEditor', 5))
        self.destEntrance.valueChanged.connect(self.HandleDestEntranceChanged)

        self.allowEntryCheckbox = QtWidgets.QCheckBox(globals.trans.string('EntranceDataEditor', 8))
        self.allowEntryCheckbox.setToolTip(globals.trans.string('EntranceDataEditor', 9))
        self.allowEntryCheckbox.clicked.connect(self.HandleAllowEntryClicked)

        self.unkFlagCheckbox = QtWidgets.QCheckBox("Unknown Flag")
        self.unkFlagCheckbox.setToolTip("It is unknown what the purpose of this option is.")
        self.unkFlagCheckbox.clicked.connect(self.HandleUnknownFlagClicked)

        self.faceLeftCheckbox = QtWidgets.QCheckBox("Face left")
        self.faceLeftCheckbox.setToolTip("Makes the player face left when spawning.")
        self.faceLeftCheckbox.clicked.connect(self.HandleFaceLeftClicked)

        self.player1Checkbox = QtWidgets.QCheckBox("Player 1")
        self.player1Checkbox.setToolTip(globals.trans.string('EntranceDataEditor', 29))
        self.player1Checkbox.clicked.connect(self.HandlePlayer1Clicked)

        self.player2Checkbox = QtWidgets.QCheckBox("Player 2")
        self.player2Checkbox.setToolTip(globals.trans.string('EntranceDataEditor', 29))
        self.player2Checkbox.clicked.connect(self.HandlePlayer2Clicked)

        self.player3Checkbox = QtWidgets.QCheckBox("Player 3")
        self.player3Checkbox.setToolTip(globals.trans.string('EntranceDataEditor', 29))
        self.player3Checkbox.clicked.connect(self.HandlePlayer3Clicked)

        self.player4Checkbox = QtWidgets.QCheckBox("Player 4")
        self.player4Checkbox.setToolTip(globals.trans.string('EntranceDataEditor', 29))
        self.player4Checkbox.clicked.connect(self.HandlePlayer4Clicked)

        self.playerDistance = QtWidgets.QComboBox()
        self.playerDistance.addItems(["1 block", "1.5 blocks", "2 blocks"])
        self.playerDistance.setToolTip('Distance between players. Only works with entrance types 25 and 34.')
        self.playerDistance.activated.connect(self.HandlePlayerDistanceChanged)

        self.otherID = QtWidgets.QSpinBox()
        self.otherID.setRange(0, 255)
        self.otherID.setToolTip('The ID of the entrance where Baby Yoshis spawn when entering the level (or area?).\nValue of 0 makes the Baby Yoshis spawn at the same entrance.')
        self.otherID.valueChanged.connect(self.HandleOtherID)

        self.goto = QtWidgets.QPushButton("Goto")
        self.goto.clicked.connect(self.GotoOtherEntrance)

        self.coinOrder = QtWidgets.QSpinBox()
        self.coinOrder.setRange(0, 255)
        self.coinOrder.setToolTip('Used in coin edit to determine the order of entrances.\nIf there are multiple entrances with the same order, the game picks the first one it finds.')
        self.coinOrder.valueChanged.connect(self.HandleCoinOrder)

        self.scrollPathID = QtWidgets.QSpinBox()
        self.scrollPathID.setRange(0, 255)
        self.scrollPathID.setToolTip('The Path ID, for autoscroll purposes.')
        self.scrollPathID.valueChanged.connect(self.HandleScrollPathID)

        self.pathnodeindex = QtWidgets.QSpinBox()
        self.pathnodeindex.setRange(0, 255)
        self.pathnodeindex.setToolTip('The Path Node Index, for autoscroll purposes.')
        self.pathnodeindex.valueChanged.connect(self.HandlePathNodeIndex)

        self.transition = QtWidgets.QComboBox()
        self.transition.addItems(["Default", "Fade", "Mario face", "Circle towards center", "Bowser face", "Circle towards entrance", "Waves (always down)", "Waves (down on fadeout, up on fadein)", "Waves (up on fadeout, down on fadein)", "Mushroom", "Circle towards entrance", "No transition"])
        self.transition.setToolTip('The screen fades out with the transition mode of the source entrance, and fades in with the transition mode of the destination entrance.')
        self.transition.activated.connect(self.HandleTransitionChanged)

        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Entrance #' label
        self.editingLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 0, 0, 1, 6, Qt.AlignTop)

        # add labels
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('EntranceDataEditor', 2)), 1, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('EntranceDataEditor', 0)), 3, 0, 1, 1, Qt.AlignRight)

        layout.addWidget(createHorzLine(), 2, 0, 1, 6)

        layout.addWidget(QtWidgets.QLabel(globals.trans.string('EntranceDataEditor', 4)), 3, 3, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('EntranceDataEditor', 6)), 5, 3, 1, 1, Qt.AlignRight)

        # add the widgets
        layout.addWidget(self.entranceType, 1, 1, 1, 5)
        layout.addWidget(self.entranceID, 3, 1, 1, 2)
        layout.addWidget(self.destEntrance, 3, 4, 1, 2)
        layout.addWidget(self.destArea, 5, 4, 1, 2)

        layout.addWidget(createHorzLine(), 6, 0, 1, 6)

        layout.addWidget(self.allowEntryCheckbox, 7, 1, 1, 2)
        layout.addWidget(self.unkFlagCheckbox, 7, 2, 1, 2)
        layout.addWidget(self.faceLeftCheckbox, 7, 4, 1, 2)

        layout.addWidget(createHorzLine(), 8, 0, 1, 6)

        layout.addWidget(QtWidgets.QLabel('Players to spawn:'), 9, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(self.player1Checkbox, 9, 1)
        layout.addWidget(self.player2Checkbox, 9, 2)
        layout.addWidget(self.player3Checkbox, 9, 3)
        layout.addWidget(self.player4Checkbox, 9, 4)
        layout.addWidget(QtWidgets.QLabel('Players Distance:'), 10, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(self.playerDistance, 10, 1, 1, 5)

        layout.addWidget(createHorzLine(), 11, 0, 1, 6)

        layout.addWidget(QtWidgets.QLabel('Baby Yoshi Entrance ID:'), 12, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(self.otherID, 12, 1, 1, 2)
        layout.addWidget(self.goto, 13, 1, 1, 2)

        layout.addWidget(createHorzLine(), 14, 0, 1, 6)

        layout.addWidget(QtWidgets.QLabel('Entrance Order:'), 12, 3, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('Path ID:'), 16, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('Path Node Index:'), 16, 3, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('Transition:'), 18, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(self.coinOrder, 12, 4, 1, 2)
        layout.addWidget(self.scrollPathID, 16, 1, 1, 2)
        layout.addWidget(self.pathnodeindex, 16, 4, 1, 2)
        layout.addWidget(self.transition, 18, 1, 1, 5)

        layout.addWidget(createHorzLine(), 19, 0, 1, 6)

        layout.addWidget(QtWidgets.QLabel('Camera X:'), 20, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('Camera Y:'), 20, 3, 1, 1, Qt.AlignRight)
        layout.addWidget(self.cameraX, 20, 1, 1, 2)
        layout.addWidget(self.cameraY, 20, 4, 1, 2)

        self.ent = None
        self.UpdateFlag = False

    def setEntrance(self, ent):
        """
        Change the entrance being edited by the editor, update all fields
        """
        if self.ent == ent: return

        self.editingLabel.setText(globals.trans.string('EntranceDataEditor', 23, '[id]', ent.entid))
        self.ent = ent
        self.UpdateFlag = True

        self.cameraX.setValue(ent.camerax)
        self.cameraY.setValue(ent.cameray)
        self.entranceID.setValue(ent.entid)
        self.entranceType.setCurrentIndex(ent.enttype)
        self.destArea.setValue(ent.destarea)
        self.destEntrance.setValue(ent.destentrance)
        self.playerDistance.setCurrentIndex(ent.playerDistance)
        self.otherID.setValue(ent.otherID)
        self.coinOrder.setValue(ent.coinOrder)
        self.scrollPathID.setValue(ent.pathID)
        self.pathnodeindex.setValue(ent.pathnodeindex)
        self.transition.setCurrentIndex(ent.transition)

        self.allowEntryCheckbox.setChecked(((ent.entsettings & 0x80) == 0))
        self.unkFlagCheckbox.setChecked(((ent.entsettings & 2) != 0))
        self.faceLeftCheckbox.setChecked(((ent.entsettings & 1) != 0))
        self.player1Checkbox.setChecked(((ent.players & 1) != 0))
        self.player2Checkbox.setChecked(((ent.players & 2) != 0))
        self.player3Checkbox.setChecked(((ent.players & 4) != 0))
        self.player4Checkbox.setChecked(((ent.players & 8) != 0))

        self.UpdateFlag = False

    def HandleCameraXChanged(self, i):
        """
        Handler for the camera x pos changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.camerax = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleCameraYChanged(self, i):
        """
        Handler for the camera y pos changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.cameray = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleEntranceIDChanged(self, i):
        """
        Handler for the entrance ID changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.entid = i
        self.ent.update()
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
        self.editingLabel.setText(globals.trans.string('EntranceDataEditor', 23, '[id]', i))

    def HandleEntranceTypeChanged(self, i):
        """
        Handler for the entrance type changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.enttype = i
        self.ent.TypeChange()
        self.ent.update()
        self.ent.UpdateTooltip()
        globals.mainWindow.scene.update()
        self.ent.UpdateListItem()

    def HandleDestAreaChanged(self, i):
        """
        Handler for the destination area changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.destarea = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleDestEntranceChanged(self, i):
        """
        Handler for the destination entrance changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.destentrance = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandlePlayerDistanceChanged(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.playerDistance = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleOtherID(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.otherID = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def GotoOtherEntrance(self):
        otherID = self.ent.otherID
        otherEnt = None
        for ent in globals.Area.entrances:
            if ent.entid == otherID:
                otherEnt = ent
                break

        if otherEnt:
            globals.mainWindow.view.centerOn(otherEnt.objx * (globals.TileWidth / 16), otherEnt.objy * (globals.TileWidth / 16))
        

    def HandleCoinOrder(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.coinOrder = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleScrollPathID(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.pathID = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandlePathNodeIndex(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.pathnodeindex = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleTransitionChanged(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.transition = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleAllowEntryClicked(self, checked):
        """
        Handle for the Allow Entry checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if not checked:
            self.ent.entsettings |= 0x80
        else:
            self.ent.entsettings &= ~0x80
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleUnknownFlagClicked(self, checked):
        """
        Handle for the Unknown Flag checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.entsettings |= 2
        else:
            self.ent.entsettings &= ~2
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleFaceLeftClicked(self, checked):
        """
        Handle for the Face Left checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.entsettings |= 1
        else:
            self.ent.entsettings &= ~1
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandlePlayer1Clicked(self, checked):
        """
        Handle for the Player 1 checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.players |= 1
        else:
            self.ent.players &= ~1
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandlePlayer2Clicked(self, checked):
        """
        Handle for the Player 2 checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.players |= 2
        else:
            self.ent.players &= ~2
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandlePlayer3Clicked(self, checked):
        """
        Handle for the Player 3 checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.players |= 4
        else:
            self.ent.players &= ~4
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandlePlayer4Clicked(self, checked):
        """
        Handle for the Player 4 checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.players |= 8
        else:
            self.ent.players &= ~8
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()


class PathNodeEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing path node properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        # [20:52:41]  [Angel-SL] 1. (readonly) pathid 2. (readonly) nodeid 3. x 4. y 5. speed (float spinner) 6. accel (float spinner)
        # not doing [20:52:58]  [Angel-SL] and 2 buttons - 7. 'Move Up' 8. 'Move Down'
        self.speed = QtWidgets.QDoubleSpinBox()
        self.speed.setRange(min(sys.float_info), max(sys.float_info))
        self.speed.setToolTip(globals.trans.string('PathDataEditor', 3))
        self.speed.setDecimals(int(sys.float_info.__getattribute__('dig')))
        self.speed.valueChanged.connect(self.HandleSpeedChanged)
        self.speed.setMaximumWidth(256)

        self.accel = QtWidgets.QDoubleSpinBox()
        self.accel.setRange(min(sys.float_info), max(sys.float_info))
        self.accel.setToolTip(globals.trans.string('PathDataEditor', 5))
        self.accel.setDecimals(int(sys.float_info.__getattribute__('dig')))
        self.accel.valueChanged.connect(self.HandleAccelChanged)
        self.accel.setMaximumWidth(256)

        self.delay = QtWidgets.QSpinBox()
        self.delay.setRange(0, 65535)
        self.delay.setToolTip(globals.trans.string('PathDataEditor', 7))
        self.delay.valueChanged.connect(self.HandleDelayChanged)
        self.delay.setMaximumWidth(256)

        self.loops = QtWidgets.QCheckBox()
        self.loops.setToolTip(globals.trans.string('PathDataEditor', 1))
        self.loops.stateChanged.connect(self.HandleLoopsChanged)

        self.unk1 = QtWidgets.QSpinBox()
        self.unk1.setRange(-128, 127)
        self.unk1.setToolTip(globals.trans.string('PathDataEditor', 12))
        self.unk1.valueChanged.connect(self.Handleunk1Changed)
        self.unk1.setMaximumWidth(256)

        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Path #' label
        self.editingLabel = QtWidgets.QLabel('-')
        self.editingPathLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 4, 0, 1, 2, Qt.AlignTop)
        layout.addWidget(self.editingPathLabel, 0, 0, 1, 2, Qt.AlignTop)
        # add labels
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 11)), 1, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 0)), 2, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 2)), 5, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 4)), 6, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 6)), 7, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(createHorzLine(), 3, 0, 1, 2)

        # add the widgets
        layout.addWidget(self.unk1, 1, 1)
        layout.addWidget(self.loops, 2, 1)
        layout.addWidget(self.speed, 5, 1)
        layout.addWidget(self.accel, 6, 1)
        layout.addWidget(self.delay, 7, 1)

        self.path = None
        self.UpdateFlag = False

    def setPath(self, path):
        """
        Change the path being edited by the editor, update all fields
        """
        if self.path == path: return
        self.editingPathLabel.setText(globals.trans.string('PathDataEditor', 8, '[id]', path.pathid))
        self.editingLabel.setText(globals.trans.string('PathDataEditor', 9, '[id]', path.nodeid))
        self.path = path
        self.UpdateFlag = True

        self.speed.setValue(path.nodeinfo['speed'])
        self.accel.setValue(path.nodeinfo['accel'])
        self.delay.setValue(path.nodeinfo['delay'])
        self.loops.setChecked(path.pathinfo['loops'])

        self.UpdateFlag = False

    def HandleSpeedChanged(self, i):
        """
        Handler for the speed changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.path.nodeinfo['speed'] = i

    def HandleAccelChanged(self, i):
        """
        Handler for the accel changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.path.nodeinfo['accel'] = i

    def HandleDelayChanged(self, i):
        """
        Handler for the delay changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.path.nodeinfo['delay'] = i

    def Handleunk1Changed(self, i):
        """
        Handler for the delay changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.path.nodeinfo['unk1'] = i

    def HandleLoopsChanged(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.path.pathinfo['peline'].loops = self.path.pathinfo['loops'] = (i == Qt.Checked)
        self.path.pathinfo['peline'].update()
        globals.mainWindow.scene.update()


class NabbitPathNodeEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing path node properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        self.unk1 = QtWidgets.QSpinBox()
        self.unk1.setRange(0, 0xFFFF)
        self.unk1.valueChanged.connect(self.HandleUnk1Changed)

        self.unk2 = QtWidgets.QSpinBox()
        self.unk2.setRange(0, 0xFF)
        self.unk2.valueChanged.connect(self.HandleUnk2Changed)

        self.unk3 = QtWidgets.QSpinBox()
        self.unk3.setRange(0, 0xFF)
        self.unk3.valueChanged.connect(self.HandleUnk3Changed)

        self.unk4 = QtWidgets.QSpinBox()
        self.unk4.setRange(0, 0xFF)
        self.unk4.valueChanged.connect(self.HandleUnk4Changed)

        self.action = QtWidgets.QComboBox()
        self.action.addItems(['0: Run to the right',
                              '1: Jump to the next node',
                              '6: Unknown, probably the same as 0',
                              '7: Unknown',
                              '8: Same as 0 and look behind?',
                              '11: Same as 0?',
                              '20: Same as 0 except don\'t look behind?',
                              '23: Wait, then slide',
                              '24: Stop at the next node',
                              '25: Same as 0?',
                              '26: Same as 0?'])

        self.action.setToolTip(globals.trans.string('PathDataEditor', 16))
        self.action.currentIndexChanged.connect(self.HandleActionChanged)
        self.action.setMaximumWidth(256)

        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Path #' label
        self.editingLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 0, 0, 1, 2, Qt.AlignTop)
        # add labels
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 17)), 1, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 18)), 2, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 19)), 3, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 20)), 4, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('PathDataEditor', 15)), 6, 0, 1, 1, Qt.AlignRight)

        # add the widgets
        layout.addWidget(self.unk1, 1, 1)
        layout.addWidget(self.unk2, 2, 1)
        layout.addWidget(self.unk3, 3, 1)
        layout.addWidget(self.unk4, 4, 1)
        layout.addWidget(createHorzLine(), 5, 0, 1, 2)
        layout.addWidget(self.action, 6, 1)

        self.path = None
        self.UpdateFlag = False

        self.indecies = {
            0: 0,
            1: 1,
            6: 2,
            7: 3,
            8: 4,
            11: 5,
            20: 6,
            23: 7,
            24: 8,
            25: 9,
            26: 10,
        }

        self.rIndecies = {
            0: 0,
            1: 1,
            2: 6,
            3: 7,
            4: 8,
            5: 11,
            6: 20,
            7: 23,
            8: 24,
            9: 25,
            10: 26,
        }

    def setPath(self, path):
        """
        Change the path node being edited by the editor, update the action field
        """
        if self.path == path: return
        self.editingLabel.setText(globals.trans.string('PathDataEditor', 14, '[id]', path.nodeid))
        self.path = path
        self.UpdateFlag = True

        self.unk1.setValue(path.nodeinfo['unk1'])
        self.unk2.setValue(path.nodeinfo['unk2'])
        self.unk3.setValue(path.nodeinfo['unk3'])
        self.unk4.setValue(path.nodeinfo['unk4'])

        if path.nodeinfo['action'] in self.indecies:
            self.action.setCurrentIndex(self.indecies[path.nodeinfo['action']])

        else:
            print("Unknown nabbit path node action found: %d" % path.nodeinfo['action'])
            self.action.setCurrentIndex(0)

        self.UpdateFlag = False

    def HandleUnk1Changed(self, v):
        """
        Handler for unknown value 1 changing
        """
        if self.UpdateFlag: return
        SetDirty()

        self.path.nodeinfo['unk1'] = v

    def HandleUnk2Changed(self, v):
        """
        Handler for unknown value 2 changing
        """
        if self.UpdateFlag: return
        SetDirty()

        self.path.nodeinfo['unk2'] = v

    def HandleUnk3Changed(self, v):
        """
        Handler for unknown value 3 changing
        """
        if self.UpdateFlag: return
        SetDirty()

        self.path.nodeinfo['unk3'] = v

    def HandleUnk4Changed(self, v):
        """
        Handler for unknown value 4 changing
        """
        if self.UpdateFlag: return
        SetDirty()

        self.path.nodeinfo['unk4'] = v

    def HandleActionChanged(self, i):
        """
        Handler for the action changing
        """
        if self.UpdateFlag: return
        SetDirty()

        self.path.nodeinfo['action'] = self.rIndecies[i]


class LocationEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing location properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        self.locationID = QtWidgets.QSpinBox()
        self.locationID.setToolTip(globals.trans.string('LocationDataEditor', 1))
        self.locationID.setRange(0, 255)
        self.locationID.valueChanged.connect(self.HandleLocationIDChanged)

        self.locationX = QtWidgets.QSpinBox()
        self.locationX.setToolTip(globals.trans.string('LocationDataEditor', 3))
        self.locationX.setRange(16, 65535)
        self.locationX.valueChanged.connect(self.HandleLocationXChanged)

        self.locationY = QtWidgets.QSpinBox()
        self.locationY.setToolTip(globals.trans.string('LocationDataEditor', 5))
        self.locationY.setRange(16, 65535)
        self.locationY.valueChanged.connect(self.HandleLocationYChanged)

        self.locationWidth = QtWidgets.QSpinBox()
        self.locationWidth.setToolTip(globals.trans.string('LocationDataEditor', 7))
        self.locationWidth.setRange(8, 65535)
        self.locationWidth.valueChanged.connect(self.HandleLocationWidthChanged)

        self.locationHeight = QtWidgets.QSpinBox()
        self.locationHeight.setToolTip(globals.trans.string('LocationDataEditor', 9))
        self.locationHeight.setRange(8, 65535)
        self.locationHeight.valueChanged.connect(self.HandleLocationHeightChanged)

        self.snapButton = QtWidgets.QPushButton(globals.trans.string('LocationDataEditor', 10))
        self.snapButton.clicked.connect(self.HandleSnapToGrid)

        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Location #' label
        self.editingLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 0, 0, 1, 4, Qt.AlignTop)

        # add labels
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('LocationDataEditor', 0)), 1, 0, 1, 1, Qt.AlignRight)

        layout.addWidget(createHorzLine(), 2, 0, 1, 4)

        layout.addWidget(QtWidgets.QLabel(globals.trans.string('LocationDataEditor', 2)), 3, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('LocationDataEditor', 4)), 4, 0, 1, 1, Qt.AlignRight)

        layout.addWidget(QtWidgets.QLabel(globals.trans.string('LocationDataEditor', 6)), 3, 2, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals.trans.string('LocationDataEditor', 8)), 4, 2, 1, 1, Qt.AlignRight)

        # add the widgets
        layout.addWidget(self.locationID, 1, 1, 1, 1)
        layout.addWidget(self.snapButton, 1, 3, 1, 1)

        layout.addWidget(self.locationX, 3, 1, 1, 1)
        layout.addWidget(self.locationY, 4, 1, 1, 1)

        layout.addWidget(self.locationWidth, 3, 3, 1, 1)
        layout.addWidget(self.locationHeight, 4, 3, 1, 1)

        self.loc = None
        self.UpdateFlag = False

    def setLocation(self, loc):
        """
        Change the location being edited by the editor, update all fields
        """
        self.loc = loc
        self.UpdateFlag = True

        self.FixTitle()
        self.locationID.setValue(loc.id)
        self.locationX.setValue(loc.objx)
        self.locationY.setValue(loc.objy)
        self.locationWidth.setValue(loc.width)
        self.locationHeight.setValue(loc.height)

        self.UpdateFlag = False

    def FixTitle(self):
        self.editingLabel.setText(globals.trans.string('LocationDataEditor', 11, '[id]', self.loc.id))

    def HandleLocationIDChanged(self, i):
        """
        Handler for the location ID changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.id = i
        self.loc.update()
        self.loc.UpdateTitle()
        self.FixTitle()

    def HandleLocationXChanged(self, i):
        """
        Handler for the location X-pos changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.objx = i
        self.loc.autoPosChange = True
        self.loc.setX(int(i * globals.TileWidth / 16))
        self.loc.autoPosChange = False
        self.loc.UpdateRects()
        self.loc.update()

    def HandleLocationYChanged(self, i):
        """
        Handler for the location Y-pos changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.objy = i
        self.loc.autoPosChange = True
        self.loc.setY(int(i * globals.TileWidth / 16))
        self.loc.autoPosChange = False
        self.loc.UpdateRects()
        self.loc.update()

    def HandleLocationWidthChanged(self, i):
        """
        Handler for the location width changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.width = i
        self.loc.UpdateRects()
        self.loc.update()

    def HandleLocationHeightChanged(self, i):
        """
        Handler for the location height changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.height = i
        self.loc.UpdateRects()
        self.loc.update()

    def HandleSnapToGrid(self):
        """
        Snaps the current location to an 8x8 grid
        """
        SetDirty()

        loc = self.loc
        left = loc.objx
        top = loc.objy
        right = left + loc.width
        bottom = top + loc.height

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

        loc.objx = left
        loc.objy = top
        loc.width = right - left
        loc.height = bottom - top

        loc.setPos(int(left * globals.TileWidth / 16), int(top * globals.TileWidth / 16))
        loc.UpdateRects()
        loc.update()
        self.setLocation(loc)  # updates the fields


class LoadingTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.entrance = QtWidgets.QSpinBox()
        self.entrance.setRange(0, 255)
        self.entrance.setToolTip(globals.trans.string('AreaDlg', 6))
        self.entrance.setValue(globals.Area.startEntrance)

        self.entranceCoinBoost = QtWidgets.QSpinBox()
        self.entranceCoinBoost.setRange(0, 255)
        self.entranceCoinBoost.setToolTip(globals.trans.string('AreaDlg', 39))
        self.entranceCoinBoost.setValue(globals.Area.startEntranceCoinBoost)

        self.wrap = QtWidgets.QCheckBox(globals.trans.string('AreaDlg', 7))
        self.wrap.setToolTip(globals.trans.string('AreaDlg', 8))
        self.wrap.setChecked(globals.Area.wrapFlag)

        self.unk1 = QtWidgets.QCheckBox(globals.trans.string('AreaDlg', 40))
        self.unk1.setToolTip(globals.trans.string('AreaDlg', 41))
        self.unk1.setChecked(globals.Area.unkFlag1)

        self.unk2 = QtWidgets.QCheckBox(globals.trans.string('AreaDlg', 42))
        self.unk2.setToolTip(globals.trans.string('AreaDlg', 43))
        self.unk2.setChecked(globals.Area.unkFlag2)

        self.unk3 = QtWidgets.QCheckBox(globals.trans.string('AreaDlg', 44))
        self.unk3.setToolTip(globals.trans.string('AreaDlg', 45))
        self.unk3.setChecked(globals.Area.unkFlag3)

        self.unk4 = QtWidgets.QCheckBox(globals.trans.string('AreaDlg', 46))
        self.unk4.setToolTip(globals.trans.string('AreaDlg', 47))
        self.unk4.setChecked(globals.Area.unkFlag4)

        self.timer = QtWidgets.QSpinBox()
        self.timer.setRange(0, 999)
        self.timer.setToolTip(globals.trans.string('AreaDlg', 4))
        self.timer.setValue(globals.Area.timelimit)

        self.timelimit2 = QtWidgets.QSpinBox()
        self.timelimit2.setRange(0, 999)
        self.timelimit2.setToolTip(globals.trans.string('AreaDlg', 38))
        self.timelimit2.setValue(globals.Area.timelimit2)

        self.timelimit3 = QtWidgets.QSpinBox()
        self.timelimit3.setRange(0, 999)
        self.timelimit3.setToolTip(globals.trans.string('AreaDlg', 38))
        self.timelimit3.setValue(globals.Area.timelimit3)

        settingsLayout = QtWidgets.QFormLayout()
        settingsLayout.addRow(globals.trans.string('AreaDlg', 3), self.timer)
        settingsLayout.addRow(globals.trans.string('AreaDlg', 36), self.timelimit2)
        settingsLayout.addRow(globals.trans.string('AreaDlg', 37), self.timelimit3)
        settingsLayout.addRow(globals.trans.string('AreaDlg', 5), self.entrance)
        settingsLayout.addRow(globals.trans.string('AreaDlg', 34), self.entranceCoinBoost)
        settingsLayout.addRow(self.wrap)
        settingsLayout.addRow(self.unk1)
        settingsLayout.addRow(self.unk2)
        settingsLayout.addRow(self.unk3)
        settingsLayout.addRow(self.unk4)

        Layout = QtWidgets.QVBoxLayout()
        Layout.addLayout(settingsLayout)
        Layout.addStretch(1)
        self.setLayout(Layout)


class TilesetsTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.tile0 = QtWidgets.QComboBox()

        name = globals.Area.tileset0
        slot = self.HandleTileset0Choice

        self.currentChoice = None

        data = SimpleTilesetNames()

        # First, find the current index and custom-tileset strings
        if name == '':  # No tileset selected, the current index should be None
            ts_index = globals.trans.string('AreaDlg', 15)  # None
            custom = ''
            custom_fname = globals.trans.string('AreaDlg', 16)  # [CUSTOM]
        else:  # Tileset selected
            ts_index = globals.trans.string('AreaDlg', 18, '[name]', name)  # Custom filename... [name]
            custom = name
            custom_fname = globals.trans.string('AreaDlg', 17, '[name]', name)  # [CUSTOM] [name]

        # Add items to the widget:
        # - None
        self.tile0.addItem(globals.trans.string('AreaDlg', 15), '')  # None
        # - Retail Tilesets
        for tfile, tname in data:
            if tfile in globals.szsData:
                text = globals.trans.string('AreaDlg', 19, '[name]', tname, '[file]', tfile)  # [name] ([file])
                self.tile0.addItem(text, tfile)
                if name == tfile:
                    ts_index = text
                    custom = ''
        # - Custom Tileset
        self.tile0.addItem(globals.trans.string('AreaDlg', 18, '[name]', custom), custom_fname)  # Custom filename... [name]

        # Set the current index
        item_idx = self.tile0.findText(ts_index)
        self.currentChoice = item_idx
        self.tile0.setCurrentIndex(item_idx)

        # Handle combobox changes
        self.tile0.activated.connect(slot)

        ## don't allow ts0 to be removable
        #self.tile0.removeItem(0)

        mainLayout = QtWidgets.QVBoxLayout()
        tile0Box = QtWidgets.QGroupBox(globals.trans.string('AreaDlg', 11))

        t0 = QtWidgets.QVBoxLayout()
        t0.addWidget(self.tile0)

        tile0Box.setLayout(t0)

        mainLayout.addWidget(tile0Box)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    def HandleTileset0Choice(self, index):
        w = self.tile0

        if index == (w.count() - 1):
            fname = str(w.itemData(index))
            fname = fname[len(globals.trans.string('AreaDlg', 17, '[name]', '')):]

            import dialogs
            dbox = dialogs.InputBox()
            del dialogs

            dbox.setWindowTitle(globals.trans.string('AreaDlg', 20))
            dbox.label.setText(globals.trans.string('AreaDlg', 21))
            dbox.textbox.setMaxLength(31)
            dbox.textbox.setText(fname)
            result = dbox.exec_()

            if result == QtWidgets.QDialog.Accepted:
                fname = str(dbox.textbox.text())
                if fname.endswith('.szs'): fname = fname[:-4]
                elif fname.endswith('.sarc'): fname = fname[:-5]

                w.setItemText(index, globals.trans.string('AreaDlg', 18, '[name]', fname))
                w.setItemData(index, globals.trans.string('AreaDlg', 17, '[name]', fname))
            else:
                w.setCurrentIndex(self.currentChoice)
                return

        self.currentChoice = index

    def value(self):
        """
        Returns the main tileset choice
        """
        idx = self.tile0.currentIndex()
        name = str(self.tile0.itemData(idx))
        return name


class LevelViewWidget(QtWidgets.QGraphicsView):
    """
    QGraphicsView subclass for the level view
    """
    PositionHover = QtCore.pyqtSignal(int, int)
    FrameSize = QtCore.pyqtSignal(int, int)
    repaint = QtCore.pyqtSignal()
    dragstamp = False

    def __init__(self, scene, parent):
        """
        Constructor
        """
        super().__init__(scene, parent)

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(119,136,153)))
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        # self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setMouseTracking(True)
        # self.setOptimizationFlags(QtWidgets.QGraphicsView.IndirectPainting)
        self.YScrollBar = QtWidgets.QScrollBar(Qt.Vertical, parent)
        self.XScrollBar = QtWidgets.QScrollBar(Qt.Horizontal, parent)
        self.setVerticalScrollBar(self.YScrollBar)
        self.setHorizontalScrollBar(self.XScrollBar)

        self.currentobj = None
        self.selectionFix = False  # Fixes Qt selection bug

        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed
        """
        # The button that triggered this event
        eventButton = event.button()

        # Currently held buttons
        eventButtons = event.buttons()

        # Do not allow processing more than one held button at a time
        # It triggers many bugs in Qt
        if eventButton != eventButtons:
            if eventButton == Qt.LeftButton and not self.currentobj:
                # Left button has been pressed as another button is already being held
                # This causes an interesting bug where any selected object jumps to the cursor
                self.selectionFix = True
                globals.app.restoreOverrideCursor()
                self.scene().clearSelection()

            event.accept()
            return

        if eventButton == Qt.MidButton:
            self.__prevMousePos = event.pos()
            QtWidgets.QGraphicsView.mousePressEvent(self, event)

        elif eventButton == Qt.RightButton:
            if globals.CurrentPaintType in (0, 1, 2, 3) and globals.CurrentObject != -1:
                # return if the Embedded tab is empty
                if (globals.CurrentPaintType in (1, 2, 3)
                    and not len(globals.mainWindow.objPicker.objTS123Tab.getActiveModel().items)):
                    globals.CurrentObject = -1
                    return

                # paint an object
                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int(clicked.x() / globals.TileWidth)
                clickedy = int(clicked.y() / globals.TileWidth)

                ln = globals.CurrentLayer
                layer = globals.Area.layers[globals.CurrentLayer]
                if len(layer) == 0:
                    z = (2 - ln) * 8192
                else:
                    z = layer[-1].zValue() + 1

                obj = ObjectItem(globals.CurrentPaintType, globals.CurrentObject, ln, clickedx, clickedy, 1, 1, z, 0)
                layer.append(obj)
                mw = globals.mainWindow
                obj.positionChanged = mw.HandleObjPosChange
                mw.scene.addItem(obj)

                self.dragstamp = False
                self.currentobj = obj
                self.dragstartx = clickedx
                self.dragstarty = clickedy
                SetDirty()

            elif globals.CurrentPaintType == 10 and globals.CurrentObject != -1:
                assert globals.CurrentObject == globals.ObjectAllDefinitions[globals.CurrentObject].objAllIndex
                type_ = globals.CurrentObject

                # Check if the object is already in one of the tilesets
                if globals.CurrentObject in globals.ObjectAddedtoEmbedded[globals.CurrentArea][globals.mainWindow.folderPicker.currentIndex()]:
                    (globals.CurrentPaintType,
                     globals.CurrentObject) = globals.ObjectAddedtoEmbedded[globals.CurrentArea][globals.mainWindow.folderPicker.currentIndex()][
                         globals.CurrentObject]

                # Try to add the object to one of the tilesets
                else:
                    # Get the object definition, collision data, image and normal map
                    obj = globals.ObjectAllDefinitions[globals.CurrentObject]
                    colldata = globals.ObjectAllCollisions[globals.CurrentObject]
                    img, nml = globals.ObjectAllImages[globals.CurrentObject]

                    # Add the object to one of the tilesets and set CurrentPaintType and CurrentObject
                    (globals.CurrentPaintType,
                     globals.CurrentObject) = addObjToTileset(obj, colldata, img, nml, True)

                    # Checks if the object fit in one of the tilesets
                    if globals.CurrentPaintType == 10:
                        # Revert CurrentObject back to what it was
                        globals.CurrentObject = type_

                        # Throw a messagebox because the object didn't fit
                        QtWidgets.QMessageBox.critical(None, 'Cannot Paint', "There isn't enough room left for this object!")
                        return

                    # Add the object to ObjectAddedtoEmbedded
                    globals.ObjectAddedtoEmbedded[globals.CurrentArea][obj.folderIndex][type_] = (globals.CurrentPaintType, globals.CurrentObject)

                # paint an object
                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int(clicked.x() / globals.TileWidth)
                clickedy = int(clicked.y() / globals.TileWidth)

                ln = globals.CurrentLayer
                layer = globals.Area.layers[globals.CurrentLayer]
                if len(layer) == 0:
                    z = (2 - ln) * 8192
                else:
                    z = layer[-1].zValue() + 1

                obj = ObjectItem(globals.CurrentPaintType, globals.CurrentObject, ln, clickedx, clickedy, 1, 1, z, 0)
                layer.append(obj)
                mw = globals.mainWindow
                obj.positionChanged = mw.HandleObjPosChange
                mw.scene.addItem(obj)

                self.dragstamp = False
                self.currentobj = obj
                self.dragstartx = clickedx
                self.dragstarty = clickedy
                SetDirty()

                globals.CurrentPaintType = 10
                globals.CurrentObject = type_

            elif globals.CurrentPaintType == 4 and globals.CurrentSprite != -1:
                # paint a sprite
                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)

                if globals.CurrentSprite >= 0:  # fixes a bug -Treeki
                    # [18:15:36]  Angel-SL: I found a bug in Reggie
                    # [18:15:42]  Angel-SL: you can paint a 'No sprites found'
                    # [18:15:47]  Angel-SL: results in a sprite -2

                    if globals.CurrentSprite == 564:
                        # Get the previous flower/grass type
                        oldGrassType = 5
                        for sprite in globals.Area.sprites:
                            if sprite.type == 564:
                                oldGrassType = min(sprite.spritedata[5] & 0xf, 5)
                                if oldGrassType < 2:
                                    oldGrassType = 0

                                elif oldGrassType in [3, 4]:
                                    oldGrassType = 3

                    # paint a sprite
                    clickedx = int((clicked.x() - globals.TileWidth / 2) / globals.TileWidth * 16)
                    clickedy = int((clicked.y() - globals.TileWidth / 2) / globals.TileWidth * 16)

                    if clickedx % 8 < 4:
                        clickedx -= (clickedx % 8)
                    else:
                        clickedx += 8 - (clickedx % 8)
                    if clickedy % 8 < 4:
                        clickedy -= (clickedy % 8)
                    else:
                        clickedy += 8 - (clickedy % 8)

                    data = globals.mainWindow.defaultDataEditor.data
                    spr = SpriteItem(globals.CurrentSprite, clickedx, clickedy, data)

                    mw = globals.mainWindow
                    spr.positionChanged = mw.HandleSprPosChange
                    mw.scene.addItem(spr)

                    spr.listitem = ListWidgetItem_SortsByOther(spr)
                    mw.spriteList.addItem(spr.listitem)
                    globals.Area.sprites.append(spr)

                    if globals.CurrentSprite == 564:
                        # Get the current flower/grass type
                        grassType = 5
                        for sprite in globals.Area.sprites:
                            if sprite.type == 564:
                                grassType = min(sprite.spritedata[5] & 0xf, 5)
                                if grassType < 2:
                                    grassType = 0

                                elif grassType in [3, 4]:
                                    grassType = 3

                        # If the current type is not the previous type, reprocess the Overrides
                        # update the objects and flower sprite instances and update the scene
                        if grassType != oldGrassType and globals.Area.tileset0:
                            ProcessOverrides(globals.Area.tileset0)
                            mw.objPicker.LoadFromTilesets()
                            for layer in globals.Area.layers:
                                for tObj in layer:
                                    tObj.updateObjCache()

                            for sprite in globals.Area.sprites:
                                if sprite.type == 546:
                                    sprite.UpdateDynamicSizing()

                            mw.scene.update()

                    self.dragstamp = False
                    self.currentobj = spr
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy

                    self.scene().update()

                    spr.UpdateDynamicSizing()
                    spr.UpdateListItem()

                SetDirty()

            elif globals.CurrentPaintType == 5:
                # paint an entrance
                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int((clicked.x() - globals.TileWidth / 2) / globals.TileWidth * 16)
                clickedy = int((clicked.y() - globals.TileWidth / 2) / globals.TileWidth * 16)

                if clickedx % 8 < 4:
                    clickedx -= (clickedx % 8)
                else:
                    clickedx += 8 - (clickedx % 8)
                if clickedy % 8 < 4:
                    clickedy -= (clickedy % 8)
                else:
                    clickedy += 8 - (clickedy % 8)

                getids = [False for x in range(256)]
                for ent in globals.Area.entrances: getids[ent.entid] = True
                minimumID = getids.index(False)

                ent = EntranceItem(clickedx, clickedy, 0, 0, minimumID, 0, 0, 0, 0, 0, 0, 0x80, 0, 0, 0, 0, 0)
                mw = globals.mainWindow
                ent.positionChanged = mw.HandleEntPosChange
                mw.scene.addItem(ent)

                elist = mw.entranceList
                # if it's the first available ID, all the other indexes should match right?
                # so I can just use the ID to insert
                ent.listitem = ListWidgetItem_SortsByOther(ent)
                elist.insertItem(minimumID, ent.listitem)

                globals.PaintingEntrance = ent
                globals.PaintingEntranceListIndex = minimumID

                globals.Area.entrances.insert(minimumID, ent)

                self.dragstamp = False
                self.currentobj = ent
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                ent.UpdateListItem()

                SetDirty()
            elif globals.CurrentPaintType == 6:
                # paint a path node
                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int((clicked.x() - globals.TileWidth / 2) / globals.TileWidth * 16)
                clickedy = int((clicked.y() - globals.TileWidth / 2) / globals.TileWidth * 16)
                if clickedx % 8 < 4:
                    clickedx -= (clickedx % 8)
                else:
                    clickedx += 8 - (clickedx % 8)
                if clickedy % 8 < 4:
                    clickedy -= (clickedy % 8)
                else:
                    clickedy += 8 - (clickedy % 8)
                mw = globals.mainWindow
                plist = mw.pathList
                selectedpn = None if len(plist.selectedItems()) < 1 else plist.selectedItems()[0]
                # if selectedpn is None:
                #    QtWidgets.QMessageBox.warning(None, 'Error', 'No pathnode selected. Select a pathnode of the path you want to create a new node in.')
                if selectedpn is None:
                    getids = [False for x in range(256)]
                    getids[0] = True
                    getids[90] = True  # Skip Nabbit path
                    for pathdatax in globals.Area.pathdata:
                        # if(len(pathdatax['nodes']) > 0):
                        getids[int(pathdatax['id'])] = True

                    newpathid = getids.index(False)
                    newpathdata = {'id': newpathid,
                                   'unk1': 0,
                                   'nodes': [
                                       {'x': clickedx, 'y': clickedy, 'speed': 0, 'accel': 0, 'delay': 0}],
                                   'loops': False
                                   }
                    globals.Area.pathdata.append(newpathdata)
                    newnode = PathItem(clickedx, clickedy, newpathdata, newpathdata['nodes'][0], 0, 0, 0, 0)
                    newnode.positionChanged = mw.HandlePathPosChange

                    mw.scene.addItem(newnode)

                    peline = PathEditorLineItem(newpathdata['nodes'])
                    newpathdata['peline'] = peline
                    mw.scene.addItem(peline)

                    globals.Area.pathdata.sort(key=lambda path: int(path['id']))

                    newnode.listitem = ListWidgetItem_SortsByOther(newnode)
                    plist.clear()
                    for fpath in globals.Area.pathdata:
                        for fpnode in fpath['nodes']:
                            fpnode['graphicsitem'].listitem = ListWidgetItem_SortsByOther(fpnode['graphicsitem'],
                                                                                          fpnode[
                                                                                              'graphicsitem'].ListString())
                            plist.addItem(fpnode['graphicsitem'].listitem)
                            fpnode['graphicsitem'].updateId()
                    newnode.listitem.setSelected(True)
                    globals.Area.paths.append(newnode)

                    self.dragstamp = False
                    self.currentobj = newnode
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy

                    newnode.UpdateListItem()

                    SetDirty()
                else:
                    pathd = None
                    for pathnode in globals.Area.paths:
                        if pathnode.listitem == selectedpn:
                            pathd = pathnode.pathinfo

                    if not pathd: return  # shouldn't happen

                    newnodedata = {'x': clickedx, 'y': clickedy, 'speed': 0, 'accel': 0, 'delay': 0}
                    pathd['nodes'].append(newnodedata)

                    newnode = PathItem(clickedx, clickedy, pathd, newnodedata, 0, 0, 0, 0)

                    newnode.positionChanged = mw.HandlePathPosChange
                    mw.scene.addItem(newnode)

                    newnode.listitem = ListWidgetItem_SortsByOther(newnode)
                    plist.clear()
                    for fpath in globals.Area.pathdata:
                        for fpnode in fpath['nodes']:
                            fpnode['graphicsitem'].listitem = ListWidgetItem_SortsByOther(fpnode['graphicsitem'],
                                                                                          fpnode[
                                                                                              'graphicsitem'].ListString())
                            plist.addItem(fpnode['graphicsitem'].listitem)
                            fpnode['graphicsitem'].updateId()
                    newnode.listitem.setSelected(True)
                    # globals.PaintingEntrance = ent
                    # globals.PaintingEntranceListIndex = minimumID

                    globals.Area.paths.append(newnode)
                    pathd['peline'].nodePosChanged()
                    self.dragstamp = False
                    self.currentobj = newnode
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy

                    newnode.UpdateListItem()

                    SetDirty()

            elif globals.CurrentPaintType == 7:
                # paint a location
                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)

                clickedx = int(clicked.x() // globals.TileWidth) * 16
                clickedy = int(clicked.y() // globals.TileWidth) * 16

                allID = set()  # faster 'x in y' lookups for sets
                newID = 1
                for i in globals.Area.locations:
                    allID.add(i.id)

                while newID <= 255:
                    if newID not in allID:
                        break
                    newID += 1

                globals.OverrideSnapping = True
                loc = LocationItem(clickedx, clickedy, 8, 8, newID)
                globals.OverrideSnapping = False

                mw = globals.mainWindow
                loc.positionChanged = mw.HandleLocPosChange
                loc.sizeChanged = mw.HandleLocSizeChange
                loc.listitem = ListWidgetItem_SortsByOther(loc)
                mw.locationList.addItem(loc.listitem)
                mw.scene.addItem(loc)

                globals.Area.locations.append(loc)

                self.dragstamp = False
                self.currentobj = loc
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                self.scene().update()

                loc.UpdateListItem()

                SetDirty()

            elif globals.CurrentPaintType == 8:
                # paint a stamp
                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)

                clickedx = int(clicked.x() / globals.TileWidth * 16)
                clickedy = int(clicked.y() / globals.TileWidth * 16)

                stamp = globals.mainWindow.stampChooser.currentlySelectedStamp()
                if stamp is not None:
                    # Get the previous flower/grass type
                    oldGrassType = 5
                    for sprite in globals.Area.sprites:
                        if sprite.type == 564:
                            oldGrassType = min(sprite.spritedata[5] & 0xf, 5)
                            if oldGrassType < 2:
                                oldGrassType = 0

                            elif oldGrassType in [3, 4]:
                                oldGrassType = 3

                    objs = globals.mainWindow.placeEncodedObjects(stamp.MiyamotoClip, False, clickedx, clickedy)

                    # Get the current flower/grass type
                    grassType = 5
                    for sprite in globals.Area.sprites:
                        if sprite.type == 564:
                            grassType = min(sprite.spritedata[5] & 0xf, 5)
                            if grassType < 2:
                                grassType = 0

                            elif grassType in [3, 4]:
                                grassType = 3

                    # If the current type is not the previous type, reprocess the Overrides
                    # update the objects and flower sprite instances and update the scene
                    if grassType != oldGrassType and globals.Area.tileset0:
                        ProcessOverrides(globals.Area.tileset0)
                        globals.mainWindow.objPicker.LoadFromTilesets()
                        for layer in globals.Area.layers:
                            for tObj in layer:
                                tObj.updateObjCache()

                        for sprite in globals.Area.sprites:
                            if sprite.type == 546:
                                sprite.UpdateDynamicSizing()

                    for obj in objs:
                        obj.dragstartx = obj.objx
                        obj.dragstarty = obj.objy
                        obj.update()

                    globals.mainWindow.scene.update()

                    self.dragstamp = True
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy
                    self.currentobj = objs

                    SetDirty()

            elif globals.CurrentPaintType == 9:
                # paint a comment

                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int((clicked.x() - globals.TileWidth / 2) / globals.TileWidth * 16)
                clickedy = int((clicked.y() - globals.TileWidth / 2) / globals.TileWidth * 16)

                if clickedx % 8 < 4:
                    clickedx -= (clickedx % 8)
                else:
                    clickedx += 8 - (clickedx % 8)
                if clickedy % 8 < 4:
                    clickedy -= (clickedy % 8)
                else:
                    clickedy += 8 - (clickedy % 8)

                com = CommentItem(clickedx, clickedy, '')
                mw = globals.mainWindow
                com.positionChanged = mw.HandleComPosChange
                com.textChanged = mw.HandleComTxtChange
                mw.scene.addItem(com)
                com.setVisible(globals.CommentsShown)

                clist = mw.commentList
                com.listitem = QtWidgets.QListWidgetItem()
                clist.addItem(com.listitem)

                globals.Area.comments.append(com)

                self.dragstamp = False
                self.currentobj = com
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                globals.mainWindow.SaveComments()

                com.UpdateListItem()

                SetDirty()


            elif globals.CurrentPaintType == 12:
                if globals.Area.areanum == 1:
                    # paint a nabbit path node
                    clicked = self.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickedx = int((clicked.x() - globals.TileWidth / 2) / globals.TileWidth * 16) + 8
                    clickedy = int((clicked.y() - globals.TileWidth / 2) / globals.TileWidth * 16) + 8
                    if clickedx % 8 < 4:
                        clickedx -= (clickedx % 8)
                    else:
                        clickedx += 8 - (clickedx % 8)
                    if clickedy % 8 < 4:
                        clickedy -= (clickedy % 8)
                    else:
                        clickedy += 8 - (clickedy % 8)
                    mw = globals.mainWindow
                    plist = mw.nabbitPathList
                    selectedpn = None if len(plist.selectedItems()) < 1 else plist.selectedItems()[0]
                    if not globals.Area.nPathdata:
                        newpathdata = {'nodes': [
                                           {'x': clickedx, 'y': clickedy, 'action': 0,
                                            'unk1': 0, 'unk2': 0, 'unk3': 0, 'unk4': 0}],
                                       }
                        globals.Area.nPathdata = newpathdata
                        newnode = NabbitPathItem(clickedx, clickedy, newpathdata, newpathdata['nodes'][0], 0, 0, 0, 0)
                        newnode.positionChanged = mw.HandlePathPosChange

                        mw.scene.addItem(newnode)

                        peline = NabbitPathEditorLineItem(newpathdata['nodes'])
                        newpathdata['peline'] = peline
                        mw.scene.addItem(peline)

                        newnode.listitem = ListWidgetItem_SortsByOther(newnode)
                        plist.clear()
                        fpath = globals.Area.nPathdata
                        for fpnode in fpath['nodes']:
                            fpnode['graphicsitem'].listitem = ListWidgetItem_SortsByOther(fpnode['graphicsitem'],
                                                                                          fpnode[
                                                                                              'graphicsitem'].ListString())
                            plist.addItem(fpnode['graphicsitem'].listitem)
                            fpnode['graphicsitem'].updateId()
                        newnode.listitem.setSelected(True)
                        globals.Area.nPaths.append(newnode)

                        self.dragstamp = False
                        self.currentobj = newnode
                        self.dragstartx = clickedx
                        self.dragstarty = clickedy

                        newnode.UpdateListItem()

                        SetDirty()
                    else:
                        pathd = None
                        for pathnode in globals.Area.nPaths:
                            if selectedpn and pathnode.listitem == selectedpn:
                                pathd = pathnode.pathinfo

                        if not pathd:
                            pathd = globals.Area.nPaths[-1].pathinfo

                        newnodedata = {'x': clickedx, 'y': clickedy, 'action': 0,
                                       'unk1': 0, 'unk2': 0, 'unk3': 0, 'unk4': 0}
                        pathd['nodes'].append(newnodedata)

                        newnode = NabbitPathItem(clickedx, clickedy, pathd, newnodedata, 0, 0, 0, 0)

                        newnode.positionChanged = mw.HandlePathPosChange
                        mw.scene.addItem(newnode)

                        newnode.listitem = ListWidgetItem_SortsByOther(newnode)
                        plist.clear()
                        fpath = globals.Area.nPathdata
                        for fpnode in fpath['nodes']:
                            fpnode['graphicsitem'].listitem = ListWidgetItem_SortsByOther(fpnode['graphicsitem'],
                                                                                          fpnode[
                                                                                              'graphicsitem'].ListString())
                            plist.addItem(fpnode['graphicsitem'].listitem)
                            fpnode['graphicsitem'].updateId()
                        newnode.listitem.setSelected(True)
                        # globals.PaintingEntrance = ent
                        # globals.PaintingEntranceListIndex = minimumID

                        globals.Area.nPaths.append(newnode)
                        pathd['peline'].nodePosChanged()
                        self.dragstamp = False
                        self.currentobj = newnode
                        self.dragstartx = clickedx
                        self.dragstarty = clickedy

                        newnode.UpdateListItem()

                        SetDirty()

                else:
                    dlg = QtWidgets.QMessageBox()
                    dlg.setText(globals.trans.string('Paths', 4))
                    dlg.exec_()

            event.accept()

        elif eventButton == Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
            pos = self.mapToScene(event.x(), event.y())
            addsel = self.scene().items(pos)
            for i in addsel:
                if (int(i.flags()) & i.ItemIsSelectable) != 0:
                    i.setSelected(not i.isSelected())
                    break

        else:
            QtWidgets.QGraphicsView.mousePressEvent(self, event)

        globals.mainWindow.levelOverview.update()

    def resizeEvent(self, event):
        """
        Catches resize events
        """
        self.FrameSize.emit(event.size().width(), event.size().height())
        event.accept()
        QtWidgets.QGraphicsView.resizeEvent(self, event)

    @staticmethod
    def translateRect(rect, x, y):
        """
        Returns a translated copy of the rect
        """
        return rect.translated(x*globals.TileWidth, y*globals.TileWidth)

    @staticmethod
    def setOverrideCursor(cursor):
        """
        Safe way to override the cursor
        """
        if globals.app.overrideCursor() is None:
            globals.app.setOverrideCursor(cursor)

        else:
            globals.app.changeOverrideCursor(cursor)

    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed
        """

        inv = False  # if set to True, invalidates the scene at the end of this function.

        pos = self.mapToScene(event.x(), event.y())
        if pos.x() < 0: pos.setX(0)
        if pos.y() < 0: pos.setY(0)
        self.PositionHover.emit(int(pos.x()), int(pos.y()))

        if event.buttons() == Qt.MidButton:
            offset = self.__prevMousePos - event.pos()
            self.__prevMousePos = event.pos()

            self.YScrollBar.setValue(self.YScrollBar.value() + offset.y())
            self.XScrollBar.setValue(self.XScrollBar.value() + (-offset.x() if self.isRightToLeft() else offset.x()))

        elif event.buttons() & Qt.RightButton and self.currentobj is not None and not self.dragstamp:

            # possibly a small optimization
            type_obj = ObjectItem
            type_spr = SpriteItem
            type_ent = EntranceItem
            type_loc = LocationItem
            type_path = PathItem
            type_nPath = NabbitPathItem
            type_com = CommentItem

            # iterate through the objects if there's more than one
            if isinstance(self.currentobj, list) or isinstance(self.currentobj, tuple):
                objlist = self.currentobj
            else:
                objlist = (self.currentobj,)

            for obj in objlist:

                if isinstance(obj, type_obj):
                    # resize/move the current object
                    cx = obj.objx
                    cy = obj.objy
                    cwidth = obj.width
                    cheight = obj.height

                    dsx = self.dragstartx
                    dsy = self.dragstarty
                    clicked = self.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickx = int(clicked.x() / globals.TileWidth)
                    clicky = int(clicked.y() / globals.TileWidth)

                    # allow negative width/height and treat it properly :D
                    if clickx >= dsx:
                        x = dsx
                        width = clickx - dsx + 1
                    else:
                        x = clickx
                        width = dsx - clickx + 1

                    if clicky >= dsy:
                        y = dsy
                        height = clicky - dsy + 1
                    else:
                        y = clicky
                        height = dsy - clicky + 1

                    # if the position changed, set the new one
                    if cx != x or cy != y:
                        obj.objx = x
                        obj.objy = y
                        obj.setPos(x * globals.TileWidth, y * globals.TileWidth)
                        globals.mainWindow.levelOverview.update()

                    # if the size changed, recache it and update the area
                    if cwidth != width or cheight != height:
                        obj.updateObjCacheWH(width, height)
                        obj.width = width
                        obj.height = height

                        oldrect = obj.BoundingRect
                        oldrect.translate(cx * globals.TileWidth, cy * globals.TileWidth)
                        newrect = QtCore.QRectF(obj.x(), obj.y(), obj.width * globals.TileWidth, obj.height * globals.TileWidth)
                        updaterect = oldrect.united(newrect)

                        obj.UpdateRects()
                        obj.scene().update(updaterect)
                        globals.mainWindow.levelOverview.update()

                elif isinstance(obj, type_loc):
                    # resize/move the current location
                    cx = obj.objx
                    cy = obj.objy
                    cwidth = obj.width
                    cheight = obj.height

                    dsx = self.dragstartx
                    dsy = self.dragstarty
                    clicked = self.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickx = int(clicked.x() / globals.TileWidth * 16)
                    clicky = int(clicked.y() / globals.TileWidth * 16)

                    if clickx % 8 < 4:
                        clickx -= (clickx % 8)
                    else:
                        clickx += 8 - (clickx % 8)
                    if clicky % 8 < 4:
                        clicky -= (clicky % 8)
                    else:
                        clicky += 8 - (clicky % 8)

                    # allow negative width/height and treat it properly :D
                    if clickx >= dsx:
                        x = dsx
                        width = clickx - dsx
                    else:
                        x = clickx
                        width = dsx - clickx

                    if clicky >= dsy:
                        y = dsy
                        height = clicky - dsy
                    else:
                        y = clicky
                        height = dsy - clicky

                    width = max(width, 8)
                    height = max(height, 8)

                    # if the position changed, set the new one
                    if cx != x or cy != y:
                        obj.objx = x
                        obj.objy = y

                        globals.OverrideSnapping = True
                        obj.setPos(x * (globals.TileWidth / 16), y * (globals.TileWidth / 16))
                        globals.OverrideSnapping = False
                        obj.UpdateListItem()
                        globals.mainWindow.levelOverview.update()

                    # if the size changed, recache it and update the area
                    if cwidth != width or cheight != height:
                        obj.width = width
                        obj.height = height
                        #                    obj.updateObjCache()

                        delta = globals.TileWidth / 2

                        oldrect = obj.BoundingRect
                        oldrect.translate(cx * globals.TileWidth / 16, cy * globals.TileWidth / 16)
                        newrect = QtCore.QRectF(obj.x() - delta, obj.y() - delta, obj.width * globals.TileWidth / 16 + globals.TileWidth,
                                                obj.height * globals.TileWidth / 16 + globals.TileWidth)
                        updaterect = oldrect.united(newrect)

                        obj.UpdateRects()
                        obj.scene().update(updaterect)
                        globals.mainWindow.levelOverview.update()

                elif isinstance(obj, type_spr):
                    # move the created sprite
                    clicked = self.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickedx = int((clicked.x() - globals.TileWidth / 2) / globals.TileWidth * 16)
                    clickedy = int((clicked.y() - globals.TileWidth / 2) / globals.TileWidth * 16)

                    if clickedx % 8 < 4:
                        clickedx -= (clickedx % 8)
                    else:
                        clickedx += 8 - (clickedx % 8)
                    if clickedy % 8 < 4:
                        clickedy -= (clickedy % 8)
                    else:
                        clickedy += 8 - (clickedy % 8)

                    if obj.objx != clickedx or obj.objy != clickedy:
                        obj.objx = clickedx
                        obj.objy = clickedy
                        obj.setPos(int((clickedx + obj.ImageObj.xOffset) * globals.TileWidth / 16),
                                   int((clickedy + obj.ImageObj.yOffset) * globals.TileWidth / 16))
                        obj.ImageObj.positionChanged()
                        obj.UpdateListItem()
                        globals.mainWindow.levelOverview.update()

                elif isinstance(obj, type_ent) or isinstance(obj, type_path) or isinstance(obj, type_nPath) or isinstance(obj, type_com):
                    # move the created entrance/path/comment
                    clicked = self.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickedx = int((clicked.x() - globals.TileWidth / 2) / globals.TileWidth * 16)
                    clickedy = int((clicked.y() - globals.TileWidth / 2) / globals.TileWidth * 16)

                    if clickedx % 8 < 4:
                        clickedx -= (clickedx % 8)
                    else:
                        clickedx += 8 - (clickedx % 8)
                    if clickedy % 8 < 4:
                        clickedy -= (clickedy % 8)
                    else:
                        clickedy += 8 - (clickedy % 8)

                    if obj.objx != clickedx or obj.objy != clickedy:
                        oldx = obj.objx
                        oldy = obj.objy

                        obj.objx = clickedx
                        obj.objy = clickedy

                        obj.setPos(int(clickedx * globals.TileWidth / 16), int(clickedy * globals.TileWidth / 16))

                        if isinstance(obj, type_path) or isinstance(obj, type_nPath):
                            obj.updatePos()
                            obj.pathinfo['peline'].nodePosChanged()

                        elif isinstance(obj, type_com):
                            obj.UpdateTooltip()
                            obj.handlePosChange(oldx, oldy)

                        obj.UpdateListItem()
                        globals.mainWindow.levelOverview.update()

            event.accept()

        elif event.buttons() & Qt.RightButton and self.currentobj is not None and self.dragstamp:
            # The user is dragging a stamp - many objects.

            # possibly a small optimization
            type_obj = ObjectItem
            type_spr = SpriteItem

            # iterate through the objects if there's more than one
            if isinstance(self.currentobj, list) or isinstance(self.currentobj, tuple):
                objlist = self.currentobj
            else:
                objlist = (self.currentobj,)

            for obj in objlist:

                clicked = self.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)

                changex = clicked.x() - (self.dragstartx * globals.TileWidth / 16)
                changey = clicked.y() - (self.dragstarty * globals.TileWidth / 16)
                changexobj = int(changex / globals.TileWidth)
                changeyobj = int(changey / globals.TileWidth)
                changexspr = changex * 2 / 3
                changeyspr = changey * 2 / 3

                if isinstance(obj, type_obj):
                    # move the current object
                    newx = int(obj.dragstartx + changexobj)
                    newy = int(obj.dragstarty + changeyobj)

                    if obj.objx != newx or obj.objy != newy:
                        obj.objx = newx
                        obj.objy = newy
                        obj.setPos(newx * globals.TileWidth, newy * globals.TileWidth)

                elif isinstance(obj, type_spr):
                    # move the created sprite

                    newx = int(obj.dragstartx + changexspr)
                    newy = int(obj.dragstarty + changeyspr)

                    if obj.objx != newx or obj.objy != newy:
                        obj.objx = newx
                        obj.objy = newy
                        obj.setPos(int((newx + obj.ImageObj.xOffset) * globals.TileWidth / 16),
                                   int((newy + obj.ImageObj.yOffset) * globals.TileWidth / 16))

            self.scene().update()

        elif not self.selectionFix:
            type_obj = ObjectItem
            type_loc = LocationItem
            type_zone = ZoneItem

            objlist = [obj for obj in self.scene().selectedItems() if isinstance(obj, type_obj)]
            loclist = [loc for loc in self.scene().selectedItems() if isinstance(loc, type_loc)]
            zonelist = [zone for zone in self.scene().items() if isinstance(zone, type_zone)]

            dragging = any(thing.dragging for sel in (objlist, loclist, zonelist) for thing in sel)
            if not dragging:
                objCursorOverriden = True
                locCursorOverriden = True
                zoneCursorOverriden = True

                if objlist:
                    for obj in objlist:
                        if self.translateRect(obj.SelectionRect, obj.objx, obj.objy).contains(pos):
                            if self.translateRect(obj.GrabberRectTL, obj.objx, obj.objy).contains(pos):
                                self.setOverrideCursor(Qt.SizeFDiagCursor); objCursorOverriden = True
                                break

                            elif self.translateRect(obj.GrabberRectTR, obj.objx, obj.objy).contains(pos):
                                self.setOverrideCursor(Qt.SizeBDiagCursor); objCursorOverriden = True
                                break

                            elif self.translateRect(obj.GrabberRectBL, obj.objx, obj.objy).contains(pos):
                                self.setOverrideCursor(Qt.SizeBDiagCursor); objCursorOverriden = True
                                break

                            elif self.translateRect(obj.GrabberRectBR, obj.objx, obj.objy).contains(pos):
                                self.setOverrideCursor(Qt.SizeFDiagCursor); objCursorOverriden = True
                                break

                            elif (self.translateRect(obj.GrabberRectMT, obj.objx, obj.objy).contains(pos)
                                  or self.translateRect(obj.GrabberRectMB, obj.objx, obj.objy).contains(pos)):
                                self.setOverrideCursor(Qt.SizeVerCursor); objCursorOverriden = True
                                break

                            elif (self.translateRect(obj.GrabberRectML, obj.objx, obj.objy).contains(pos)
                                  or self.translateRect(obj.GrabberRectMR, obj.objx, obj.objy).contains(pos)):
                                self.setOverrideCursor(Qt.SizeHorCursor); objCursorOverriden = True
                                break

                            else:
                                self.setOverrideCursor(Qt.SizeAllCursor); objCursorOverriden = True
                                break

                        else:
                            objCursorOverriden = False

                else:
                    objCursorOverriden = False

                if loclist:
                    for loc in loclist:
                        if loc.SelectionRect.contains(pos.x(), pos.y()):
                            if self.translateRect(loc.GrabberRectTL, loc.objx/16, loc.objy/16).contains(pos):
                                self.setOverrideCursor(Qt.SizeFDiagCursor); locCursorOverriden = True
                                break

                            elif self.translateRect(loc.GrabberRectTR, loc.objx/16, loc.objy/16).contains(pos):
                                self.setOverrideCursor(Qt.SizeBDiagCursor); locCursorOverriden = True
                                break

                            elif self.translateRect(loc.GrabberRectBL, loc.objx/16, loc.objy/16).contains(pos):
                                self.setOverrideCursor(Qt.SizeBDiagCursor); locCursorOverriden = True
                                break

                            elif self.translateRect(loc.GrabberRectBR, loc.objx/16, loc.objy/16).contains(pos):
                                self.setOverrideCursor(Qt.SizeFDiagCursor); locCursorOverriden = True
                                break

                            elif (self.translateRect(loc.GrabberRectMT, loc.objx/16, loc.objy/16).contains(pos)
                                  or self.translateRect(loc.GrabberRectMB, loc.objx/16, loc.objy/16).contains(pos)):
                                self.setOverrideCursor(Qt.SizeVerCursor); locCursorOverriden = True
                                break

                            elif (self.translateRect(loc.GrabberRectML, loc.objx/16, loc.objy/16).contains(pos)
                                  or self.translateRect(loc.GrabberRectMR, loc.objx/16, loc.objy/16).contains(pos)):
                                self.setOverrideCursor(Qt.SizeHorCursor); locCursorOverriden = True
                                break

                            else:
                                self.setOverrideCursor(Qt.SizeAllCursor); locCursorOverriden = True
                                break

                        else:
                            locCursorOverriden = False

                else:
                    locCursorOverriden = False

                if zonelist:
                    for zone in zonelist:
                        if zone.sceneBoundingRect().contains(pos.x(), pos.y()):
                            if self.translateRect(zone.GrabberRectTL, zone.objx/16, zone.objy/16).contains(pos):
                                self.setOverrideCursor(Qt.SizeFDiagCursor); zoneCursorOverriden = True
                                break

                            elif self.translateRect(zone.GrabberRectTR, zone.objx/16, zone.objy/16).contains(pos):
                                self.setOverrideCursor(Qt.SizeBDiagCursor); zoneCursorOverriden = True
                                break

                            elif self.translateRect(zone.GrabberRectBL, zone.objx/16, zone.objy/16).contains(pos):
                                self.setOverrideCursor(Qt.SizeBDiagCursor); zoneCursorOverriden = True
                                break

                            elif self.translateRect(zone.GrabberRectBR, zone.objx/16, zone.objy/16).contains(pos):
                                self.setOverrideCursor(Qt.SizeFDiagCursor); zoneCursorOverriden = True
                                break

                            elif (self.translateRect(zone.GrabberRectMT, zone.objx/16, zone.objy/16).contains(pos)
                                  or self.translateRect(zone.GrabberRectMB, zone.objx/16, zone.objy/16).contains(pos)):
                                self.setOverrideCursor(Qt.SizeVerCursor); zoneCursorOverriden = True
                                break

                            elif (self.translateRect(zone.GrabberRectML, zone.objx/16, zone.objy/16).contains(pos)
                                  or self.translateRect(zone.GrabberRectMR, zone.objx/16, zone.objy/16).contains(pos)):
                                self.setOverrideCursor(Qt.SizeHorCursor); zoneCursorOverriden = True
                                break

                            else:
                                zoneCursorOverriden = False
                                break

                        else:
                            zoneCursorOverriden = False

                else:
                    zoneCursorOverriden = False

                if (not (objlist or loclist or zonelist) or not (objCursorOverriden or locCursorOverriden or zoneCursorOverriden)) and globals.app.overrideCursor():
                    globals.app.restoreOverrideCursor()

            QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

        if inv: self.scene().invalidate()

    def mouseReleaseEvent(self, event):
        """
        Overrides mouse release events if needed
        """
        if event.button() == Qt.RightButton:
            self.currentobj = None

        elif event.button() == Qt.LeftButton:
            self.selectionFix = False

        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

    def paintEvent(self, e):
        """
        Handles paint events and fires a signal
        """
        self.repaint.emit()
        QtWidgets.QGraphicsView.paintEvent(self, e)

    def wheelEvent(self, event):
        """
        Handles wheel events for zooming in/out
        """
        if QtWidgets.QApplication.keyboardModifiers() == Qt.ControlModifier:
            numDegrees = event.angleDelta() / 8
            if not numDegrees.isNull():
                numSteps = numDegrees / 15
                numStepsY = numSteps.y()
                globals.mainWindow.ZoomWidget.slider.setSliderPosition(globals.mainWindow.ZoomWidget.slider.value() + numStepsY)

        elif QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
            numDegrees = event.angleDelta() / 8
            if not numDegrees.isNull():
                numSteps = numDegrees / 15
                numStepsY = numSteps.y()
                self.XScrollBar.setSliderPosition(self.XScrollBar.value() - numStepsY * 24 * 8)

        else:
            QtWidgets.QGraphicsView.wheelEvent(self, event)

    def drawForeground(self, painter, rect):
        """
        Draws a foreground grid and other stuff
        """
        # Draw the grid
        drawForegroundGrid(painter, rect)


class InfoPreviewWidget(QtWidgets.QWidget):
    """
    Widget that shows a preview of the level metadata info - available in vertical & horizontal flavors
    """

    def __init__(self, direction):
        """
        Creates and initializes the widget
        """
        super().__init__()
        self.direction = direction

        self.Label1 = QtWidgets.QLabel('')
        if self.direction == Qt.Horizontal: self.Label2 = QtWidgets.QLabel('')
        self.updateLabels()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.Label1)
        if self.direction == Qt.Horizontal: self.mainLayout.addWidget(self.Label2)
        self.setLayout(self.mainLayout)

        if self.direction == Qt.Horizontal: self.setMinimumWidth(256)

    def updateLabels(self):
        """
        Updates the widget labels
        """
        if ('Area' not in globals.globals()) or not hasattr(globals.Area, 'filename'):  # can't get level metadata if there's no level
            self.Label1.setText('')
            if self.direction == Qt.Horizontal: self.Label2.setText('')
            return

        a = [  # MUST be a list, not a tuple
            globals.mainWindow.fileTitle,
            globals.Area.Title,
            globals.trans.string('InfoDlg', 8, '[name]', globals.Area.Creator),
            globals.trans.string('InfoDlg', 5) + ' ' + globals.Area.Author,
            globals.trans.string('InfoDlg', 6) + ' ' + globals.Area.Group,
            globals.trans.string('InfoDlg', 7) + ' ' + globals.Area.Webpage,
        ]

        for b, section in enumerate(a):  # cut off excessively long strings
            if self.direction == Qt.Vertical:
                short = clipStr(section, 128)
            else:
                short = clipStr(section, 184)
            if short is not None: a[b] = short + '...'

        if self.direction == Qt.Vertical:
            str1 = a[0] + '<br>' + a[1] + '<br>' + a[2] + '<br>' + a[3] + '<br>' + a[4] + '<br>' + a[5]
            self.Label1.setText(str1)
        else:
            str1 = a[0] + '<br>' + a[1] + '<br>' + a[2]
            str2 = a[3] + '<br>' + a[4] + '<br>' + a[5]
            self.Label1.setText(str1)
            self.Label2.setText(str2)

        self.update()


class GameDefViewer(QtWidgets.QWidget):
    """
    Widget which displays basic info about the current game definition
    """

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QWidget.__init__(self)
        self.imgLabel = QtWidgets.QLabel()
        self.imgLabel.setToolTip(globals.trans.string('Gamedefs', 0))
        self.imgLabel.setPixmap(GetIcon('sprites', False).pixmap(16, 16))
        self.versionLabel = QtWidgets.QLabel()
        self.titleLabel = QtWidgets.QLabel()
        self.descLabel = QtWidgets.QLabel()
        self.descLabel.setWordWrap(True)
        self.descLabel.setMinimumHeight(40)

        # Make layouts
        left = QtWidgets.QVBoxLayout()
        left.addWidget(self.imgLabel)
        left.addWidget(self.versionLabel)
        left.addStretch(1)
        right = QtWidgets.QVBoxLayout()
        right.addWidget(self.titleLabel)
        right.addWidget(self.descLabel)
        right.addStretch(1)
        main = QtWidgets.QHBoxLayout()
        main.addLayout(left)
        main.addWidget(createVertLine())
        main.addLayout(right)
        main.setStretch(2, 1)
        self.setLayout(main)
        self.setMaximumWidth(256 + 64)

        self.updateLabels()

    def updateLabels(self):
        """
        Updates all labels
        """
        empty = QtGui.QPixmap(16, 16)
        empty.fill(QtGui.QColor(0, 0, 0, 0))
        img = GetIcon('sprites', False).pixmap(16, 16) if (
        (globals.gamedef.recursiveFiles('sprites', False, True) != []) or (not globals.gamedef.custom)) else empty
        ver = '' if globals.gamedef.version is None else '<i><p style="font-size:10px;">v' + str(globals.gamedef.version) + '</p></i>'
        title = '<b>' + str(globals.gamedef.name) + '</b>'
        desc = str(globals.gamedef.description)

        self.imgLabel.setPixmap(img)
        self.versionLabel.setText(ver)
        self.titleLabel.setText(title)
        self.descLabel.setText(desc)


class GameDefSelector(QtWidgets.QWidget):
    """
    Widget which lets you pick a new game definition
    """
    gameChanged = QtCore.pyqtSignal()

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QWidget.__init__(self)

        # Populate a list of gamedefs
        import gamedefs
        self.GameDefs = gamedefs.getAvailableGameDefs()

        # Add them to the main layout
        self.group = QtWidgets.QButtonGroup()
        self.group.setExclusive(True)
        L = QtWidgets.QGridLayout()
        row = 0
        col = 0
        current = setting('LastGameDef')
        id = 0
        for folder in self.GameDefs:
            def_ = gamedefs.MiyamotoGameDefinition(folder)
            btn = QtWidgets.QRadioButton()
            if folder == current: btn.setChecked(True)
            btn.toggled.connect(self.HandleRadioButtonClick)
            self.group.addButton(btn, id)
            btn.setToolTip(def_.description)
            id += 1
            L.addWidget(btn, row, col)

            name = QtWidgets.QLabel(def_.name)
            name.setToolTip(def_.description)
            L.addWidget(name, row, col + 1)

            row += 1
            if row > 2:
                row = 0
                col += 2

        del gamedefs

        self.setLayout(L)

    def HandleRadioButtonClick(self, checked):
        """
        Handles radio button clicks
        """
        if not checked: return  # this is called twice; one button is checked, another is unchecked

        import gamedefs
        gamedefs.loadNewGameDef(self.GameDefs[self.group.checkedId()])
        del gamedefs

        self.gameChanged.emit()


class GameDefMenu(QtWidgets.QMenu):
    """
    A menu which lets the user pick gamedefs
    """
    gameChanged = QtCore.pyqtSignal()

    def __init__(self):
        """
        Creates and initializes the menu
        """
        QtWidgets.QMenu.__init__(self)

        # Add the gamedef viewer widget
        self.currentView = GameDefViewer()
        self.currentView.setMinimumHeight(100)
        self.gameChanged.connect(self.currentView.updateLabels)

        v = QtWidgets.QWidgetAction(self)
        v.setDefaultWidget(self.currentView)
        self.addAction(v)
        self.addSeparator()

        # Add entries for each gamedef
        import gamedefs
        self.GameDefs = gamedefs.getAvailableGameDefs()

        self.actGroup = QtWidgets.QActionGroup(self)
        loadedDef = setting('LastGameDef')
        for folder in self.GameDefs:
            def_ = gamedefs.MiyamotoGameDefinition(folder)
            act = QtWidgets.QAction(self)
            act.setText(def_.name)
            act.setToolTip(def_.description)
            act.setData(folder)
            act.setActionGroup(self.actGroup)
            act.setCheckable(True)
            if folder == loadedDef:
                act.setChecked(True)
            act.toggled.connect(self.handleGameDefClicked)
            self.addAction(act)

        del gamedefs

    def handleGameDefClicked(self, checked):
        """
        Handles the user clicking a gamedef
        """
        if not checked: return

        name = self.actGroup.checkedAction().data()

        import gamedefs
        gamedefs.loadNewGameDef(name)
        del gamedefs

        self.gameChanged.emit()


class RecentFilesMenu(QtWidgets.QMenu):
    """
    A menu which displays recently opened files
    """
    def __init__(self):
        """
        Creates and initializes the menu
        """
        QtWidgets.QMenu.__init__(self)
        self.setMinimumWidth(192)

        # Here's how this works:
        # - Upon startup, RecentFiles is obtained from QSettings and put into self.FileList
        # - All modifications to the menu thereafter are then applied to self.FileList
        # - The actions displayed in the menu are determined by whatever's in self.FileList
        # - Whenever self.FileList is changed, self.writeSettings is called which writes
        #      it all back to the QSettings

        # Populate FileList upon startup
        if globals.settings.contains('RecentFiles'):
            self.FileList = str(setting('RecentFiles')).split('|')

        else:
            self.FileList = ['']

        # This fixes bugs
        self.FileList = [path for path in self.FileList if path.lower() not in ('', 'none', 'false', 'true')]

        self.updateActionList()


    def writeSettings(self):
        """
        Writes FileList back to the Registry
        """
        setSetting('RecentFiles', str('|'.join(self.FileList)))

    def updateActionList(self):
        """
        Updates the actions visible in the menu
        """

        self.clear()  # removes any actions already in the menu
        ico = GetIcon('new')

        for i, filename in enumerate(self.FileList):
            filename = os.path.basename(filename)
            short = clipStr(filename, 72)
            if short is not None: filename = short + '...'

            act = QtWidgets.QAction(ico, filename, self)
            if i <= 9: act.setShortcut(QtGui.QKeySequence('Ctrl+Alt+%d' % i))
            act.setToolTip(str(self.FileList[i]))
            act.triggered.connect(lambda checked, x=i: self.HandleOpenRecentFile(x))

            self.addAction(act)

    def AddToList(self, path):
        """
        Adds an entry to the list
        """
        MaxLength = 16

        if path in ('None', 'True', 'False', None, True, False): return  # fixes bugs
        path = str(path).replace('/', '\\')

        new = [path]
        for filename in self.FileList:
            if filename != path:
                new.append(filename)
        if len(new) > MaxLength: new = new[:MaxLength]

        self.FileList = new
        self.writeSettings()
        self.updateActionList()

    def RemoveFromList(self, index):
        """
        Removes an entry from the list
        """
        del self.FileList[index]
        self.writeSettings()
        self.updateActionList()

    def clearAll(self):
        """
        Clears all recent files from the list and the registry
        """
        self.FileList = []
        self.writeSettings()
        self.updateActionList()

    def HandleOpenRecentFile(self, number):
        """
        Open a recently opened level picked from the main menu
        """
        if globals.mainWindow.CheckDirty():
            return

        if not globals.mainWindow.LoadLevel(None, self.FileList[number], True, 1, True):
            self.RemoveFromList(number)


class ZoomWidget(QtWidgets.QWidget):
    """
    Widget that allows easy zoom level control
    """

    def __init__(self):
        """
        Creates and initializes the widget
        """
        super().__init__()
        maxwidth = 512 - 128
        maxheight = 20

        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.minLabel = QtWidgets.QPushButton()
        self.minusLabel = QtWidgets.QPushButton()
        self.plusLabel = QtWidgets.QPushButton()
        self.maxLabel = QtWidgets.QPushButton()

        self.slider.setMaximumHeight(maxheight)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(globals.mainWindow.ZoomLevels) - 1)
        self.slider.setTickInterval(2)
        self.slider.setTickPosition(self.slider.TicksAbove)
        self.slider.setPageStep(1)
        self.slider.setTracking(True)
        self.slider.setSliderPosition(self.findIndexOfLevel(100))
        self.slider.valueChanged.connect(self.sliderMoved)

        self.minLabel.setIcon(GetIcon('zoommin'))
        self.minusLabel.setIcon(GetIcon('zoomout'))
        self.plusLabel.setIcon(GetIcon('zoomin'))
        self.maxLabel.setIcon(GetIcon('zoommax'))
        self.minLabel.setFlat(True)
        self.minusLabel.setFlat(True)
        self.plusLabel.setFlat(True)
        self.maxLabel.setFlat(True)
        self.minLabel.clicked.connect(globals.mainWindow.HandleZoomMin)
        self.minusLabel.clicked.connect(globals.mainWindow.HandleZoomOut)
        self.plusLabel.clicked.connect(globals.mainWindow.HandleZoomIn)
        self.maxLabel.clicked.connect(globals.mainWindow.HandleZoomMax)

        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.minLabel, 0, 0)
        self.layout.addWidget(self.minusLabel, 0, 1)
        self.layout.addWidget(self.slider, 0, 2)
        self.layout.addWidget(self.plusLabel, 0, 3)
        self.layout.addWidget(self.maxLabel, 0, 4)
        self.layout.setVerticalSpacing(0)
        self.layout.setHorizontalSpacing(0)
        self.layout.setContentsMargins(0, 0, 4, 0)

        self.setLayout(self.layout)
        self.setMinimumWidth(maxwidth)
        self.setMaximumWidth(maxwidth)
        self.setMaximumHeight(maxheight)

    def sliderMoved(self):
        """
        Handle the slider being moved
        """
        globals.mainWindow.ZoomTo(globals.mainWindow.ZoomLevels[self.slider.value()])

    def setZoomLevel(self, newLevel):
        """
        Moves the slider to the zoom level given
        """
        self.slider.setSliderPosition(self.findIndexOfLevel(newLevel))

    def findIndexOfLevel(self, level):
        for i, mainlevel in enumerate(globals.mainWindow.ZoomLevels):
            if float(mainlevel) == float(level): return i


class ZoomStatusWidget(QtWidgets.QWidget):
    """
    Shows the current zoom level, in percent
    """

    def __init__(self):
        """
        Creates and initializes the widget
        """
        super().__init__()
        self.label = QtWidgets.QPushButton('100%')
        self.label.setFlat(True)
        self.label.clicked.connect(globals.mainWindow.HandleZoomActual)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(4, 0, 8, 0)
        self.setMaximumWidth(56)

        self.setLayout(self.layout)

    def setZoomLevel(self, zoomLevel):
        """
        Updates the widget
        """
        if float(int(zoomLevel)) == float(zoomLevel):
            self.label.setText(str(int(zoomLevel)) + '%')
        else:
            self.label.setText(str(float(zoomLevel)) + '%')


class EmbeddedTabSeparate(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.currentChanged.connect(self.tabChanged)

        self.objTS1Tab = QtWidgets.QWidget()
        self.objTS2Tab = QtWidgets.QWidget()
        self.objTS3Tab = QtWidgets.QWidget()

        tsicon = GetIcon('objects')
        self.addTab(self.objTS1Tab, tsicon, '2')
        self.addTab(self.objTS2Tab, tsicon, '3')
        self.addTab(self.objTS3Tab, tsicon, '4')

        self.m1 = ObjectPickerWidget.ObjectListModel()
        self.m2 = ObjectPickerWidget.ObjectListModel()
        self.m3 = ObjectPickerWidget.ObjectListModel()

    def tabChanged(self, nt, layout=None):
        if nt >= 0 and nt <= 2:
            if not layout and hasattr(globals.mainWindow, 'createObjectLayout'):
                layout = globals.mainWindow.createObjectLayout

            if layout:
                globals.mainWindow.objPicker.ShowTileset(2)
                if nt == 0:
                    self.objTS1Tab.setLayout(layout)
                elif nt == 1:
                    self.objTS2Tab.setLayout(layout)
                else:
                    self.objTS3Tab.setLayout(layout)

    def setLayout(self, layout):
        self.tabChanged(self.currentIndex(), layout)

    def getObjectAndPaintType(self, type):
        return type, self.currentIndex()+1

    def getModels(self):
        return self.m1, self.m2, self.m3

    def getActiveModel(self):
        return self.getModels()[self.currentIndex()]

    def LoadFromTilesets(self):
        self.m1.LoadFromTileset(1)
        self.m2.LoadFromTileset(2)
        self.m3.LoadFromTileset(3)


class EmbeddedTabJoined(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.m123 = ObjectPickerWidget.ObjectListModel()

    @staticmethod
    def getObjectAndPaintType(type):
        type += 1
        paintType = 1

        if type > globals.numObj[1]:
            paintType = 3
            type -= globals.numObj[1]

        elif type > globals.numObj[0]:
            paintType = 2
            type -= globals.numObj[0]

        return type-1, paintType

    def getModels(self):
        return self.m123,

    def getActiveModel(self):
        return self.m123

    def LoadFromTilesets(self):
        self.m123.LoadFromTileset(4)


class ListWidgetWithToolTipSignal(QtWidgets.QListWidget):
    """
    A QtWidgets.QListWidget that includes a signal that
    is emitted when a tooltip is about to be shown. Useful
    for making tooltips that update every time you show
    them.
    """
    toolTipAboutToShow = QtCore.pyqtSignal(QtWidgets.QListWidgetItem)

    def viewportEvent(self, e):
        """
        Handles viewport events
        """
        if e.type() == e.ToolTip:
            item = self.itemFromIndex(self.indexAt(e.pos()))
            if item is not None:
                self.toolTipAboutToShow.emit(item)

        return super().viewportEvent(e)


class ListWidgetItem_SortsByOther(QtWidgets.QListWidgetItem):
    """
    A ListWidgetItem that defers sorting to another object.
    """

    def __init__(self, reference, text=''):
        super().__init__(text)
        self.reference = reference

    def __lt__(self, other):
        return self.reference < other.reference


class IconsOnlyTabBar(QtWidgets.QTabBar):
    """
    A QTabBar subclass that is designed to only display icons.
    From "Reggie-Updated".

    On macOS Mojave (and probably other versions around there),
    QTabWidget tabs are way too wide when only displaying icons.
    This ultimately causes the Miyamoto palette itself to have a really
    high minimum width.

    This subclass limits tab widths to fix the problem.
    """
    def tabSizeHint(self, index):
        res = super().tabSizeHint(index)
        if globals.app.style().metaObject().className() == 'QMacStyle':
            res.setWidth(res.height() * 2)

        return res
