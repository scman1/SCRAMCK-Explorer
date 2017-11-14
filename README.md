# SCRAMCK-Explorer
Prototype RE Tool for Requirements Management

Current status: 

  Searching a term list like the following guives the results below
     terms=['metadata catalogue','metadata', 'catalogue', "cataloguing", "data"]
  
    metadata catalogue "exact match top"
        3.000000	Data Cataloguing
    metadata "or"
        3.000000	Metadata Registration
        2.666667	Metadata Harvesting
        1.666667	Data Cataloguing
        1.333333	Data Processing
        1.333333	Data Curation
        1.333333	Data Storage and Preservation
        1.333333	Data Versioning
        1.333333	Real-Time Data Collection
        1.333333	Data Collection
    catalogue "or"
        3.000000	Instrument Configuration
        3.000000	Instrument Integration
        2.241379	Data Cataloguing
    cataloguing "steming (inverse)"
        4.000000	Data Cataloguing
    data "related term (too wide)"
        3.000000	Data Processing
        3.000000	Data Curation
        3.000000	Data Extraction
        3.000000	Data Analysis
        3.000000	Data Discovery and Access
        3.000000	Data Publication
        3.000000	Data Conversion
        3.000000	Data Storage and Preservation
        3.000000	Data Versioning
        3.000000	Data Product Generation
        
        
Next Steps:
  SearchEngine:

    Generate neural network and test queries
    Add stemming to retrieve closely related terms
    Improve requirements class to facilitate access to requirements attributes
    Map attributes to ENVRI RM terms using OIL-E
    Include links to ENVRI RM in search results

  ENVRIplus requirements

    use them as queries to the current Requirements base to check how well we did
    use them to expand the CK spaces
      standardise them as EARS
      add them to the requirements base indexing
   ***use their manual alignments to train the nn. Really relevant. Also using the NN to map to OIL-E and RM

  UI

    Create django ui to submit queries
    Use requirement IDs as links to display results
    where appropriate, rewrite as MVC 
 