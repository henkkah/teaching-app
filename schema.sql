CREATE TABLE users (id SERIAL PRIMARY KEY, username TEXT, password TEXT, teacher TEXT);
CREATE TABLE courses (id SERIAL PRIMARY KEY, code TEXT, name TEXT, teacher_id INTEGER REFERENCES users, lang TEXT, lev TEXT, ects INTEGER, lim INTEGER, visible TEXT, deleted TEXT);
CREATE TABLE courses_students (id SERIAL PRIMARY KEY, course_id INTEGER REFERENCES courses, student_id INTEGER REFERENCES users, completed TEXT, deleted TEXT);
