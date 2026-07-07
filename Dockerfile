# Build stage
# Will be removed once the RADIUS plugin moves here (likely eduMFA v3.0.0)
FROM debian:trixie@sha256:4ae67669760b807c19f23902a3fd7c121a6a70cf2ae709035674b23e712e4d62 AS builder
WORKDIR /tmp
RUN apt-get update && \
    apt-get install -y git
RUN git clone --depth=1 --branch=v2.9.3 'https://github.com/eduMFA/eduMFA.git'

# Final stage
FROM debian:trixie@sha256:4ae67669760b807c19f23902a3fd7c121a6a70cf2ae709035674b23e712e4d62

# Install system dependencies
RUN apt-get update && \
    apt-get install -y freeradius libwww-perl libconfig-inifiles-perl libdata-dump-perl libtry-tiny-perl libjson-perl liblwp-protocol-https-perl liburi-encode-perl && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy necessary files
COPY --from=builder /tmp/eduMFA/deploy/edumfa_radius.pm /usr/share/edumfa/freeradius/edumfa_radius.pm
COPY --from=builder /tmp/eduMFA/deploy/rlm_perl.ini /etc/edumfa/rlm_perl.ini
COPY --from=builder /tmp/eduMFA/deploy/config/freeradius3/edumfa /etc/freeradius/3.0/sites-available/edumfa
COPY --from=builder /tmp/eduMFA/deploy/config/freeradius3/mods-perl-edumfa /etc/freeradius/3.0/mods-available/mods-perl-edumfa

RUN ln -sf /etc/freeradius/3.0/mods-available/mods-perl-edumfa /etc/freeradius/3.0/mods-enabled/ && \
    rm -f /etc/freeradius/3.0/sites-enabled/* && \
    ln -s /etc/freeradius/3.0/sites-available/edumfa /etc/freeradius/3.0/sites-enabled/ && \
    rm /etc/freeradius/3.0/mods-enabled/eap

# remove freerad from superfluous groups
RUN gpasswd shadow -d freerad && gpasswd ssl-cert -d freerad

USER freerad

HEALTHCHECK --interval=5s --timeout=5s --retries=2 CMD echo "User-Name=_dockerprobe,User-Password=pass" | radclient -r 1  localhost:1812 auth testing123 | grep '^Received Access-'

ENTRYPOINT ["/usr/bin/bash"]
CMD ["-c", "/usr/sbin/freeradius -l stdout -Cx && /usr/sbin/freeradius -lstdout -f"]
