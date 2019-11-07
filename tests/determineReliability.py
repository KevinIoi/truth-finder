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
reliability = defaultdict(lambda : [0,0])

featDict = featureBag.getFeatureFile("../resources/featsV2.pickle")
model = llu.load_model("../resources/models/gen2v1.model")

#load data from all source files
for file_ in os.listdir("../resources//partialSnopes"):    
    truthValue = None

    if file_.endswith(".json"):
        with open("../resources//partialSnopes/" + file_, 'r') as doc:
            fileData =  json.loads(doc.read())

        if fileData['Credibility'] == 'false' or fileData['Credibility'] == 'mostly false':
            truthValue = 0
        else:#fileData['Credibility'] == 'true' or fileData['Credibility'] == 'mostly true'
            truthValue = 1

        for page in fileData["Google Results"]:#load page of google results
            for resultsDict in page.values():#load sources from google page
                for source in resultsDict:#process each source
                    if (source["domain"] != "www.snopes.com"):
                        print(source["domain"])
                        try:
                            text = textProcessor.pullArticleText(source["link"])
                            snippets = textProcessor.getSnippets(text, 4, fileData["Claim"])

                            releventSnips = len(snippets)

                            if releventSnips > 0:
                                snipData = textProcessor.prepListForClassification(snippets,featDict)
                                p_labels, p_acc, p_vals = llu.predict( [], snipData, model, '-b 1 -q')

                                probSum = [0,0]
                                for probVals in p_vals:
                                    probSum[0] += probVals[0]
                                    probSum[1] += probVals[1]
                                probSum[0] /= releventSnips
                                probSum[1] /= releventSnips

                                if (probSum[truthValue] > probSum[1]):
                                    (reliability[source["domain"]])[0] += 1#correct
                                else:
                                    (reliability[source["domain"]])[1] += 1#incorrect
                        except:
                            continue
                    # break#each entry in page
                # break#each page?
            # break #each page.
        # break#each file
    # break#each file?

with open("reliability.txt", "w") as fp:
    for r in reliability:
        articleStances = reliability[r]
        percentCorrect = articleStances[0]/(articleStances[0]+ articleStances[1])
        fp.write(r + "\t" + str(percentCorrect) + "\t" + str(articleStances) + "\n")    


"""
****************************************************************************************************************
"""

# for claim in file:
#     #default dict
#     reliability[domain] = {[correct, incorrect]}
#                 'www.wiki.com' , [5, 8]
#     sources[] = pullwebSources

#     truthValue = claim.truth

#     for source in sources:
#         data = pullData
#         snips = data.getReleventSnips
#         stance = avgStance(snips)

#         if stance == truthValue:
#             (reliability[getCleanUrl(source)])[0] += 1
#         else:
#             (reliability[getCleanUrl(source)])[1] += 1


# calcedReliability = {}

# for source in reliability.keys():
#     calcedReliability[domain] = (reliability[source])[0]/((reliability[source])[0] +(reliability[source])[1])
