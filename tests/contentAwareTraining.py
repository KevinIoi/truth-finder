import os 
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append('../')

import json
from nltk.tokenize import word_tokenize
import nltk
import numpy as np
from liblinearpkg import *
from liblinearpkg import liblinearutil as llu
from util import featureBag
from util import textProcessor
from collections import defaultdict
import pickle

#dictionary containing all possible features 
featureDict = featureBag.getFeatureFile("../resources/fullFeats.pickle")
reliabilityDict = featureBag.getFeatureFile("../resources/reliability.pickle")


dataSet = ([], [])
truthValue = None

#load data from all source files
for file_ in os.listdir("../resources//contentTrain"):
    if file_.endswith(".json"):
        with open("../resources//contentTrain/" + file_, 'r') as doc:#read snopes file
            fileData =  json.loads(doc.read())

        if fileData['Credibility'] == 'false' or fileData['Credibility'] == 'mostly false':
            truthValue = 0
        elif fileData['Credibility'] == 'true' or fileData['Credibility'] == 'mostly true':
            truthValue = 1

        articleFeatures = []
        truthValues = []

        for page in fileData["Google Results"]:#load page of google results
            for resultsDict in page.values():#load sources from google page
                for source in resultsDict:#process each source
                    if (source["domain"] != "www.snopes.com"):
                        print(source["domain"])
                        wordBagList =  textProcessor.pullArticleText(source["link"],timeoutTime=6)
                        articleFeatures.append(textProcessor.prepArticleForClassification(wordBagList, featureDict))  
                        truthValues.append(truthValue)

    #********************web scrape this******************
    """
    wordBag = word_tokenize(fileData['Description'])
    wordBagTagged = nltk.pos_tag(wordBag)
    wordBag = [word[0] for word in wordBagTagged if ((word[1] != 'NNP') & (word[1] != 'NNPS'))]
    wordBag = [word.lower() for word in wordBag if word.isalpha()]

    #get uni/bigrams
    unigrams = nltk.ngrams(wordBag,n=1)
    bigrams = nltk.ngrams(wordBag,n=2)
    """
    #**************************************************
    
    #add data to training/testing Sample
    dataSet[0].append(truthValue)
    features = defaultdict(featureBag.defDictFunc())

    for gram in unigrams:
        if featDict[gram] != 0:#don't count gram that aren't known features
            features[featDict[gram]] += 1
    for gram in bigrams:
        if featDict[gram] != 0:#don't count gram that aren't known features
            features[featDict[gram]] += 1
    dataSet[1].append(dict(features))

with open('dataSetV2.pickle', 'wb') as handle:
    pickle.dump(dataSet, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('../resources/dataSetV2.pickle', 'rb') as handle:
    dataSet = pickle.load(handle)

model = llu.train(dataSet[0], dataSet[1], '-s 0 -c 4 -w1 10')
model = llu.train(dataSet[0], dataSet[1], '-s 0 -w1 1')
model = llu.train(dataSet[0], dataSet[1], '-s 0 -c 4 -w1 10 -v 10')



# p_labels, p_acc, p_vals = llu.predict( [], [(dataSet[1])[0]],model, '-b 1')

llu.save_model("../resources//models/gen2v2.model",model)








truthValue = 1
infolist = [[truthValue], ["features"]]

#given article
