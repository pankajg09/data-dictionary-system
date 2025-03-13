CREATE TABLE categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT
);

CREATE TABLE suppliers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  contact_name TEXT,
  email TEXT,
  phone TEXT,
  address TEXT
);

CREATE TABLE items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  category_id INTEGER,
  supplier_id INTEGER,
  unit_price REAL NOT NULL,
  stock_quantity INTEGER DEFAULT 0,
  reorder_level INTEGER DEFAULT 5,
  FOREIGN KEY (category_id) REFERENCES categories(id),
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

CREATE TABLE inventory_transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  transaction_type TEXT NOT NULL, -- 'in' or 'out'
  quantity INTEGER NOT NULL,
  transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  notes TEXT,
  FOREIGN KEY (item_id) REFERENCES items(id)
);

INSERT INTO categories (name, description) VALUES
('Electronics', 'Electronic devices and components'),
('Office Supplies', 'Items used in office environments'),
('Furniture', 'Office and home furniture');

INSERT INTO suppliers (name, contact_name, email, phone, address) VALUES
('Tech Supplies Inc.', 'John Tech', 'john@techsupplies.com', '555-1234', '123 Tech St, San Francisco, CA'),
('Office Depot', 'Jane Office', 'jane@officedepot.com', '555-5678', '456 Office Ave, New York, NY'),
('Furniture World', 'Bob Furniture', 'bob@furnitureworld.com', '555-9012', '789 Chair Blvd, Chicago, IL');

INSERT INTO items (name, description, category_id, supplier_id, unit_price, stock_quantity, reorder_level) VALUES
('Laptop', 'Business laptop with 16GB RAM', 1, 1, 1200.00, 15, 3),
('Desk Chair', 'Ergonomic office chair', 3, 3, 250.00, 8, 2),
('Printer Paper', 'A4 printer paper, 500 sheets', 2, 2, 5.99, 100, 20),
('Wireless Mouse', 'Bluetooth wireless mouse', 1, 1, 25.99, 30, 5),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 2, 2, 35.50, 12, 3);

INSERT INTO inventory_transactions (item_id, transaction_type, quantity, notes) VALUES
(1, 'in', 20, 'Initial stock'),
(1, 'out', 5, 'Sold to marketing department'),
(2, 'in', 10, 'Initial stock'),
(2, 'out', 2, 'Sold to HR department'),
(3, 'in', 100, 'Initial stock'),
(4, 'in', 30, 'Initial stock'),
(5, 'in', 15, 'Initial stock'),
(5, 'out', 3, 'Sold to finance department'); 