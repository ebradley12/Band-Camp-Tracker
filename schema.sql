
CREATE TABLE country (
    country_id BIGINT PRIMARY KEY,
    country_name VARCHAR UNIQUE NOT NULL
);


CREATE TABLE customer (
    customer_id BIGINT PRIMARY KEY,
    customer_name VARCHAR NOT NULL,
    country_id BIGINT,
    FOREIGN KEY (country_id) REFERENCES country(country_id)
);


CREATE TABLE artist (
    artist_id BIGINT PRIMARY KEY,
    artist_name VARCHAR NOT NULL,
    country_id BIGINT,
    FOREIGN KEY (country_id) REFERENCES country(country_id)
);


CREATE TABLE genre (
    genre_id BIGINT PRIMARY KEY,
    genre_name VARCHAR NOT NULL
);


CREATE TABLE type (
    type_id BIGINT PRIMARY KEY,
    type_name VARCHAR NOT NULL
);


CREATE TABLE release (
    release_id BIGINT PRIMARY KEY,
    release_name VARCHAR NOT NULL,
    release_date DATE NOT NULL,
    genre_id BIGINT,
    artist_id BIGINT,
    type_id BIGINT,
    FOREIGN KEY (genre_id) REFERENCES genre(genre_id),
    FOREIGN KEY (artist_id) REFERENCES artist(artist_id),
    FOREIGN KEY (type_id) REFERENCES type(type_id)
);


CREATE TABLE sale (
    sale_id BIGINT PRIMARY KEY,
    sale_price FLOAT NOT NULL,
    sale_date DATE NOT NULL,
    customer_id BIGINT,
    release_id BIGINT,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (release_id) REFERENCES release(release_id)
);


CREATE TABLE subscriber (
    subscriber_id BIGINT PRIMARY KEY,
    subscriber_email VARCHAR UNIQUE NOT NULL,
    alerts BOOLEAN DEFAULT FALSE,
    CHECK (subscriber_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);


CREATE TABLE subscriber_genre (
    subscriber_id BIGINT,
    genre_id BIGINT,
    PRIMARY KEY (subscriber_id, genre_id),
    FOREIGN KEY (subscriber_id) REFERENCES subscriber(subscriber_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genre(genre_id) ON DELETE CASCADE
);
