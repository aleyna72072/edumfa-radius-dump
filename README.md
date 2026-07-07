# edumfa-radius
This repository contains the Dockerfile for the edumfa-radius container (and
soon the plugin itself).  
TODO for upstream

# Installation
Until this is upstreamed:
1. Build the image:

- either with `docker build -t my-edumfa-radius:0.1.0 .`
- or by using `docker compose up` with the `--build` flag. Your compose service has to use `build:` instead of `image:` then (see `/deploy/docker-example/docker-compose.yaml`).

2. In your existing `docker-compose`, add a new service (see `/deploy/docker-example/docker-compose.yaml`).
3. Copy `/deploy/docker-example/rlm_perl.ini` and `/deploy/docker-example/clients.conf` and modify them.
4. Rebuild the image and recreate the container for OS and FreeRADIUS updates.

# Maintenance
TODO for upstream

## eduMFA update
If there is a new eduMFA version released, do:
1. Update the version in:

- `/Dockerfile`
- `/tests/test_auth.py`
- `/deploy/docker-example/docker-compose.yml`

2. Run the test to make sure everything is working: `uv run --with-requirements requirements.txt pytest`
3. Create a PR with your changes.

OS and FreeRADIUS updates are handled by floating tags and automatic rebuilds. TODO upstream  
