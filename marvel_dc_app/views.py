from django.shortcuts import render
from django.shortcuts import render, redirect
from SPARQLWrapper import SPARQLWrapper, JSON
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

namespace = "kb"
# set host pake url blazegraph local/remote
host = "http://10.5.88.151:9999/"
sparql = SPARQLWrapper(f"{host}bigdata/namespace/"+ namespace + "/sparql")
sparql.setReturnFormat(JSON)


@csrf_exempt
def search_result(request):
    response = {}
    search = request.POST['search']
    search = search.lower()

    sparql.setQuery(f"""
    prefix :      <{host}>
    prefix owl:   <http://www.w3.org/2002/07/owl#>
    prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    prefix vcard: <http://www.w3.org/2006/vcard/ns#>
    prefix wd:    <http://www.wikidata.org/entity/>
    prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?film_wiki_uri ?film_name ?year ?film_type ?runtime ?mpa_rating ?desc ?crit_cons ?director (group_concat(distinct ?star;separator=", ") as ?stars) (group_concat(distinct ?distributor;separator=", ") as ?distributors) (group_concat(distinct ?genre;separator=", ") as ?genres) ?imdb_gross ?imdb_rating ?imdb_votes ?tom_aud_score ?tom_ratings ?tomato_meter ?tomato_review 
    WHERE{{
        ?film_wiki_uri rdf:type :Film;
                        rdfs:label ?film_name .
        FILTER contains(LCASE(?film_name),"%s")
        ?film_wiki_uri :year ?year; 
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
                       :tomato_review ?tomato_review.
        
        ?film_wiki_uri :genre ?genre .
        ?film_wiki_uri :distributed_by ?distributor .
        ?film_wiki_uri :stars ?star_wiki_uri .
        
        ?director_wiki_uri rdfs:label ?director.
        
        ?star_wiki_uri rdfs:label ?star.
        
    }}
    GROUP BY ?film_wiki_uri ?film_name ?year ?film_type ?runtime ?mpa_rating ?desc ?crit_cons ?director ?imdb_gross ?imdb_rating ?imdb_votes ?tom_aud_score ?tom_ratings ?tomato_meter ?tomato_review 
	ORDER BY ?film_name
    """ % search)

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
    prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?film_name 
    WHERE{{
        ?film rdf:type :Film;
                rdfs:label ?film_name .
    }}
    """)
    results_2 = sparql.query().convert()
    data_2 = results_2["results"]["bindings"]
    similar_res = {}
    for i in range(len(data_2)):
        ratio = fuzz.ratio(search, data_2[i]["film_name"]["value"].lower())
    if ratio >= 50:
        similar_res[data_2[i]["player_name"]["value"]] = ratio

    sorted_similar = sorted(similar_res.items(), key=lambda x:x[1], reverse=True)
    if len(sorted_similar) > 5:
        sorted_similar = sorted_similar[0:5]

    for i in range(0, len(sorted_similar)):
        for j in sorted_similar[i]:
            if (type(j) == str):
                sorted_similar[i] = j

    response['similar'] = sorted_similar
    
    response['search'] = request.POST['search']
    
    # return render(request, 'search_result.html', response)

    return JsonResponse(response, status=200)

def index(request):
    return render(request, 'index.html')

def search_result_person(request):
    response = {}
    return render(request, 'search_person.html', response)

def search_result_film(request):
    response = {}
    return render(request, 'search_film.html', response)


@csrf_exempt
def get_film_detail(request):
    response = {}
    film_wiki_uri = request.POST['film_wiki_uri']
    film_wiki_uri = film_wiki_uri.replace("http://www.wikidata.org/entity/", "wd:")

    sparql.setQuery(f"""
      prefix :      <{host}>
      prefix owl:   <http://www.w3.org/2002/07/owl#>
      prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
      prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
      prefix vcard: <http://www.w3.org/2006/vcard/ns#>
      prefix wd:    <http://www.wikidata.org/entity/>
      prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?film_name ?year ?film_type ?runtime ?mpa_rating ?desc ?crit_cons ?director (group_concat(distinct ?star;separator=", ") as ?stars) (group_concat(distinct ?distributor;separator=", ") as ?distributors) (group_concat(distinct ?genre;separator=", ") as ?genres) ?imdb_gross ?imdb_rating ?imdb_votes ?tom_aud_score ?tom_ratings ?tomato_meter ?tomato_review
    WHERE{{
        {film_wiki_uri} rdf:type :Film;
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
    GROUP BY ?film_name ?year ?film_type ?runtime ?mpa_rating ?desc ?crit_cons ?director ?imdb_gross ?imdb_rating ?imdb_votes ?tom_aud_score ?tom_ratings ?tomato_meter ?tomato_review 
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    response['data'] = results["results"]["bindings"]
    # return render(request, 'player_detail.html', response)
    return JsonResponse(response, status=200)