Example request to inference server:
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