-- Reference schema (Django migrations are the source of truth)
CREATE TABLE core_profile (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNIQUE NOT NULL,
  role VARCHAR(10) NOT NULL
);

CREATE TABLE core_doctorprofile (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNIQUE NOT NULL,
  specialization VARCHAR(100),
  phone VARCHAR(20),
  fee DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE core_patientprofile (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNIQUE NOT NULL,
  age INT DEFAULT 0,
  gender VARCHAR(10) DEFAULT 'Other',
  contact VARCHAR(20),
  medical_history LONGTEXT
);

CREATE TABLE core_availabilityslot (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  doctor_id BIGINT NOT NULL,
  date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  is_booked BOOLEAN DEFAULT FALSE,
  UNIQUE KEY uniq_slot (doctor_id, date, start_time, end_time)
);

CREATE TABLE core_appointment (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_id BIGINT NOT NULL,
  doctor_id BIGINT NOT NULL,
  slot_id BIGINT NOT NULL,
  gmail VARCHAR(254) NOT NULL,
  status VARCHAR(10) DEFAULT 'BOOKED',
  created_at DATETIME
);

CREATE TABLE core_medicalrecord (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_id BIGINT NOT NULL,
  doctor_id BIGINT NOT NULL,
  notes LONGTEXT,
  created_at DATETIME
);

CREATE TABLE core_prescription (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  appointment_id BIGINT NOT NULL,
  medicines LONGTEXT,
  dosage LONGTEXT,
  notes LONGTEXT,
  created_at DATETIME
);

CREATE TABLE core_invoice (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  appointment_id BIGINT UNIQUE NOT NULL,
  doctor_fee DECIMAL(10,2) DEFAULT 0,
  service_charge DECIMAL(10,2) DEFAULT 0,
  total DECIMAL(10,2) DEFAULT 0,
  created_at DATETIME
);

CREATE TABLE core_staff (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  role VARCHAR(120) NOT NULL,
  contact VARCHAR(20),
  email VARCHAR(254)
);

CREATE TABLE core_reportfile (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_id BIGINT NOT NULL,
  file VARCHAR(100) NOT NULL,
  uploaded_at DATETIME
);

CREATE TABLE core_notification (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  message VARCHAR(255) NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  created_at DATETIME
);