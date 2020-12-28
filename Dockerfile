FROM rust:1.48
MAINTAINER Simon Egersand "s.egersand@gmail.com"

RUN cargo install urlsup

COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
