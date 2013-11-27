#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

import os
#import sys
from optparse import OptionParser
import configServerCCM, commands
import buildCCMRepLab
import buildMatrixCCM, extractContextCCM, learnSVMmodelCCM, processRejectionEntitySpaceCCM

#import RCutils
#import RClauncher
#import TSTutils
#import TSTlauncher

# ====================================================================== #
def writeSTestVMfile(svmMatFile, matrix ):
	if not os.path.exists(svmMatFile) :
		outputMat = []
		for p in matrix :
			currentLine = '0 '
			counter = 1 
			for number in  p : 
				currentLine += str(counter) + ':' + str("%.4e" % number) + ' '
				counter += 1 
			outputMat.append(currentLine)
		fOut = open(svmMatFile, 'w')
		for line in outputMat :
			fOut.write(line + '\n')
		fOut.close()
	else:
		print(svmMatFile + ' already exists' )

# ====================================================================== #

def scaleData(svmRangeFile, svmScaleCommand):
	if os.path.exists(svmRangeFile):
		print('scaling')
		print(svmScaleCommand)
		SCALE = commands.getstatusoutput(svmScaleCommand)
# ====================================================================== #
def predictData(svmModelFile,svmTrainCommand):
	if os.path.exists(svmModelFile):
		print('training')
		print(svmTrainCommand)
		MODEL = commands.getstatusoutput(svmTrainCommand)
# ====================================================================== #

if __name__ == '__main__':
	usage = "usage: %prog -c ctm_file -s searched_speaker_list -u uemFile -r time_request_file -t trainConfig"
	parser = OptionParser(usage=usage)
	parser.add_option("-c", "--config" 		, dest="config",    help="train data confg file")
	parser.add_option("-d", "--testDir"     , dest="testDir",   help="request time list file + speakers")
	parser.add_option("-T", "--TestDir"     , dest="outDir",   help="request time list file + speakers")
	parser.add_option("-m", "--svmMatDir"    , dest="svmMatDir",help="request time list file + speakers")
	parser.add_option("-r", "--svdDir    "  , dest="svdDir",    help="request time list file + speakers")
	parser.add_option("-L", "--lexiconDir"  , dest="lexiconDir",help="request time list file + speakers")
	parser.add_option("-l", "--spkList"    , dest="spkList",    help="request time list file + speakers")
	parser.add_option("-t", "--tag"         , dest="tag",       help="request time list file + speakers")
	parser.add_option("-R", "--recoRule"    , dest="recoRule",  help="request time list file + speakers")
	(options, args) = parser.parse_args()


	# == check configuration file == #
	if options.config == None :
		print("configuration file is not optional")
		print(usage)
		exit()
	else : 
		if not os.path.exists(options.config):
			print("check configuration file")
			print(usage)
			exit()
		else :
			# -- loading config file  -- #	
			expe = configServerCCM.Configuration(options.config)

	# == overwrite spkList (-l option) == #
	if options.spkList != None :
		if os.path.exists(options.spkList) :
			print("rule list passed as an option "+  options.spkList)
			(expe.itemList,  expe.acceptation, expe.rejection) = configServerCCM.loadRules(options.spkList)
		else :
			print ("speaker list file  "  + options.spkList + " does not exists. exiting")
			exit()
	
	''' la variable tag correspond a l'identifiant du modele '''
	
	# == chargement de la liste des fichiers dans le répertoire de test == #
	expe.corpusList = [options.testDir]
	expe.contextDir = options.outDir
	expe.lexiconDir	= options.lexiconDir
	expe.svdDir		= options.svdDir
	expe.svmMatDir  = options.svmMatDir
	
	print(expe.corpusList, expe.contextDir, expe.lexiconDir, expe.svdDir, expe.svmMatDir)
		 
	
	# == construction des contextes de test == #
	buildCCMRepLab.extractContext(expe)
	
	# cree un fichier dans le repertoire contextDir (repertoire de test)
	# == chargement de ce context a partir du fichier generé == #
	contextGlobal   		= buildMatrixCCM.loadContextFile(expe.contextDir +'/'+ options.tag + expe.contextExt)
	
	# == chargement du lexique du modele
	lexiconFile = expe.lexiconDir + '/' + options.recoRule + expe.lexiconExt
	lexicon 			= processRejectionEntitySpaceCCM.loadLexiconFile(lexiconFile)
	lexiconPosition 	= processRejectionEntitySpaceCCM.loadLexiconPositionTable(lexiconFile)
	
	denseMat = buildMatrixCCM.computeMatrix(int(expe.contextBuildMatrixWindow) , lexicon, lexiconPosition, contextGlobal)
	svdMat  = expe.svdDir + '/' + options.recoRule + expe.svdExt

	cutOffSVD = int(expe.cutoffSVD)
	vt = buildMatrixCCM.loadMatFile(svdMat)
	
	reducedMatrix = buildMatrixCCM.computeReduction(vt, denseMat, cutOffSVD)
	
	svmMatFile = expe.contextDir + '/' + options.tag  + expe.svmMatExt 
	print(svmMatFile)
	# mettre le fichier au format pour le svm
	writeSTestVMfile(svmMatFile,reducedMatrix)
	
	svmScaleFile = svmMatFile + '.scale'
	svmTrainFile = expe.svmMatDir + '/' + options.recoRule + expe.svmMatExt
	svmModelFile = svmTrainFile + '.model'
	svmRangeFile = svmTrainFile + '.range'
	svmPredictionFile = svmMatFile + '.predict'
	svmScaleCommand = expe.commandSVMscale + ' -r ' + svmRangeFile + ' ' + svmMatFile + ' > ' + svmScaleFile
	svmPredictCommand = expe.commandSVMpredict +' '+ svmScaleFile + ' ' + svmModelFile + ' ' + svmPredictionFile
	
	print svmScaleCommand , svmRangeFile
	print svmPredictCommand
	
	scaleData(svmRangeFile, svmScaleCommand)
	predictData(svmModelFile,svmPredictCommand)
	
	
	
