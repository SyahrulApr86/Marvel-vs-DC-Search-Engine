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
    
    # JSON configuration untuk repository
    local config='{
        "id": "'$REPOSITORY_ID'",
        "title": "Marvel DC Knowledge Base",
        "type": "file-repository",
        "params": {
            "ruleset": {
                "label": "Ruleset",
                "name": "ruleset",
                "value": "empty"
            },
            "disableSameAs": {
                "label": "Disable same as",
                "name": "disableSameAs",
                "value": "true"
            },
            "checkForInconsistencies": {
                "label": "Check for inconsistencies",
                "name": "checkForInconsistencies",
                "value": "false"
            },
            "enableContextIndex": {
                "label": "Enable context index",
                "name": "enableContextIndex",
                "value": "false"
            },
            "enablePredicateList": {
                "label": "Enable predicate list",
                "name": "enablePredicateList",
                "value": "true"
            },
            "cacheMemory": {
                "label": "Cache memory",
                "name": "cacheMemory",
                "value": "80m"
            },
            "tupleIndexMemory": {
                "label": "Tuple index memory", 
                "name": "tupleIndexMemory",
                "value": "80m"
            }
        }
    }'
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$config" \
        "${GRAPHDB_HOST}/rest/repositories")
    
    if [ "$response" = "201" ] || [ "$response" = "200" ]; then
        echo "Repository '$REPOSITORY_ID' created successfully!"
        return 0
    else
        echo "ERROR: Failed to create repository. HTTP status: $response"
        return 1
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