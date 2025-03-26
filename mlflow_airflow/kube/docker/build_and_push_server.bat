docker build -f Dockerfile-server-base -t fastapi-server-base:latest .
docker build -f Dockerfile-server -t lordbelasco/fastapi-server:latest .
docker push lordbelasco/fastapi-server:latest