import csv
import string
from sqlite3 import dbapi2 as sqlite

# Create a list of words to ignore
ignorewords=set(['the','of','to','and','a','in','is','it', 'their', 'so', 'as'])
  
class searcher:
  def __init__(self,dbname):
    self.con=sqlite.connect(dbname)
    
  def __del__(self):
    self.con.close( )

  def getmatchrows(self,q):
    # Strings to build the query
    fieldlist='w0.requirementid'
    tablelist=''
    clauselist=''
    wordids=[]
    rows=[]

    # remove punctuation from query string
    plainquery = q.translate(string.maketrans("",""), string.punctuation)
    
    # Split the words by spaces
    words=plainquery.lower().split(' ')

    # remove ignore words
    words=list(set(words)-set(ignorewords))
    
    tablenumber=0
    for word in words:
      # Get the word ID
      wordrow=self.con.execute(
        "select rowid from wordlist where word='%s'" % word).fetchone( )
      if wordrow!=None:
        wordid=wordrow[0]
        wordids.append(wordid)
        if tablenumber>0:
          tablelist+=','
          clauselist+=' and '
          clauselist+='w%d.requirementid=w%d.requirementid and ' % (tablenumber-1,tablenumber)
        fieldlist+=',w%d.location' % tablenumber
        tablelist+='wordlocation w%d' % tablenumber
        clauselist+='w%d.wordid=%d' % (tablenumber,wordid)
        tablenumber+=1
        
    # Create the query from the separate parts
    if clauselist != '':
      fullquery='select %s from %s where %s' % (fieldlist,tablelist,clauselist)
      cur=self.con.execute(fullquery)
      rows=[row for row in cur]
    
    return rows,wordids
    

  def getscoredlist(self,rows,wordids):
    totalscores=dict([(row[0],0) for row in rows])
    # Scoring functions
    # Frequency: scores a requirement based on how many time the words
    # appear on the requirement description
    #
    #   weights=[(1.0,self.frequencyscore(rows))]
    #
    # Location: scores a requirement based on how far from the start the
    # words appear, assigning higher scores to those closser to the start
    #
    #   weights=[(1.0,self.locationscore(rows))]
    #
    # Distance: scores a requirement based on how far each other the words
    # appear, assigining higher scores to those which are closer to each other
    #
    #   weights=[(2.5,self.distancescore(rows))]
    #
    #
    # Inbound links: scores a requirement based on how many requirements point
    # to it, a requirement with more inbound links is higher in the ranks
    #
    #   weights=[(2.5,self.inboundlinks(rows))]
    #
    #
    # The scoring functions can be combined together to provide finer scoring
    # weights=[(1.5,self.frequencyscore(rows)),
    #         (2.0,self.locationscore(rows)),
    #         (2.5,self.distancescore(rows)),
    #         (1.0,self.inboundlinkscore(rows))]
    weights=[(1.0,self.locationscore(rows)),
             (1.0,self.frequencyscore(rows)),
             (1.0,self.pagerankscore(rows)),
             (1.0,self.linktextscore(rows,wordids))]
    for (weight,scores) in weights:
      for requirement in totalscores:
        totalscores[requirement]+=weight*scores[requirement]
    return totalscores
  
  def getrequirementname(self,id):
    return self.con.execute(
      "select requirement from requirementlist where rowid=%d" % id).fetchone( )[0]

  def getrequirementidentifier(self,id):
    return self.con.execute(
      "select requirementid from requirementlist where rowid=%d" % id).fetchone( )[0]

  # complex query
  # Extra step added to return results which match any of the words in query string (or)
  def query(self, querystring):
    # try exact match first
    scores = self.simplequery(querystring)
     
    # extend the search to individual terms
    termscores = {}
    if ' ' in querystring:    
      terms=querystring.lower().split(' ')
      # remove ignore words
      terms=list(set(terms)-set(ignorewords))
      # query each term in the list of individual words    
      for term in terms:
        wordscores = self.simplequery(term)
        if wordscores != None:
          # add word scores to term scores
          # but if duplicated keys keep max only
          for (reqid,score) in wordscores.items():
            if reqid in termscores:
              if termscores[reqid]<wordscores[reqid]:
                termscores[reqid]=wordscores[reqid]
            else:
              termscores.update({reqid:score})
          
    if termscores != None:
      if scores is None:
        scores=termscores
      else:
        # add word scores to full match scores
        # but if duplicated keys keep full match scores only
        for (reqid,score) in termscores.items():
          if not reqid in scores:
            scores.update({reqid:score})
          
    if scores != None:
      print "results for term %s: %i"% (querystring, len(scores))
      rankedscores=sorted([(score,reqid) for (reqid,score) in scores.items( )],reverse=1)
      for (score,reqid) in rankedscores[0:10]:
        print '%f\t%d\t%s\t%s' % (score,reqid,self.getrequirementidentifier(reqid),self.getrequirementname(reqid))
      return {self.getrequirementidentifier(reqid):(reqid,score,self.getrequirementname(reqid)) for (score,reqid) in rankedscores}
    

      
  # simple query 
  def simplequery(self,q):
    rows, wordids = self.getmatchrows(q)
    if (rows != []) & (wordids != []):
      scores=self.getscoredlist(rows,wordids)
      return scores
  
  def normalizescores(self,scores,smallIsBetter=0):
    vsmall=0.00001 # Avoid division by zero errors
    if smallIsBetter:
      minscore=min(scores.values( ))
      return dict([(u,float(minscore)/max(vsmall,l)) for (u,l) \
        in scores.items( )])
    else:
      maxscore=max(scores.values( ))
      if maxscore==0: maxscore=vsmall
      return dict([(u,float(c)/maxscore) for (u,c) in scores.items( )])

  def frequencyscore(self,rows):
    counts=dict([(row[0],0) for row in rows])
    for row in rows: counts[row[0]]+=1
    return self.normalizescores(counts)

  def locationscore(self,rows):
    locations=dict([(row[0],1000000) for row in rows])
    for row in rows:
      loc=sum(row[1:])
      if loc<locations[row[0]]: locations[row[0]]=loc
    return self.normalizescores(locations,smallIsBetter=1)
  
  def distancescore(self,rows):
    # If there's only one word, everyone wins!
    if len(rows[0])<=2: return dict([(row[0],1.0) for row in rows])

    # Initialize the dictionary with large values
    mindistance=dict([(row[0],1000000) for row in rows])
    
    for row in rows:
      dist=sum([abs(row[i]-row[i-1]) for i in range(2,len(row))])
      if dist<mindistance[row[0]]: mindistance[row[0]]=dist
    return self.normalizescores(mindistance,smallIsBetter=1)

  def inboundlinkscore(self,rows):
    uniquerequirements=set([row[0] for row in rows])
    inboundcount=dict([(u,self.con.execute( \
      'select count(*) from link where toid=%d' % u).fetchone( )[0]) \
      for u in uniquerequirements])
    return self.normalizescores(inboundcount)

  def pagerankscore(self,rows):
    requirementranks=dict([(row[0],self.con.execute('select score from requirementrank where requirementid=%d' % row[0]).fetchone( )[0]) for row in rows])
    maxrank=max(requirementranks.values( ))
    normalizedscores=dict([(u,float(l)/maxrank) for (u,l) in requirementranks.items( )])
    return normalizedscores

  def linktextscore(self,rows,wordids):
    linkscores=dict([(row[0],0) for row in rows])
    for wordid in wordids:
      cur=self.con.execute('select link.fromid,link.toid from linkwords,link where wordid=%d and linkwords.requirementid=link.rowid' % wordid)
      for (fromid,toid) in cur:
        if toid in linkscores:
          pr=self.con.execute('select score from requirementrank where requirementid=%d' % fromid).fetchone( )[0]
          linkscores[toid]+=pr
    maxscore=max(linkscores.values( ))
    # Added fix for some cases in which maxscore is 0
    # i.e all linkscores are 0 and no need to normalise
    # Bigger KB with more cross links may not need it
    if maxscore != 0:
      normalizedscores=dict([(u,float(l)/maxscore) for (u,l) in linkscores.items( )])
      return normalizedscores
    else:
      return linkscores
