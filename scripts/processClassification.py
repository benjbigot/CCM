#!/usr/bin/python 
# -*- coding: utf-8 -*- 
import os, sys, threading, time, random   
import numpy
import scipy
## implementation de svm multiclass avec interface Python :
## http://pyml.sourceforge.net/index.html 
## http://shogun-toolbox.org/page/home/

## smv muliclass sans interface
## http://www.cs.cornell.edu/people/tj/svm_light/svm_multiclass.html
## SVM Torch



# = utilisation du sklearn = #
from sklearn.cross_validation import LeaveOneOut
from sklearn import svm
#from sklearn.svm import SVC

# les donnees : X = np.array([[0., 0.], [1., 1.], [-1., -1.], [2., 2.]])
# les labels  : Y = np.array([0, 1, 0, 1])
# loo = LeaveOneOut(len(Y))
# for train, test in loo: donne les indices des sous ensemble de données


# svm multi- class
# SVC and NuSVC implement the “one-against-one” approach (Knerr et al., 1990) 
# for multi- class classification. 
# If n_class is the number of classes, then n_class * (n_class - 1) / 2 classifiers 
# are constructed and each one trains data from two classes:
# http://scikit-learn.org/stable/modules/svm.html#multi-class-classification

# == for grid search == #
#http://stackoverflow.com/questions/14866228/combining-grid-search-and-cross-validation-in-scikit-learn

# == for numpuy array slicing == #
#http://docs.scipy.org/doc/numpy/glossary.html#term-slice

def SVMmulticlass_LeaveOne_Out(matrix, labels):
	'''
	process a leave one out svm multiclass classification using svmC
	'''
	Lab = numpy.asarray(labels)
	loo = LeaveOneOut(len(labels))
	for train, test in loo:
		#print train, test
		# == preparer les sous matrices X et y 
		# y[np.array([0,2,4]),1:3] donnerait simplement
		X = matrix[ train, : ]
		L = Lab[train , : ]
		
		Y = matrix[test , :  ]
	
		clf = svm.SVC()
		clf.fit(X, L)
		print(clf.predict(Y))
		
	return 1
