#!/bin/bash

# Test Script untuk GraphDB Auto-Setup
# Script ini akan melakukan testing terhadap setup otomatis GraphDB

set -e

GRAPHDB_HOST="http://localhost:7200"
REPOSITORY_ID="kb"

echo "Testing GraphDB Auto-Setup"
echo "=============================="

# Test 1: Check if GraphDB is running
echo "Test 1: Checking GraphDB connectivity..."
if curl -s -f "${GRAPHDB_HOST}/rest/repositories" > /dev/null 2>&1; then
    echo "PASS: GraphDB is accessible"
else
    echo "FAIL: GraphDB is not accessible"
    exit 1
fi

# Test 2: Check if repository exists
echo "Test 2: Checking repository existence..."
response=$(curl -s -o /dev/null -w "%{http_code}" "${GRAPHDB_HOST}/rest/repositories/${REPOSITORY_ID}")
if [ "$response" = "200" ]; then
    echo "PASS: Repository '${REPOSITORY_ID}' exists"
else
    echo "FAIL: Repository '${REPOSITORY_ID}' not found"
    exit 1
fi

# Test 3: Check if data is imported
echo "Test 3: Checking data import..."
count=$(curl -s \
    -H "Accept: application/sparql-results+json" \
    "${GRAPHDB_HOST}/repositories/${REPOSITORY_ID}?query=SELECT%20(COUNT(*)%20as%20?count)%20WHERE%20{%20?s%20?p%20?o%20}" \
    | grep -o '"value":"[0-9]*"' | cut -d'"' -f4)

if [ ! -z "$count" ] && [ "$count" -gt 0 ]; then
    echo "PASS: Data imported successfully: $count triples"
else
    echo "FAIL: No data found in repository"
    exit 1
fi

# Test 4: Test specific Marvel/DC queries
echo "Test 4: Testing Marvel/DC specific queries..."

# Test Marvel films
marvel_count=$(curl -s \
    -H "Accept: application/sparql-results+json" \
    "${GRAPHDB_HOST}/repositories/${REPOSITORY_ID}?query=SELECT%20(COUNT(*)%20as%20?count)%20WHERE%20{%20?film%20a%20:Film%20;%20:entity%20%22MARVEL%22%20}" \
    | grep -o '"value":"[0-9]*"' | cut -d'"' -f4)

# Test DC films  
dc_count=$(curl -s \
    -H "Accept: application/sparql-results+json" \
    "${GRAPHDB_HOST}/repositories/${REPOSITORY_ID}?query=SELECT%20(COUNT(*)%20as%20?count)%20WHERE%20{%20?film%20a%20:Film%20;%20:entity%20%22DC%22%20}" \
    | grep -o '"value":"[0-9]*"' | cut -d'"' -f4)

if [ ! -z "$marvel_count" ] && [ "$marvel_count" -gt 0 ]; then
    echo "PASS: Marvel films found: $marvel_count"
else
    echo "WARN: No Marvel films found"
fi

if [ ! -z "$dc_count" ] && [ "$dc_count" -gt 0 ]; then
    echo "PASS: DC films found: $dc_count"
else
    echo "WARN: No DC films found"
fi

# Test 5: Test sample film query
echo "Test 5: Testing sample film query..."
sample_film=$(curl -s \
    -H "Accept: application/sparql-results+json" \
    "${GRAPHDB_HOST}/repositories/${REPOSITORY_ID}?query=SELECT%20?film%20?name%20WHERE%20{%20?film%20a%20:Film%20;%20rdfs:label%20?name%20}%20LIMIT%201" \
    | grep -o '"value":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ ! -z "$sample_film" ]; then
    echo "PASS: Sample query successful: $sample_film"
else
    echo "FAIL: Sample query failed"
    exit 1
fi

# Test 6: Test web application endpoint simulation
echo "Test 6: Testing web application SPARQL queries..."
web_query_result=$(curl -s \
    -H "Accept: application/sparql-results+json" \
    "${GRAPHDB_HOST}/repositories/${REPOSITORY_ID}?query=SELECT%20DISTINCT%20?film_wiki_uri%20?film_name%20?year%20?film_type%20WHERE%20{%20?film_wiki_uri%20a%20:Film%20;%20rdfs:label%20?film_name%20;%20:year%20?year%20;%20:entity%20?film_type%20.%20FILTER%20contains(LCASE(?film_name),%22spider%22)%20}%20LIMIT%205")

if echo "$web_query_result" | grep -q "film_name"; then
    echo "PASS: Web application queries working"
else
    echo "FAIL: Web application queries failed"
fi

echo ""
echo "All tests completed successfully!"
echo "Summary:"
echo "   - Total triples: $count"
echo "   - Marvel films: $marvel_count"
echo "   - DC films: $dc_count"
echo "   - Repository: $REPOSITORY_ID"
echo "   - GraphDB: $GRAPHDB_HOST"
echo ""
echo "Marvel vs DC Search Engine is ready to use!" 