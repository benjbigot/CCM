#!/usr/bin/python
# -*- coding: utf-8 -*-
# python 2.6 sur le cluster

import threading, os, sys
sys.path.append('/local_disk/hera2/PERCOL/bigot/PlateformeRecoName/bin/scikit-learn-0.13/build/lib.linux-x86_64-2.6/')
sys.path.append('/local_disk/hera2/PERCOL/bigot/PlateformeRecoName/bin/joblib-0.7.0b/build/lib.linux-x86_64-2.6/')
import numpy
import joblib
import sklearn 
import sklearn.mixture 
import pylab
import matplotlib
import utilsCCM
import buildMatrixCCM


#------------------#


class processGMM(threading.Thread) :
	def __init__(self, expe, rule, acceptationFile, rejectionFile, gmmModelOutFile ):
		threading.Thread.__init__(self)
		self.rule = rule
		self.expe = expe
		
		self.acceptationFile = acceptationFile
		self.rejectionFile = rejectionFile
		
		self.gmmAcceptFile = gmmModelOutFile + '.accept'
		self.gmmRejectFile = gmmModelOutFile + '.reject'
		
		self.acceptation = []
		self.rejection   = []
		self.acceptationLabel = []
		self.rejectionLabel   = []
		
	#___________________________________________#

	def run(self):
		self.acceptation = buildMatrixCCM.loadMatFile(self.acceptationFile)
		self.rejection   = buildMatrixCCM.loadMatFile(self.rejectionFile)
		self.acceptationLabel = [1]*len(self.acceptation)		
		self.rejectionLabel = [-1]*len(self.rejection)
	
		self.acceptationModel = learnModel(self.acceptation, self.gmmAcceptFile)
		self.rejectionModel   = learnModel(self.rejection,   self.gmmRejectFile)
	
#______________________________________________#
def learnModel(data , name): 
	# covar_type = 'spherical', 'diag', 'tied', 'full'
	# eventuellement proposer une approche tenter plusieurs valeurs de nb de composantes et 
	# evaluer le bic ou le aic pour determiner le nombre idéal.
	# proposer l'édition d'un rapport sur le modéle appris en proposant notamment les proba a posteriori
	# return classifier, report
	classifier = sklearn.mixture.GMM(n_components=16, covariance_type='diag' , init_params='wc' , n_iter=20)
	try:
		classifier.fit(data)
		joblib.dump(classifier, name, compress=9, cache_size=1000)
	except : 
		print('----> not enough contexts for ' + name)
	return classifier
#______________________________________________#
