'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Command to run a query against an example query against an ontology and return results. 

'''

from pathlib import Path
import rdflib

'''
    query() runs the query based on the queryInput from the user's command call.
'''
def query(queryInput = ""):
    
    #Instantiate the RDF Graph
    g = rdflib.Graph()
    results = []
    
    #Adding RDF triples to the graph
    g.parse(str(Path(__file__).parent.parent.parent.parent) + "/resources/rdf/AirCrash.rdf")

    #Query execution, under development for customization
    queryResults = g.query(
    """
    PREFIX crash: <http://www.semanticweb.org/theaviationmaniac/ontologies/2017/11/untitled-ontology-32#>
    SELECT DISTINCT ?eventid ?location
    WHERE
    {
        ?aircrash crash:hasEventID ?eventid.
        ?aircrash crash:hasLocation ?location.
        FILTER regex(?location, "Newark, NJ" )
    }
    """)
    
    for row in queryResults:
        results.append("Event #" + row[0] + "occured in " + row[1] + "\n")
        
    return '\n'.join(results)
