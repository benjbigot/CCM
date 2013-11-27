#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

import threading, os, sys, math, time, commands
import numpy
from random import choice
import copy
import scipy
import utilsCCM
import buildMatrixCCM
#-----------------------#

class computeSVMmodel(threading.Thread):    
	def __init__(self, expe, rule, acceptationFile, rejectionFile, svmModelOutFile ):
		threading.Thread.__init__(self)
		
		self.rule = rule
		self.expe = expe
		self.acceptationFile = acceptationFile
		self.rejectionFile = rejectionFile
		
		self.svmMatFile   = svmModelOutFile
		self.svmScaleFile = self.svmMatFile + '.scale'
		self.svmRangeFile = self.svmMatFile + '.range'
		self.svmModelFile = self.svmMatFile + '.model'

		self.svmScaleCommand = self.expe.commandSVMscale + ' -s ' + self.svmRangeFile + ' ' + self.svmMatFile + ' > ' + self.svmScaleFile
		self.svmTrainCommand = self.expe.commandSVMtrain + ' ' +self.svmScaleFile  + ' ' + self.svmModelFile
				
		self.acceptation = []
		self.rejection   = []
		self.acceptationLabel = []
		self.rejectionLabel   = []
		self.problem = []
		self.problemLabel = []
	#_____________________________________________#
	
	def run(self):
		#print(self.redMatFile , self.rejMatFile )
		self.acceptation = buildMatrixCCM.loadMatFile(self.acceptationFile)
		self.rejection   = buildMatrixCCM.loadMatFile(self.rejectionFile)
				
		self.acceptationLabel = [1]*len(self.acceptation)		
		self.rejectionLabel = [-1]*len(self.rejection)
				
		writeSVMfile(self.svmMatFile, self.acceptationLabel, self.acceptation, self.rejectionLabel, self.rejection )
		scaleData(self.svmRangeFile, self.svmScaleCommand)
		trainSVM(self.svmModelFile, self.svmTrainCommand)
		os.remove(self.svmMatFile)
		os.remove(self.svmScaleFile)
#_____________________________________________#
def writeSVMfile(svmMatFile, acceptationLabel, acceptation, rejectionLabel, rejection):
	if not os.path.exists(svmMatFile) :
		outputMat = []
		for i, classe in enumerate(acceptationLabel) :
			currentLine = str(classe) +' '
			for j,value in enumerate(acceptation[i]):
				currentLine += str(j+1) + ':' + str(value) + ' '
			outputMat.append(currentLine)
			
		for i,classe in enumerate(rejectionLabel) :
			currentLine = str(classe) + ' '
			for j, value in enumerate(rejection[i]):
				currentLine += str(j+1) + ':' + str(value) + ' '
			outputMat.append(currentLine)
		
		fOut = open(svmMatFile, 'w')
		for line in outputMat :
			fOut.write(line + '\n')
		fOut.close()
		
	else:
		print(svmMatFile + ' already exists' )
#_____________________________________________#
def scaleData(svmRangeFile, svmScaleCommand):
	if not os.path.exists(svmRangeFile):
		print('scaling')
		print(svmScaleCommand)
		SCALE = commands.getstatusoutput(svmScaleCommand)
#_____________________________________________#
def trainSVM(svmModelFile,svmTrainCommand):
		if not os.path.exists(svmModelFile):
			print('training')
			print(svmTrainCommand)
			MODEL = commands.getstatusoutput(svmTrainCommand)
#_____________________________________________#




