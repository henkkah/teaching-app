CREATE TABLE users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT);
CREATE TABLE courses (id SERIAL PRIMARY KEY, code TEXT, name TEXT, teacher_id INTEGER REFERENCES users, lang TEXT, lev TEXT, ects INTEGER, lim INTEGER, visible INTEGER);
CREATE TABLE courses_students (id SERIAL PRIMARY KEY, course_id INTEGER REFERENCES courses ON DELETE CASCADE, student_id INTEGER REFERENCES users, completed INTEGER);
CREATE TABLE materials (id SERIAL PRIMARY KEY, material TEXT, course_id INTEGER REFERENCES courses ON DELETE CASCADE);
