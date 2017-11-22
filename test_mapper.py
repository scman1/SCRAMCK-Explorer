import csvloader

print ("**********MAPPING WORDS***********")
mapper=csvloader.csvloader('reqindex.db')
sourcefile="requirementsenvri02.csv"
mapper.readdata(sourcefile)
