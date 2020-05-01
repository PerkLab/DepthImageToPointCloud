import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from vtk.util import numpy_support

#
# DepthImageToPointCloud
#

class DepthImageToPointCloud(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "DepthImageToPointCloud" # TODO make this more human readable by adding spaces
    self.parent.categories = ["RealSense"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# DepthImageToPointCloudWidget
#

class DepthImageToPointCloudWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    #Instantiate the logic module
    self.logic = DepthImageToPointCloudLogic()

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/DepthImageToPointCloud.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    self.ui.inputSelector.setMRMLScene(slicer.mrmlScene)
    self.ui.outputSelector.setMRMLScene(slicer.mrmlScene)

    # connections
    self.ui.updateButton.connect('clicked(bool)', self.onUpdateButton)
    self.ui.startStreamingButton.connect('clicked(bool)', self.onStartStreamingButton)
    self.ui.stopStreamingButton.connect('clicked(bool)', self.onStopStreamingButton)
    self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.ui.updateButton.enabled = self.ui.inputSelector.currentNode() and self.ui.outputSelector.currentNode()
    self.ui.startStreamingButton.enabled = self.ui.inputSelector.currentNode() and self.ui.outputSelector.currentNode()

  def onUpdateButton(self):
    [cameraParams, pointCloudParams] = self.getParams()
    self.logic.run(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(), cameraParams, pointCloudParams)

  def onStartStreamingButton(self):
    [cameraParams, pointCloudParams] = self.getParams()

    #Disable the start streaming and update buttons, enable stop streaming button
    self.ui.startStreamingButton.enabled = False
    self.ui.updateButton.enabled = False
    self.ui.stopStreamingButton.enabled = True
    self.disableAllInputs()

    self.logic.startStreaming(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(), cameraParams, pointCloudParams)

  def onStopStreamingButton(self):
    #Enable the start streaming and update buttons, Disable stop streaming button
    self.ui.startStreamingButton.enabled = True
    self.ui.updateButton.enabled = True
    self.ui.stopStreamingButton.enabled = False
    self.enableAllInputs()

    self.logic.stopStreaming(self.ui.inputSelector.currentNode())

  def getParams(self):
    cameraParams = {"focalLength" : self.ui.focalLength.value, 
                    "principlePointX" : self.ui.principlePointX.value,
                    "principlePointY" : self.ui.principlePointY.value}
    pointCloudParams = {"thresholdLower" : self.ui.thresholdLower.value, 
                    "thresholdUpper" : self.ui.thresholdUpper.value,
                    "depthScale" : self.ui.depthScale.value,
                    "ptCloudDensity" : self.ui.ptCloudDensity.value}
    return [cameraParams, pointCloudParams]   

  def disableAllInputs(self):
     self.ui.inputSelector.enabled = False
     self.ui.outputSelector.enabled = False
     self.ui.focalLength.enabled = False
     self.ui.principlePointX.enabled = False
     self.ui.principlePointY.enabled = False
     self.ui.thresholdLower.enabled = False
     self.ui.thresholdUpper.enabled = False
     self.ui.depthScale.enabled = False
     self.ui.ptCloudDensity.enabled = False

  def enableAllInputs(self):
     self.ui.inputSelector.enabled = True
     self.ui.outputSelector.enabled = True
     self.ui.focalLength.enabled = True
     self.ui.principlePointX.enabled = True
     self.ui.principlePointY.enabled = True
     self.ui.thresholdLower.enabled = True
     self.ui.thresholdUpper.enabled = True
     self.ui.depthScale.enabled = True
     self.ui.ptCloudDensity.enabled = True

#
# DepthImageToPointCloudLogic
#

class DepthImageToPointCloudLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  #Update the polydata
  def pointCloudCallback(self,caller, eventId):
    self.run(self.inputVolume, self.outputVolume, self.cameraParams, self.pointCloudParams)

  def startStreaming(self, inputVolume, outputVolume, cameraParams, pointCloudParams):
    #Save all values locally in logic object
    self.inputVolume = inputVolume
    self.outputVolume = outputVolume
    self.cameraParams = cameraParams
    self.pointCloudParams = pointCloudParams

    #Add an observer to the input image to continue updating point cloud continuously
    inputVolume.AddObserver(inputVolume.ImageDataModifiedEvent, self.pointCloudCallback)

  def stopStreaming(self, inputVolume):
    #Remove the observer on inputVolume
    inputVolume.RemoveAllObservers()

  #Takes a dim[0] by dim[1] numpy array, and returns a list of [X Y Z] coordinates
  def generate_pointcloud(self,depthData, cameraParams, pointCloudParams):
    points = []    
    for i in range(0,depthData.shape[0],pointCloudParams['ptCloudDensity']):
        for j in range(0,depthData.shape[1],pointCloudParams['ptCloudDensity']):
            Z = depthData[i,j] / pointCloudParams['depthScale']
            if Z==0 or Z > pointCloudParams['thresholdUpper'] or Z < pointCloudParams['thresholdLower']: continue
            X = (i - cameraParams["principlePointX"]) * Z / cameraParams["focalLength"]
            Y = (j - cameraParams["principlePointY"]) * Z / cameraParams["focalLength"]
            points.append([X,Y,Z])
    return points

  #Takes a list of [X Y Z] coordinates and returns a vtkPolyData object
  def generatePolyData(self,pts):
    allPoints = vtk.vtkPoints()
    poly = vtk.vtkPolyData()
    conn = vtk.vtkCellArray()
    for i, point in enumerate(pts):
        allPoints.InsertNextPoint(point)
        conn.InsertNextCell(1)
        conn.InsertCellPoint(i)
    poly.SetPoints(allPoints)
    poly.SetVerts(conn)
    return poly

  def run(self, inputVolume, outputVolume, cameraParams, pointCloudParams):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    if not self.hasImageData(inputVolume):
      return False

    inputImage = inputVolume.GetImageData()
    imageDims = inputImage.GetDimensions()[0:2]
    
    #Extract the vtkImageData from the vtkMRMLScalarVolumeNode
    extractFilterDepth = vtk.vtkImageExtractComponents()
    extractFilterDepth.SetInputData(inputImage)
    extractFilterDepth.SetComponents(0)
    extractFilterDepth.Update()
    imageDepth = extractFilterDepth.GetOutput()

    #Convert depth data to numpy array
    vtkDataDepth = imageDepth.GetPointData().GetScalars()
    numpyDataDepth = numpy_support.vtk_to_numpy(vtkDataDepth)
    numpyDataDepth = numpyDataDepth.reshape(imageDims[1], imageDims[0])

    listOfPoints = self.generate_pointcloud(numpyDataDepth, cameraParams, pointCloudParams)
    polyData = self.generatePolyData(listOfPoints)

    outputVolume.SetAndObservePolyData(polyData)

    return True


class DepthImageToPointCloudTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_DepthImageToPointCloud1()

  def test_DepthImageToPointCloud1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import SampleData
    SampleData.downloadFromURL(
      nodeNames='FA',
      fileNames='FA.nrrd',
      uris='http://slicer.kitware.com/midas3/download?items=5767')
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = DepthImageToPointCloudLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
