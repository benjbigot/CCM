#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster
# import re,os
import os, sys, threading, time
from collections import defaultdict
import utilsCCM
import buildMatrixCCM
#import commands
#import subprocess
#import cProfile

#______ entity class _____#
class extractContext(threading.Thread):
	''' for one personId (rule), accepation and rejection rules, 
		in one corpusDir extracts the contexts centered on the speaker name 
		produces 2 files : one lexicon and one context file
		search in the unfiltred context and get the POS filtered.
	'''
	def __init__(self, rule, corpusDirContent, corpusDirContentPOS, subCorpusName, expe,fileList):
		threading.Thread.__init__(self)	
	
		# == basic class atributes == #
		self.rule = rule
		self.expe = expe
		self.fileList = fileList
		self.corpusDirContent   = corpusDirContent
		self.corpusDirContentPOS   = corpusDirContentPOS
		self.subCorpusName      = subCorpusName

		self.outContextFile     = self.expe.contextDir + self.rule + self.expe.contextExt
	
	#____________________________________________________________#
	
	def run(self):	
		# == recherche et ecriture des contextes == #
		self.getContext()

		# == once work is done, update the done list == #
		fDone = open(self.expe.contextDir + '/' + self.rule + '.subcorpusDone' , 'a')	
		fDone.write(self.subCorpusName.rstrip() + "\n")
		fDone.close()
		
	#____________________________________________________________#
	
	def getContext(self):
		''' 
		start by looking for pattern quickly, then check 
		acceptation and rejection finally produce indexed vectors 
		output are written for each subcorpus
		'''
		fTrace = open(self.expe.contextDir + '/' + self.rule + '.traces', 'w')
		
		
		# == for each subcorpus == #
		for m in range(len(self.corpusDirContent)):
			subcorpus = self.corpusDirContent[m]
			subcorpusPOS = self.corpusDirContentPOS[m]
			
			# == clear output for every subcoprpus == #
			outputContextPosition = []
			outputContext = []
			
			# ======== 1. get positions of rule in the unfiltred file content ==== #
			if(checkExistence(subcorpus, self.expe.acceptation[self.rule])):	
				for position in range(len(subcorpus)) :
					for elmt in self.expe.acceptation[self.rule] :
						# == accept or reject the pattern, if accepted, get its position == #
						if validate_elmt(subcorpus, position, elmt , self.expe.rejection[self.rule]):
							outputContextPosition.append(position)


			# ======== 2.once for a subcorpus every occurrences have been found === #
			if ( len(outputContextPosition) > 0 ) :
				fTrace.write(self.fileList[m] + '  ' + str(len(outputContextPosition)) + ' contexte\n')
				for occurrence in outputContextPosition :
					outputContext.append(writeContext(occurrence, int(self.expe.contextExtractionWindow), subcorpusPOS))
			else:
				fTrace.write(self.fileList[m] + '  ' + str(len(outputContextPosition)) + ' contexte\n')
			
			# ======== 3.  write output contexts to a file ============ #
			if (len(outputContext)  > 0 ) : 
				write2ContextFile(self.outContextFile,outputContext)

		fTrace.close()






#__________________________________________________________#
def checkExistence(cleanCorpusWords, currentAcceptation):
	''' if at least one acceptation rule shape is in the sub-crpus '''
	for i in currentAcceptation:
		if i.split()[-1] in cleanCorpusWords :
			return True
	return False
#___________________________________________________________#
def validate_elmt(cleanCorpusWords,position, elmt, rejection ) :
	''' searching for a n-word pattern in the corpus caution to indexes in slices'''
	if ( ( position - len(elmt.split() )) >= 0 ):
		if ( elmt ==   ' '.join(cleanCorpusWords[position - len(elmt.split()) + 1 : (position + 1) ])):
			for non_elmt in rejection :
				if( non_elmt ==   ' '.join(cleanCorpusWords[position - len(non_elmt.split()) +  1  : ( position + 1) ] ) ):
					return 0
			return 1
	return 0
#___________________________________________________________#
def writeContext(positionDepart, winLength, cleanCorpusWords):
	''' buils the context vector with position and word index, thisfunction should call the dictionnary class variable
		The outputFilewritting is done during a higher step; because contexts are just Ko
		NEW versions, use of a hash of list where entries are words and contain positions
	'''
	# == defining parsing boundaries == #
	if (int(winLength) == -1):
		positionDebut = 0 
		positionFin = len(cleanCorpusWords)
	else:
		positionDebut = (int(positionDepart) - int(winLength)) if ( int(positionDepart) - int(winLength)) >= 0 else 0
		positionFin   = (int(positionDepart) + int(winLength)) if ( int(positionDepart) + int(winLength)) < len(cleanCorpusWords) else len(cleanCorpusWords)
	
	# == start parsing == #
	contextWords = defaultdict(list)
	contextWords[cleanCorpusWords[positionDepart]].append('0')
	
	#______backwards context_____#
	counter = 0
	for i in range(positionDepart - 1 , positionDebut - 1 , -1 ):
		counter -= 1
		if (cleanCorpusWords[i] != '--') : 
			contextWords[cleanCorpusWords[i]].append(str(counter))
	
	#____forward context______#
	counter = 0
	for i in range(positionDepart + 1, positionFin, 1):
		counter +=1
		if (cleanCorpusWords[i] != '--') :
			contextWords[cleanCorpusWords[i]].append(str(counter))
	
	# ===== formating context line before returning ==== #
	contextLine = [];
	contextLine.append(str(positionDebut))
	contextLine.append(str(positionFin))

	for item in contextWords : 
		 contextLine.append(item+':'+','.join(contextWords[item]))

	return ';'.join(contextLine)
		
#___________________________________________________________#
def write2ContextFile(outContextFile,outputContext):
	''' appending one or several context in the context file'''
	# == removing redundancies in the list == #
	
	if (os.path.exists(outContextFile)):
		fContext = open(outContextFile , 'a')
	else :
		fContext = open(outContextFile, 'w') 
	
	contextUniq = utilsCCM.uniq(outputContext)
		
	#for line in self.outputContext :
	for line in contextUniq :
		fContext.write(line + '\n')
	fContext.close()

	
#___________________________________________________________#
def buildCollocContext(content):
	'''
	content = [[w1,w2,...][w1, w2,...]]
	establishing collocation of 1-grams
	retuns 
	globalLexicon (dict[collocation] => count)
	contextAll (dict[lineIt][w1 w2] => distance  )
	contextOut = [['w1 w2:dist', 'w1 w3:dist', ... ][ 'w1 w2:dist', 'w1 w3:dist',...]]
	
	'''
		
	contextAll = dict()
	contextOut = list()
	
	for lineNb, lineContent  in enumerate(content) :
		contextAll[lineNb] = dict()
		
		for pos_w1 in range(0, len(lineContent)-1):
			for pos_w2 in range (pos_w1 + 1, len(lineContent) ):
				#~ print (pos_w1, pos_w2)
				mot1 = lineContent[pos_w1]
				mot2 = lineContent[pos_w2]
				distance = abs(pos_w2 - pos_w1)
				pattern = ' '.join([mot1, mot2])
				if pattern not in contextAll[lineNb]:
					contextAll[lineNb][pattern] = distance
				elif abs(distance) <= abs(contextAll[lineNb][pattern]):
					contextAll[lineNb][pattern] = distance
		
		currentLine = list()
		for item in contextAll[lineNb] :
			currentLine.append(item +"<COUNT>" + str(contextAll[lineNb][item]))
		contextOut.append(currentLine)
		
	return contextOut
	

#____________________________________________________________#

	#def loadLexiconFile(self):
		#'''	lexicon file is written and loaded for every subcorpus
			#index, word and count are put in dictionnaries
			#return the index of the last item of the lexicon
		#'''
		#self.lastLexiconIndex = -1
		#self.contextLexicon = {}
		#self.contextLexiconSize = {}
		
		#if ( os.path.exists(self.outLexiconFile) ):	
			##print('loading lexicon '+ self.outLexiconFile + ' ' +  self.rule)
			#fLexicon = open(self.outLexiconFile, 'r')
			#lines = fLexicon.readlines()
			#fLexicon.close()
	
			#for lexiconItem in lines:
				##print(lexiconItem)
				#self.contextLexicon[lexiconItem.rstrip().split(' ')[1]] = int(lexiconItem.rstrip().split(' ')[0])
				#self.contextLexiconSize[lexiconItem.rstrip().split(' ')[1]] = int(lexiconItem.rstrip().split(' ')[2])
				#if ( int(lexiconItem.rstrip().split(' ')[0]) > self.lastLexiconIndex ) : 
					#self.lastLexiconIndex = int(lexiconItem.rstrip().split(' ')[0])
					##print(self.lastIndex)
								
	#________________________________________________________________#
	
	#~ def write2LexiconFile(self):
		#~ '''
			#~ lexicon is saved and loaded for each subcorpus
			#~ index  word and counter
			#~ very time consuming !!! have to be improved !!
		#~ '''
		#~ #print('writting to lexicon '+ self.rule)
		#~ fLexicon = open(self.outLexiconFile, 'w')
		#~ for token in self.contextLexiconSize:
			#~ fLexicon.write(str(self.contextLexicon[token]) + ' ' +  str(token) + ' ' + str(self.contextLexiconSize[token]) + '\n')
		#~ fLexicon.close()
	#________________________________________________________________#
	
	#~ def processTreeTaggerOnContext(self):
		#~ ''' 
			#~ realizes the treetagging of subcorpus, 
			#~ conserve the aDV, NOM and VER Part-Of-Speech 
			#~ and return a new subcorpus list 
		#~ '''	
		#~ 
		#~ # == whatever the length of the subcorpus or windonws length, the wole subcorpus is tree-tagged == #
		#~ fTreeTagger = open(self.outContextTempFile, "w")
		#~ 
		#~ # == write context one word by line == #
		#~ for word in self.subcorpus:
			#~ fTreeTagger.write(RCutils.bdlex2win(word) + '\n')
		#~ fTreeTagger.close()
		#~ 
		#~ # == process tree-tagger a tenter == #
		#~ POS = commands.getoutput(self.expe.commandTT + ' ' + self.outContextTempFile)
		#~ 
		#~ for index,tag in enumerate(POS.split('\n')):
			#~ # == for special cases inthe treetagging return == #
			#~ token = tag.split('\t')[2] 
			#~ if ( '|' in tag.split('\t')[2]) :
				#~ token = tag.split('\t')[2].split('|')[1]
			#~ 
			#~ # == building the tree-tagged subcorpus == #
			#~ if ( 'ADJ' in tag.split('\t')[1]) or ('NOM' in tag.split('\t')[1]) or ('VER' in tag.split('\t')[1]): 					
				#~ self.outContextFiltered.append(RCutils.win2bdlex(token))
			#~ else:
				#~ self.outContextFiltered.append('--')
		#~ 
		#~ return self.outContextFiltered
		
	#___________________________________________________________#

	#~ def addAndGetLexiconItem(self, currentWord):
		#~ 
		#~ ''' the lexicon is composed of two dictionnaries
			#~ the first one is an index of words 
			#~ the second one contains the number of occurrences of the word
			#~ if the name is in the dict, the index is returned
		#~ '''
		#~ if not (self.contextLexicon.has_key(currentWord)):
			#~ self.lastLexiconIndex += 1
			#~ self.contextLexicon[currentWord] = self.lastLexiconIndex
			#~ self.contextLexiconSize[currentWord] = 1
		#~ else:
			#~ self.contextLexiconSize[currentWord] += 1
		#~ return  str(self.contextLexicon[currentWord])

