CREATE TABLE IF NOT EXISTS car_products (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,           -- Unique URL
    title TEXT,                         -- Car name
    price_usd INTEGER,                  -- Price in $ (number)
    odometer INTEGER,                   -- Mileage kilometers (95000)
    username TEXT,                      -- Seller name
    phone_number BIGINT[],              -- Phone number (38063......)
    image_url TEXT[],                   -- URL images
    image_count INTEGER,                -- Number of images
    car_number TEXT,                    -- Car number
    car_vin TEXT,                       -- VIN number
    datetime_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    datetime_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);