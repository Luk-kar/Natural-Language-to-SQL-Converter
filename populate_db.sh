docker exec -it nl2sql-mvp-postgres-1 psql -U admin -d business -c "
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(50)
);

INSERT INTO customers (name, email, city) VALUES
('John Doe', 'john@example.com', 'New York'),
('Jane Smith', 'jane@example.com', 'London'),
('Bob Wilson', 'bob@example.com', 'Paris');
"