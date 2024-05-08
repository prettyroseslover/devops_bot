FROM postgres:15.6

# no env or expose as they're specified in docker-compose.yaml

# ARG DB_USER
# ARG DB_PASSWORD
ARG DB_DATABASE
ARG DB_REPL_USER
ARG DB_REPL_PASSWORD
ARG DB_REPL_HOST
ARG DB_PORT

RUN apt-get update
RUN apt-get install gettext-base
COPY ./init.sql /docker-entrypoint-initdb.d/init.sql.raw
RUN envsubst < /docker-entrypoint-initdb.d/init.sql.raw > /docker-entrypoint-initdb.d/init.sql


RUN mkdir -p /etc/postgresql/
RUN echo "listen_addresses = '*'" >> /etc/postgresql/postgresql.conf
RUN echo "port = $DB_PORT" >> /etc/postgresql/postgresql.conf
RUN echo "local all postgres peer" >> /etc/postgresql/pg_hba.conf
RUN echo "host all all 0.0.0.0/0 password" >> /etc/postgresql/pg_hba.conf

RUN echo "archive_mode = on\narchive_command = 'cp %p /oracle/pg_data/archive/%f'\nmax_wal_senders = 10\nwal_level = replica\nwal_log_hints = on\nlog_replication_commands = on" >> /etc/postgresql/postgresql.conf
RUN echo "host replication $DB_REPL_USER $DB_REPL_HOST trust" >> /etc/postgresql/pg_hba.conf

RUN mkdir -p /oracle/pg_data/archive/
RUN chown postgres:postgres /oracle/pg_data/archive/

USER postgres
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf", "-c", "hba_file=/etc/postgresql/pg_hba.conf"]