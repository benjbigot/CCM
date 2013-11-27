#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

import os, re, sys, commands, shutil
from random import choice



#=========================================#
def loadContentAndTags(fileList):
	'''
	fileList is a file with 2 cols separated by a tabulation
	first col is a tweet id 
	second col is the content of the tweet
	'''

	corpusContent = []
	labelList     = []

	Flist = open(fileList , 'r')
	Flist_content = Flist.readlines()

	for line in Flist_content:
		labelList.append(line.rstrip().split('\t')[0])
		content = line.rstrip().split('\t')[1]
		# suppose to contain only one line
		corpusContent.append(re.sub(r' \+', ' ', content).split())
	return corpusContent, labelList

#=========================================#

def loadFromFileList(fileList) :
	corpusContent = []
	labelList     = []
	for f in fileList :
		fn = open(options.inputDirectory +'/' + f)
		tempLine = fn.read()                        
		corpusContent.append(re.sub(r' \+', ' ', tempLine).split())
		fn.close()
	return corpusContent, labelList

#=========================================#

def loadFileList(fN):
	''' fileList is a two-column file
		col 1 is the file name
		col 2 is a label
	'''
	if os.path.exists(fN) :
		fileDesc = open(fN, "r")
		data     = fileDesc.readlines()
		fileDesc.close()

		data2 = []
		for item in data : 
			data2.append(item.rstrip().split(' '))
		return data2

	else :
		print( 'File ' + fN + ' does not exist\nExiting the program...')
		return -1
		
#____________________________________#

def loadFile(fN):
	''' Loads the content of a file in a list,
		quits if the file does not exist
	'''
	if os.path.exists(fN) :
		fileDesc = open(fN, "r")
		data     = fileDesc.readlines()	
		data2 = []
		fileDesc.close()
		
		for item in data : 
			data2.append(item.rstrip())
		return data2
		
	else : 
		print( 'File ' + fN + ' does not exist\nExiting the program...')
		return -1


#_______________________________________#

def getCorpusDirContent(dirCorpus):
	''' load all text file from a directory in a tuple
		Words are separated, if cleaning rules have to be done it's here
	'''
	corpusContent = []
	for root, dirs, files in os.walk(dirCorpus.rstrip()):
		# == one line per corpus file == #
		for i in files :
			fn = open( root + i , "r")
			# has to be tested #
			tempLine = fn.read().replace('\n', ' ').replace(':', ' ').replace(';', ' ').replace('&amp;', ' ').replace('&gt', ' ').replace('&lt', ' ').replace(',', ' ').replace('(', ' ').replace(')', ' ').replace('!', ' ').replace('?',' ').replace('.',' ').replace('-',' ').lower()
			corpusContent.append(re.sub(r' \+', ' ', tempLine).split())
			#corpusContent.append(fn.read().replace('\n', ' ').replace('  ', ' ').split())
			fn.close() 
	print('--> ' + str(len(corpusContent)) + ' files')		
	return corpusContent, files
			
#_____________________________________________________________________#

def bdlex2win(mot):
	newMot = str(mot).replace('e1','é').replace('e2','è').replace('e3','ê').replace('e4','ë').replace('a1','á').replace('a2','à').replace('a3','â').replace('a4','ä').replace('i1','í').replace('i2','ì').replace('i3','î').replace('i4','ï').replace('u1','ú').replace('u2','ù').replace('u3','û').replace('u4','ü').replace('o1','ó').replace('o2','ò').replace('o3','ô').replace('o4','ö').replace('c5', 'ç')
	return newMot
	
#__________________________________________________________#

def win2bdlex(mot):
	newMot = str(mot).replace('é','e1').replace('è','e2').replace('ê','e3').replace('ë','e4').replace('á','a1').replace('à','a2').replace('â','a3').replace('ä','a4').replace('í','i1').replace('ì','i2').replace('î','i3').replace('ï','i4').replace('ú','u1').replace('ù','u2').replace('û','u3').replace('ü','u4').replace('ó','o1').replace('ò','o2').replace('ô','o3').replace('ö','o4').replace('ç','c5')
	return newMot

#__________________________________________________________#

def processTreeTaggerOnContext(subCorpus,expe):
	''' 
		realizes the treetagging of subcorpus, 
		conserve the aDV, NOM and VER Part-Of-Speech 
		and return a new subcorpus list 
	'''	
		
	# == whatever the length of the subcorpus or windonws length, the wole subcorpus is tree-tagged == #
	# a tester #
	outContextFiltered = []
	idFile = str(os.getpid())
	outContextTempFile = expe.contextDir + '/' + idFile + '.temp'
	fTreeTagger = open( outContextTempFile , "w")
		
	# == write context one word by line == #
	for word in subCorpus:
		fTreeTagger.write(bdlex2win(word) + '\n')
	fTreeTagger.close()
	
	# == process tree-tagger a tenter == #
	POS = commands.getoutput(expe.commandTT + ' ' + outContextTempFile)
	
	for index,tag in enumerate(POS.split('\n')):
		# == for special cases inthe treetagging return == #
		token = tag.split('\t')[2] 
		if ( '|' in tag.split('\t')[2]) :
			token = tag.split('\t')[2].split('|')[1]
			
		# == building the tree-tagged subcorpus == #
		if ( 'ADJ' in tag.split('\t')[1]) or ('NOM' in tag.split('\t')[1]) or ('VER' in tag.split('\t')[1]): 					
			outContextFiltered.append(win2bdlex(token))
		else:
			outContextFiltered.append('--')
	os.remove(outContextTempFile)
	return outContextFiltered

#__________________________________________________________#

def processCorpusDirContentPOS(corpusDirContent, expe) :
	corpusDirContentPOS = []
	if (expe.processTreeTagging == 'True'):
		for subcorpus in corpusDirContent :
			sys.stdout.write('.')
			sys.stdout.flush()
			
			outContextFiltered = []
			outContextFiltered = processTreeTaggerOnContext(subcorpus,expe)
			corpusDirContentPOS.append(outContextFiltered)
	elif (expe.processTreeTagging == 'False'):
		corpusDirContentPOS = corpusDirContent
	else :
		print ('check pos tagging rule : ' + expe.processTreeTagging )
	sys.stdout.write('\n')	
	return corpusDirContentPOS
	
#__________________________________________________________
	
def isAlreadyDone(doneFile, corpusToDo):
	# check is corpusToDo is an element of DoneFile
	alreadyDone = []
	if os.path.exists(doneFile) :
		done = loadFile(doneFile)
		for i in done :
			alreadyDone.append(i.rstrip())

		if corpusToDo.rstrip() not in alreadyDone :
			return 0
		else : 
			return 1
	else : 
		return 0
#__________________________________________________________		

def uniq(seq, idfun=None): 
	seen = {}
	result = []
	for item in seq:
		marker = item
		# in old Python versions:
		# if seen.has_key(marker)
		# but in new ones:
		if marker in seen: continue
		seen[marker] = 1
		result.append(item)
	return result		
		
#__________________________________________________________		

def removeRedundancy(orig, dest):
	if os.path.exists(orig) :
		shutil.copy(orig , dest)
		content = loadFile(orig)
		keys = {}
		for line in content : 
			keys[line.rstrip()] = 1

		# verifier les lignes mal formatées : les indicateurs de champs doivent être unique
		fOut = open(orig, 'w');
		for i in keys : 
			fOut.write(i + "\n")
		fOut.close()
		os.remove(dest)

#__________________________________________________________		

def takeRandomContext(contextFile, contextNumber):
	if (os.path.exists(contextFile)) :
		#lines = [l.strip() for l in open(contextFile , 'r')]
		fContext = open(contextFile, 'r')
		lines = fContext.readlines()
		fContext.close()
		takenContext = []
		for i in range(0, int(contextNumber)):
			subLine = choice(lines)
			if subLine not in takenContext :
				takenContext.append(subLine)
	return takenContext



