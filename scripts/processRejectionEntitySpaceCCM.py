#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

import threading, os, sys, math, time
import numpy
import utilsCCM
import buildMatrixCCM
#------------------#

class writeReject(threading.Thread):	
	def __init__(self, rule , expe):
		threading.Thread.__init__(self)
		self.rule = rule
		self.expe = expe 
		
		# == full rejection list and context files == #
		self.rejContext 	= self.expe.rejMatDir +'/Rejection.context'
		self.rejList    	= self.expe.rejMatDir +'/Rejection.list'
	
		self.contextFile 	= self.expe.contextDir + '/' + self.rule + self.expe.contextExt	
		self.lexiconFile 	= self.expe.lexiconDir + '/' + self.rule + self.expe.lexiconExt	
		self.svdMatFile 	= self.expe.svdDir + '/' + self.rule + self.expe.svdExt	
		
		self.rejMatFile 	= self.expe.rejMatDir + '/' + self.rule + self.expe.rejMatExt	

		self.winLength 		= int(self.expe.contextBuildMatrixWindow)
		self.lexicon 		= []
		self.lexiconPosition = dict()		
		self.context 		= []
		self.matrix  		= []	
		self.reducedMat 	= []
		self.cutOffSVD 		= int(self.expe.cutoffSVD)
	#_____________________________________________________#
	def run(self):
		if ( os.path.exists(self.contextFile)):
			self.context 	= loadRejContextFile(self.rejContext, self.rejList, self.rule)
			self.lexicon 	= loadLexiconFile(self.lexiconFile)		
			self.lexiconPosition = loadLexiconPositionTable(self.lexiconFile)
			self.matrix  	= buildMatrixCCM.computeMatrix(self.winLength, self.lexicon, self.lexiconPosition, self.context)
			self.vt			= buildMatrixCCM.loadMatFile(self.svdMatFile)
			self.reducedMat = buildMatrixCCM.computeReduction(self.vt, self.matrix, self.cutOffSVD)
			buildMatrixCCM.dump2File(self.reducedMat, self.rejMatFile)
			
			#computeRejMatrix()
			#self.computeReduction()
			#self.write2File()
#________________________________________________________________#
def loadRejContextFile(rejContext, rejList, rule):
	''' load lines not corresponding to the current rule '''
	#print('processing context file ' + self.contextFile)
	context		= []
	contextOut		= []
	fContext    = open(rejContext, 'r')
	fList       = open(rejList   , 'r')
	contextTemp = fContext.readlines()
	listTemp    = fList.readlines()
	fContext.close()
	fList.close()

	for index, name in enumerate(listTemp) : 
		if (name.rstrip() != rule): 
   	   		currentLine = contextTemp[index].rstrip().split(';')
   	   		context.append(currentLine)
   	for line in context:
		contextOut.append(line[2:])
	return contextOut
#_____________________________________________________________________#
def loadLexiconFile(lexFile):
	lexicon = {}
	for line in utilsCCM.loadFile(lexFile) :
		lexicon[line.rstrip().split(' ')[0] ] = int(line.rstrip().split(' ')[1])
		#print( line.rstrip().split(' ')[0] ,  lexicon[line.rstrip().split(' ')[0] ] )
	return lexicon
#_____________________________________________________________________#	
def loadLexiconPositionTable(lexFile):
	lexicon  = {}
	position = 0
	for line in utilsCCM.loadFile(lexFile) :
		lexicon[line.rstrip().split(' ')[0] ] = position
		position += 1
	return lexicon
#_____________________________________________________________________#
