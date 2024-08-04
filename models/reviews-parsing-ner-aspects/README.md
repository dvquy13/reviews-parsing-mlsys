# Start server with Jaeger

> ![IMPORANT]
> Do note that by default the server depends on a working $ENV K8s deployment running MLflow with trained model to download model from and serve.

```
docker compose up -d
```

# Example request to inference server:
```shell
curl -X POST "http://localhost:8080/v2/models/reviews-parsing-ner-aspects/infer" \
     -H "Content-Type: application/json" \
     -d '{
           "inputs": [
             {
               "name": "input-0",
               "shape": [2],
               "datatype": "BYTES",
               "data": ["Delicious food friendly staff and one good celebration!", "What an amazing dining experience"]
             }
           ]
         }'
```