# Quiz Master Application

## Overview

The Quiz Master Application is a comprehensive platform designed for managing quizzes, chapters, and subjects. It provides an intuitive interface for administrators to manage quizzes and users, while also offering students a seamless experience to attempt quizzes and track their performance. The project is built using Flask, Jinja2 templates, Bootstrap, and SQLite.

---

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
- [Roles](#roles)
  - [Admin](#admin)
  - [Users](#users)
- [Core Functionalities](#core-functionalities)
- [Recommended Functionalities](#recommended-functionalities)
- [Optional Functionalities](#optional-functionalities)
- [Project Structure](#project-structure)

---

## Features

- **Admin Dashboard**:
  - Manage users, subjects, chapters, and quizzes.
  - View detailed statistics, including subject-wise performance and quiz participation.
  - Create, Delete or edit questions, quizzes, chapters, subject .
  - Monitor flagged users and inappropriate activities.

- **User Dashboard**:
  - Attempt quizzes and view performance summaries.
  - Reattempt quizzes.
  - View subject-wise and chapter-wise performance.
  - View personal rank and Leaderboard with peers.

- **Quiz Management**:
  - Add, edit, and delete quizzes.
  - Associate quizzes with specific chapters and subjects.
  - Track the number of questions in each quiz.
  - Make the quiz active or Deactive (admin)

- **Chapter and Subject Management**:
  - Add, edit, and delete chapters and subjects.
  - Associate chapters with subjects.

- **Performance Tracking**:
  - Subject-wise and chapter-wise performance charts.
  - Quiz-wise performance tracking for users.
  - Overall performance tracking by admin

- **Responsive Design**:
  - Fully responsive frontend using Bootstrap.

---

## Technologies Used

- **Backend**: Flask, SQLite
- **Frontend**: Jinja2, Bootstrap, HTML, CSS, JavaScript
- **Charts**: Chart.js for visualizing performance data

---

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd QuizMaster-v1

3. *Create and activate a virtual environment*:
   bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   
4. *Install dependencies*:
   bash
   pip install -r requirements.txt
   
5. *Run the application*:
   bash
   flask run
   
6. *Access the application*:
   Open your web browser and go to http://127.0.0.1:5000.

## Roles

### Admin

- Monitor all users (flag & unflag them)
- View statistics (active users, number of chapters, subjects, quizzes, questions)
- Manage (create, edit , delete)- Subjects, Chapters, Quizzes, Questions
- Activate & Deactivate quizzes

## Users
- Attempt, Reattempt Quizzes
- Search for Chapters, subjects, quizzes, questions
- Update Profile Details
- View subject-wise, chapter-wise, and overall performance.
- Check personal rank and leaderboard.

## Core Functionalities

1. **Admin login and User login**
    - Login/register forms for Admin & Users
    - Differentiation of user types (Admin & Users) in the model

2. **Admin Dashboard**:
    - Auto creation of Admin on creating new Database
    - The admin creates/edits/deletes a subject
    - The admin creates/edits/deletes a chapter under the subject
    - The admin creates/edits/deletes new quiz under a chapter
    - The admin creates/edits/deletes multiple questions under a quiz( 4 option --> 1 correct)
    - The admin can search the subjects/chapters/quizzes/questions
    - Shows the summary charts (admin side)

3. **Search for Users and Manage**:
    - Admin Search user based on name.
    - Can see data like Average Score, no.of quizzes attempted etc.
    - Manages them ( Flags or Unflags them)

3. **Quiz management** (for the Admin)
    - Create/Edit/delete a quiz under a chapter
    - The admin specifies the date and duration(HH: MM) of the quiz
    - The admin creates/edits/deletes the MCQ (only one option correct) questions inside the specific quiz

4. **User dashboard** (for the User)
    - The user can attempt any quiz of his/her interest(Search function)
    - Every quiz has a timer 
    - Each quiz score is recorded
    - The earlier quiz attempts are shown
    - Self Assess page to compare with chosen and corrrect option after a quiz.
    - Reattempt Quiz option available
    - Shows the summary charts and leaderboard.


## Recommended Functionalities
- External library (Chart JS) for creating charts dynamically.
- Frontend validation using HTML5 form validation /JavaScript
- Backend validation within controllers

## Optional Functionalities
- Responsive Frontend design using CSS/ Bootstrap with styling and asthetics.
- Any additional feature 
    - **Self Assess** page for comparing with chosen and correct option after a quiz.
    - Admin can Activate/Deactivate a Quiz (giving admin exclusive control)
