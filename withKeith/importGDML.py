# -*- coding: utf8 -*-
#**************************************************************************
#*                                                                        *
#*   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
#*                                                                        *
#*   This program is free software; you can redistribute it and/or modify *
#*   it under the terms of the GNU Lesser General Public License (LGPL)   *
#*   as published by the Free Software Foundation; either version 2 of    *
#*   the License, or (at your option) any later version.                  *
#*   for detail see the LICENCE text file.                                *
#*                                                                        *
#*   This program is distributed in the hope that it will be useful,      *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of       *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        *
#*   GNU Library General Public License for more details.                 *
#*                                                                        *
#*   You should have received a copy of the GNU Library General Public    *
#*   License along with this program; if not, write to the Free Software  *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 *
#*   USA                                                                  *
#*                                                                        *
#*   Acknowledgements :                                                   *
#*                                                                        *
#*                                                                        *
#**************************************************************************
__title__="FreeCAD - GDML importer"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD 
import os, io, sys, re
import Part, Draft

from math import *
from . import GDMLShared

##########################
# Globals Dictionarys    #
##########################
#global setup, define, materials, solids, structure
#globals constDict, filesDict 

if FreeCAD.GuiUp:
   import PartGui, FreeCADGui
   gui = True
else:
   print("FreeCAD Gui not present.")
   gui = False

import Part

if open.__module__ == '__builtin__':
    pythonopen = open # to distinguish python built-in open function from the one declared here


#try:
#    _encoding = QtGui.QApplication.UnicodeUTF8
#    def translate(context, text):
#        "convenience function for Qt translator"
#        from PySide import QtGui
#        return QtGui.QApplication.translate(context, text, None, _encoding)
#except AttributeError:
#    def translate(context, text):
#        "convenience function for Qt translator"
#        from PySide import QtGui
#        return QtGui.QApplication.translate(context, text, None)



def open(filename):
    "called when freecad opens a file."
    global doc
    docname = os.path.splitext(os.path.basename(filename))[0]
    doc = FreeCAD.newDocument(docname)
    if filename.lower().endswith('.gdml'):
        processGDML(doc,filename,True)
    return doc

def insert(filename,docname):
    "called when freecad imports a file"
    global doc
    groupname = os.path.splitext(os.path.basename(filename))[0]
    try:
        doc=FreeCAD.getDocument(docname)
    except NameError:
        doc=FreeCAD.newDocument(docname)
    if filename.lower().endswith('.gdml'):
        processGDML(doc,filename,True)

class switch(object):
    value = None
    def __new__(class_, value):
        class_.value = value
        return True

def case(*args):
    return any((arg == switch.value for arg in args))

def translate(shape,base) :
    # Input Object and displacement vector - return a transformed shape
    myPlacement = FreeCAD.Placement()
    myPlacement.move(base)
    mat1 = myPlacement.toMatrix()
    #print(mat1)
    mat2 = shape.Matrix
    mat  = mat1.multiply(mat2)
    #print(mat)
    retShape = shape.copy()
    retShape.transformShape(mat, True)
    return retShape

def checkConstant(vval):
    GDMLShared.trace(vval)

def getName(ptr) :
    return (ptr.attrib.get('name'))

def getText(ptr,var,default) :
    #print("Get Texti : "+str(ptr.attrib.get(var))+" : "+str(var))
    if var in ptr.attrib :
       return (ptr.attrib.get(var))
    else :
       return default

def setDisplayMode(obj,mode):
    GDMLShared.trace("setDisplayMode : "+str(mode))
    if mode == 2 :
       obj.ViewObject.DisplayMode = 'Hide'

    if mode == 3 :
       obj.ViewObject.DisplayMode = 'Wireframe'


def createArb8(part,solid,material,px,py,pz,rot,displayMode) :
    # parent, sold
    from .GDMLObjects import GDMLArb8, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateArb8 : ")
    #GDMLShared.trace("material : "+material)
    GDMLShared.trace(solid.attrib)


    myArb8=part.newObject("Part::FeaturePython","GDMLArb8:"+getName(solid))
    v1x = GDMLShared.getVal(solid,'v1x')
    v1y = GDMLShared.getVal(solid,'v1y')
    v2x = GDMLShared.getVal(solid,'v2x')
    v2y = GDMLShared.getVal(solid,'v2y')
    v3x = GDMLShared.getVal(solid,'v3x')
    v3y = GDMLShared.getVal(solid,'v3y')
    v4x = GDMLShared.getVal(solid,'v4x')
    v4y = GDMLShared.getVal(solid,'v4y')
    v5x = GDMLShared.getVal(solid,'v5x')
    v5y = GDMLShared.getVal(solid,'v5y')
    v6x = GDMLShared.getVal(solid,'v6x')
    v6y = GDMLShared.getVal(solid,'v6y')
    v7x = GDMLShared.getVal(solid,'v7x')
    v7y = GDMLShared.getVal(solid,'v7y')
    v8x = GDMLShared.getVal(solid,'v8x')
    v8y = GDMLShared.getVal(solid,'v8y')
    dz = GDMLShared.getVal(solid,'dz')

    lunit = getText(solid,'lunit',"mm")
    GDMLArb8(myArb8,v1x, v1y, v2x, v2y, v3x, v3y, v4x, v4y,  \
                v5x, v5y, v6x, v6y, v7x, v7y, v8x, v8y, dz, \
                lunit, material)
    GDMLShared.trace("Logical Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myArb8.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myArb8.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myArb8.ViewObject)
       setDisplayMode(myArb8,displayMode)

    return myArb8


def createBox(part,solid,material,px,py,pz,rot,displayMode) :
    # parent, sold
    from .GDMLObjects import GDMLBox, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateBox : ")
    #GDMLShared.trace("material : "+material)
    GDMLShared.trace(solid.attrib)

    # modifs lambda (otherwise each time we open the gdml file, 
    # the part name will have one more GDMLBox added
    # No - need to remove leading GDMLBox on export
    mycube=part.newObject("Part::FeaturePython","GDMLBox:"+getName(solid))
    #mycube=part.newObject("Part::FeaturePython",getName(solid))
    x = GDMLShared.getVal(solid,'x')
    y = GDMLShared.getVal(solid,'y')
    z = GDMLShared.getVal(solid,'z')
    lunit = getText(solid,'lunit',"mm")
    GDMLBox(mycube,x,y,z,lunit,material)
    GDMLShared.trace("Logical Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mycube.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mycube.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mycube.ViewObject)
       setDisplayMode(mycube,displayMode)
    #myCube.Shape = translate(mycube.Shape,base)
    return mycube

def createCone(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLCone, ViewProvider
    GDMLShared.trace("CreateCone : ")
    GDMLShared.trace(solid.attrib)
    rmin1 = GDMLShared.getVal(solid,'rmin1')
    rmax1 = GDMLShared.getVal(solid,'rmax1')
    rmin2 = GDMLShared.getVal(solid,'rmin2')
    rmax2 = GDMLShared.getVal(solid,'rmax2')
    z = GDMLShared.getVal(solid,'z')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mycone=part.newObject("Part::FeaturePython","GDMLCone:"+getName(solid))
    GDMLCone(mycone,rmin1,rmax1,rmin2,rmax2,z, \
             startphi,deltaphi,aunit,lunit,material)
    GDMLShared.trace("CreateCone : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mycone.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mycone.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set "ViewProvider before setDisplay
       ViewProvider(mycone.ViewObject)
       setDisplayMode(mycone,displayMode)
    return(mycone)

def createElcone(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLElCone, ViewProvider
    GDMLShared.trace("CreateElCone : ")
    dx = GDMLShared.getVal(solid,'dx')
    dy = GDMLShared.getVal(solid,'dy')
    zmax = GDMLShared.getVal(solid,'zmax')
    zcut = GDMLShared.getVal(solid,'zcut')
    lunit = getText(solid,'lunit',"mm")
    myelcone=part.newObject("Part::FeaturePython","GDMLElCone:"+getName(solid))
    GDMLElCone(myelcone,dx,dy,zmax,zcut,lunit,material)
    GDMLShared.trace("CreateElCone : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz-zmax/2)
    #base = FreeCAD.Vector(0,0,0)
    myelcone.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myelcone.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myelcone.ViewObject)
       setDisplayMode(myelcone,displayMode)
    return(myelcone)

def createEllipsoid(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLEllipsoid, ViewProvider
    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace(solid.attrib)
    ax = GDMLShared.getVal(solid,'ax')
    by = GDMLShared.getVal(solid,'by')
    cz = GDMLShared.getVal(solid,'cz')
    zcut1 = GDMLShared.getVal(solid,'zcut1')
    zcut2 = GDMLShared.getVal(solid,'zcut2')
    lunit = getText(solid,'lunit',"mm")
    myelli=part.newObject("Part::FeaturePython","GDMLEllipsoid:"+getName(solid))
    # cuts 0 for now
    GDMLEllipsoid(myelli,ax, by, cz,zcut1,zcut2,lunit,material)
    GDMLShared.trace("CreateEllipsoid : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myelli.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myelli.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myelli.ViewObject)
       setDisplayMode(myelli,displayMode)
    return myelli

def createEltube(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLElTube, ViewProvider
    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace(solid.attrib)
    dx = GDMLShared.getVal(solid,'dx')
    dy = GDMLShared.getVal(solid,'dy')
    dz = GDMLShared.getVal(solid,'dz')
    lunit = getText(solid,'lunit',"mm")
    myeltube=part.newObject("Part::FeaturePython","GDMLElTube:"+getName(solid))
    GDMLElTube(myeltube,dx, dy, dz,lunit,material)
    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myeltube.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myeltube.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myeltube.ViewObject)
       setDisplayMode(myeltube,displayMode)
    return myeltube

def createPolycone(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLPolycone, GDMLzplane, \
            ViewProvider, ViewProviderExtension
    GDMLShared.trace("Create Polycone : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mypolycone=part.newObject("Part::FeaturePython","GDMLPolycone:"+getName(solid))
    mypolycone.addExtension("App::OriginGroupExtensionPython", None)
    GDMLPolycone(mypolycone,startphi,deltaphi,aunit,lunit,material)
    if FreeCAD.GuiUp :
       ViewProviderExtension(mypolycone.ViewObject)

    #mypolycone.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall('zplane'))
    for zplane in solid.findall('zplane') : 
        GDMLShared.trace(zplane)
        rmin = GDMLShared.getVal(zplane,'rmin')
        rmax = GDMLShared.getVal(zplane,'rmax')
        z = GDMLShared.getVal(zplane,'z')
        myzplane=FreeCAD.ActiveDocument.addObject('App::FeaturePython','zplane') 
        mypolycone.addObject(myzplane)
        #myzplane=mypolycone.newObject('App::FeaturePython','zplane') 
        GDMLzplane(myzplane,rmin,rmax,z)
        if FreeCAD.GuiUp :
           ViewProvider(myzplane)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypolycone.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypolycone.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       setDisplayMode(mypolycone,displayMode)
    return mypolycone

def createPolyhedra(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLPolyhedra, GDMLzplane, \
            ViewProvider, ViewProviderExtension
    GDMLShared.trace("Create Polyhedra : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    numsides = GDMLShared.getVal(solid,'numsides',2)
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mypolyhedra=part.newObject("Part::FeaturePython","GDMLPolyhedra:"+ \
                getName(solid))
    mypolyhedra.addExtension("App::OriginGroupExtensionPython", None)
    GDMLPolyhedra(mypolyhedra,startphi,deltaphi,numsides,aunit,lunit,material)
    if FreeCAD.GuiUp :
       ViewProviderExtension(mypolyhedra.ViewObject)

    #mypolyhedra.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall('zplane'))
    for zplane in solid.findall('zplane') : 
        GDMLShared.trace(zplane)
        rmin = GDMLShared.getVal(zplane,'rmin')
        rmax = GDMLShared.getVal(zplane,'rmax')
        z = GDMLShared.getVal(zplane,'z')
        myzplane=FreeCAD.ActiveDocument.addObject('App::FeaturePython','zplane') 
        mypolyhedra.addObject(myzplane)
        #myzplane=mypolyhedra.newObject('App::FeaturePython','zplane') 
        GDMLzplane(myzplane,rmin,rmax,z)
        if FreeCAD.GuiUp :
           ViewProvider(myzplane)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypolyhedra.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypolyhedra.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       setDisplayMode(mypolyhedra,displayMode)
    return mypolyhedra

def createSphere(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLSphere, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateSphere : ")
    GDMLShared.trace("Display Mode : "+str(displayMode))
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid,'rmin')
    rmax = GDMLShared.getVal(solid,'rmax')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    starttheta = GDMLShared.getVal(solid,'starttheta')
    deltatheta = GDMLShared.getVal(solid,'deltatheta')
    mysphere=part.newObject("Part::FeaturePython","GDMLSphere:"+getName(solid))
    GDMLSphere(mysphere,rmin,rmax,startphi,deltaphi,starttheta, \
            deltatheta,aunit, lunit,material)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mysphere.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mysphere.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mysphere.ViewObject)
       setDisplayMode(mysphere,displayMode)
    return mysphere

def createTrap(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTrap, ViewProvider
    GDMLShared.trace("CreateTrap : ")
    GDMLShared.trace(solid.attrib)
    z  = GDMLShared.getVal(solid,'z')
    x1 = GDMLShared.getVal(solid,'x1')
    x2 = GDMLShared.getVal(solid,'x2')
    x3 = GDMLShared.getVal(solid,'x3')
    x4 = GDMLShared.getVal(solid,'x4')
    y1 = GDMLShared.getVal(solid,'y1')
    y2 = GDMLShared.getVal(solid,'y2')
    theta = GDMLShared.getVal(solid,'theta')
    phi = GDMLShared.getVal(solid,'phi')
    alpha = GDMLShared.getVal(solid,'alpah1')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    #print z
    mytrap=part.newObject("Part::FeaturePython","GDMLTrap:"+getName(solid))
    GDMLTrap(mytrap,z,theta,phi,x1,x2,x3,x4,y1,y2,alpha,aunit,lunit,material)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mytrap.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytrap.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytrap.ViewObject)
       setDisplayMode(mytrap,displayMode)
    return mytrap

def createTrd(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTrd, ViewProvider
    GDMLShared.trace("CreateTrd : ")
    GDMLShared.trace(solid.attrib)
    z  = GDMLShared.getVal(solid,'z')
    x1 = GDMLShared.getVal(solid,'x1')
    x2 = GDMLShared.getVal(solid,'x2')
    y1 = GDMLShared.getVal(solid,'y1')
    y2 = GDMLShared.getVal(solid,'y2')
    lunit = getText(solid,'lunit',"mm")
    #print z
    mytrd=part.newObject("Part::FeaturePython","GDMLTrd:"+getName(solid))
    GDMLTrd(mytrd,z,x1,x2,y1,y2,lunit,material)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mytrd.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytrd.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytrd.ViewObject)
       setDisplayMode(mytrd,displayMode)
    return mytrd

def createXtru(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLXtru, GDML2dVertex, GDMLSection, \
             ViewProvider, ViewProviderExtension
    GDMLShared.trace("CreateXtru : ")
    #print(solid)
    #print(getName(solid))
    myXtru=part.newObject("Part::FeaturePython","GDMLXtru-"+getName(solid))
    #myXtru.addExtension("App::OriginGroupExtensionPython", None)
    lunit = getText(solid,'lunit',"mm")
    GDMLXtru(myXtru,lunit,material)
    if FreeCAD.GuiUp :
       ViewProviderExtension(myXtru.ViewObject)
    for vert2d in solid.findall('twoDimVertex') : 
        x = GDMLShared.getVal(vert2d,'x')
        y = GDMLShared.getVal(vert2d,'y')
        my2dVert=FreeCAD.ActiveDocument.addObject('App::FeaturePython','GDML2DVertex') 
        #myzplane=mypolycone.newObject('App::FeaturePython','zplane') 
        GDML2dVertex(my2dVert,x,y)
        myXtru.addObject(my2dVert)
        if FreeCAD.GuiUp :
           ViewProvider(my2dVert)
    for section in solid.findall('section') : 
        zOrder = GDMLShared.getVal(section,'zOrder',2)     # Get Int
        zPosition = GDMLShared.getVal(section,'zPosition',2) # Get Int
        xOffset = GDMLShared.getVal(section,'xOffset')
        yOffset = GDMLShared.getVal(section,'yOffset')
        scalingFactor = GDMLShared.getVal(section,'scalingFactor')
        mysection=FreeCAD.ActiveDocument.addObject('App::FeaturePython','GDMLSection')
        GDMLSection(mysection,zOrder,zPosition,xOffset,yOffset,scalingFactor)
        myXtru.addObject(mysection)
        if FreeCAD.GuiUp :
           ViewProvider(mysection)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myXtru.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myXtru.Placement.Rotation)
    # Shape is still Null at this point
    #print("Xtru Shape : ")
    #print("Is Null : "+str(myXtru.Shape.isNull()))
    return(myXtru)

def createTube(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTube, ViewProvider
    GDMLShared.trace("CreateTube : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid,'rmin')
    rmax = GDMLShared.getVal(solid,'rmax')
    z = GDMLShared.getVal(solid,'z')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    GDMLShared.trace(rmin)
    GDMLShared.trace(rmax)
    GDMLShared.trace(z)
    mytube=part.newObject("Part::FeaturePython","GDMLTube:"+getName(solid))
    GDMLTube(mytube,rmin,rmax,z,startphi,deltaphi,aunit,lunit,material)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    #base = FreeCAD.Vector(0,0,0)
    base = FreeCAD.Vector(px,py,pz)
    mytube.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytube.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytube.ViewObject)
       setDisplayMode(mytube,displayMode)
    return mytube

def createCutTube(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLcutTube, ViewProvider
    GDMLShared.trace("CreateCutTube : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid,'rmin')
    rmax = GDMLShared.getVal(solid,'rmax')
    z = GDMLShared.getVal(solid,'z')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    GDMLShared.trace("aunit : "+aunit)
    lowX = GDMLShared.getVal(solid,'lowX')
    lowY = GDMLShared.getVal(solid,'lowY')
    lowZ = GDMLShared.getVal(solid,'lowZ')
    highX = GDMLShared.getVal(solid,'highX')
    highY = GDMLShared.getVal(solid,'highY')
    highZ = GDMLShared.getVal(solid,'highZ')
    lunit = getText(solid,'lunit',"mm")
    GDMLShared.trace(rmin)
    GDMLShared.trace(rmax)
    GDMLShared.trace(z)
    GDMLShared.trace(lowX)
    GDMLShared.trace(lowY)
    GDMLShared.trace(lowZ)
    GDMLShared.trace(highX)
    GDMLShared.trace(highY)
    GDMLShared.trace(highZ)
    mycuttube=part.newObject("Part::FeaturePython","GDMLcutTube:"+getName(solid))
    GDMLcutTube(mycuttube,rmin,rmax,z,startphi,deltaphi,aunit, \
                lowX, lowY, lowZ, highX, highY, highZ, lunit, material)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    #base = FreeCAD.Vector(0,0,0)
    base = FreeCAD.Vector(px,py,pz)
    mycuttube.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mycuttube.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mycuttube.ViewObject)
       setDisplayMode(mycuttube,displayMode)
    return mycuttube

def createTessellated(part,solid,material,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTessellated, GDMLTriangular, \
            GDMLQuadrangular,  ViewProvider, ViewProviderExtension
    GDMLShared.trace("CreateTessellated : ")
    GDMLShared.trace(solid.attrib)
    myTess=part.newObject("Part::FeaturePython","GDMLTessellated:"+getName(solid))
    #myTess.addExtension("App::OriginGroupExtensionPython", None)
    GDMLTessellated(myTess,material)
    if FreeCAD.GuiUp :
       ViewProviderExtension(myTess.ViewObject)
       ViewProvider(myTess.ViewObject)
    for elem in solid.getchildren() :
        GDMLShared.trace(elem)
        v1 = elem.attrib['vertex1']
        v2 = elem.attrib['vertex2']
        v3 = elem.attrib['vertex3']
        vType = elem.attrib['type']
        if elem.tag == 'triangular' :
           myTri = FreeCAD.ActiveDocument.addObject('App::FeaturePython','GDMLTriangle')
           GDMLTriangular(myTri,v1,v2,v3,vType) 
           myTess.addObject(myTri)
           if FreeCAD.GuiUp :
              ViewProvider(myTri)
        
        if elem.tag == 'quadrangular' :
           v4 = elem.attrib['vertex4']
           myQuad = FreeCAD.ActiveDocument.addObject('App::FeaturePython','GDMLQuadrangular')
           GDMLQuadrangular(myQuad,v1,v2,v3,v4,vType) 
           myTess.addObject(myQuad)
           if FreeCAD.GuiUp :
              ViewProvider(myQuad)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    #base = FreeCAD.Vector(0,0,0)
    myTess.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myTess.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myTess.ViewObject)
       setDisplayMode(myTess,displayMode)
    return myTess

def parseMultiUnion(part,solid,material,px,py,pz,rot,displayMode) :
    #GDMLShared.setTrace(True)
    GDMLShared.trace('Multi Union - MultiFuse')
    muName = solid.attrib.get('name')
    GDMLShared.trace('multi Union : '+muName)
    myMUobj = part.newObject('Part::MultiFuse',muName)
    #for s in solid.findall('multiUnionNode') :
    objList = []
    for s in solid :
        # each solid may change x,y,z,rot
        nx = px
        ny = py
        nz = pz
        nrot = rot
        if s.tag == 'multiUnionNode' :
            for t in s :
                if t.tag == 'solid' :
                    sname = t.get('ref')
                    GDMLShared.trace('solid : '+sname)
                    ssolid  = solids.find("*[@name='%s']" % sname )
                if t.tag == 'positionref' :
                    pname = t.get('ref')
                    nx, ny, nz = GDMLShared.getDefinedPosition(pname)
                    GDMLShared.trace('nx : '+str(nx))
                if t.tag == 'rotationref' :
                    rname = t.get('ref')
                    GDMLShared.trace('rotation ref : '+rname)
                    nrot = GDMLShared.getDefinedRotation(rname)
            if sname != None :        # Did we find at least one solid
                objList.append(createSolid(part,ssolid,material,nx,ny,nz, \
                    nrot,displayMode))
    #myMUobj = part.newObject('Part::MultiFuse',muName)
    myMUobj.Shapes = objList


def parseBoolean(part,solid,objType,material,px,py,pz,rot,displayMode) :
    # parent, solid, boolean Type,
    from .GDMLObjects import ViewProvider

    #GDMLShared.setTrace(True)
    GDMLShared.trace(solid.tag)
    GDMLShared.trace(solid.attrib)
    if solid.tag in ["subtraction","union","intersection"] :
       GDMLShared.trace("Boolean : "+solid.tag)
       name1st = GDMLShared.getRef(solid,'first')
       base = solids.find("*[@name='%s']" % name1st )
       GDMLShared.trace("first : "+name1st)
       #parseObject(root,base)
       name2nd = GDMLShared.getRef(solid,'second')
       tool = solids.find("*[@name='%s']" % name2nd )
       GDMLShared.trace("second : "+name2nd)
       x,y,z = GDMLShared.getPosition(solid)
       #rot = GDMLShared.getRotFromRefs(solid)
       rotBool = GDMLShared.getRotation(solid)
       mybool = part.newObject(objType,solid.tag+':'+getName(solid))
       #mybool = part.newObject('Part::Fuse',solid.tag+':'+getName(solid))
       GDMLShared.trace('Create Base Object')
       mybool.Base = createSolid(part,base,material,0,0,0,None,displayMode)
       # second solid is placed at position and rotation relative to first
       GDMLShared.trace('Create Tool Object')
       mybool.Tool = createSolid(part,tool,material,x,y,z,rotBool,displayMode)
       #mybool.Tool = createSolid(part,tool,material,x,y,z,None,displayMode)
       # Okay deal with position of boolean
       GDMLShared.trace('Boolean Position and rotation')
       GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
       #base = FreeCAD.Vector(0,0,0)
       base = FreeCAD.Vector(px,py,pz)
       mybool.Placement = GDMLShared.processPlacement(base,rot)
       #if FreeCAD.GuiUp :
       #     ViewProvider(mybool.ViewObject)
       return mybool

def createSolid(part,solid,material,px,py,pz,rot,displayMode) :
    # parent,solid, material
    # returns created Object
    GDMLShared.trace('createSolid '+solid.tag)
    GDMLShared.trace('px : '+str(px))
    while switch(solid.tag) :

        if case('arb8'):
           return(createArb8(part,solid,material,px,py,pz,rot,displayMode)) 
           break


        if case('box'):
           return(createBox(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('cone'):
           return(createCone(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('elcone'):
           return(createElcone(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('ellipsoid'):
           return(createEllipsoid(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('eltube'):
           return(createEltube(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('polycone'):
           return(createPolycone(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('polyhedra'):
           return(createPolyhedra(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('sphere'):
           return(createSphere(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('trap'):
           return(createTrap(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('trap_dimensions'):
           return(createTrap(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('trd'):
           return(createTrd(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('tube'):
           return(createTube(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('cutTube'):
           return(createCutTube(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('tessellated'):
           return(createTessellated(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('xtru'):
           return(createXtru(part,solid,material,px,py,pz,rot,displayMode)) 
           break

        if case('intersection'):
            return(parseBoolean(part,solid,'Part::Common', \
                  material,px,py,pz,rot,displayMode)) 
            break

        if case('union'):
            return(parseBoolean(part,solid,'Part::Fuse', \
                  material,px,py,pz,rot,displayMode)) 
            break

        if case('subtraction'):
            return(parseBoolean(part,solid,'Part::Cut', \
                  material,px,py,pz,rot,displayMode)) 
            break

        if case('multiUnion'):
            return(parseMultiUnion(part,solid,material, \
                  px,py,pz,rot,displayMode))
            break

        print("Solid : "+solid.tag+" Not yet supported")
        break

def getVolSolid(name):
    GDMLShared.trace("Get Volume Solid")
    vol = structure.find("/volume[@name='%s']" % name )
    sr = vol.find("solidref")
    GDMLShared.trace(sr.attrib)
    name = GDMLShared.getRef(sr)
    solid = solids.find("*[@name='%s']" % name )
    return solid

def parsePhysVol(parent,physVol,phylvl,px,py,pz,rot,displayMode):
    # physvol is xml entity
    GDMLShared.trace("ParsePhyVol : level : "+str(phylvl))
    nx, ny, nz = GDMLShared.getPosition(physVol)
    rot = GDMLShared.getRotation(physVol)
    volref = GDMLShared.getRef(physVol,"volumeref")
    if volref != None :
       #print(volref+ 'px '+str(px)+' py '+str(py)+' pz '+str(pz))
       GDMLShared.trace("Volume ref : "+volref)
       part = parent.newObject("App::Part",volref)
       part.Placement = GDMLShared.processPlacement(FreeCAD.Vector(px,py,pz),rot)
       #print('New Vol : '+volref)
       #print('px '+str(px)+' py '+str(py)+' pz '+str(pz))
       #part.Placement = GDMLShared.processPlacement(FreeCAD.Vector(px,py,pz),rot)
       GDMLShared.trace("px : "+str(px)+" : "+str(py)+" : "+str(pz))
       expandVolume(part,volref,nx,ny,nz,rot,phylvl,displayMode)

# ParseVolume name - structure is global
# We get passed position and rotation
# displayMode 1 normal 2 hide 3 wireframe
def parseVolume(parent,name,px,py,pz,rot,phylvl,displayMode) :
    global volDict

    # Has the volume already been parsed i.e in Assembly etc
    obj = volDict.get(name)
    if obj != None :
       newobj = Draft.clone(obj)
       #print(dir(newobj))
       #print(newobj.TypeId)
       #print(newobj.Name)
       #print(newobj.Label)
       parent.addObject(newobj)
       base = FreeCAD.Vector(px,py,pz)
       newobj.Placement = GDMLShared.processPlacement(base,rot)
       return

    else :
        GDMLShared.trace("ParseVolume : "+name)
        #part = parent.newObject("App::Part",name)
        #expandVolume(part,name,px,py,pz,rot,phylvl,displayMode)
        expandVolume(parent,name,px,py,pz,rot,phylvl,displayMode)

def expandVolume(parent,name,px,py,pz,rot,phylvl,displayMode) :
    import FreeCAD as App
    # also used in ScanCommand
    #GDMLShared.setTrace(True)
    GDMLShared.trace("expandVolume : "+name)
    GDMLShared.trace("Positions : px "+str(px)+' py '+str(py)+' pz '+str(pz))
    vol = structure.find("volume[@name='%s']" % name )
    if vol != None : # If not volume test for assembly
       solidref = GDMLShared.getRef(vol,"solidref")
       if solidref != None :
          solid  = solids.find("*[@name='%s']" % solidref )
          GDMLShared.trace(solid.tag)
          # Material is the materialref value
          # need to add default
          #material = GDMLShared.getRef(vol,"materialref")
          material = GDMLShared.getRef(vol,"materialref")
          #createSolid(part,solid,material,px,py,pz,rot,displayMode)
          #print('solid : '+solid.tag)
          #print('material :'+material)
          obj = createSolid(parent,solid,material,px,py,pz,rot,displayMode)
       else :
          obj = None 
       # Volume may or maynot contain physvol's
       displayMode = 1
       for pv in vol.findall("physvol") :
           # Need to clean up use of phylvl flag
           # create solids at pos & rot in physvols
           #if phylvl < 1 :
           if phylvl < 0 :
              if phylvl >= 0 :
                 phylvl += 1 
              # If negative always parse otherwise increase level    
              parsePhysVol(parent,pv,phylvl,px,py,pz,rot,displayMode)
           else :  # Just Add to structure 
              from PySide import QtGui, QtCore 
              volref = GDMLShared.getRef(pv,"volumeref")
              print(volref)
              posref = GDMLShared.getRef(pv,'positionref')
              print(posref)
              GDMLShared.trace("Volume ref : "+volref)
              GDMLShared.trace("Position ref : "+posref)
              pos = define.find("position[@name='%s']" % posref )
              print(pos)
              if pos is not None :
                 px = GDMLShared.getVal(pos,'x')
                 py = GDMLShared.getVal(pos,'y')
                 pz = GDMLShared.getVal(pos,'z')
              else :
                 px = py = pz = 0 
              part = parent.newObject("App::Part","NOT-Expanded_"+volref+"_")
              base = FreeCAD.Vector(px,py,pz)
              # For now ignore rotation
              #part.Placement = GDMLShared.processPlacement(base,rot)
              part.Placement = GDMLShared.processPlacement(base,None)
              #print(dir(part))
              #
              #obj = part.newObject("App::Annotation","Not Expanded")
              #obj.LabelText="Annotation"
              #view = obj.ViewObject
              #print(dir(view))
              #part = parent.newObject("App::DocumentObjectGroup",volref)
              #vpart2 = part2.ViewObject
              #print(dir(vpart2))
              # 100% red, 0% Green, 0% Blue
              #vpart.TextColor = (100., 0., 0., 0.)
       # Add parsed Volume to dict
       volDict[name] = obj
       App.ActiveDocument.recompute() 
       return obj

    else :
       asm = structure.find("assembly[@name='%s']" % name)
       print("Assembly : "+name)
       if asm != None :
          for pv in asm.findall("physvol") :
              # create solids at pos & rot in physvols
              #parsePhysVol(part,pv,displayMode)
              #obj = parent.newObject("App::Part",name)
              parsePhysVol(parent,pv,phylvl,px,py,pz,displayMode)
       else :
           print("Not Volume or Assembly") 

def getItem(element, attribute) :
    # returns None if not found
    return element.get(attribute)

def processIsotopes(doc) :
    from .GDMLObjects import GDMLisotope, ViewProvider
    isotopesGrp  = doc.addObject("App::DocumentObjectGroupPython","Isotopes")
    for isotope in materials.findall('isotope') :
        N = int(isotope.get('N'))
        Z = int(float(isotope.get('Z')))    # annotated.gdml file has Z=8.0 
        name = isotope.get('name')
        atom = isotope.find('atom')
        unit = atom.get('unit','g/mole')
        value = float(atom.get('value'))
        #isoObj = isotopesGrp.newObject("App::FeaturePython",name)
        isoObj = isotopesGrp.newObject("App::DocumentObjectGroupPython",name)
        GDMLisotope(isoObj,name,N,Z,unit,value)

def processElements(doc) :
    from .GDMLObjects import GDMLelement, GDMLfraction
    elementsGrp  = doc.addObject("App::DocumentObjectGroupPython","Elements")
    elementsGrp.Label = 'Elements'
    for element in materials.findall('element') :
        name = element.get('name')
        elementObj = elementsGrp.newObject("App::DocumentObjectGroupPython", name)
        Z = element.get('Z')
        if (Z != None ) :
           elementObj.addProperty("App::PropertyInteger","Z",name).Z=int(float(Z))
        N = element.get('N')
        if (N != None ) :
           elementObj.addProperty("App::PropertyInteger","N",name).N=int(N)
            
        formula = element.get('formula')
        if (formula != None ) :
           elementObj.addProperty("App::PropertyString","formula",name). \
                   formula = formula
            
        atom = element.find('atom') 
        if atom != None :
           unit = atom.get('unit')
           if unit != None :
              elementObj.addProperty("App::PropertyString","atom_unit",name). \
                                      atom_unit = unit
           value = atom.get('value')
           if value != None :
              elementObj.addProperty("App::PropertyFloat","atom_value",name). \
                                      atom_value = float(value)


        GDMLelement(elementObj,name)
        # modifs 
        if( len(element.findall('fraction'))>0 ):
           for fraction in element.findall('fraction') :
               ref = fraction.get('ref')
               n = float(fraction.get('n'))
               #fractObj = elementObj.newObject("App::FeaturePython",ref)
               fractObj = elementObj.newObject("App::DocumentObjectGroupPython",ref)
               GDMLfraction(fractObj,ref,n)
               #fractObj.Label = ref[0:5]+' : ' + '{0:0.2f}'.format(n)
               fractObj.Label = ref+' : ' + '{0:0.2f}'.format(n)
        elif(len(element.findall('composite'))>0 ):
           for fraction in element.findall('composite') :
               ref = fraction.get('ref')
               n = float(fraction.get('n'))
               #fractObj = elementObj.newObject("App::FeaturePython",ref)
               compositeObj = elementObj.newObject("App::DocumentObjectGroupPython",ref)
               GDMLcomposite(compositeObj,ref,n)
               #fractObj.Label = ref[0:5]+' : ' + '{0:0.2f}'.format(n)
               fractComposite.Label = ref+' : ' + str(n) 
        # end modifs 

def processMaterials(doc) :
    from .GDMLObjects import GDMLmaterial, GDMLfraction, GDMLcomposite, \
                            MaterialsList

    materialGrp = doc.addObject("App::DocumentObjectGroupPython","Materials")
    materialGrp.Label = "Materials"
    for material in materials.findall('material') :
        name = material.get('name')
        MaterialsList.append(name)
        materialObj = materialGrp.newObject("App::DocumentObjectGroupPython", \
                      name)
        GDMLmaterial(materialObj,name)
        formula = material.get('formula')
        if formula != None :
           materialObj.addProperty("App::PropertyString",'formula', \
                      name).formula = formula
        D = material.find('D')
        if D != None :
           Dunit = getItem(D,'unit')
           #print(Dunit)
           if Dunit != None :
                 materialObj.addProperty("App::PropertyString",'Dunit', \
                                'GDMLmaterial','Dunit').Dunit = Dunit
           Dvalue = getItem(D,'value')
           if Dvalue != None :
              materialObj.addProperty("App::PropertyFloat", \
                      'Dvalue','GDMLmaterial','value').Dvalue = float(Dvalue)

        Z = material.get('Z')
        if Z != None :
           materialObj.addProperty("App::PropertyString",'Z',name).Z = Z
        atom = material.find('atom')
        if atom != None :
           #print("Found atom in : "+name) 
           aUnit = atom.get('unit')
           if aUnit != None :
              materialObj.addProperty("App::PropertyString",'atom_unit', \
                         name).atom_unit = aUnit
           aValue = atom.get('value')
           if aValue != None :
              materialObj.addProperty("App::PropertyFloat",'atom_value', \
                         name).atom_value = float(aValue)
 
        T = material.find('T')
        if T != None :
           Tunit = T.get('unit')
           Tvalue = float(T.get('value'))
           materialObj.addProperty("App::PropertyString",'Tunit','GDMLmaterial',"T ZZZUnit").Tunit = Tunit
           materialObj.addProperty("App::PropertyFloat",'Tvalue','GDMLmaterial','T XXXXvalue').Tvalue = Tvalue
        MEE = material.find('MEE')
        if MEE != None :
           Munit = MEE.get('unit')
           Mvalue = float(MEE.get('value'))
           materialObj.addProperty("App::PropertyString",'MEEunit','GDMLmaterial','MEE unit').MEEunit = Munit
           materialObj.addProperty("App::PropertyFloat",'MEEvalue','GDMLmaterial','MEE value').MEEvalue = Mvalue
        for fraction in material.findall('fraction') :
            n = float(fraction.get('n'))
            #print(n)
            ref = fraction.get('ref')
            #print('fraction : '+ref)
            fractionObj = materialObj.newObject('App::DocumentObjectGroupPython', ref)
            #print('fractionObj Name : '+fractionObj.Name)
            GDMLfraction(fractionObj,ref,n)
            # problems with changing labels if more than one
            #
            #fractionObj.Label = ref[0:5] +' : '+'{0:0.2f}'.format(n)
            #print('Fract Label : ' +fractionObj.Label)
            #fractionObj.Label = ref +' : '+'{0:0.2f}'.format(n)
            #print('Fract Label : ' +fractionObj.Label)

        for composite in material.findall('composite') :
            #print('Composite')
            n = int(composite.get('n'))
            #print('n = '+str(n))
            ref = composite.get('ref')
            #print('ref : '+ref)
            compObj = materialObj.newObject("App::DocumentObjectGroupPython", \
                                                 ref)
            GDMLcomposite(compObj,'comp',n,ref)
            # problems with changing labels if more than one
            #
            #print('Comp Label : ' +compObj.Label)
            #compObj.Label = ref +' : '+str(n)
            #print('Comp Label : ' +compObj.Label)

    GDMLShared.trace("Materials List :")
    GDMLShared.trace(MaterialsList)

def processGDML(doc,filename,prompt):

    from . import GDMLShared
    from . import GDMLObjects
    
    #GDMLShared.setTrace(True)

    phylvl = -1 # Set default
    if FreeCAD.GuiUp :
       from . import GDMLCommands
       if prompt :
          from   .GDMLCommands import importPrompt
          dialog = importPrompt()
          dialog.exec_()
          #FreeCADGui.Control.showDialog(dialog)
          #if dialog.retStatus == 1 :
          #   print('Import')
          #   phylvl = -1

          if dialog.retStatus == 2 :
             print('Scan Vol') 
             phylvl = 0 

          params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/GDML")
          #GDMLShared.setTrace(printverbose = params.GetBool('printVerbose',False))
   
    else :
        # For Non Gui default Trace to on
        GDMLShared.setTrace(True)

    print("Print Verbose : "+ str(GDMLShared.getTrace()))

    FreeCAD.Console.PrintMessage('Import GDML file : '+filename+'\n')
    FreeCAD.Console.PrintMessage('ImportGDML Version 0.2\n')
    
    global pathName
    pathName = os.path.dirname(os.path.normpath(filename))
    FilesEntity = False

    global setup, define, materials, solids, structure, volDict
  
    # Add files object so user can change to organise files
    #  from GDMLObjects import GDMLFiles, ViewProvider
    #  myfiles = doc.addObject("App::FeaturePython","Export_Files")
    #myfiles = doc.addObject("App::DocumentObjectGroupPython","Export_Files")
    #GDMLFiles(myfiles,FilesEntity,sectionDict)

    # modifs
    #before from lxml import etree
    try:
       from lxml import etree
       FreeCAD.Console.PrintMessage("running with lxml.etree \n")
       parser = etree.XMLParser(resolve_entities=True)
       root = etree.parse(filename, parser=parser)

    except ImportError:
       try:
           import xml.etree.ElementTree as etree
           FreeCAD.Console.PrintMessage("running with etree.ElementTree (import limitations)\n")
           FreeCAD.Console.PrintMessage(" for full import add lxml library \n")
           tree = etree.parse(filename)
           FreeCAD.Console.PrintMessage(tree)
           root = tree.getroot()

       except ImportError:
           print('pb xml lib not found')
           sys.exit()
    # end modifs 
    setup     = root.find('setup')
    define    = root.find('define')
    if define != None :
       GDMLShared.trace("Call set Define")
       GDMLShared.setDefine(root.find('define'))
       GDMLShared.processConstants(doc)

       # modif
       GDMLShared.processPosition(doc)
       GDMLShared.processExpression(doc)
       GDMLShared.processRotation(doc)
       GDMLShared.processQuantity(doc)
       # end modif

       GDMLShared.trace(setup.attrib)

    materials = root.find('materials')
    if materials != None :
       processIsotopes(doc)
       processElements(doc)
       processMaterials(doc)

    solids    = root.find('solids')
    structure = root.find('structure')

    # volDict dictionary of volume names and associated FreeCAD part
    volDict = {}

    world = GDMLShared.getRef(setup,"world")
    part =doc.addObject("App::Part",world)
    #print(world)
    #scanVolume(part,world)
    parseVolume(part,world,0,0,0,None,phylvl,3)
    # If only single volume reset Display Mode
    if len(part.OutList) == 2 :
        worldGDMLobj = part.OutList[1]
        worldGDMLobj.ViewObject.DisplayMode = 'Shaded'
    if FreeCAD.GuiUp :
       FreeCADGui.SendMsgToActiveView("ViewFit")
    FreeCAD.Console.PrintMessage('End processing GDML file\n')
