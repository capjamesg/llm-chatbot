CREATE TABLE answers (
    id VARCHAR(255) NOT NULL PRIMARY KEY,
    date DATETIME,
    username VARCHAR(255),
    prompt TEXT,
    question TEXT,
    prompt_id VARCHAR(255),
    status VARCHAR(255),
    feedback INT(4) DEFAULT NULL
);

