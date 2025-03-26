docker build -f Dockerfile-test-base -t fastapi-test-base:latest .
docker build -f Dockerfile-test -t lordbelasco/fastapi-test:latest .
docker push lordbelasco/fastapi-test:latest