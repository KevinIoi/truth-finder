'''
    textProcessor.py
    
    Module of the truth-finder program containing the functions
    for scrapping websources, cleaning the text 
'''

from bs4 import BeautifulSoup
import requests
from nltk import word_tokenize, sent_tokenize, ngrams
from collections import defaultdict
from nltk.stem import PorterStemmer


def pullArticleText(webAddress, timeoutTime = 10):
    """
    Extracts text from webadress filtering scripts and html tags 
    as much as possible  

    params:
        webAddress (str):
            the url to be accessed
        timeoutTime (int):
            seconds before giving up on request, default 10

    return:
        list of text representing each section of webpage
    """
    articleText = []
    try:
        webSource = requests.get(webAddress, timeout=timeoutTime).text
    except Exception as e:
        raise e

    soup = BeautifulSoup(webSource, 'lxml')
    
    #remove scripts, it sometimes errors if there are none
    try:
        for script in soup("script"):
            script.decompose()
    except:
        print("error")
        pass

    for section in soup.find_all():
        try:
            # articleText.append(section.text)
            sectionText = "".join(line.strip() for line in section.get_text().split("\n"))

            if(len(sectionText)<100000):
                articleText.append(sectionText)
        except Exception as e:
            raise e

    return articleText

def calcOverlap(claim, chunk):
    """
    Calculates the percent of the chunk that overlaps with the claim

    params:
        claim (str):
            base claim
        chunk (str):
            segment of text to be assessed

    returns:
        float representing percent overlap
    """
    overlap = 0.0
    ps = PorterStemmer()

    claimStems = [ps.stem(word.lower()) for word in word_tokenize(claim) if word.isalpha()]
    chunkStems = [ps.stem(word.lower()) for word in word_tokenize(chunk) if word.isalpha()]

    claimGramsStemmed = set()
    snipGramsStemmed = set()

    #add all grams to lists
    for gram in ngrams(claimStems,n=1):
        claimGramsStemmed.add(gram)
    for gram in ngrams(claimStems,n=2):
        claimGramsStemmed.add(gram)
    for gram in ngrams(chunkStems,n=1):
        snipGramsStemmed.add(gram)
    for gram in ngrams(chunkStems,n=2):
        snipGramsStemmed.add(gram)

    gramOverlap = 0
    for gram in claimGramsStemmed:
        if gram in snipGramsStemmed:
            gramOverlap += 1.0

    try:
        if ((gramOverlap / len(snipGramsStemmed)) > 0.05):
            overlap = gramOverlap / len(claimGramsStemmed)
    except:
        overlap = 0.0
        pass

    return overlap

def getSnippets(textSections, maxlen=1):
    """
    params:
        textSections (list, str): list of sections of text to be processed into snippets
            Each string in list will be treated as a separate text. Will not combine
            sentences from different texts
        maxlen (int):
            the maximum number of sentences each snippet will contain (default 0)

    returns:
        list of all possible unique snippets of text ranging from 1 sentence to 'maxlen' sentences
    """
    snippets = set()

    for section in textSections:
        sectionSnips = defaultdict(lambda : [])
        for sentence in sent_tokenize(section):
            sectionSnips[1].append(sentence)                     

        if(maxlen>1):
            for snipLength in range(2, maxlen+1):#make list of sentence of each size requested
                index = 0
                if snipLength <= len(sectionSnips[1]):
                    while index < len(sectionSnips[1]):#loop through all previously read sentences
                        sip = (sectionSnips[1])[index]
                        activeIndex = index + 1
                        while activeIndex-index < snipLength and activeIndex<len(sectionSnips[1]):
                            sip += " " + (sectionSnips[1])[activeIndex]
                            activeIndex += 1
                        if activeIndex-index == snipLength:
                            sectionSnips[snipLength].append(sip)
                        index += 1
        for snipGroup in sectionSnips.keys():
            for snip in sectionSnips[snipGroup]:
                snippets.add(snip)

    return list(snippets)

def getRelevence(claim, snippets):
    """
    Calculates the relevence of a snippet to a given claim

    params:
        claim:
            string to compare snippets to
        snippets:
            list of snippets to evaluate

    returns:
        list of tuples containing the snippets with overlap score of over n
        and their respective overlap score
        [(snippet, overlapScore), ...]  -> [(String, float), ...]
    """
    releventSnips = [[],[]]

    for snip in snippets:
        overlap = calcOverlap(claim, snip)
        if overlap >= 0.3:
            releventSnips[0].append(snip)
            releventSnips[1].append(overlap)
    return releventSnips


def prepListForClassification(text, featDict):
    """
    Returns bigrams and unigram from text. Usable to define problem for linlinear predictor

    param:
        text (str):
            string to be processed 
        featDict (dict):
            dictionary of possible features for the model
    """
    dataList = []

    for block in text:
        wordBag = word_tokenize(block)
        wordBag = [word.lower() for word in wordBag if word.isalpha()]

        #get uni/bigrams
        unigrams = ngrams(wordBag,n=1)
        bigrams = ngrams(wordBag,n=2)
        
        #add data to training/testing Sample
        features = defaultdict(lambda:0)
        for gram in unigrams:
            if featDict[gram] != 0:#don't count gram that aren't known features
                features[featDict[gram]] += 1
        for gram in bigrams:
            if featDict[gram] != 0:#don't count gram that aren't known features
                features[featDict[gram]] += 1
        dataList.append(dict(features))
    return dataList

def prepArticleForClassification(textBlocks, featDict):
    """
    returns dictionary containing all feature uni/bigrams in text of article

    params:
        textBlocks:
            list of text blocks in web sourced article
        featDict:
            dictionary listing relevent features and their indices in the model 
    """
    articleFeatures = defaultdict(lambda:0)

    for block in textBlocks:
        wordBag = word_tokenize(block)
        wordBag = [word.lower() for word in wordBag if word.isalpha()]

        #get uni/bigrams
        unigrams = ngrams(wordBag,n=1)
        bigrams = ngrams(wordBag,n=2)
        
        #add data to training/testing Sample
        for gram in unigrams:
            if featDict[gram] != 0:#don't count gram that aren't known features
                articleFeatures[featDict[gram]] += 1
        for gram in bigrams:
            if featDict[gram] != 0:#don't count gram that aren't known features
                articleFeatures[featDict[gram]] += 1

    return dict(articleFeatures)
