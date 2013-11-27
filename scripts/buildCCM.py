#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

#import argparse
#import extractContext
#import computeSVD
#import threadPool
#import computeRejection

import os, sys, threading, time, random
from optparse import OptionParser
import configServerCCM
import extractContextCCM
import utilsCCM
import buildMatrixCCM
import processSvdCCM
import processRejectionEntitySpaceCCM, processRejectionCommonSpaceCCM
import learnSVMmodelCCM
import processGmmCCM

'''
Program's main script : buildCCM
--- building Continuous Context Models is made in several steps --- 
usage : buildCCM.py -c configFile -s subTask (optional) -l listeSpeaker (optional)
The subtasks are 
C : context extraction
M : matrix building
S : SVD realization
R : dimension reduction
J : rejection matrix construction
L : learning SVM models

the listeSpeaker is composed of a label and a research pattern:
LABEL:pattern pattern_subpattern -pattern_removed
'''


# ==================== Launching Zone ==================== #
def extractContext(expe):
	# corpusList			: list of directories paths
	# corpusDirContent		: list tuples of words, one line is one document
	# corpusDirContentPOS 	: corpusDirContent woth POS filtering
	# subcorpus 			: one tuple is one document words
	# doneFile 				: contains the list of already processed corpus dir of corpusList
	
	
	# == extracting contexts == #
	for corpus in expe.corpusList:
		# == prepare documents content == #
		print('=== processing ' + corpus.rstrip() + ' ====')
		corpusDirContent = utilsCCM.getCorpusDirContent(corpus)
		print('---> processing POS tagging')
		corpusDirContentPOS = utilsCCM.processCorpusDirContentPOS(corpusDirContent, expe)
		
		# == running multi threads context extraction == #
		for rule in expe.itemList :
			doneFile = expe.contextDir + '/' + rule + '.subcorpusDone'

			if (utilsCCM.isAlreadyDone(doneFile, corpus) == 0):
				print('Active Threads : ' + str(threading.activeCount()) + ' - processing ' + rule)

				while (threading.activeCount() >= 50):
					time.sleep(0.0001)
			
				# == declare an threading entity class == #
				t = extractContextCCM.extractContext(rule, corpusDirContent, corpusDirContentPOS,  corpus , expe)
				t.start()
			else : 
				print(rule  + ' already done')
				
				
		# == waiting loop == #
		while (threading.activeCount() >= 2):
			if (threading.activeCount() >= 10 ):
				print('waiting for ' + str(threading.activeCount()) + ' active process ')
				time.sleep(5)
			else :
				print('waiting for ' + str(threading.activeCount()) + ' active process ')
				time.sleep(1)


	# == removing redundant contexts == #
	for rule in expe.itemList :
		print ('--> '+ rule + ': removing redundancy in context files')
		contextFile = expe.contextDir + '/' + rule + expe.contextExt
		tempFile    = expe.contextDir + '/' + rule + expe.contextExt +'.temp'
		utilsCCM.removeRedundancy( contextFile, tempFile)
#_____________________________________________________________________#
def buildRawMatrix(expe):
	''' compute raw matrix building with threads '''
	ruleCounter = 0
	for rule in expe.itemList :
		if  os.path.exists(expe.contextDir + '/' + rule + expe.contextExt)    :
			# == rule is a name id == #
			#ruleCounter+=1
			
			while (threading.activeCount() >= 2):
				time.sleep(0.0001)
			
			if (( not os.path.exists(expe.redMatDir + '/' + rule + expe.redMatExt)) or ( not os.path.exists(expe.lexiconDir + '/' + rule + expe.lexiconExt) )) :
				# == declare a threading entity class == #
				print('---> building matrix for ' + rule)
				t = buildMatrixCCM.rawMatrix(rule, expe)
				t.start()
	
	while (threading.activeCount() >= 2):
		if (threading.activeCount() >= 10 ):
			print('waiting for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(5)
		else :
			print('waiting for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(1)
#_____________________________________________________________________#	
def prepareGlobalRejectionFile(expe):
	
	# == first step : building rejection context file == #
	# a fastest way is to build only one rejection file with an index file 
	# boucle d'attente de durée aléatoire :
	random.seed()
	n = random.random()
	time.sleep(n)
	if not os.path.exists(expe.rejMatDir +'/Rejection.running') : 
		fout = open(expe.rejMatDir +'/Rejection.running' , 'w')
		fout.close()

		# ======================================================================= #	
		# == creation d'un fichier contenant les contextes tirés aléatoirement == #
		# ======================================================================= #					
		if ( not (os.path.exists(expe.rejMatDir +'/Rejection.context')) and ( not os.path.exists(expe.rejMatDir +'/Rejection.list'))):
			fRejContext = open(expe.rejMatDir +'/Rejection.context','w')
			fRejList    = open(expe.rejMatDir +'/Rejection.list','w')
			
			listFile = [] 
			for (path, dirs, files) in os.walk(expe.contextDir) :
				for i in files :
					if '.context' in i :
						listFile.append(i)
			for rules in listFile :
				rule = rules.split('.context')[0]
				if os.path.exists(expe.contextDir + '/' + rule +  expe.contextExt ) :
					print('---> extracting rejection examples from '+ rule + '\n' )
					randomLines = utilsCCM.takeRandomContext(expe.contextDir + '/' + rule + expe.contextExt , expe.rejectionNumber)
					for line in randomLines :
						fRejContext.write(line)
						fRejList.write(rule+'\n')
			fRejContext.close()
			fRejList.close()

		# ================================================================================= #
		# ==  creation d'un fichier de lexique pour l'ensemble de contextes de rejection == #
		# ================================================================================= #
		contextInit	= buildMatrixCCM.loadContextFile(expe.rejMatDir +'/Rejection.context')
		lexicon = buildMatrixCCM.buildLexicon(contextInit, expe.stopList, 0)
		lexiconSorted	= buildMatrixCCM.getSortedLexicon(lexicon)
		lexiconPosition	= buildMatrixCCM.buildLexiconPositionTable(lexiconSorted)
		# =============================================================== #
		# == ecriture du fichier de lexique de l'ensemble de rejection == #
		# =============================================================== #
		buildMatrixCCM.writeLexicon(expe.rejMatDir +'/Rejection.lexicon', lexicon, lexiconSorted)
		
		# == suppression du fichier d'attente == #
		os.remove(expe.rejMatDir +'/Rejection.running')

	else :
		while os.path.exists(expe.rejMatDir +'/Rejection.running') == True :
			print('waiting...')
			time.sleep(10)
	
	print('==== fin rejection files prepratation ====')
#_____________________________________________________________________#	
def buildRejectionEntitySpace(expe):
	''' first rejection model using the rule lexicon '''
	for rule in expe.itemList :
		if os.path.exists(expe.redMatDir + '/' + rule + expe.redMatExt) :	
			while (threading.activeCount() >= 8):
				time.sleep(0.0001)
			
			# == declare a threading entity class == #
			if not os.path.exists(expe.rejMatDir + '/' + rule + expe.rejMatExt) :			
				t = processRejectionEntitySpaceCCM.writeReject(rule, expe)
				t.start()

	while (threading.activeCount() >= 2):
		if (threading.activeCount() >= 10 ):
			print('waitng for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(5)
		else :
			print('waitng for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(1)	
#_______________________________________________________________#
def learnSvmModel2class(expe):
	for rule in expe.itemList :	
		if (os.path.exists(expe.redMatDir+'/'+rule+expe.redMatExt) and os.path.exists(expe.rejMatDir+'/'+rule+expe.rejMatExt)):
			rejMatFile 		= expe.rejMatDir + '/' + rule + expe.rejMatExt
			accpetMatFile 	= expe.redMatDir + '/' + rule + expe.redMatExt
			svmOutFile		= expe.svmMatDir + '/' + rule + expe.svmMatExt
			print(rejMatFile,accpetMatFile,svmOutFile)
			while (threading.activeCount() >= 5):
				time.sleep(0.0001)
			
			# == declare a threading entity class == #	
			if not os.path.exists(svmOutFile) :
				t = learnSVMmodelCCM.computeSVMmodel(expe, rule, accpetMatFile, rejMatFile, svmOutFile)
				t.start()
			else: 
				print(rule  + ' 2-class svm model already learnt')
					
	while (threading.activeCount() >= 2):
		if (threading.activeCount() >= 10 ):
			print('waitng for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(5)
		else :
			print('waitng for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(1)			
#________________________________________________________________#	
def  learn2classGMM(expe):
	for rule in expe.itemList :
		if( os.path.exists(expe.redMatDir+'/'+rule+expe.redMatExt) and os.path.exists(expe.rejMatDir+'/'+rule+expe.rejMatExt)):
			rejMatFile 		= expe.rejMatDir + '/' + rule + expe.rejMatExt
			accpetMatFile 	= expe.redMatDir + '/' + rule + expe.redMatExt
			gmmOutFile		= expe.gmmDir + '/' + rule + expe.gmmExt

			while (threading.activeCount() >= 5):
				time.sleep(0.0001)
				
			# == declare a threading entity class == #      
			if ( not os.path.exists(gmmOutFile+'.accept') or not os.path.exists(gmmOutFile+'.reject') ):
				t = processGmmCCM.processGMM(expe, rule, accpetMatFile, rejMatFile,gmmOutFile)
				t.start() 
			else : 
				print(rule  + ' 2-class gmm model already learnt')

	while (threading.activeCount() >= 2):
		if (threading.activeCount() >= 10 ):
			print('waitng for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(5)
		else :   
			print('waitng for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(1)
#________________________________________________________________#
def buildRejectionCommonLexicalSpace(expe):
	''' in this process, acceptation and rejection are projected in the same lexical space
	    argument is a list of id, since this function will be used for multi-class processing  '''
	for rule in expe.itemList :
		if os.path.exists( expe.contextDir + '/' + rule + expe.contextExt) and not os.path.exists(expe.expeMatDir + '/' + rule + expe.expeMatExt) :
			print(rule)
			while (threading.activeCount() >= 2):
				time.sleep(0.0001)
                # == declare a threading entity class == #
			if not os.path.exists(expe.expeMatDir + '/' + rule + expe.expeMatExt) :
				t = processRejectionCommonSpaceCCM.writeReject(expe, [rule])
				t.start() 
		else :
			print(rule , 'pas de matrice de rejection')
	while (threading.activeCount() >= 2):
		if (threading.activeCount() >= 10 ):
			print('waitng for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(5)
		else :
			print('waitng for ' + str(threading.activeCount()) + ' active process ')
			time.sleep(1)
#_______________________________________________________________#

#========================== Main Routine ========================#
if __name__ == '__main__':
	usage = "usage: %prog -c config_file -l speaker_rule"
	parser = OptionParser(usage=usage)
	parser.add_option("-c", "--config",  dest="config",  help ="configuration file")
	parser.add_option("-s", "--subTask", dest="subTask", help="optional CMJLGS Context Matrix reJection svmmodeL Gmmmodel SameSpace")
	parser.add_option("-l", "--listSpeaker", dest="spkList", help="if defined, speaker list is used instead")
	
	(options, args) = parser.parse_args()
	
	
	
	
	# == loading configuration parameters (-s arguments)  == #	
	if options.config == None :
		print("configuraton file is not optionnal ")
		exit()
	else :
		expe = configServerCCM.Configuration(options.config)
	
	# == overwrite spkList (-l option) == #
	if options.spkList != None :
		if os.path.exists(options.spkList) : 
			print("rule list passed as an option "+  options.spkList)
			(expe.itemList,  expe.acceptation, expe.rejection) = configServerCCM.loadRules(options.spkList)
			
		else :
			print ("speaker list file  "  + options.spkList + " does not exists. exiting")
			exit()


	# == Full processing == #
	if options.subTask == None :
		options.subTask = 'CMJLGS'
	
	
	# -- extract lexicon & context -- #
	if 'C' in options.subTask :
		print('__running context extraction__')
		extractContext(expe)
	
	# -- build dense matrix -- #
	if 'M' in options.subTask :
		print('__running matrix processing__')
		buildRawMatrix(expe)
	
	# -- build rejection matrix -- #
	if 'J' in options.subTask : 
		print('__running rejection in entity space__')
		prepareGlobalRejectionFile(expe)
		buildRejectionEntitySpace(expe)

	# -- learn svm linear models -- #
	if 'L' in options.subTask : 
		print('__learning 2 class linear svm models__')
		learnSvmModel2class(expe)

	# -- learn gmm models -- #
	if 'G' in options.subTask : 
		print('__learning 2 class gmm models__')
		learn2classGMM(expe)


	# -- buils rejection same space -- #
	if 'S' in options.subTask : 
		print('__running rejection in common space__')
		buildRejectionCommonLexicalSpace(expe)

	# =============================== #
	# -- project accept and reject context in one lexical space -- #
	#if 'T' in options.subTask : 
	#	experimentalCommonLexicalSpace(expe)
	# =============================== #
	# -- learn svm model for bi class test in progress -- #
	#if 'N' in options.subTask:
	#	experimentalLearnSvmModels(expe)
