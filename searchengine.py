import urllib2
import csv
from BeautifulSoup import *
from urlparse import urljoin
from sqlite3 import dbapi2 as sqlite

# Create a list of words to ignore
ignorewords=set(['the','of','to','and','a','in','is','it'])

class csvloader:
  # Initialize the csv loader with the name of database
  # p. 75
  def __init__(self,dbname):
    self.con=sqlite.connect(dbname)
  def __del__(self):
    self.con.close( )
  def dbcommit(self):
    self.con.commit( )

  # Create the database tables for storing requirements and requirement relations
  def createindextables(self):
    self.con.execute('create table requirementlist(requirementid,requirement,description,earsdescription)')
    self.con.execute('create table wordlist(word)')
    self.con.execute('create table wordlocation(requirementid,wordid integer,location integer)')
    self.con.execute('create table link(fromid integer,toid integer)')
    self.con.execute('create table linkwords(wordid,requirementid)')
    self.con.execute('create index wordidx on wordlist(word)')
    self.con.execute('create index requirementidx on requirementlist(requirementid)')
    self.con.execute('create index wordrequirementidx on wordlocation(wordid)')
    self.con.execute('create index requirementtoidx on link(toid)')
    self.con.execute('create index requirementfromidx on link(fromid)')
    self.dbcommit( )

 # read each row in the csv file and store in the DB
  def readcsv(self, inputfile):
    inputfile = open(inputfile, "r")
    # Requirements file structure
    # Header row:
    # 0 NUM           int    
    # 1 ID            string  requirementslist.requirementid
    # 2 Requirement   string  requirementslist.requirement
    # 3 Definition    string  requirementslist.description
    # 4 MinimumModel  boolean
    # 5 Rewrite 1     string
    # 6 Parent        string  link to parent feature
    # 7 Type          string
    # 8 Use example   string
    # 9 Problems      string
    #10 Cataloguing   string
    #11 EARSdesc      string requirementslist.earsdescription
    #12 Reason        string
    # detect and ignore header
    has_header = csv.Sniffer().has_header(inputfile.read(1024))
    inputfile.seek(0)  # rewind
    reader= csv.reader(inputfile)
    if has_header:
       next(reader)  # skip header row
    for row in reader:
      # from each row extract reqid,req,reqdesc,and earsrecdesc
      # and add them as requirements
      self.addrequirement(row[1], row[2], row[3], row[11])
    #rewind and add relationships to create requirements hierarchy
    inputfile.seek(0)  # rewind
    reader= csv.reader(inputfile)  
    if has_header:
       next(reader)  # skip header row
    for row in reader:
      # from each row extract reqid,req,reqdesc,and earsrecdesc
      # and add them as requirements
      self.addlinkref(row[6], row[1], row[2])
      print 'Indexing '+ row[1] + " " + row[2]
      self.dbcommit( )
      
  # Index an individual requirement
  def addrequirement(self,requirementid,requirement,description,earsdescription):
    if self.isindexed(requirementid): return
    print 'Indexing '+ requirementid + " " + requirement
    # Get the individual words
    words=self.separatewords(earsdescription)
    cur=self.con.execute("insert into requirementlist (requirementid,requirement,description,earsdescription)\
      values('%s','%s','%s','%s')" % (requirementid,requirement,description,earsdescription))
    reqid=cur.lastrowid
    # Link each word in the EARS description to this requirement
    for i in range(len(words)):
      word=words[i]
      if word in ignorewords: continue
      wordid=self.getentryid('wordlist','word',word)
      self.con.execute("insert into wordlocation(requirementid,wordid,location) \
        values (%d,%d,%d)" % (reqid,wordid,i))
    self.dbcommit( )
  
  # Auxilliary function for getting an entry id and adding
  # it if it's not present
  def getentryid(self,table,field,value,createnew=True):
    cur=self.con.execute(
    "select rowid from %s where %s='%s'" % (table,field,value))
    res=cur.fetchone( )
    if res==None:
      cur=self.con.execute(
      "insert into %s (%s) values ('%s')" % (table,field,value))
      return cur.lastrowid
    else:
      return res[0]
      
  # Separate the words by any non-whitespace character
  def separatewords(self,text):
    splitter=re.compile('\\W*')
    return [s.lower( ) for s in splitter.split(text) if s!='']

  # Return true if this requirement is already indexed
  def isindexed(self,page):
    u=self.con.execute \
      ("select rowid from requirementlist where requirementid='%s'" % page).fetchone( )
    if u!=None:
      # Check if it has actually been crawled
      v=self.con.execute(
      'select * from wordlocation where requirementid=%d' % u[0]).fetchone( )
      if v!=None: return True
    return False
  
  # Add a link between two pages
  def addlinkref(self,urlFrom,urlTo,linkText):
    words=self.separatewords(linkText)
    fromid=self.getentryid('requirementlist','requirementID',urlFrom)
    toid=self.getentryid('requirementlist','requirementID',urlTo)
    if fromid==toid: return
    cur=self.con.execute("insert into link(fromid,toid) values (%d,%d)" % (fromid,toid))
    linkid=cur.lastrowid
    for word in words:
      if word in ignorewords: continue
      wordid=self.getentryid('wordlist','word',word)
      self.con.execute("insert into linkwords(requirementid,wordid) values (%d,%d)" % (linkid,wordid))  

  # page rank is called only once
  # ideally after crawling
  def calculatepagerank(self,iterations=20):
    # clear out the current RequirementRank tables
    self.con.execute('drop table if exists requirementrank')
    self.con.execute('create table requirementrank(requirementid primary key,score)')
    
    # initialize every requirement with a rank of 1
    self.con.execute('insert into requirementrank select rowid, 1.0 from requirementlist')
    self.dbcommit( )
    
    for i in range(iterations):
      print "Iteration %d" % (i)
      for (urlid,) in self.con.execute('select rowid from requirementlist'):
        pr=0.15
        
        # Loop through all the pages that link to this one
        for (linker,) in self.con.execute(
        'select distinct fromid from link where toid=%d' % urlid):
          # Get the Rank of the linker
          linkingpr=self.con.execute(
          'select score from requirementrank where requirementid=%d' % linker).fetchone( )[0]
          
          # Get the total number of links from the linker
          linkingcount=self.con.execute(
          'select count(*) from link where fromid=%d' % linker).fetchone( )[0]
          pr+=0.85*(linkingpr/linkingcount)
        self.con.execute(
        'update requirementrank set score=%f where requirementid=%d' % (pr,urlid))
      self.dbcommit( )
  
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
    
    # Split the words by spaces
    words=q.split(' ')
    tablenumber=0
    for word in words:
      if word in ignorewords: continue
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
      for url in totalscores:
        totalscores[url]+=weight*scores[url]
    return totalscores
  
  def getrequirementname(self,id):
    return self.con.execute(
      "select requirement from requirementlist where rowid=%d" % id).fetchone( )[0]

  def getrequirementidentifier(self,id):
    return self.con.execute(
      "select requirementid from requirementlist where rowid=%d" % id).fetchone( )[0]
  
  def query(self,q):
    rows, wordids = self.getmatchrows(q)
    if (rows != []) & (wordids != []):
      scores=self.getscoredlist(rows,wordids)
      rankedscores=sorted([(score,url) for (url,score) in scores.items( )],reverse=1)
      for (score,reqid) in rankedscores[0:10]:
        print '%f\t%d\t%s\t%s' % (score,reqid,self.getrequirementidentifier(reqid),self.getrequirementname(reqid))

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
    uniqueurls=set([row[0] for row in rows])
    inboundcount=dict([(u,self.con.execute( \
      'select count(*) from link where toid=%d' % u).fetchone( )[0]) \
      for u in uniqueurls])
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
