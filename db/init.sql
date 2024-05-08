-- ALTER ROLE postgres PASSWORD '$DB_PASSWORD';
-- create user $DB_USER login password '$DB_PASSWORD';
CREATE USER ${DB_REPL_USER} REPLICATION LOGIN PASSWORD '${DB_REPL_PASSWORD}';

create database ${DB_DATABASE};
\c ${DB_DATABASE};
create table phonenumbers(id serial primary key, phone varchar(20) not null);
create table emails(id serial primary key, email varchar(30) not null);
