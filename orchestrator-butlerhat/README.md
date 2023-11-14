# Start Chrome with playwright orchestrator

`kubectl apply -f test_chrome.yml`

# Start api
`cd api`
`python app.py`

# Production

## Configure minikube
`kubectl create serviceaccount my-service-account --namespace default
