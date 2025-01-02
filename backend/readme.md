run the docker compose:
```
docker compose -f docker-compose.yml up --build --remove-orphans
```

run the tests:
```
docker compose -f docker-compose.test.yml up --build --remove-orphans
```


status:

- get data endpoints are hanging.
- issue seems to be FileResponse:
    when we return the report as a string, it works.
    when we return the report as a FileResponse, it hangs.

- running the batch experiments synchronously is working.
- the issue with treatments failing because of permissions on the first run is still a problem.
- merging Julians code for the side car container is needed.