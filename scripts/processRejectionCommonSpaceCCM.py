#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

import threading, os, sys, math, time, commands, numpy
sys.path.append('/local_disk/hera2/PERCOL/bigot/PlateformeRecoName/lib/sparsesvd/lib.linux-x86_64-2.6')
import scipy.sparse
import sparsesvd
import copy
import utilsCCM
import buildMatrixCCM
import processRejectionEntitySpaceCCM
import learnSVMmodelCCM
sys.path.append('/local_disk/hera2/PERCOL/bigot/PlateformeRecoName/bin/scikit-learn-0.13/build/lib.linux-x86_64-2.6/')
sys.path.append('/local_disk/hera2/PERCOL/bigot/PlateformeRecoName/bin/joblib-0.7.0b/build/lib.linux-x86_64-2.6/')
import joblib
import sklearn 
import sklearn.mixture 
import pylab
import matplotlib


#------------------#
class writeReject(threading.Thread):	
	def __init__(self, expe, listCandidates):
		threading.Thread.__init__(self)
		''' differneces with the first rejection rules 
		 is in the lexicon choice and the reduction process
		 one large lexcion is used and SVD is processed on the whole rejection matrix
		'''
		
		
		self.rule = ''
		self.expe = expe 
		self.candidates = listCandidates
		#self.candidates = ['NICOLAS_SARKOZY', 'FRANCOIS_HOLLANDE', 'FRANCOIS_BAYROU']
		print('______________processing ' + '+'.join(self.candidates) + '___________________')

		
		self.candidateContextFiles = []
		self.candidateLexiconFiles = []
		
		for i in self.candidates:
			self.candidateContextFiles.append(self.expe.contextDir + '/' + i + self.expe.contextExt)
			self.candidateLexiconFiles.append(self.expe.lexiconDir + '/' + i + self.expe.lexiconExt)
		#print self.candidateLexiconFiles 
		#print self.candidateContextFiles
		
		self.context   	= []
		self.label		= []
		self.lexicon    = dict()
		
		# == rejection file variables == #
		self.rejContextFile = self.expe.rejMatDir +'/Rejection.context'
		self.rejListFile    = self.expe.rejMatDir +'/Rejection.list'
		self.rejLexiconFile = self.expe.rejMatDir +'/Rejection.lexicon'

		self.rejContext = []
		self.rejLexicon	= []
		self.rejLabel   = []
		
		self.globalLexicon = []
		self.globalContext = []
		self.globalLabel   = []
		self.globalLexiconPosition = []
		
		
	
		self.winLength  = self.expe.contextBuildMatrixWindow	
		self.denseMat     = []	
		self.cutOffSVD = int(self.expe.cutoffSVD)

		self.sparseMat	= []
		self.vt = []
	#_____________________________________________________#
	def run(self):

		print('toto' ,  self.candidates)
		# == preparing data for every candidates == #
		for i, name in enumerate(self.candidates):
			for j in buildMatrixCCM.loadContextFile(self.candidateContextFiles[i]):	
				self.context.append(j)
			for j in range(len(buildMatrixCCM.loadContextFile(self.candidateContextFiles[i]))) : 
				self.label.append(name)
			self.lexicon = mergeLexicon(self.lexicon , processRejectionEntitySpaceCCM.loadLexiconFile(self.candidateLexiconFiles[i]))
			print(name + ': '+str(len(buildMatrixCCM.loadContextFile(self.candidateContextFiles[i])))+' contextes')
			print(name + ': '+str(len(processRejectionEntitySpaceCCM.loadLexiconFile(self.candidateLexiconFiles[i])))+' lexicon items')
		#print('concatenation: '+str(len(self.context))+' contextes')
		#print('concatenation: '+str(len(self.label))+' label items')
		#print('concatenation: '+str(len(self.lexicon))+' lexicon items')		
		
		if len(self.candidates) > 1 :
			# prepare sorted lexicon #
			self.globalLexicon = self.lexicon
			self.globalContext = self.context
			self.globalLabel   = self.label

		# == if only one name use rejection List instead == #
		elif len(self.candidates) == 1 :
			self.rejContext = processRejectionEntitySpaceCCM.loadRejContextFile(self.rejContextFile, self.rejListFile, self.candidates[0])
			self.rejLabel   = ['rejection'] * len(self.rejContext)			
			self.rejLexicon = processRejectionEntitySpaceCCM.loadLexiconFile(self.rejLexiconFile)
			#print('number of rejection Context : ' + str(len(self.rejContext)))
			#print('number of rejection lexicon item : ' + str(len(self.rejLexicon)))
			#print('number of rejection label item : ' + str(len(self.rejLabel)))
		
			if (len(self.rejContext) > 0):
				# == verifier la premiere ligne des fichiers de contextes == #
				# == garder une trace du nombre de contexte pour chaque classe concerne
				self.globalContext = self.context + self.rejContext	
				self.globalLabel   = self.label + self.rejLabel			
				self.globalLexicon = mergeLexicon(self.lexicon, self.rejLexicon)
				# sort lexicon and put it in a global container #				
			else:
				print('problem no rejection example found')
				exit()
					
		# == so far self.globalContext self.globalLabel self.globalLexicon are information containers == #
		self.globalLexiconSorted	= buildMatrixCCM.getSortedLexicon(self.globalLexicon)
		self.globalLexiconPosition    = buildMatrixCCM.buildLexiconPositionTable(self.globalLexiconSorted)	
		buildMatrixCCM.writeLexicon(self.expe.expeMatDir+'/'+'+'.join(self.candidates)+'.lexicon', self.globalLexicon, self.globalLexiconSorted)
	
		print('__________________')
		print('global context : ' + str(len(self.globalContext)))
		print('globalLexicon  : ' + str(len(self.globalLexicon)))
		print('globalLabel    : ' + str(len(self.globalLabel  )))

		# == print label List in a file == #
		fLabel = open(self.expe.expeMatDir + '/' +  '+'.join(self.candidates) + '.list', 'w' )
		for i in self.globalLabel :
			fLabel.write(i.strip() + '\n')
		fLabel.close()

		print( '---> building matrix')
		self.denseMat = buildMatrixCCM.computeMatrix(self.winLength,self.globalLexicon, self.globalLexiconPosition, self.globalContext)
		print('matrix shape : ' + str(self.denseMat.shape))
		#print self.denseMat
                #buildMatrixCCM.dump2File(self.denseMat, self.expe.expeMatDir+ '/' + '+'.join(self.candidates) + '.dense')

		if int(len(self.denseMat)) >= self.cutOffSVD :
			print('---> creating sparse representation matrix')
			self.sparseMat	= scipy.sparse.csc_matrix(self.denseMat)
			print('--->  computind svd')
			ut, s, self.vt 	= sparsesvd.sparsesvd(self.sparseMat, self.cutOffSVD)
			print('vmatrix shape : ' + str(self.vt.shape))
			print('dumping Vt matric to a file :'  + self.expe.expeMatDir + '/' +  '+'.join(self.candidates) + '-Vt')
			buildMatrixCCM.dump2File(self.vt, self.expe.expeMatDir + '/' +  '+'.join(self.candidates) + '-Vt')
			print('---> reducing matrix')
			self.reducedMatrix = buildMatrixCCM.computeReduction(self.vt, self.denseMat, self.cutOffSVD)
			print('----> saving mapped matrix to a file')
			buildMatrixCCM.dump2File(self.reducedMatrix, self.expe.expeMatDir+ '/' + '+'.join(self.candidates) + '.mapped')
	
	
	
	
	
		# == classification is realized in a one against all manner == #
		# == everything is in an only file == #
		# == learning SVM == #
		# == needed self.reducedMatrix and self.globalLabel
		# == tout est fait dans la foulée == #	
		# ce qui est fait est de prender l'une ou l'autres classes comme égale à 1 ou -1
		# dans le cas de deux noms àa ne change rien mais pas dans les autres cas.
		
		
		# ajouter un condition si il n'y a que deux classes.
		
		for i, name in enumerate(self.candidates):
			svmOutputMatrix = []
			print('_____processing SVM model for ' + name +'______')
			for j, label in enumerate(self.globalLabel):
				if label.rstrip() == name:
					#print('ok')
					currentLine = '1 '
				elif label.rstrip() != name:
					#print('nok')
					currentLine = '-1 '
				for k, valeur in enumerate(self.reducedMatrix[j]):
					#print(name, label.rstrip(),  currentLine)
					currentLine += str(k+1) +':'+str(valeur) + ' '
				svmOutputMatrix.append(currentLine)
		
			if len(self.candidates) == 2 :
				svmOutputFile = self.expe.expeMatDir + '/' +  '+'.join(self.candidates) +  self.expe.svmMatExt 
			else :
				svmOutputFile = self.expe.expeMatDir + '/' +  '+'.join(self.candidates) + '.' + name + self.expe.svmMatExt 

			fOut = open(svmOutputFile, 'w')
			for line in svmOutputMatrix :
				fOut.write(line + '\n')
			fOut.close()
			
			
			svmMatFile   = svmOutputFile
			svmScaleFile = svmMatFile + '.scale'
			svmRangeFile = svmMatFile + '.range'
			svmModelFile = svmMatFile + '.model'

			svmScaleCommand = self.expe.commandSVMscale + ' -s ' + svmRangeFile + ' ' + svmMatFile + ' > ' + svmScaleFile
			svmTrainCommand = self.expe.commandSVMtrain + ' '    + svmScaleFile  + ' ' + svmModelFile
			
			learnSVMmodelCCM.scaleData(svmRangeFile, svmScaleCommand)
			learnSVMmodelCCM.trainSVM(svmModelFile, svmTrainCommand)
			#os.remove(svmMatFile)
			#~ os.remove(svmScaleFile)
			
			if  len(self.candidates) == 1 :
				break









		
		# == apprentissage des modeles de gaussiennes == #
		if len(self.candidates) > 1 :
			for i, name in enumerate(self.candidates):
				print('_____processing GMM model for ' + name +'______')
				gmmOutputFile = self.expe.expeMatDir + '/' +  '+'.join(self.candidates) + '.' + name + self.expe.gmmExt
			
				ligne =[]
				for j, label in enumerate(self.globalLabel):
					if label.rstrip() == name:
						ligne.append(j)

				gmmOutputMatrix = numpy.empty([len(ligne), self.cutOffSVD ], dtype=float)

				n = 0
				for k in ligne:
					for p, m in enumerate(self.reducedMatrix[k]) :
						gmmOutputMatrix[n][p] = self.reducedMatrix[k][p]
					n += 1
					
			
			
				print(name, gmmOutputMatrix.shape)
				classifier = sklearn.mixture.GMM(n_components=16, covariance_type='diag' , init_params='wc' , n_iter=20)
				try:
					classifier.fit(svmOutputMatrix)
					joblib.dump(classifier, gmmOutputFile, compress=9, cache_size=1000)
				except : 
					print('----> not enough contexts for ' + name)
					
					
		elif len(self.candidates) == 1 :
			for i, name in enumerate(self.candidates):
				print('_____processing GMM model for ' + name +'______')
				gmmOutputFileAccept = self.expe.expeMatDir + '/' +  '+'.join(self.candidates) + '.' + name + self.expe.gmmExt + '.accept'
				gmmOutputFileReject = self.expe.expeMatDir + '/' +  '+'.join(self.candidates) + '.' + name + self.expe.gmmExt + '.reject'

				ligneAccept =[]
				ligneReject =[]
				
				for j, label in enumerate(self.globalLabel):
					if label.rstrip() == name:
						ligneAccept.append(j)
					else :
						ligneReject.append(j)
						
				gmmOutputMatrixAccept = numpy.empty([len(ligneAccept), self.cutOffSVD ], dtype=float)
				gmmOutputMatrixReject = numpy.empty([len(ligneReject), self.cutOffSVD ], dtype=float)
				
				n = 0
				for k in ligneAccept:
					for p, m in enumerate(self.reducedMatrix[k]) :
						gmmOutputMatrixAccept[n][p] = self.reducedMatrix[k][p]
					n += 1

				n = 0
				for k in ligneReject:
					for p, m in enumerate(self.reducedMatrix[k]) :
						gmmOutputMatrixReject[n][p] = self.reducedMatrix[k][p]
					n += 1

				print(name, gmmOutputMatrixAccept.shape)
				print(name, gmmOutputMatrixReject.shape)
				
				
				classifierAccept = sklearn.mixture.GMM(n_components=16, covariance_type='diag' , init_params='wc' , n_iter=20)
				classifierReject = sklearn.mixture.GMM(n_components=16, covariance_type='diag' , init_params='wc' , n_iter=20)
				try:
					classifierAccept.fit(gmmOutputMatrixAccept)
					joblib.dump(classifierAccept, gmmOutputFileAccept, compress=9, cache_size=1000)
				except : 
					print('----> not enough contexts for acceptation ' + name)
					
				try:
					classifierReject.fit(gmmOutputMatrixReject)
					joblib.dump(classifierReject, gmmOutputFileReject, compress=9, cache_size=1000)
				except : 
					print('----> not enough contexts for rejection ' + name)
		
		
#________________________________________________________________#
def mergeLexicon(lexicon1 , lexicon2) :
	''' merging hash depending on value'''
	globalLexicon = copy.copy(lexicon1)
	
	for item in lexicon2 :
		if globalLexicon.has_key(item) :
			globalLexicon[item] += lexicon2[item]
		else :
			globalLexicon[item] = lexicon2[item]
	# == attention au retour par reference qui pourrait modifier le contenu == #
	return globalLexicon	
#________________________________________________________________#	
