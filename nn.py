from math import tanh
from sqlite3 import dbapi2 as sqlite

#function to calculate slope of the tan function for any output value
def dtanh(y):
    return 1.0-y*y

class searchnet:
    def __init__(self,dbname):
      self.con=sqlite.connect(dbname)
  
    def __del__(self):
      self.con.close()

    # method that creates the tables of the nn
    def maketables(self):
      self.con.execute('create table hiddennode(create_key)')
      self.con.execute('create table wordhidden(fromid,toid,strength)')
      self.con.execute('create table hiddenreq(fromid,toid,strength)')
      self.con.commit()

    # method that determines the current strength of a connection
    def getstrength(self,fromid,toid,layer):
      if layer==0: table='wordhidden'
      else: table='hiddenreq'
      res=self.con.execute('select strength from %s where fromid=%d and toid=%d' % (table,fromid,toid)).fetchone()
      if res==None: 
          if layer==0: return -0.2
          if layer==1: return 0
      return res[0]

    # method to determine if a connection already exists, and to update or create
    # the connection with the new strength
    def setstrength(self,fromid,toid,layer,strength):
      if layer==0: table='wordhidden'
      else: table='hiddenreq'
      res=self.con.execute('select rowid from %s where fromid=%d and toid=%d' % (table,fromid,toid)).fetchone()
      if res==None: 
        self.con.execute('insert into %s (fromid,toid,strength) values (%d,%d,%f)' % (table,fromid,toid,strength))
      else:
        rowid=res[0]
        self.con.execute('update %s set strength=%f where rowid=%d' % (table,strength,rowid))

    # method that creates a new node in the hidden layer every time it is passed
    # a combination of words that it has never seen together before. 
    def generatehiddennode(self,wordids,requirements):
      if len(wordids)>3: return None
      # Check if we already created a node for this set of words
      sorted_words=[str(id) for id in wordids]
      sorted_words.sort()
      createkey='_'.join(sorted_words)
      res=self.con.execute(
      "select rowid from hiddennode where create_key='%s'" % createkey).fetchone()

      # If not, create it
      if res==None:
        cur=self.con.execute(
        "insert into hiddennode (create_key) values ('%s')" % createkey)
        hiddenid=cur.lastrowid
        # Put in some default weights
        for wordid in wordids:
          self.setstrength(wordid,hiddenid,0,1.0/len(wordids))
        for reqid in requirements:
          self.setstrength(hiddenid,reqid,1,0.1)
        self.con.commit()

    # method that finds all the nodes from the hidden layer that are relevant to
    # a specific query
    def getallhiddenids(self,wordids,reqids):
      l1={}
      for wordid in wordids:
        cur=self.con.execute(
        'select toid from wordhidden where fromid=%d' % wordid)
        for row in cur: l1[row[0]]=1
      for reqid in reqids:
        cur=self.con.execute(
        'select fromid from hiddenreq where toid=%d' % reqid)
        for row in cur: l1[row[0]]=1
      return l1.keys()

    # method for constructing the relevant network with all the current weights
    # from the database
    def setupnetwork(self,wordids,reqids):
        # value lists
        self.wordids=wordids
        self.hiddenids=self.getallhiddenids(wordids,reqids)
        self.reqids=reqids
 
        # node outputs
        self.ai = [1.0]*len(self.wordids)
        self.ah = [1.0]*len(self.hiddenids)
        self.ao = [1.0]*len(self.reqids)
        
        # create weights matrix
        self.wi = [[self.getstrength(wordid,hiddenid,0) 
                    for hiddenid in self.hiddenids] 
                   for wordid in self.wordids]
        self.wo = [[self.getstrength(hiddenid,reqid,1) 
                    for reqid in self.reqids] 
                   for hiddenid in self.hiddenids]

    # method that takes a list of inputs, pushes them through the network, and
    # returns the output of all the nodes in the output layer    
    def feedforward(self):
        # the only inputs are the query words
        for i in range(len(self.wordids)):
            self.ai[i] = 1.0

        # hidden activations
        for j in range(len(self.hiddenids)):
            sum = 0.0
            for i in range(len(self.wordids)):
                sum = sum + self.ai[i] * self.wi[i][j]
            self.ah[j] = tanh(sum)

        # output activations
        for k in range(len(self.reqids)):
            sum = 0.0
            for j in range(len(self.hiddenids)):
                sum = sum + self.ah[j] * self.wo[j][k]
            self.ao[k] = tanh(sum)

        return self.ao[:]

    # method to set up the network and use feedforward to get the outputs for a
    # set of words and requirements
    def getresult(self,wordids,reqids):
      self.setupnetwork(wordids,reqids)
      return self.feedforward()
    
    # backpropagation:  the method moves backward through the network adjusting
    # the weights
    def backPropagate(self, targets, N=0.5):
        # calculate errors for output
        output_deltas = [0.0] * len(self.reqids)
        for k in range(len(self.reqids)):
            error = targets[k]-self.ao[k]
            output_deltas[k] = dtanh(self.ao[k]) * error

        # calculate errors for hidden layer
        hidden_deltas = [0.0] * len(self.hiddenids)
        for j in range(len(self.hiddenids)):
            error = 0.0
            for k in range(len(self.reqids)):
                error = error + output_deltas[k]*self.wo[j][k]
            hidden_deltas[j] = dtanh(self.ah[j]) * error

        # update output weights
        for j in range(len(self.hiddenids)):
            for k in range(len(self.reqids)):
                change = output_deltas[k]*self.ah[j]
                self.wo[j][k] = self.wo[j][k] + N*change

        # update input weights
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                change = hidden_deltas[j]*self.ai[i]
                self.wi[i][j] = self.wi[i][j] + N*change

    # method that will set up the network, run feedforward, and run the
    # backpropagation
    def trainquery(self,wordids,reqids,selectedreq): 
      # generate a hidden node if necessary
      self.generatehiddennode(wordids,reqids)

      self.setupnetwork(wordids,reqids)      
      self.feedforward()
      targets=[0.0]*len(reqids)
      targets[reqids.index(selectedreq)]=1.0
      error = self.backPropagate(targets)
      self.updatedatabase()

    def updatedatabase(self):
      # set them to database values
      for i in range(len(self.wordids)):
          for j in range(len(self.hiddenids)):
              self.setstrength(self.wordids[i],self. hiddenids[j],0,self.wi[i][j])
      for j in range(len(self.hiddenids)):
          for k in range(len(self.reqids)):
              self.setstrength(self.hiddenids[j],self.reqids[k],1,self.wo[j][k])
      self.con.commit()
