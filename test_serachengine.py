import searchengine
e=searchengine.searcher('reqindex.db')

def test1():
    crawler=searchengine.crawler('reqindex.db')
    crawler.createindextables()
    sourcefile="requirementsenvri01.csv"
    crawler.readcsv(sourcefile)
    [row for row in crawler.con.execute('select rowid from wordlocation where wordid=1')]

def test2():
    matches=e.getmatchrows('agile software development')
    #matches=e.getmatchrows('functional programming')
    #matches=e.getmatchrows('functional programming language')
    #matches=e.getmatchrows('programming languages')
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
        print "This is the doc ID :" + str(x)
        cursor.execute("SELECT url FROM urllist WHERE rowid=%s;" % str(x))
        wordlocs=cursor.fetchall()
        print wordlocs
        
def test3():
  terms=['functional programming','functional programming language', 'programming language', "agile software development"]
  for term in terms:
      print term
      e.query(term)

def test4():
    crawler=searchengine.crawler('searchindex2.db')
    crawler.calculatepagerank()

def build_nn():
    import nn
    mynet=nn.searchnet('nn.db')
    mynet.maketables( )
    wWorld,wRiver,wBank =101,102,103
    uWorldBank,uRiver,uEarth =201,202,203
    mynet.generatehiddennode([wWorld,wBank],[uWorldBank,uRiver,uEarth])
    for c in mynet.con.execute('select * from wordhidden'): print c
    for c in mynet.con.execute('select * from hiddenurl'): print c

def test5():
    import nn
    #static word ids for testing
    wWorld,wRiver,wBank =101,102,103
    uWorldBank,uRiver,uEarth =201,202,203
    mynet=nn.searchnet('nn.db')
    x = mynet.getresult([wWorld,wBank],[uWorldBank,uRiver,uEarth])
    print x

print ("**********TEST 1***********")
test1()

##print ("**********TEST 2***********")
##test2()

##print ("**********TEST 3***********")
##test3()

#print ("**********TEST 4***********")
#test4()

##print ("**********Build Neural Network***********")
##build_nn()

##print ("**********TEST 5 NN***********")
##test5()
