FROM postgres:15.6

ARG DB_REPL_HOST
ARG DB_REPL_PORT
ARG DB_HOST


RUN mkdir -p /etc/postgresql/
RUN echo "listen_addresses = 'localhost, $DB_REPL_HOST'" >> /etc/postgresql/postgresql.conf
RUN echo "port = $DB_REPL_PORT" >> /etc/postgresql/postgresql.conf

 
RUN chmod 750 /var/lib/postgresql/data
USER postgres

CMD echo "$DB_REPL_PASSWORD" | pg_basebackup -v -R -h $DB_HOST -U $DB_REPL_USER -W -P -D /var/lib/postgresql/data && postgres -c config_file=/etc/postgresql/postgresql.conf
