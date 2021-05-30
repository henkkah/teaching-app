# TeachingApp

Purpose of the application is to provide a teaching&learning platform for teachers and students.  
Teachers can create courses to the platform - Students can study and complete these courses.  
Courses contain study material and assignments which are automatically graded by the system.  

## Functionalities & Plan [30.5.2021]

### Existing functionalities:
- Users can log in to and log out from the app
- Users can create new user accounts
- Teachers can create courses
- Teachers can see list of courses they teach
- Teachers can publish courses, hide courses, and delete courses taught by them
- Teachers can modify course parameters
- Students can see list of available courses and join courses which are published for students
- Students can see courses they have enrolled in and courses they have completed
- Students can leave courses

### To Do:
- Functionality for teachers to add material and assignments for their courses
- Functionality for students to study material and do assignments on their courses
- Statistics for teachers about student performance on their courses
- Statistics for students about performance on their courses
- Filtering functionality for students when viewing available courses

### To Do (if time permitting):
- Chat area on a course where students and teachers can chat about the course
- Students can rate the course (give stars based on how good the course was) and give free comment about the course - Other students then see these ratings when choosing which course to participate in
- Teachers can create groups and add students to groups - Possible to limit that certain course can be participated by certain group(s) only

## Testing on Heroku

TeachingApp can be tested on Heroku:  
[Link to the app on Heroku](https://teaching-app-henkkah.herokuapp.com/)  
- One can log in with existing user account or create new user account
- With role 'Teacher' one can create courses, see list of own courses, publish/hide/delete courses and modify course parameters
- With role 'Student' one can see list of available courses and join them, see list of enrolled and completed courses and leave courses
