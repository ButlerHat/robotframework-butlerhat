# Chrome with desktop

Launch with ports:

- 6080: No Vnc to fluxbox
- 4445: To connect playwright with `Connect To Browser  wsEndpoint`

## Arguments

WS Path: str -> A path to add to ws://127.0.0.1:4445/{WS Path}

## Run in docker

Example: With Argument

`docker run -p 4445:4445 -p 6080:6080 --rm playwright_chrome /my_endpoint`

Example: With environment variable

`docker run -p 4445:4445 -p 6080:6080 --rm -it --network bridge -e WS_PATH=/other_endpoint  playwright_chrome`
