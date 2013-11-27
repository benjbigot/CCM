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

# ==================== Launching Zone ==================== #
def extractContext(expe):
	# corpusList                    : list of directories paths
	# corpusDirContent              : list tuples of words, one line is one document
	# corpusDirContentPOS   : corpusDirContent woth POS filtering
	# subcorpus                     : one tuple is one document words
	# doneFile                              : contains the list of already processed corpus dir of corpusList
	
	# TODO : garder une trace de l'indice du document dans lesquels un contexte a été trouvé
	# histoire de faire quelques stats.
	
	#~ # == extracting contexts == #
	for corpus in expe.corpusList:
		#~ print (expe.corpusList, corpus)
		#~ # == prepare documents content == #
		print('=== processing ' + corpus.rstrip('\n') + ' ====')
		corpusDirContent, fileList = utilsCCM.getCorpusDirContent(corpus)
		print('---> processing POS tagging')
		corpusDirContentPOS = utilsCCM.processCorpusDirContentPOS(corpusDirContent, expe)
		#~ # == running multi threads context extraction == #
		
		for rule in expe.itemList:
			doneFile = expe.contextDir + '/' + rule + '.subcorpusDone'
			
			if (utilsCCM.isAlreadyDone(doneFile, corpus) == 0):
				print('Active Threads : ' + str(threading.activeCount()) + ' - processing ' + rule)
				
				while (threading.activeCount() >= 50):
					time.sleep(0.0001)
					
				# == declare an threading entity class == #
				t = extractContextCCM.extractContext(rule, corpusDirContent, corpusDirContentPOS,  corpus , expe,fileList)
				t.start()
			else :
				print(rule  + ' already done')
				
		#~ # == waiting loop == #
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
		tempFile = expe.contextDir + '/' + rule + expe.contextExt +'.temp'
		utilsCCM.removeRedundancy( contextFile, tempFile)


# ================== extraction par fichier text ========================== #






#========================== Main Routine ========================#
if __name__ == '__main__':
	usage = "usage: %prog -c config_file -l speaker_rule"
	parser = OptionParser(usage=usage)
	parser.add_option("-c", "--config",  dest="config",  help ="configuration file")
	parser.add_option("-s", "--subTask", dest="subTask", help="optional C:M:J:L:G:S Context Matrix reJection svmmodeL Gmmmodel SameSpace")
	parser.add_option("-l", "--listSpeaker", dest="spkList", help="if defined, speaker list is used instead")
	parser.add_option("-a", "--acceptCorpus", dest="acceptCorpusList",  help="if defined, speaker list is used instead")
	parser.add_option("-r", "--rejectCorpus", dest="rejectCorpusList", help="if defined, speaker list is used instead")
	parser.add_option("-t", "--tag", dest="tag", help="if defined, speaker list is used instead")

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


	# ________= pour la liste de fichiers d'acceptation =_________#
	print('__extracting accepation context__')
	expe.corpusList = [options.acceptCorpusList]
	print(expe.corpusList ) 
	expe.contextExt = '.accept.context'
	expe.lexiconExt = '.accept.lexicon'
	extractContext(expe)
	contextGlobal     = buildMatrixCCM.loadContextFile(expe.contextDir +'/'+ options.tag + expe.contextExt)
	lexicon = buildMatrixCCM.buildLexicon(contextGlobal, expe.stopList, 0)
	lexiconSorted   = buildMatrixCCM.getSortedLexicon(lexicon)
	lexiconPosition = buildMatrixCCM.buildLexiconPositionTable(lexiconSorted)
	buildMatrixCCM.writeLexicon(expe.lexiconDir + '/' +  options.tag +  expe.lexiconExt , lexicon, lexiconSorted)

	#contextAccept = buildMatrixCCM.loadContextFile(expe.contextDir + expe.rule +  expe.contextExt )

	# _________= pour la liste de fichiers de rejection =__________ #
	print('__extracting rejection context__')
	expe.corpusList = [options.rejectCorpusList]
	expe.contextExt = '.reject.context'
	expe.lexiconExt = '.reject.lexicon'
	extractContext(expe)
	#contextReject     = buildMatrixCCM.loadContextFile(expe.contextDir + expe.rule +  expe.contextExt )
	# == corpus list est un chemin vers un repertoire == #
	contextGlobal     = buildMatrixCCM.loadContextFile(expe.contextDir +'/'+ options.tag + expe.contextExt)
	lexicon = buildMatrixCCM.buildLexicon(contextGlobal, expe.stopList, 0)
	lexiconSorted   = buildMatrixCCM.getSortedLexicon(lexicon)
	lexiconPosition = buildMatrixCCM.buildLexiconPositionTable(lexiconSorted)
	buildMatrixCCM.writeLexicon(expe.lexiconDir + '/' +  options.tag + expe.lexiconExt , lexicon, lexiconSorted)

	print options.tag
	expe.contextExt = '.context'
	expe.lexiconExt = '.lexicon'
	t = processRejectionCommonSpaceCCM.writeReject(expe, [options.tag +'.accept' , options.tag + '.reject' ])
	t.start()

