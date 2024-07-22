# Stop all running containers
docker stop $(docker ps -aq)

# Remove all containers
docker rm $(docker ps -aq)

# Remove all images
docker rmi $(docker images -q)

# Remove all volumes
docker volume rm $(docker volume ls -q)

# Remove all networks (excluding default ones)
docker network rm $(docker network ls | grep "bridge\|host\|none" -v | awk '/ / { print $1 }')

# Prune all unused Docker objects
docker system prune -a --volumes
#
## Rebuild the Docker image
#docker build -t grainger_recommendations_chatbot .
#
## Run the Docker container
#docker run -p 8000:8000 -p 8505:8505 grainger_recommendations_chatbot
