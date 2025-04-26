USE my_database_name;
CREATE TABLE otp_verification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20),
    otp_code VARCHAR(10),
    expires_at DATETIME
);
