#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

#import extractContext
#import computeSVD
#import threadPool
#import computeRejection

import os, sys, threading, time, random, argparse
#~ from optparse import OptionParser
import extractContextCCM
import utilsCCM
import buildMatrixCCM
import processClassification
import gzip
#========================== Main Routine ========================#
if __name__ == '__main__':
	
	parser = argparse.ArgumentParser(description='build collocation matrices for EACL')
	parser.add_argument("-f", "--fileDir", dest="fileDir" , help="one tweet per line, the label is in the filename", required='True') 
	parser.add_argument("-o", "--outDir", dest="outDir" , help="one tweet per line, the label is in the filename", required='True') 
	options = parser.parse_args()
	
	content, listLabel  = utilsCCM.loadContentAndTags(options.fileDir)
	context = extractContextCCM.buildCollocContext(content)
	lexicon	= buildMatrixCCM.buildLexicon(context, [], 10000, 1)	
	lexiconSorted	= buildMatrixCCM.getSortedLexicon(lexicon)
	lexiconPosition	= buildMatrixCCM.buildLexiconPositionTable(lexiconSorted)
	print "building matrix...."
	outputMatrix    = buildMatrixCCM.computeMatrix(-1, lexiconSorted, lexiconPosition, context, False)

	# === post edition de la matrice et des labels === # 
	reducedMatrix, reducedListLabel = buildMatrixCCM.removeMatrixEmptyLines(outputMatrix, listLabel)


	# === mise en oeuvre du leave-one-out === #
	#processClassification.SVMmulticlass_LeaveOne_Out(reducedMatrix, reducedListLabel)


	print "done.."



	# === écriture des fichiers text en sortie de tritement == #
	#buildMatrixCCM.dump2File(outputMatrix, options.outDir +'/matrix', False, True)
	buildMatrixCCM.writeLexicon(options.outDir + '/lexicon' , lexicon, lexiconSorted, True)
	buildMatrixCCM.dump2File(reducedMatrix, options.outDir +'/matrix', False, True)
	utilsCCM.writeList2File(options.outDir +'/label', reducedListLabel, True)

	# == zip de la matrice dense == #
	#~ indata = open(options.fileDir +'/matrix', 'r').read()
	#~ output = gzip.open(options.fileDir +'/matrix.gz', 'wb', 9)
	#~ try:
		#~ output.write(indata)
	#~ finally:
		#~ output.close()
	#~ os.remove(options.fileDir +'/matrix')

#=========================================================#
