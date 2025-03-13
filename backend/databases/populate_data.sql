-- Inventory Database Population

-- Clear existing data
DELETE FROM inventory_transactions;
DELETE FROM items;
DELETE FROM suppliers;
DELETE FROM categories;

-- Reset auto-increment
DELETE FROM sqlite_sequence WHERE name IN ('categories', 'suppliers', 'items', 'inventory_transactions');

-- Categories
INSERT INTO categories (name, description) VALUES
('Electronics', 'Electronic devices and components for office use'),
('Office Supplies', 'Essential supplies for daily office operations'),
('Furniture', 'Office furniture and workspace equipment'),
('Storage', 'Storage solutions and organization systems'),
('Networking', 'Network equipment and connectivity solutions'),
('Accessories', 'Computer and office accessories');

-- Suppliers
INSERT INTO suppliers (name, contact_name, email, phone, address) VALUES
('Tech Solutions', 'John Smith', 'john.smith@techsolutions.com', '(555) 123-4567', '123 Tech Park, Silicon Valley, CA 94025'),
('Office World', 'Sarah Johnson', 'sarah.j@officeworld.com', '(555) 234-5678', '456 Business Ave, New York, NY 10001'),
('Furniture Plus', 'Michael Brown', 'mbrown@furnitureplus.com', '(555) 345-6789', '789 Design District, Miami, FL 33127'),
('Storage Kings', 'Lisa Anderson', 'lisa@storagekings.com', '(555) 456-7890', '321 Warehouse Rd, Chicago, IL 60601'),
('Network Pro', 'David Wilson', 'david@networkpro.net', '(555) 567-8901', '567 Server Lane, Austin, TX 78701'),
('Accessory Hub', 'Emma Davis', 'emma@accessoryhub.com', '(555) 678-9012', '890 Gadget Street, Seattle, WA 98101');

-- Items
INSERT INTO items (name, description, category_id, supplier_id, unit_price, stock_quantity, reorder_level) VALUES
('Desktop Computer', 'High-performance workstation with i7 processor', 1, 1, 1200.00, 15, 5),
('Monitor', '27-inch 4K LED Display', 1, 1, 400.00, 20, 8),
('Paper Clips', 'Premium steel paper clips, box of 100', 2, 2, 3.50, 500, 100),
('Office Chair', 'Ergonomic mesh office chair with lumbar support', 3, 3, 250.00, 25, 10),
('Storage Cabinet', 'Metal storage cabinet with adjustable shelves', 4, 4, 350.00, 8, 3),
('Network Switch', '24-port Gigabit managed switch', 5, 5, 180.00, 12, 4),
('Mouse Pad', 'Premium cloth mouse pad with wrist rest', 6, 6, 15.00, 50, 20),
('Keyboard', 'Mechanical keyboard with RGB backlight', 1, 1, 80.00, 30, 10),
('Stapler', 'Heavy-duty desktop stapler', 2, 2, 12.00, 40, 15),
('Desk', 'L-shaped corner desk with cable management', 3, 3, 300.00, 10, 3);

-- Inventory Transactions
INSERT INTO inventory_transactions (item_id, transaction_type, quantity, notes) VALUES
(1, 'in', 20, 'Initial stock order from Tech Solutions'),
(1, 'out', 5, 'Distributed to Marketing department'),
(2, 'in', 25, 'Quarterly stock replenishment'),
(2, 'out', 5, 'Allocated to new hires'),
(3, 'in', 1000, 'Bulk order for office supplies'),
(3, 'out', 500, 'Monthly office supply distribution'),
(4, 'in', 30, 'New office furniture order'),
(4, 'out', 5, 'Setup for meeting rooms'),
(5, 'in', 12, 'Storage expansion project'),
(5, 'out', 4, 'Department reorganization');

-- Sample Database Population

-- Clear existing data
DELETE FROM order_items;
DELETE FROM orders;
DELETE FROM products;
DELETE FROM users WHERE username NOT IN ('john_doe', 'jane_smith', 'bob_johnson');

-- Reset auto-increment
DELETE FROM sqlite_sequence WHERE name IN ('products', 'orders', 'order_items');

-- Products
INSERT INTO products (name, description, price, stock) VALUES
('Desktop PC', 'Custom-built gaming PC with RTX 3080', 2200.00, 5),
('Monitor 27"', 'Ultra-wide curved gaming monitor', 500.00, 12),
('Wireless Keyboard', 'Low-profile mechanical keyboard', 120.00, 25),
('Wireless Mouse', 'Gaming mouse with 20K DPI sensor', 80.00, 30),
('USB Hub', '7-port USB 3.0 hub with power delivery', 45.00, 40),
('External SSD', '1TB NVMe portable SSD', 180.00, 15),
('Webcam HD', '4K webcam with noise-canceling mic', 150.00, 20),
('Gaming Headset', '7.1 surround sound with RGB', 130.00, 18),
('Bluetooth Speaker', 'Portable speaker with 24h battery', 90.00, 22),
('Power Bank', '20000mAh with fast charging', 65.00, 35);

-- Orders (using existing users)
INSERT INTO orders (user_id, status, order_date) VALUES
(1, 'pending', datetime('now', '-5 days')),
(2, 'processing', datetime('now', '-4 days')),
(3, 'completed', datetime('now', '-3 days')),
(1, 'completed', datetime('now', '-2 days')),
(2, 'pending', datetime('now', '-1 day'));

-- Order Items
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 2200.00),
(1, 3, 2, 120.00),
(2, 2, 1, 500.00),
(2, 4, 2, 80.00),
(3, 5, 3, 45.00),
(3, 6, 1, 180.00),
(4, 7, 1, 150.00),
(4, 8, 2, 130.00),
(5, 9, 2, 90.00),
(5, 10, 3, 65.00); 