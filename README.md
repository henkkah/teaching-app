# TeachingApp

Purpose of the application is to provide a teaching&learning platform for teachers and students.  
Teachers can create courses to the platform - Students can study and complete these courses.  
Courses contain study material and assignments which are automatically graded by the system.  

## Functionalities & Plan [10.6.2021]

### Existing Functionalities:

#### Release 1 [30.5.2021]
- Users can log in to and log out from the app
- Users can create new user accounts
- Teachers can create courses
- Teachers can see list of courses they teach
- Teachers can publish courses, hide courses, and delete courses taught by them
- Teachers can modify course parameters
- Students can see list of available courses and join courses which are published for students
- Students can see courses they have enrolled in and courses they have completed
- Students can leave courses

#### Release 2 [10.6.2021]
- Teachers can add, modify and delete study material on their courses
- Teachers can add multiple-choice and text-field assignments for their courses (question, correct answer, possible choices)
- Teachers can modify and delete assignments they have added
- Students can study material on courses they have enrolled in
- Students can do assignments on their courses and get automatic grading from the system
- Students can complete a course when they have completed enough assignments of the course correctly (teachers set completion limit, e.g. 90%)
- Users are authenticated based on role and user_id if trying to access pages they are not allowed to access (by entering URLs)

### To Do:

#### Release 3 [planned: 24.6.2021]
- Statistics for teachers about student performance on own courses
- Statistics for students about own performance on own courses
- Filtering and searching functionality for students when viewing available courses
- Enhancing external visual design of the whole application

#### Release 4 (if time permitting)
- Chat area on a course where students and teachers can chat about the course
- Students can rate the course (give stars based on how good the course was) and give free comment about the course - Other students then see these ratings when choosing which course to participate in
- Teachers can create groups and add students to groups - Possible to limit that certain course can be participated by certain group(s) only

## Testing on Heroku

TeachingApp can be tested [on Heroku](https://teaching-app-henkkah.herokuapp.com/).
- One can use following test accounts when testing app:
    - role 'Student':
        - username: student_test
        - password: test
    - role 'Teacher':
        - username: teacher_test
        - password: test
- Available functionalities:
    - One can log in with existing user account or create new user account
    - With role 'Student' one can
        - see list of available courses and join them
        - see list of enrolled and completed courses
        - leave courses
        - study course materials
        - do course assignments and get automatic grading
        - get course completion when enough assignments completed
    - With role 'Teacher' one can
        - create courses
        - see list of own courses
        - publish/hide/delete courses
        - modify course parameters
        - add/modify/delete assignments for courses
        - add/modify/delete multiple-choice and text-field assignments for courses




