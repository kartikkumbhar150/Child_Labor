USE my_database_name;

-- Create the complaints table to store complaints from users
CREATE TABLE complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    description TEXT NOT NULL,
    location VARCHAR(255) NOT NULL,
    num_children INT NOT NULL,
    gender VARCHAR(50) NOT NULL,
    age INT NOT NULL,
    photo1 VARCHAR(255),
    photo2 VARCHAR(255),
    photo3 VARCHAR(255),
    photo4 VARCHAR(255),
    severity INT NOT NULL, -- 0 = Not a Child Labor Case, 1 = Less Severe, 2 = Severe
    status VARCHAR(50) NOT NULL DEFAULT 'unresolved'
);



