import searchengine
import datetime
e=searchengine.searcher('reqindex.db')

def test1():
    csvloader=searchengine.csvloader('reqindex.db')
    csvloader.createindextables()
    sourcefile="requirementsenvri01.csv"
    csvloader.readcsv(sourcefile)
    [row for row in csvloader.con.execute('select rowid from wordlocation where wordid=1')]

def test2():
    matches=e.getmatchrows('metadata catalogue')
    print matches
    #([(83, 1769), (101, 67), (101, 69), (101, 131)], [19504])
    rows = matches [0]
    cursor = e.con.cursor()
    print rows[0][0]
    print "this is the word ID: "+ str(matches[1][0])
    print "this is the word:    " + str(cursor.execute("SELECT word FROM wordlist WHERE rowid='%s';" % str(matches[1][0])).fetchone()[0])

    docids=[]
    for x in rows:
        if not x[0] in docids:
          docids.append(x[0])
          
    print docids

    for x in docids:    
        print "This is the requirement ID :" + str(x)
        cursor.execute("SELECT requirement FROM requirementlist WHERE rowid=%s;" % str(x))
        wordlocs=cursor.fetchall()
        print wordlocs

def test3():
    csvloader=searchengine.csvloader('reqindex.db')
    csvloader.calculatepagerank()

        
def test4():
  terms=['metadata catalogue','metadata', 'catalogue', "cataloguing", "data"]
  for term in terms:
      print term
      e.query(term)
##    metadata catalogue "exact match top"
##        3.000000	Data Cataloguing
##    metadata "or"
##        3.000000	Metadata Registration
##        2.666667	Metadata Harvesting
##        1.666667	Data Cataloguing
##        1.333333	Data Processing
##        1.333333	Data Curation
##        1.333333	Data Storage and Preservation
##        1.333333	Data Versioning
##        1.333333	Real-Time Data Collection
##        1.333333	Data Collection
##    catalogue "or"
##        3.000000	Instrument Configuration
##        3.000000	Instrument Integration
##        2.241379	Data Cataloguing
##    cataloguing "steming (inverse)"
##        4.000000	Data Cataloguing
##    data "related term (too wide)"
##        3.000000	Data Processing
##        3.000000	Data Curation
##        3.000000	Data Extraction
##        3.000000	Data Analysis
##        3.000000	Data Discovery and Access
##        3.000000	Data Publication
##        3.000000	Data Conversion
##        3.000000	Data Storage and Preservation
##        3.000000	Data Versioning
##        3.000000	Data Product Generation
      
# Next Steps:
# SearchEngine:
#   Generate neural network and test queries
#   Add stemming to retrieve closely related terms
#   Improve requirements class to facilitate access to requirements attributes
#
# ENVRIplus requirements
#   use them as queries to the current Requirements base to check how well we did
#   use them to expand the CK spaces
#     standardise them as EARS
#     add them to the requirements base indexing
#   use their manual alignments to train the algorithm:
#
# UI
#   Create django ui to submit queries
#   Use requirement IDs as links to display results
#   where appropriate, rewrite as MVC 

def test5():
  # This search has only one term and sends a search request for every separate word in the query
  #ignorewords=set(['the','of','to','and','a','in','is','it'])  
  #terms=['the metadata catalogue,', 'data harmonisation','to improve their interoperability so as to make their data as accessible and understandable as possible to others,']
  print(datetime.datetime.now().time())
  terms=['to improve their interoperability so as to make their data as accessible and understandable as possible to others,']
  for term in terms: terms.extend(term.split(' ')) if ' ' in term else None
  for term in terms:
      print term
      e.query(term)
  print(datetime.datetime.now().time())    
      
def build_nn():
    import nn
    mynet=nn.searchnet('nn.db')
    mynet.maketables( )
    wWorld,wRiver,wBank =101,102,103
    uWorldBank,uRiver,uEarth =201,202,203
    mynet.generatehiddennode([wWorld,wBank],[uWorldBank,uRiver,uEarth])
    for c in mynet.con.execute('select * from wordhidden'): print c
    for c in mynet.con.execute('select * from hiddenurl'): print c

def test6():
    import nn
    #static word ids for testing
    wWorld,wRiver,wBank =101,102,103
    uWorldBank,uRiver,uEarth =201,202,203
    mynet=nn.searchnet('nn.db')
    x = mynet.getresult([wWorld,wBank],[uWorldBank,uRiver,uEarth])
    print x

#print ("**********TEST 1***********")
#test1()

#print ("**********TEST 2***********")
#test2()

#print ("**********TEST 3***********")
#test3()

print ("**********TEST 4***********")
#test4()
test5()

##print ("**********Build Neural Network***********")
##build_nn()

##print ("**********TEST 6 NN***********")
##test5()
