#!/bin/sh

# GraphDB Initialization Script
# Script ini akan membuat repository 'kb' dan import data secara otomatis

set -e

GRAPHDB_HOST="http://graphdb:7200"
REPOSITORY_ID="kb"
DATA_FILE="/data/mdc_processed_csv_csv.ttl"
MAX_WAIT=300  # 5 minutes max wait

echo "Starting GraphDB initialization..."

# Function untuk menunggu GraphDB ready
wait_for_graphdb() {
    echo "Waiting for GraphDB to be ready..."
    local count=0
    while [ $count -lt $MAX_WAIT ]; do
        if curl -s -f "${GRAPHDB_HOST}/rest/repositories" > /dev/null 2>&1; then
            echo "GraphDB is ready!"
            return 0
        fi
        echo "   GraphDB not ready yet... waiting ($count/$MAX_WAIT)"
        sleep 2
        count=$((count + 2))
    done
    echo "ERROR: GraphDB failed to start within $MAX_WAIT seconds"
    return 1
}

# Function untuk check apakah repository sudah ada
repository_exists() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" "${GRAPHDB_HOST}/rest/repositories/${REPOSITORY_ID}")
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# Function untuk membuat repository
create_repository() {
    echo "Creating repository '$REPOSITORY_ID'..."
    
    # Buat config file TTL untuk repository
    local config_file="/tmp/repo-config.ttl"
    cat > "$config_file" << 'EOF'
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep: <http://www.openrdf.org/config/repository#> .
@prefix sr: <http://www.openrdf.org/config/repository/sail#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix owlim: <http://www.ontotext.com/config/owlim#> .

[] a rep:Repository ;
   rep:repositoryID "kb" ;
   rdfs:label "Marvel DC Knowledge Base" ;
   rep:repositoryImpl [
      rep:repositoryType "graphdb:SailRepository" ;
      sr:sailImpl [
         sail:sailType "graphdb:Sail" ;
         owlim:repository-type "file-repository" ;
         owlim:entity-index-size "10000000" ;
         owlim:entity-id-size "32" ;
         owlim:imports "" ;
         owlim:cache-memory "80m" ;
         owlim:tuple-index-memory "80m" ;
         owlim:enable-context-index "false" ;
         owlim:enablePredicateList "true" ;
         owlim:in-memory-literal-properties "true" ;
         owlim:enable-literal-index "true" ;
         owlim:check-for-inconsistencies "false" ;
         owlim:disable-sameAs "true" ;
         owlim:query-timeout "0" ;
         owlim:query-limit-results "0" ;
         owlim:throw-QueryEvaluationException-on-timeout "false" ;
         owlim:read-only "false" ;
         owlim:ruleset "empty" ;
         owlim:storage-folder "storage"
      ]
   ] .
EOF

    # Upload config file untuk membuat repository
    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Content-Type: text/turtle" \
        --data-binary "@$config_file" \
        "${GRAPHDB_HOST}/rest/repositories")
    
    # Cleanup temp file
    rm -f "$config_file"
    
    if [ "$response" = "201" ] || [ "$response" = "200" ]; then
        echo "Repository '$REPOSITORY_ID' created successfully!"
        return 0
    else
        echo "ERROR: Failed to create repository. HTTP status: $response"
        # Mari coba method alternatif dengan JSON sederhana
        echo "Trying alternative method..."
        local json_response=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d '{"id":"'$REPOSITORY_ID'","title":"Marvel DC Knowledge Base","type":"free"}' \
            "${GRAPHDB_HOST}/rest/repositories")
        
        if [ "$json_response" = "201" ] || [ "$json_response" = "200" ]; then
            echo "Repository '$REPOSITORY_ID' created successfully with alternative method!"
            return 0
        else
            echo "ERROR: Alternative method also failed. HTTP status: $json_response"
            return 1
        fi
    fi
}

# Function untuk import data
import_data() {
    if [ ! -f "$DATA_FILE" ]; then
        echo "WARNING: Data file not found: $DATA_FILE"
        echo "   Skipping data import..."
        return 0
    fi
    
    echo "Importing data from $DATA_FILE..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Content-Type: text/turtle" \
        --data-binary "@$DATA_FILE" \
        "${GRAPHDB_HOST}/repositories/${REPOSITORY_ID}/statements")
    
    if [ "$response" = "204" ] || [ "$response" = "200" ]; then
        echo "Data imported successfully!"
        
        # Get count of triples
        local count=$(curl -s \
            -H "Accept: application/sparql-results+json" \
            "${GRAPHDB_HOST}/repositories/${REPOSITORY_ID}?query=SELECT%20(COUNT(*)%20as%20?count)%20WHERE%20{%20?s%20?p%20?o%20}" \
            | grep -o '"value":"[0-9]*"' | cut -d'"' -f4)
        
        if [ ! -z "$count" ]; then
            echo "Total triples imported: $count"
        fi
        return 0
    else
        echo "ERROR: Failed to import data. HTTP status: $response"
        return 1
    fi
}

# Function untuk verify setup
verify_setup() {
    echo "Verifying setup..."
    
    # Check repository
    if repository_exists; then
        echo "Repository '$REPOSITORY_ID' exists"
    else
        echo "ERROR: Repository verification failed"
        return 1
    fi
    
    # Simple SPARQL query test
    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Accept: application/sparql-results+json" \
        "${GRAPHDB_HOST}/repositories/${REPOSITORY_ID}?query=SELECT%20?s%20WHERE%20{%20?s%20?p%20?o%20}%20LIMIT%201")
    
    if [ "$response" = "200" ]; then
        echo "SPARQL endpoint is working"
    else
        echo "ERROR: SPARQL endpoint test failed"
        return 1
    fi
}

# Main execution
main() {
    echo "GraphDB Auto-Setup for Marvel vs DC Search Engine"
    echo "================================================="
    
    # Wait for GraphDB to be ready
    if ! wait_for_graphdb; then
        echo "ERROR: GraphDB initialization failed - GraphDB not ready"
        exit 1
    fi
    
    # Check if repository already exists
    if repository_exists; then
        echo "INFO: Repository '$REPOSITORY_ID' already exists"
        echo "   Skipping repository creation..."
    else
        # Create repository
        if ! create_repository; then
            echo "ERROR: GraphDB initialization failed - could not create repository"
            exit 1
        fi
        
        # Wait a bit for repository to be fully ready
        echo "Waiting for repository to be ready..."
        sleep 5
        
        # Import data
        if ! import_data; then
            echo "WARNING: Data import failed, but repository was created"
            echo "   You can manually import data later"
        fi
    fi
    
    # Verify setup
    if verify_setup; then
        echo ""
        echo "GraphDB initialization completed successfully!"
        echo "GraphDB Workbench: http://localhost:7200"
        echo "Repository: $REPOSITORY_ID"
        echo "Ready for Marvel vs DC Search queries!"
    else
        echo "ERROR: Setup verification failed"
        exit 1
    fi
}

# Run main function
main "$@" 