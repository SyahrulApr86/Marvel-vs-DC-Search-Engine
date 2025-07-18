from django.shortcuts import render
from django.shortcuts import render, redirect
from SPARQLWrapper import SPARQLWrapper, JSON
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime
import os

repository = "kb"
# set host pake url GraphDB local/remote
# Gunakan environment variable atau fallback ke remote server
host = os.getenv('GRAPHDB_HOST', "http://localhost:7200/")
if not host.endswith('/'):
    host += '/'

# Namespace untuk data (sesuai dengan yang ada di RDF file)    
data_namespace = "http://192.168.31.138:9999/blazegraph/"
    
sparql = SPARQLWrapper(f"{host}repositories/"+ repository)
sparql.setReturnFormat(JSON)


@csrf_exempt
def search_result(request):
    response = {}
    start_time = datetime.now()
    totalTime = None

    if request.method == 'POST':
        search = request.POST.get('search', '').lower()
    elif request.method == 'GET':
        search = request.GET.get('search', '').lower()
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    if not search:
        return render(request, 'index.html', {'error_message': 'No search query'})

    sparql.setQuery(f"""
    prefix :      <{data_namespace}>
    prefix owl:   <http://www.w3.org/2002/07/owl#>
    prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    prefix vcard: <http://www.w3.org/2006/vcard/ns#>
    prefix wd:    <http://www.wikidata.org/entity/>
    prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?film_wiki_uri ?film_name ?year ?film_type
    WHERE{{
        ?film_wiki_uri rdf:type :Film;
                        rdfs:label ?film_name .
        FILTER contains(LCASE(?film_name),"%s")
        ?film_wiki_uri :year ?year; 
                       :entity ?film_type.
    }}
	ORDER BY ?film_name
    """ % search)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    response['data'] = results["results"]["bindings"]
    response['sumDocs'] = len(response['data'])
    # If there are no exact match results, try to find similar movies
    if not response['data']:
        sparql.setQuery(f"""
        prefix :      <{data_namespace}>
        prefix owl:   <http://www.w3.org/2002/07/owl#>
        prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
        prefix vcard: <http://www.w3.org/2006/vcard/ns#>
        prefix wd:    <http://www.wikidata.org/entity/>
        prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

        SELECT DISTINCT ?film_wiki_uri ?film_name ?year ?film_type
        WHERE{{
            ?film_wiki_uri rdf:type :Film;
                            rdfs:label ?film_name;
                            :year ?year; 
                            :entity ?film_type.
        }}
        """)
        results_2 = sparql.query().convert()
        data_2 = results_2["results"]["bindings"]
        similar_res = {}
        
        for i in range(len(data_2)):
            ratio = fuzz.ratio(search, data_2[i]["film_name"]["value"].lower())
            if ratio >= 50:
                similar_res[data_2[i]["film_name"]["value"]] = data_2[i]

        sorted_similar = sorted(similar_res.items(), key=lambda x: fuzz.ratio(search, x[0].lower()), reverse=True)
        if len(sorted_similar) > 5:
            sorted_similar = sorted_similar[0:5]

        response['similar'] = [movie[1] for movie in sorted_similar]
        response['sumDocs'] = len(response['similar'])
    
    response['search'] = request.POST['search']
    end_time = datetime.now()
    totalTime = end_time - start_time
    response['totalTime'] = totalTime
    
    
    return render(request, 'search_result.html', response)

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def get_film_detail(request):
    response = {}
    film_wiki_uri = request.POST['film_wiki_uri']

    sparql.setQuery(f"""
      prefix :      <{data_namespace}>
      prefix owl:   <http://www.w3.org/2002/07/owl#>
      prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
      prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
      prefix vcard: <http://www.w3.org/2006/vcard/ns#>
      prefix wd:    <http://www.wikidata.org/entity/>
      prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?film_name
    WHERE{{
        OPTIONAL {{<{film_wiki_uri}> rdf:type :Film;
                          rdfs:label ?film_name.}}
    }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if results["results"]["bindings"] == []:
        response["status_code"] = 404
        response["error_message"] = "URI not found in Marvel DC App Database"
        return render(request, 'film_details.html', response)
        # return JsonResponse(response, status=404)
    
    sparql.setQuery(f"""
      prefix :      <{data_namespace}>
      prefix owl:   <http://www.w3.org/2002/07/owl#>
      prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
      prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
      prefix vcard: <http://www.w3.org/2006/vcard/ns#>
      prefix wd:    <http://www.wikidata.org/entity/>
      prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?film_name ?year ?film_type ?runtime ?mpa_rating ?desc ?crit_cons ?director ?director_wiki_uri (group_concat(distinct ?star;separator=", ") as ?stars) (group_concat(distinct ?star_wiki_uri;separator=", ") as ?star_wiki_uris) (group_concat(distinct ?distributor;separator=", ") as ?distributors) (group_concat(distinct ?genre;separator=", ") as ?genres) ?imdb_gross ?imdb_rating ?imdb_votes ?tom_aud_score ?tom_ratings ?tomato_meter ?tomato_review
    WHERE{{
        <{film_wiki_uri}> rdf:type :Film;
                       rdfs:label ?film_name; 
                       :year ?year; 
                       :entity ?film_type; 
                       :runtime ?runtime;
                       :mpa_rating ?mpa_rating;
                       :description ?desc;
                       :crit_consensus ?crit_cons;
                       :director ?director_wiki_uri;
                       :imdb_gross ?imdb_gross;
                       :imdb_rating ?imdb_rating;
                       :imdb_votes ?imdb_votes;
                       :tom_aud_score ?tom_aud_score;
                       :tom_ratings ?tom_ratings;
                       :tomato_meter ?tomato_meter;
                       :tomato_review ?tomato_review;
                       :genre ?genre;
                       :distributed_by ?distributor;
                       :stars ?star_wiki_uri .
        
        ?director_wiki_uri rdfs:label ?director.
        
        ?star_wiki_uri rdfs:label ?star.
        
    }}
    GROUP BY ?film_name ?year ?film_type ?runtime ?mpa_rating ?desc ?crit_cons ?director ?director_wiki_uri ?imdb_gross ?imdb_rating ?imdb_votes ?tom_aud_score ?tom_ratings ?tomato_meter ?tomato_review 
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    response['data'] = results["results"]["bindings"]
    
    sparql.setQuery(f"""
    prefix :      <{host}>
    prefix owl:   <http://www.w3.org/2002/07/owl#>
    prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    prefix vcard: <http://www.w3.org/2006/vcard/ns#>
    prefix wd:    <http://www.wikidata.org/entity/>
    prefix wdt:   <http://www.wikidata.org/prop/direct/>
    prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT ?image ?awarded_for ?nominated_for 
    WHERE {{
        SERVICE <https://query.wikidata.org/sparql> {{
        {{
    select ?image (group_concat(distinct ?label_awards;separator=", ") as ?awarded_for) (group_concat(distinct ?label_nominations;separator=", ") as ?nominated_for)
    where {{
        OPTIONAL{{ <{film_wiki_uri}> wdt:P1411 ?nominations .
                    ?nominations rdfs:label ?label_nominations .
                    FILTER(lang(?label_nominations) = 'en')}}
        OPTIONAL{{ <{film_wiki_uri}> wdt:P166 ?awards .
                    ?awards rdfs:label ?label_awards .
                    FILTER(lang(?label_awards) = 'en')}}
        OPTIONAL{{ <{film_wiki_uri}> wdt:P154 ?image .}}
        }}
    GROUP BY ?image                                                               
        }}
        }}
    }}
    """)

    results = sparql.query().convert()
    response['data2'] = results["results"]["bindings"]
    return render(request, 'film_details.html', response)
    # return JsonResponse(response, status=200)

@csrf_exempt
def get_person_detail(request):
    response = {}
    person_wiki_uri = request.POST['person_wiki_uri']

    sparql.setQuery(f"""
      prefix :      <{data_namespace}>
      prefix owl:   <http://www.w3.org/2002/07/owl#>
      prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
      prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
      prefix vcard: <http://www.w3.org/2006/vcard/ns#>
      prefix wd:    <http://www.wikidata.org/entity/>
      prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?person_name
    WHERE{{
        OPTIONAL {{<{person_wiki_uri}> rdf:type :Star;
                          rdfs:label ?person_name.}}
                          
        OPTIONAL {{<{person_wiki_uri}> rdf:type :Director;
                          rdfs:label ?person_name.}}
    }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if results["results"]["bindings"] == []:
        response["status_code"] = 404
        response["error_message"] = "URI not found in Marvel DC App Database"
        return render(request, 'person_details.html', response)
        # return JsonResponse(response, status=404)
    
    sparql.setQuery(f"""
      prefix :      <{data_namespace}>
      prefix owl:   <http://www.w3.org/2002/07/owl#>
      prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
      prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
      prefix vcard: <http://www.w3.org/2006/vcard/ns#>
      prefix wd:    <http://www.wikidata.org/entity/>
      prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?person_name ?date_of_birth ?sex (group_concat(distinct ?nationality;separator=", ") as ?nationalities) (group_concat(distinct ?film_name;separator=", ") as ?associated_films) (group_concat(distinct ?film_wiki_uri;separator=", ") as ?associated_films_wiki_uri)
    WHERE{{
        <{person_wiki_uri}> rdfs:label ?person_name; 
                       :date_of_birth ?date_of_birth; 
                       :nationality ?nationality; 
                       :sex ?sex .
        
        OPTIONAL {{?film_wiki_uri :stars <{person_wiki_uri}> ;
                 				  rdf:type :Film;
                       	          rdfs:label ?film_name.}}
        OPTIONAL {{?film_wiki_uri :director <{person_wiki_uri}> ;
                 				  rdf:type :Film;
                       	          rdfs:label ?film_name.}}
        FILTER(bound(?film_wiki_uri))
    }}
    GROUP BY ?person_name ?date_of_birth ?sex
    LIMIT 1
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    response['data'] = results["results"]["bindings"]
    
    sparql.setQuery(f"""
    prefix :      <{data_namespace}>
    prefix owl:   <http://www.w3.org/2002/07/owl#>
    prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    prefix vcard: <http://www.w3.org/2006/vcard/ns#>
    prefix wd:    <http://www.wikidata.org/entity/>
    prefix wdt:   <http://www.wikidata.org/prop/direct/>
    prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT ?image ?net_worth ?occupations ?awarded_for ?nominated_for 
    WHERE {{
        SERVICE <https://query.wikidata.org/sparql> {{
        {{
    select ?image ?net_worth (group_concat(distinct ?label_occupation;separator=", ") as ?occupations) (group_concat(distinct ?label_awards;separator=", ") as ?awarded_for) (group_concat(distinct ?label_nominations;separator=", ") as ?nominated_for)
    where {{
                OPTIONAL{{ <{person_wiki_uri}> wdt:P106 ?occupation .
                    ?occupation rdfs:label ?label_occupation .
                    FILTER(lang(?label_occupation) = 'en')}}
        OPTIONAL{{ <{person_wiki_uri}> wdt:P1411 ?nominations .
                    ?nominations rdfs:label ?label_nominations .
                    FILTER(lang(?label_nominations) = 'en')}}
        OPTIONAL{{ <{person_wiki_uri}> wdt:P166 ?awards .
                    ?awards rdfs:label ?label_awards .
                    FILTER(lang(?label_awards) = 'en')}}
        OPTIONAL{{ <{person_wiki_uri}> wdt:P2218 ?net_worth .}}
        OPTIONAL{{ <{person_wiki_uri}> wdt:P18 ?image_raw .
                   BIND(REPLACE(STR(?image_raw), "http://commons.wikimedia.org/wiki/Special:FilePath/", "https://commons.wikimedia.org/wiki/File:") as ?image) }}
        }}
    GROUP BY ?image ?net_worth                                                         
        }}
        }}
    }}
    """)

    results = sparql.query().convert()
    response['data2'] = results["results"]["bindings"]
    return render(request, 'person_details.html', response)
    # return JsonResponse(response, status=200)