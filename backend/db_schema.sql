CREATE DATABASE IF NOT EXISTS dag_generator;
USE dag_generator;

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT,
    message_type ENUM('user', 'system'),
    content TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);

CREATE TABLE IF NOT EXISTS generated_dags (
    dag_id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT,
    dag_script TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);