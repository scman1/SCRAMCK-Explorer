import csv
import csvloader
import searchengine
# class for querying requirements database
searcher=searchengine.searcher('reqindex.db')
# class for mapping requirements
mapper=csvloader.csvloader('reqindex.db')
# fike source of new requirements
sourcefile="requirementsenvri02.csv"

# Read CSV file line by line

# detect and ignore header
inputfile = open(sourcefile, "r")
has_header = csv.Sniffer().has_header(inputfile.read(1024))
inputfile.seek(0)  # rewind
reader= csv.reader(inputfile)
if has_header:
  next(reader)  # skip header row
for row in reader:
  # from each row extract reqid,req,reqdesc,and earsrecdesc
  # and add them as requirements
  print "Query = %s;" % str(row[2])
  term=str(row[2])
  # Try to finf a match in ENVRI requirements
  print term
  searcher.query(term)
  # if match found add terms to NN 

  # if no match found ask if:
  # a) mapping to named requirement in input
  # b) map to another requirement
  # c) add as new requirement
  # d) ignore
  # 
  print "no match found for query %s Options:" % str(row[6])
  print "a) map to requirement ABCDmapp"
  print "b) map to another requirement"
  print "c) add as new requirement"
  print "d) move to next"
  print "e) end"

  print "Enter option (a, b, c, d): "
  char = raw_input() # User input

  if char.lower() =="y":
    print "adding new requirement ABCD"
  elif char.lower() =="e":
    print "END MAPPING"
    inputfile.close
    break

