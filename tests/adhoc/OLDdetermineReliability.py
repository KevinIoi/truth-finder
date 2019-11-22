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

#dict to store results of correct/incorrect stance classifications during training
# key will be web domains
# initialize values to [0 correct, 0 incorrect] on new domain

featDict = featureBag.getFeatureFile("../resources/stanceFeatsV2.pickle")
model = llu.load_model("../resources/models/stance2v2.model")

count = 0

#load data from all source files
for file_ in os.listdir("../resources//reliability//source_file_in_use"):    
    truthValue = None
    print("********************************************************")
    print(file_)
    print(count)
    count+=1

    if file_.endswith(".json"):
        reliability = defaultdict(lambda : [0,0])

        with open("../resources//reliability//source_file_in_use/" + file_, 'r') as doc:
            fileData =  json.loads(doc.read())

        if fileData['Credibility'] == 'false' or fileData['Credibility'] == 'mostly false':
            truthValue = 0
        else:
            truthValue = 1

        for page in fileData["Google Results"]:#load page of google results
            for resultsDict in page.values():#load sources from google page
                for source in resultsDict:#process each source
                    if (source["domain"] != "www.snopes.com"):
                        print(source["domain"])
                        print(source["link"])
                        try:
                            text = textProcessor.pullArticleText(source["link"],timeoutTime=6)
                            snippets = textProcessor.getSnippets(text, 4)
                            releventSnips = textProcessor.getRelevence(fileData["Claim"],snippets)
                            numRelevent = len(releventSnips[0])                  

                            if numRelevent > 0:
                                snipData = textProcessor.prepListForClassification(releventSnips[0],featDict)
                                p_labels, p_acc, p_vals = llu.predict( [], snipData, model, '-b 1 -q')

                                """
                                see all relevent snips and their probabilities 
                                """
                                # for i, snip in enumerate(releventSnips[0]):
                                #     print("*******************")
                                #     print(p_vals[i])
                                #     print(snip)

                                stanceImpact = []
                                for index, probVals in enumerate(p_vals):
                                    probs = [0,0]
                                    probs[0] = (releventSnips[1])[index]*probVals[0]
                                    probs[1] = (releventSnips[1])[index]*probVals[1]
                                    stanceImpact.append(probs)
                                stanceImpact.sort(key= lambda instance: max(instance[0], instance[1]),reverse=True)

                                probSum = [0,0]
                                for index, probVals in enumerate(stanceImpact[:10]):
                                    probSum[0] += probVals[0]
                                    probSum[1] += probVals[1]
                                probSum[0] /= index + 1
                                probSum[1] /= index + 1

                                if (probSum[truthValue] > probSum[abs(truthValue-1)]):
                                    (reliability[source["domain"]])[0] += 1#correct
                                else:
                                    (reliability[source["domain"]])[1] += 1#incorrect
                        except Exception as e:
                            # raise e
                            continue


    with open("../resources//reliability//output/" + file_, "w") as fp:
        for r in reliability:
            articleStances = reliability[r]
            percentCorrect = articleStances[0]/(articleStances[0]+ articleStances[1])
            fp.write(r + "\t" + str(percentCorrect) + "\t" + str(articleStances) + "\n")    

