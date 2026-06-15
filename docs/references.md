# References

## FRONTEND

npm create vite@latest frontend

choose react, typescript, npm install

Dockerize a React App: 
https://www.docker.com/blog/how-to-dockerize-react-app/

steps:

test:

docker build -t stock-dashboard-frontend-dev -f Dockerfile.dev .
docker run -p 5173:5173 stock-dashboard-frontend-dev

open: http://localhost:5173

Production:

docker build -t stock-dashboard-frontend -f Dockerfile .
docker run -p 3000:3000 stock-dashboard-frontend

open: http://localhost:3000