from Products.CMFCore.utils import getToolByName
from zope.component import getUtility, getAdapter
from zope.component.interfaces import ComponentLookupError

from plone.app.learning.behaviors import IMachineLearning
from plone.app.learning.interfaces import ILearningString
from plone.app.learning.machinelearning.utils.base import CatalogEmpty
from plone.app.learning.machinelearning.utils.vectorizers import new_hashing_vectorizer




class Vectorizer(object):
    """
    Computes vectorizer for objects with IVectorizer schema

    :iparam context: Any object (for obtaining portal_catalog, etc.)
    :iparam schema: A plone.app.learning.settings.ISettings registry proxy
    :iparam learned_objs: The list of objects learned (by order of learning)

    :iparam vectorizer: The Bag-of-words dictionary of strs2ints
    :iparam corpus: The Bag-of-words for samples

    """

    def __init__(self,context, schema):
        self.context = context
        self.schema = schema
        self.learned_objs = []

    def _new_vectorizer(self, dictionary=None, remembering=True):

        stopwords = self.schema.stopWords
        if not stopwords == 'english':
            stopwords = stopwords.split()

        ngramrange = (self.schema.ngramRangeMin, self.schema.ngramRangeMax)

        useremembering = False
        if remembering:
            useremembering = self.schema.useRemembering

        #HashingVectorizer
        return new_hashing_vectorizer(
            stop_words=stopwords, ngram_range=ngramrange,
            nltk=self.schema.useNltk, remembering=useremembering,
            )
    
    def get_vectorizer(self):
        #HashingVectorizer
        return self._new_vectorizer(remembering=False)

    def _iterator_objects_strings_tags(self):  
        catalog = getToolByName(self.context, 'portal_catalog')
        samples = catalog({'object_provides': IMachineLearning.__identifier__})    

        if not samples:
            error = 'Catalog search for MachineLearning objects is empty. Please check:\n'
            error += '1. MachineLearning behavior enabled for any content type?\n'
            error += '2. object_provides index has been reindexed after enabling the behavior?'
            raise CatalogEmpty(error)


        self.learned_objs = []
        for o in samples:
            obj = o.getObject()
            try:
                adapt = getAdapter(obj,ILearningString)
            except ComponentLookupError:
                continue        

            self.learned_objs.append(obj)
            yield adapt.learningString()
            #?adapt.learningTags()


    def iterator_learning_attributes(self):
        #Get objects, strings and tags
        iterstrings = self._iterator_objects_strings_tags() 
        #Transform strs to corpus
        vectorizer = self._new_vectorizer()
        corpus = vectorizer.fit_transform(iterstrings) 

        return vectorizer, corpus

