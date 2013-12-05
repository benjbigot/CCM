#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

import threading, os, sys, math, time
import numpy
sys.path.append('/local_disk/hera2/PERCOL/bigot/PlateformeRecoName/lib/sparsesvd/lib.linux-x86_64-2.6')
import scipy.sparse
import sparsesvd
import utilsCCM
#------------------#

class rawMatrix(threading.Thread):
	def __init__(self, rule , expe):
		threading.Thread.__init__(self)
		self.rule 				= rule 
		self.expe 				= expe
		self.contextFile   		= self.expe.contextDir + '/' + self.rule + self.expe.contextExt
		self.lexiconFile   		= self.expe.lexiconDir + '/' + self.rule + self.expe.lexiconExt
		self.outMatrixFile 		= self.expe.rawMatDir  + '/' + self.rule + self.expe.rawMatExt
		self.stopList      		= self.expe.stopList
		self.winLength 			= int(self.expe.contextBuildMatrixWindow)
		self.lexiconCutoff 		= int(self.expe.lexiconCutoff)
		self.context			= []
		self.lexicon 			= []
		self.lexicon4write 		= []
		self.lexiconPosition 	= dict()
		self.cutOffSVD = int(self.expe.cutoffSVD)
		self.VtFile     = expe.svdDir + '/' + rule + expe.svdExt
		self.redMatFile = self.expe.redMatDir + '/' + self.rule + self.expe.redMatExt	
		self.vt = []
	#___________________________________________________________#
	def run(self):
		self.context 			= loadContextFile(self.contextFile)
		self.lexicon		 	= buildLexicon(self.context, self.stopList, self.lexiconCutoff)
		self.lexiconSorted		= getSortedLexicon(self.lexicon)
		self.lexiconPosition	= buildLexiconPositionTable(self.lexiconSorted)
		writeLexicon(self.lexiconFile, self.lexicon, self.lexiconSorted)
		self.denseMat 			= computeMatrix(int(self.winLength) , self.lexicon, self.lexiconPosition, self.context)		
		
		if int(len(self.denseMat)) >= self.cutOffSVD :
			self.sparseMat	= scipy.sparse.csc_matrix(self.denseMat)
			ut, s, self.vt 	= sparsesvd.sparsesvd(self.sparseMat, self.cutOffSVD)
			dump2File(self.vt, self.VtFile)
			self.reducedMatrix = computeReduction(self.vt, self.denseMat, self.cutOffSVD)
			dump2File(self.reducedMatrix, self.redMatFile)		
		else : 
			print('--> not enough contexts')

#___________________________________________________________#		
def loadContextFile(contextFile):
	''' liste de tuple retrait de l'entête de la ligne de contexte'''
	print('--> loading context file')
	context = []
	if (os.path.exists(contextFile)):	
		fContext = open(contextFile, 'r')
		contextTemp = fContext.readlines()
		fContext.close()
	print('--> ' + str(len(contextTemp)) + ' contexts')
	
	for line in contextTemp :
		print "caution separator changed"
		currentLine = line.rstrip().split('<SEP>')
		context.append( currentLine[2:] )
	return context	
#___________________________________________________________#
def buildLexicon(context, stopList, cutOff, nbOver):
	'''
	input : Context, stopList, cutOff, nbOver
	context = [['w1 w2<COUNT>dist1,dist2', 'w1 w3<COUNT>dist1,dist2',]...
	['w1 w2<COUNT>dist1,dist2', 'w1 w3<COUNT>dist1,dist2',]]
	'''
	print('--> compiling lexicon')
	lexiconOut 		= {}
	lexiconGlobal 	= {}		
	
	# == threshold over the number of term appearings == #
	if cutOff == 0 :
		lexiconThreshold = 0;
	else : 
		lexiconThreshold = int(len(context)/cutOff)
	
	for p , currentLine in enumerate(context):
		for i in currentLine:
			try :
				currentTerm = i.split('<COUNT>')[0]
				currentList = i.split('<COUNT>')[1]				
			except : 
				print('caution: ', p,  currentTerm, currentList, currentLine )
				print('line with a problem ' ,  currentLine)
			
			# == the central item of the context is not kept == #				
			if '0' not  in currentList.split(','):				
				# == a stop list is used == #
				if currentTerm not in stopList :
					# adding the number of appearance of the pattern to lexicon counter
					if (currentTerm in lexiconGlobal):
						lexiconGlobal[currentTerm] += len(currentList.split(',')) #listLength
					else :
						lexiconGlobal[currentTerm] =  len(currentList.split(',')) #listLength
			else :
				print currentList.split(',')
	
	for w in lexiconGlobal:
		## priority to nbOver => if nbOver == 0 => use lexiconThreshold
		## else use nbOver as a threshold
		if (nbOver == 0) and (int(lexiconGlobal[w]) >= lexiconThreshold):
			lexiconOut[w] = lexiconGlobal[w]
		elif (nbOver != 0) and (	int(lexiconGlobal[w]) > nbOver):
			lexiconOut[w] = lexiconGlobal[w]
	return lexiconOut
#___________________________________________________________#
def getSortedLexicon(lexiconGlobal):		
	lexicon = []
	for w in sorted(lexiconGlobal, key=lexiconGlobal.get, reverse=True): 
		lexicon.append(w)
		#print(w, lexiconGlobal[w])
	return lexicon
#___________________________________________________________#
def buildLexiconPositionTable(lexicon):
	lexiconPosition = {}
	for position, token in enumerate(lexicon):
		lexiconPosition[token] = position
	return lexiconPosition
#___________________________________________________________#
def writeLexicon(lexiconFile, lexicon, lexiconPosition, overwrite):
	print('--> writing lexicon')
	if (not (os.path.exists(lexiconFile))) or overwrite:
		fLexicon= open(lexiconFile, 'w')
		for item in lexiconPosition:
			fLexicon.write(item + '\t' + str(lexicon[item]) +'\n')
		fLexicon.close()
	else : 
		print('lexicon file already exists')
#___________________________________________________________#
def headingMatrixOutput(outMatrixFile, lineCnt, rawCnt):
	print('--> writting output file')
	if not (os.path.exists(outMatrixFile)):
		fMatrix = open(outMatrixFile, 'w')
		fMatrix.write(lineCnt  + ' ' + rawCnt + '\n')
		fMatrix.close()
	else : 
		print(outMatrixFile + ' already exists')
		exit()
#___________________________________________________________#
def computeMatrix(windowsLimit, lexicon, lexiconPosition, context, weighting):
	''' from lexcion and context, order depends on the lexicon	'''
	
	matrix = numpy.empty([len(context), len(lexicon) ] , dtype=numpy.float64)	
	# == contrainst on the windows length == #
	if (windowsLimit == -1):
		windowsLimit = 100000
		
	for cL, currentContext in enumerate(context):	
		# == one vecteur_distance per context == #
		vecteur_distance = {}
		
		# == for elements of the context : get only the nearer occurrence
		for element in currentContext :
			term = element.split('<COUNT>')[0];
			if term in lexicon :
				positionList = element.split('<COUNT>')[1].split(',')
				minPosition = int(positionList[0])

				for i in positionList:
					if abs(int(i)) <= minPosition :
						minPosition = int(i)

				# == test on the distance == #
				if  abs(minPosition) <= windowsLimit  :
					# == center of the context is forced to 0 == #
					if minPosition == 0 :
						# == should not happen
						vecteur_distance[term] = 0
					else :
						if weighting :
							vecteur_distance[term] = round(((1.0 + math.log10(10) ) / (1.0 + math.log10(10 * abs(minPosition)))), 4)
						else :
							vecteur_distance[term] = minPosition

			currentMatrixLine = numpy.zeros([1,len(lexicon) ],dtype=numpy.float64 )

			for lex in vecteur_distance :
				cPosition = lexiconPosition[lex]
				if cPosition >= 0 :
					currentMatrixLine[0][cPosition] = vecteur_distance[lex] 		
			matrix[cL] =  currentMatrixLine
	return matrix
#_____________________________________________________________#
def write2rawMatrix(matriceSortie,outMatrixFile):
	print type(matriceSortie)
	exit()	
	fout = open(outMatrixFile , 'a')
	for line in matriceSortie :
		fout.write(line + '\n')
	fout.close()
#_____________________________________________________________#
def dump2File(mat2Dump, DestFile, header, overwrite):
	print('--> dumping matrix')
	if (not (os.path.exists(DestFile))) or overwrite:
		fDest = open(DestFile, 'w')
		if header :
			fDest.write( str(int(mat2Dump.shape[0])) +  ' ' + str(int(mat2Dump.shape[1])) + '\n')
		for p in mat2Dump :
			line = []
			for number in p :
				line.append(str("%.4e" % number)) 
			fDest.write( ' '.join(line) + '\n')
		fDest.close()	
	else : 
		print('file already exists')
#_____________________________________________________________#
def removeMatrixEmptyLines(matrix, label):
	rows = matrix.shape[0]
	cols = matrix.shape[1]
	it   = -1
	emptyLine    = list()
	nonEmptyLine = list()
	outLabel     = list()
	
	for row in matrix :
		it += 1
		if numpy.sum(row) == 0:
			emptyLine.append(it)
		else:
			nonEmptyLine.append(it)
			outLabel.append(label[it])
	
	# _______ preparing new output matrix ________ #
	outMatrix = numpy.empty([len(nonEmptyLine), cols ] , dtype=numpy.float64)
	
	newItem = 0 
	for item in nonEmptyLine :
		outMatrix[newItem] = matrix[item]
		newItem += 1
		
	return outMatrix, outLabel
#_____________________________________________________________#
def computeReduction(vt, mat2Project, cutOffSVD):
	print('--> computing reduction')
	tsvdMatrix = numpy.transpose(vt)		
	reducedMatrix = numpy.empty([ len(mat2Project), cutOffSVD ], dtype=numpy.float64)
	cmpt_Line = 0
	for currentLine in mat2Project:
		result = numpy.dot(currentLine,tsvdMatrix)
		reducedMatrix[cmpt_Line] = result
		cmpt_Line += 1
	return reducedMatrix
#_____________________________________________________________#
def loadMatFile(fName):
	print('--> loading ' + fName)
	''' loading file with header on one line '''
	matContent = utilsCCM.loadFile(fName)
	if (len(matContent[0].rstrip().split()) != 2) :
			print('check first line format in ' + fName)
	else :
		matrix=numpy.empty([int((matContent[0].split())[0]), int((matContent[0].split())[1])],dtype=numpy.float64)
		for i in range(1, len(matContent)) :
			j= 0
			for item in matContent[i].split() :
				matrix[i-1][j] = float(item)
				j += 1
	return matrix
#_____________________________________________________________#	

def buildCollocMatrix(lexicon, contextVect):
	'''
	lexicon = dict[w1 w2] => nb_of_occurrences
	contextVect = dict[lineId][w1 w2] => distance_mini
	'''
	sortedLexicon = getSortedLexicon(lexicon)
	outputMatrix = list()
	
	# == for each line of the context vector using index== #
	for i in range(0, len(contextVect)-1):
		currentLine = list()
		currentContext = contextVect[i]
		# == for each word of the lexicon if found add the distance to currentLine == #
		for item in sortedLexicon :
			if item in currentContext :
				currentLine.append(str(currentContext[item]))
			else :
				currentLine.append('0')
		outputMatrix.append(' '.join(currentLine))
	
	return outputMatrix
	
#___________________________________________________________"
def writeLexiconColloc(lexiconFile, lexicon):
	print('--> writing lexicon')
	if not (os.path.exists(lexiconFile)):
		fLexicon= open(lexiconFile, 'w')
		for item in lexicon:
			fLexicon.write(item + ' ' + str(lexicon[item]) +'\n')
		fLexicon.close()
	else : 
		print('lexicon file already exists')
#___________________________________________________________#




