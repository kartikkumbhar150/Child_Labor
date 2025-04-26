USE my_database_name;

CREATE TABLE lost_children (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    age INT,
    description TEXT,
    location VARCHAR(255),
    contact VARCHAR(100),
    photo VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
