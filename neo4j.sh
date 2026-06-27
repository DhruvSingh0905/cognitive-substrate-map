#!/usr/bin/env bash
# PrimeKG / Neo4j control script.
#   ./neo4j.sh start     -> start (or create) the container
#   ./neo4j.sh stop      -> stop the container (data persists)
#   ./neo4j.sh status    -> container + node/edge counts
#   ./neo4j.sh shell     -> open an interactive cypher-shell
#   ./neo4j.sh query "MATCH ... RETURN ..."   -> run one Cypher statement
#   ./neo4j.sh browser   -> open Neo4j Browser in your default browser
#   ./neo4j.sh reimport  -> rebuild the store from data/primekg (prep + bulk import)
#   ./neo4j.sh logs      -> tail container logs
#
# Connection:  http://localhost:7474   (Browser)  ·  bolt://localhost:7687
# Login:       neo4j / primekg123

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEO="$HERE/neo4j"
NAME=primekg
IMAGE=neo4j:5.26
USER=neo4j
PASS=primekg123

cy() { docker exec "$NAME" cypher-shell -u "$USER" -p "$PASS" "$1"; }

cmd="${1:-status}"
case "$cmd" in

  start)
    if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
      docker start "$NAME" >/dev/null && echo "started existing container '$NAME'"
    else
      docker run -d --name "$NAME" \
        -p 7474:7474 -p 7687:7687 \
        -v "$NEO/data":/data -v "$NEO/logs":/logs -v "$NEO/plugins":/plugins \
        -e NEO4J_AUTH="$USER/$PASS" \
        -e 'NEO4J_PLUGINS=["apoc"]' \
        -e NEO4J_server_memory_heap_max__size=2G \
        -e NEO4J_server_memory_pagecache_size=2G \
        "$IMAGE" >/dev/null && echo "created new container '$NAME'"
    fi
    echo -n "waiting for Bolt … "
    until docker exec "$NAME" cypher-shell -u "$USER" -p "$PASS" "RETURN 1;" >/dev/null 2>&1; do sleep 2; done
    echo "ready → http://localhost:7474  (login: $USER / $PASS)"
    ;;

  stop)
    docker stop "$NAME" >/dev/null && echo "stopped '$NAME' (data persists in neo4j/data)"
    ;;

  status)
    docker ps --filter "name=$NAME" --format '{{.Names}}: {{.Status}}  {{.Ports}}' || true
    if docker exec "$NAME" cypher-shell -u "$USER" -p "$PASS" "RETURN 1;" >/dev/null 2>&1; then
      cy "MATCH (n) RETURN count(n) AS nodes;"
      cy "MATCH ()-[r]->() RETURN count(r) AS relationships;"
    else
      echo "(container not running — './neo4j.sh start')"
    fi
    ;;

  shell)
    exec docker exec -it "$NAME" cypher-shell -u "$USER" -p "$PASS"
    ;;

  query)
    shift; cy "$*"
    ;;

  browser)
    open "http://localhost:7474"
    ;;

  logs)
    docker logs -f --tail 50 "$NAME"
    ;;

  reimport)
    echo "regenerating import files …"
    "$HERE/.venv/bin/python" "$HERE/prep_neo4j.py"
    cp "$HERE/data/primekg/neo4j_import/"*.csv "$NEO/import/"
    docker rm -f "$NAME" 2>/dev/null || true
    echo "bulk importing …"
    docker run --rm -v "$NEO/data":/data -v "$NEO/import":/import "$IMAGE" \
      neo4j-admin database import full neo4j \
        --nodes=/import/nodes_neo4j.csv \
        --relationships=/import/edges_neo4j.csv \
        --overwrite-destination
    "$0" start
    ;;

  *)
    echo "usage: ./neo4j.sh {start|stop|status|shell|query <cypher>|browser|logs|reimport}"
    exit 1
    ;;
esac
