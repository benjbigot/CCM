#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

import threading, os, sys, math, time, subprocess,commands
import numpy
sys.path.append('/local_disk/hera2/PERCOL/bigot/PlateformeRecoName/lib/sparsesvd/lib.linux-x86_64-2.6')
import scipy.sparse
import sparsesvd
import utilsCCM
#------------------#

class processSVD(threading.Thread):
	def __init__(self, rule , expe):
		threading.Thread.__init__(self)
		self.rule = rule
		self.expe = expe 
		self.cutOffSVD = int(self.expe.cutoffSVD)
		self.rawMatFile = self.expe.rawMatDir + '/' + self.rule + self.expe.rawMatExt
		self.VtFile     = expe.svdDir + '/' + rule + expe.svdExt
		self.redMatFile = self.expe.redMatDir + '/' + self.rule + self.expe.redMatExt	
	#___________________________________________________________#
	def run(self):
		denseMat 	= loadMatFile(self.rawMatFile)
		sparseMat	= scipy.sparse.csc_matrix(denseMat)
		if int(len(denseMat)) >= self.cutOffSVD :
			ut, s, vt 	= sparsesvd.sparsesvd(sparseMat, self.cutOffSVD)
			dump2File(vt, self.VtFile)
			reducedMatrix = computeReduction(vt, denseMat, self.cutOffSVD)
			dump2File(reducedMatrix, self.redMatFile)
		else : 
			print('--> not enough contexts')
#________________________________________________________#
def computeReduction(vt, mat2Project, cutOffSVD):
	print('--> computing reduction')
	tsvdMatrix = numpy.transpose(vt)		
	reducedMatrix = numpy.empty([ len(mat2Project), cutOffSVD ], dtype=float)
	
	#print(rawMatrix.shape)
	#print(tsvdMatrix.shape)
	
	cmpt_Line = 0
	for currentLine in mat2Project:
		result = numpy.dot(currentLine,tsvdMatrix)
		reducedMatrix[cmpt_Line] = result
		cmpt_Line += 1
	return reducedMatrix
#__________________________________________________________#
def dump2File(mat2Dump, DestFile):
	fDest = open(DestFile, 'w')
	fDest.write( str(int(mat2Dump.shape[0])) +  ' ' + str(int(mat2Dump.shape[1])) + '\n')
	for p in mat2Dump :
		line = []
		for number in p :
			line.append(str("%.4e" % number)) 
		fDest.write( ' '.join(line) + '\n')
	fDest.close()		
#___________________________________________________________#		
def loadMatFile(fName):
	print('--> loading ' + fName)
	''' loading file with header on one line '''
	matContent = utilsCCM.loadFile(fName)
	if (len(matContent[0].rstrip().split()) != 2) :
			print('check first line format in ' + fName)
	else :
		matrix=numpy.empty([int((matContent[0].split())[0]), int((matContent[0].split())[1])],dtype=float)
		for i in range(1, len(matContent)) :
			j= 0
			for item in matContent[i].split() :
				matrix[i-1][j] = float(item)
				j += 1
	return matrix
#___________________________________________________________#		
