import csv
import datetime
import csvloader
import searchengine
import nn

# object for querying requirements database
searcher=searchengine.searcher('reqindex.db')
# object for mapping requirements
mapper=csvloader.csvloader('reqindex.db')
# object for neural network training
neuralnet=nn.searchnet('nn_02.db')


# build nn tables
neuralnet.maketables()

# file source of new requirements
sourcefile="requirementsenvri02.csv"



# Read CSV file line by line


# detect and ignore header
inputfile = open(sourcefile, "r")
has_header = csv.Sniffer().has_header(inputfile.read(1024))
inputfile.seek(0)  # rewind
reader= csv.reader(inputfile)
if has_header:
  next(reader)  # skip header row
correct = 0
incorrect = 0
nomatch = 0
#bad mappings
badmapping={}
print(datetime.datetime.now().time())
for row in reader:
  # from each row extract the terms to search for and the
  # requirement it to which they were matched
  print "Query = %s;" % str(row[2])
  term=str(row[2])
  reqid=str(row[6])
  # Try to finf a match in ENVRI requirements
  queryresult = searcher.query(term)
  # if match found add terms to NN
  if queryresult!=None and reqid in queryresult:
    #the mapping was correct add to nn
    correct+=1
    # get the word ids
    wordids = mapper.getwordids(term)
    #get the id of the selected requirement
    selectedreq = queryresult[reqid][0]
    #get top ten ids of the results
    topscored=[]
    rankedscores=sorted([(items[1],items[0]) for (reqid,items) in queryresult.items( )],reverse=1)
    for (score,reqid) in rankedscores[0:10]:
      topscored.append(reqid)
    # if the selected requirement is not in the top ten then just add it to the list
    if not selectedreq in topscored:
      topscored.append(selectedreq)
    # print row
    # print rankedscores
    print topscored
    print selectedreq
    print wordids
    neuralnet.trainquery(wordids,topscored,selectedreq)
    x=neuralnet.getresult(wordids,topscored)
    print x
    #print queryresult
    
  elif queryresult!=None:
    #print "mapping did not match search results"
    # if no match found ask if:
    # a) mapping to named requirement in input
    # b) map to another requirement
    # c) add as new requirement
    # d) ignore
    # e) end
    incorrect+=1
    badmapping[str(row[0])+" "+str(row[3])]=row
  else:
    # if no match found ask if:
    # a) mapping to named requirement in input
    # b) map to another requirement
    # c) add as new requirement
    # d) ignore
    # e) end
    #print "no match found for query"#\n Options:"
    nomatch+=1
##    print "a) force map to requirement %s" % reqid
##    print "b) map to another requirement"
##    print "c) add as new requirement"
##    print "d) move to next"
##    print "e) end"
##    print "Enter option (a, b, c, d): "
##    char = raw_input() # User input

##    if char.lower() =="y":
##      print "adding new requirement ABCD"
##    elif char.lower() =="e":
##      print "END MAPPING"
##      inputfile.close
##      break
print "correctly mapped term searches: %i" % correct
print "incorrectly mapped term searches: %i" % incorrect
print "no match found: %i" % nomatch

print(datetime.datetime.now().time())
print badmapping
