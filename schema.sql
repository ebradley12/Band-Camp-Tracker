DROP TABLE IF EXISTS subscriber_genre CASCADE;
DROP TABLE IF EXISTS release_genre CASCADE;
DROP TABLE IF EXISTS subscriber CASCADE;
DROP TABLE IF EXISTS sale CASCADE;
DROP TABLE IF EXISTS release CASCADE;
DROP TABLE IF EXISTS genre CASCADE;
DROP TABLE IF EXISTS artist CASCADE;
DROP TABLE IF EXISTS type CASCADE;
DROP TABLE IF EXISTS country CASCADE;


CREATE TABLE country (
    country_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_name VARCHAR UNIQUE NOT NULL
);


CREATE TABLE artist (
    artist_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    artist_name VARCHAR NOT NULL
);


CREATE TABLE genre (
    genre_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    genre_name VARCHAR UNIQUE NOT NULL
);


CREATE TABLE type (
    type_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    type_name VARCHAR NOT NULL
);


CREATE TABLE release (
    release_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    release_name VARCHAR NOT NULL,
    release_date DATE NOT NULL,
    artist_id INT,
    type_id SMALLINT,
    FOREIGN KEY (artist_id) REFERENCES artist(artist_id),
    FOREIGN KEY (type_id) REFERENCES type(type_id)
);

CREATE TABLE release_genre (
    release_id INT,
    genre_id SMALLINT,
    PRIMARY KEY (release_id, genre_id),
    FOREIGN KEY (release_id) REFERENCES release(release_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genre(genre_id) ON DELETE CASCADE
);

CREATE TABLE sale (
    sale_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sale_price FLOAT NOT NULL,
    sale_date TIMESTAMP NOT NULL,
    country_id INT,
    release_id INT,
    FOREIGN KEY (country_id) REFERENCES country(country_id),
    FOREIGN KEY (release_id) REFERENCES release(release_id)
);


CREATE TABLE subscriber (
    subscriber_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subscriber_email VARCHAR UNIQUE NOT NULL,
    subscribe_alert BOOLEAN DEFAULT FALSE,
    subscribe_report BOOLEAN DEFAULT FALSE,
    CHECK (subscriber_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);


CREATE TABLE subscriber_genre (
    subscriber_id INT,
    genre_id SMALLINT,
    PRIMARY KEY (subscriber_id, genre_id),
    FOREIGN KEY (subscriber_id) REFERENCES subscriber(subscriber_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genre(genre_id) ON DELETE CASCADE
);

INSERT INTO type (type_name) VALUES
('album'), 
('track');