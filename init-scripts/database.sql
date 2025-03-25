CREATE SCHEMA IF NOT EXISTS showcase;

CREATE TABLE showcase.counters (
    counter_id integer  NOT NULL,
    value integer NOT NULL,
    CONSTRAINT pk_counters PRIMARY KEY ( counter_id )
);

INSERT INTO showcase.counters VALUES (1,0), (2,0);
