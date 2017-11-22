import csv
from BeautifulSoup import *
from sqlite3 import dbapi2 as sqlite

# Create a list of words to ignore
ignorewords=set(['the','of','to','and','a','in','is','it'])

class csvloader:
  # Initialize the csv loader with the name of database
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
  
#######################################################
# Mapping new definitions to existing requirements
# implies no extension but just mapping requirements to the existing base
# no new requirements are added
#######################################################
 # read each row in the csv file and store in the DB
  def readdata(self, sourcefile):
    inputfile = open(sourcefile, "r")
    # New requirements file sourcefile
    # Header row:
    #  0 ID              integer
    #  1 Source          string
    #  2 Description     string
    #  3 SourceDocP      integer
    #  4 type            string
    #  5 DLC             string
    #  6 ENVRIReqID      string
    #  7 Keyword         string
    #  8 Interpretation  string
    #  9 ENVRI concern   boolean
    # 10 Action          string
    # 11 Comment         string

    # detect and ignore header
    has_header = csv.Sniffer().has_header(inputfile.read(1024))
    inputfile.seek(0)  # rewind
    reader= csv.reader(inputfile)
    if has_header:
       next(reader)  # skip header row
    for row in reader:
      # from each row extract reqid,req,reqdesc,and earsrecdesc
      # and add them as requirements
      self.mapsearchwordtorequirement(row[6], row[2])

  # Map search words to requirements
  def mapsearchwordtorequirement(self,requirementid,description):
    if not self.isindexed(requirementid):
        print 'could not map: '+ description
        return
    print 'mapping:  '+ requirementid + " " + description
    # Get the individual words
    words=self.separatewords(description)
    reqid=self.getentryid('requirementlist','requirementid',requirementid)
    # Link each word in the description to the requirement
    for i in range(len(words)):
      word=words[i]
      if word in ignorewords: continue
      wordid=self.getentryid('wordlist','word',word)
      self.con.execute("insert into wordlocation(requirementid,wordid,location) \
        values (%d,%d,%d)" % (reqid,wordid,i))
    self.dbcommit( )



