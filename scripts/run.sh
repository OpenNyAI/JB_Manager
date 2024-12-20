#!/bin/bash

# Default environment file
env_file=".env-dev"

# Process command-line arguments
while getopts 'e:-:' flag; do
  case "${flag}" in
    e) env_file="${OPTARG}" ;;
    -) case "${OPTARG}" in
            stage)
                stage=true
                ;;
            *)
                echo "Unknown option --${OPTARG}" >&2
                exit 1
                ;;
        esac
        ;;
    *) echo "Usage: $0 [-e env_file] [service1 service2 ...]"
       exit 1 ;;
  esac
done

# Remove processed options from the arguments list
shift $((OPTIND -1))

mkdir -p media
# set -a
# source ./set_jbhost.sh
# set +a
export JB_API_SERVER_HOST="http://localhost:8000"
echo "Setting JB_API_SERVER_HOST: ${JB_API_SERVER_HOST}"
if grep -qi microsoft /proc/version && grep -q WSL2 /proc/version; then
    JBHOST=$(hostname -I | awk '{print $1}')
    export JBHOST
    export JB_KAFKA_BROKER=${JBHOST}
    export JB_POSTGRES_DATABASE_HOST=${JBHOST}
    echo "Setting Kakfa & Postgres host by WSL2 IP: ${JBHOST}"
else
    export JBHOST=localhost
    export JB_KAFKA_BROKER=kafka:9092
    export JB_POSTGRES_DATABASE_HOST=postgres
    echo "Setting Kakfa & Postgres host by docker-compose service name: kafka, postgres"
fi

if [ -n "$stage" ]; then
  for arg in "$@"
  do
    if [[ "$arg" == "frontend" ]]; then
        # Build the frontend with the specified environment file
        docker compose build "$arg" --build-arg VITE_SERVER_HOST=$JB_API_SERVER_HOST
        break
    fi
  done
  # Run docker-compose with the specified environment file and services
  echo "Running docker-compose with existing images"
  docker-compose --env-file "$env_file" -f "docker-compose.yml" -f docker-compose.stage.yml up $@
else
  echo "Building and running docker-compose"
  # Build the services with the specified environment file
  docker compose build $@ --build-arg VITE_SERVER_HOST=$JB_API_SERVER_HOST
  # Run docker-compose with the specified environment file and services
  docker-compose --env-file "$env_file" up $@
fi
