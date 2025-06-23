-- Tabla de usuarios
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de cámaras
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    camera_name VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    rtsp_url VARCHAR(255),
    location VARCHAR(100),
    status VARCHAR(10) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    camera_id INT NOT NULL,
    coords JSONB NOT NULL,
    type VARCHAR(50) NOT NULL,
    alert_threshold INT NOT NULL,
    schedule_start TIME NOT NULL,
    schedule_end TIME NOT NULL,
    alert_telegram VARCHAR(255),
    alert_email VARCHAR(255),
    FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE
);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL,
    alert_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    video_url VARCHAR(255) NOT NULL,
    person_count INTEGER DEFAULT 1 NOT NULL,
    CONSTRAINT fk_zone
        FOREIGN KEY (zone_id)
        REFERENCES zones(id)
        ON DELETE CASCADE
);
