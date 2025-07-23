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
data_namespace = os.getenv('RDF_NAMESPACE', "https://marveldc.rul.blue/")
    
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
    search_time = (end_time - start_time).total_seconds()
    response['search_time'] = search_time
    
    
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
    
    # Try to get cached image first for film details
    from .image_cache import image_cache
    cached_image = image_cache.get_cached_image(film_wiki_uri, 'film')
    
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
        OPTIONAL{{ <{film_wiki_uri}> wdt:P154 ?logo .}}
        OPTIONAL{{ <{film_wiki_uri}> wdt:P18 ?first_image .}}
        BIND(COALESCE(?logo, ?first_image) as ?image)
        }}
    GROUP BY ?image                                                               
        }}
        }}
    }}
    """)

    results = sparql.query().convert()
    
    # Cache the image URL if we fetched it and it wasn't cached
    if results["results"]["bindings"] and results["results"]["bindings"][0].get("image"):
        image_url = results["results"]["bindings"][0]["image"]["value"]
        if cached_image is None:
            image_cache.cache_image(film_wiki_uri, image_url, 'film')
    elif cached_image is None:
        image_cache.cache_image(film_wiki_uri, None, 'film')
        
    # Use cached image if available and query returned no image
    if cached_image and (not results["results"]["bindings"] or not results["results"]["bindings"][0].get("image")):
        if not results["results"]["bindings"]:
            results["results"]["bindings"] = [{}]
        results["results"]["bindings"][0]["image"] = {"value": cached_image}
    
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
    
    # Get person basic info
    sparql.setQuery(f"""
      prefix :      <{data_namespace}>
      prefix owl:   <http://www.w3.org/2002/07/owl#>
      prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
      prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
      prefix vcard: <http://www.w3.org/2006/vcard/ns#>
      prefix wd:    <http://www.wikidata.org/entity/>
      prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?person_name ?date_of_birth ?sex ?nationality
    WHERE {{
        <{person_wiki_uri}> rdfs:label ?person_name .
        OPTIONAL {{ <{person_wiki_uri}> :date_of_birth ?date_of_birth }}
        OPTIONAL {{ <{person_wiki_uri}> :sex ?sex }}
        OPTIONAL {{ <{person_wiki_uri}> :nationality ?nationality }}
    }}
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    response['data'] = results["results"]["bindings"]
    
    # Get associated films where person is either a star or director
    # Convert full URI to prefixed format if needed
    person_uri_for_query = person_wiki_uri
    if person_wiki_uri.startswith('http://www.wikidata.org/entity/'):
        # Extract the entity ID and use prefixed format
        entity_id = person_wiki_uri.split('/')[-1]
        person_uri_for_query = f"wd:{entity_id}"
    
    sparql.setQuery(f"""
      prefix :      <{data_namespace}>
      prefix owl:   <http://www.w3.org/2002/07/owl#>
      prefix rdf:   <http://www.w3.org/2000/01/rdf-syntax-ns#>
      prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
      prefix vcard: <http://www.w3.org/2006/vcard/ns#>
      prefix wd:    <http://www.wikidata.org/entity/>
      prefix xsd:   <http://www.w3.org/2001/XMLSchema#>

    SELECT (group_concat(distinct ?film_name;separator=", ") as ?associated_films) (group_concat(distinct ?film_wiki_uri;separator=", ") as ?associated_film_wiki_uris)
    WHERE {{
        {{
            ?film_wiki_uri rdf:type :Film;
                          rdfs:label ?film_name;
                          :stars {person_uri_for_query} .
        }}
        UNION
        {{
            ?film_wiki_uri rdf:type :Film;
                          rdfs:label ?film_name;
                          :director {person_uri_for_query} .
        }}
    }}
    """)
    
    sparql.setReturnFormat(JSON)
    films_results = sparql.query().convert()
    
    # Merge films data with person data
    if films_results["results"]["bindings"]:
        films_data = films_results["results"]["bindings"][0]
        if response['data']:
            response['data'][0].update(films_data)
        else:
            response['data'] = [films_data]
    
    # Check cache for person image first
    cached_person_image = image_cache.get_cached_image(person_wiki_uri, 'person')
    
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
                   BIND(REPLACE(STR(?image_raw), "http://commons.wikimedia.org/wiki/Special:FilePath/", "https://commons.wikimedia.org/wiki/Special:FilePath/") as ?image) }}
        }}
    GROUP BY ?image ?net_worth                                                         
        }}
        }}
    }}
    """)

    results = sparql.query().convert()
    
    # Cache person image if fetched and not already cached
    if results["results"]["bindings"] and results["results"]["bindings"][0].get("image"):
        person_image_url = results["results"]["bindings"][0]["image"]["value"]
        if cached_person_image is None:
            image_cache.cache_image(person_wiki_uri, person_image_url, 'person')
    elif cached_person_image is None:
        image_cache.cache_image(person_wiki_uri, None, 'person')
        
    # Use cached image if available and query returned no image
    if cached_person_image and (not results["results"]["bindings"] or not results["results"]["bindings"][0].get("image")):
        if not results["results"]["bindings"]:
            results["results"]["bindings"] = [{}]
        results["results"]["bindings"][0]["image"] = {"value": cached_person_image}
    
    response['data2'] = results["results"]["bindings"]
    return render(request, 'person_details.html', response)
    # return JsonResponse(response, status=200)

@csrf_exempt
def get_film_image(request):
    """
    API endpoint to fetch film poster image from Wikidata with Redis caching
    Used for lazy loading in search results
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        from .image_cache import image_cache
        
        data = json.loads(request.body)
        film_uri = data.get('film_uri')
        
        if not film_uri:
            return JsonResponse({'error': 'Missing film_uri'}, status=400)
        
        # Try to get image from cache first
        cached_image = image_cache.get_cached_image(film_uri, 'film')
        if cached_image is not None:
            return JsonResponse({
                'success': True,
                'image_url': cached_image,
                'film_uri': film_uri,
                'cached': True
            })
        
        # Query Wikidata for film image (logo first, then fallback to first image)
        sparql.setQuery(f"""
        prefix wd:    <http://www.wikidata.org/entity/>
        prefix wdt:   <http://www.wikidata.org/prop/direct/>
        
        SELECT ?image 
        WHERE {{
            SERVICE <https://query.wikidata.org/sparql> {{
                OPTIONAL{{ <{film_uri}> wdt:P154 ?logo .}}
                OPTIONAL{{ <{film_uri}> wdt:P18 ?first_image .}}
                BIND(COALESCE(?logo, ?first_image) as ?image)
            }}
        }}
        """)
        
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        
        image_url = None
        if results["results"]["bindings"] and results["results"]["bindings"][0].get("image"):
            image_url = results["results"]["bindings"][0]["image"]["value"]
        
        # Cache the result (even if None)
        image_cache.cache_image(film_uri, image_url, 'film')
        
        return JsonResponse({
            'success': True,
            'image_url': image_url,
            'film_uri': film_uri,
            'cached': False
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def cache_stats(request):
    """
    API endpoint to get cache statistics and manage cache
    """
    from .image_cache import image_cache
    
    if request.method == 'GET':
        # Return cache statistics
        stats = image_cache.get_cache_stats()
        return JsonResponse(stats)
    
    elif request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'clear':
                image_type = data.get('image_type')  # 'film', 'person', or None for all
                cleared = image_cache.clear_cache(image_type)
                return JsonResponse({
                    'success': True,
                    'message': f'Cleared {cleared} cached images',
                    'cleared_count': cleared
                })
            else:
                return JsonResponse({'error': 'Unknown action'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)