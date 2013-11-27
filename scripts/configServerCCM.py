#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster
import re,os
import utilsCCM

#===============================================================#

class   Configuration:
	def __init__(self, configFile):
		'''
		initialization of a test configuration file
		'''
		
		# == loading Configuration File Content == #
		self.paramContent = utilsCCM.loadFile(configFile)
		
		# == getting framework variables == #
		self.binDir     = self.getParam(self.paramContent, 'BIN_DIR','d')
		self.scriptDir  = self.getParam(self.paramContent, 'SCRIPT_DIR','d')
		
		self.contextDir = self.getParam(self.paramContent, 'CONTEXT_DIR','d')
		self.contextExt = self.getParam(self.paramContent, 'CONTEXT_EXT', 'p')
		
		self.lexiconDir 	= self.getParam(self.paramContent, 'LEXICON_DIR','d')
		self.lexiconExt 	= self.getParam(self.paramContent, 'LEXICON_EXT', 'p')
		self.lexiconCutoff 	= self.getParam(self.paramContent, 'LEXICON_CUTOFF', 'p')
		
		
		self.rawMatDir  = self.getParam(self.paramContent, 'RAW_MATRIX_DIR', 'd')
		self.rawMatExt  = self.getParam(self.paramContent, 'RAW_MAT_EXT', 'p')
		
		self.svdDir     = self.getParam(self.paramContent, 'SVD_DIR','d')
		self.svdExt     = self.getParam(self.paramContent, 'SVD_EXT', 'p')
		
		self.redMatDir  = self.getParam(self.paramContent, 'RED_MATRIX_DIR','d')
		self.redMatExt  = self.getParam(self.paramContent, 'RED_MAT_EXT', 'p')
		
		self.rejMatDir  = self.getParam(self.paramContent, 'REJECTION_MATRIX_DIR','d')
		self.rejMatExt  = self.getParam(self.paramContent, 'REJECTION_EXT', 'p')
		
		self.svmMatDir  = self.getParam(self.paramContent, 'SVM_MODEL_DIR','d')
		self.svmMatExt  = self.getParam(self.paramContent, 'SVM_EXT', 'p')
		
		self.gmmDir  = self.getParam(self.paramContent, 'GMM_MODEL_DIR','d')
		self.gmmExt  = self.getParam(self.paramContent, 'GMM_EXT', 'p')
		

		self.testDir  = self.getParam(self.paramContent, 'TEST_DIR','d')

		self.itemFile   = self.getParam(self.paramContent, 'ITEM_LIST','d')
		self.corpusFile = self.getParam(self.paramContent, 'CORPUS_LIST','d')

		# == variables créées pour le test sur l'espace commun de représentation == #
		self.expeMatDir = self.getParam(self.paramContent, 'EXPE_MATRIX_DIR','d')
		self.expeMatExt = self.getParam(self.paramContent, 'EXPE_EXT', 'p')

		self.testTESTDir = self.getParam(self.paramContent, 'EXPE_TEST_DIR','d')

		
		self.contextExtractionWindow  = self.getParam(self.paramContent, 'EXTRACT_CONTEXT_PM_WINDOW', 'p')
		self.contextBuildMatrixWindow = self.getParam(self.paramContent, 'BUILD_MATRIX_PM_WINDOW', 'p')

		
		self.processTreeTagging = self.getParam(self.paramContent, 'PROCESSTREETAGGER', 'p')
		self.commandTT = self.getParam(self.paramContent, 'COMMANDTT', 'p')
		
		
		self.cutoffSVD  = self.getParam(self.paramContent, 'SVD_CUTOFF', 'p')
		self.commandSVD = self.getParam(self.paramContent, 'COMMANDSVD', 'p')
		
		self.commandSVMscale = self.getParam(self.paramContent,'SVM_SCALE_COMMAND', 'p')		
		self.commandSVMtrain = self.getParam(self.paramContent,'SVM_TRAIN_COMMAND', 'p')		
		self.commandSVMpredict = self.getParam(self.paramContent,'SVM_PREDICT_COMMAND', 'p')

		self.rejectionNumber = self.getParam(self.paramContent, 'REJECTION_NUMBER', 'p')

		self.analysisWindow = self.getParam(self.paramContent, 'EXTRACT_CONTEXT_PM_WINDOW','p')
		
		#self.itemList  = self.loadRules(self.itemFile)
		(self.itemList,  self.acceptation, self.rejection) = self.loadRules(self.itemFile)
		
		self.corpusList= utilsCCM.loadFile(self.corpusFile)

		self.stopListFile = self.getParam(self.paramContent, 'STOP_LIST', 'p')
		self.stopList     = utilsCCM.loadFile(self.stopListFile)

	
	# ============================================================== #

	def getParam(self, f, pattern, type):
		''' 
		returns parameters defined by a 
		keyword in the configuration file
		'''
		prog = re.compile('^%s=' %pattern)
		for line in f:
			if  (prog.match(line)) != None :
				if ( type == 'd'):
					if (os.path.exists(line.rstrip().split('=')[1])):
						return line.rstrip().split('=')[1]
					else : 
						os.mkdir(line.rstrip().split('=')[1])
						return line.rstrip().split('=')[1]
				elif ( type == 'p'):
					return line.rstrip().split('=')[1]
					
	# ============================================================== #

	def loadRules(self, fN ):
		''' 
		reads the learning set from 
		the rule file and returns it 
		'''
		items = utilsCCM.loadFile(fN)
		
		acceptation = {}
		rejection   = {}
		itemList    = []
		
		for rule in items :
			if (':' not in rule )  and ( ' ' not in rule ):
				itemList.append(rule)
				rejection[rule].append('')
				acceptation[rule].append(' '.join(rule.rstrip().split('_')))
			
			elif (':' in rule) : 
				idSpeaker = rule.split(':')[0]

				itemList.append(idSpeaker)
				acceptation[idSpeaker] = []
				rejection[idSpeaker]   = []
				
				ruleSpeaker = rule.split(':')[1]
				etiquettes = ruleSpeaker.rstrip().split(' ')

				for x in etiquettes  :
					if (x != '') and ( '-' in x) :
						rejection[idSpeaker].append(' '.join(x.replace('-', '').split('_')))
					elif (x != '') and ( '-' not in x) :
						acceptation[idSpeaker].append(' '.join(x.split('_')))
						
		return itemList, acceptation, rejection

	# =============================================================== #		
		

def loadRules( fN ):
	''' 
	reads the learning set from 
	the rule file and returns it 
	'''

	items = utilsCCM.loadFile(fN)

	acceptation = {}
	rejection   = {}
	itemList    = []

	for rule in items :
		if (':' not in rule )  and ( ' ' not in rule ):
			itemList.append(rule)
			rejection[rule].append('')
			acceptation[rule].append(' '.join(rule.rstrip().split('_')))
		elif (':' in rule) :
			idSpeaker = rule.split(':')[0]
			itemList.append(idSpeaker)
			acceptation[idSpeaker] = []
			rejection[idSpeaker]   = []

			ruleSpeaker = rule.split(':')[1]
			etiquettes = ruleSpeaker.rstrip().split(' ')

			for x in etiquettes  :
				if (x != '') and ( '-' in x) :
					rejection[idSpeaker].append(' '.join(x.replace('-', '').split('_')))
				elif (x != '') and ( '-' not in x) :
					acceptation[idSpeaker].append(' '.join(x.split('_')))
	return itemList, acceptation, rejection
		
	
