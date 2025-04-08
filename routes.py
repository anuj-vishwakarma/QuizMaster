from flask import Flask,request,jsonify, render_template, request, redirect, url_for, flash, session,jsonify, make_response, send_file,jsonify 
from app import app
from models import db, User, Subject, Chapter, Quiz, Questions, Scores
from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from datetime import time
import pytz
import os
import re 
import requests
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

## Decorators

def auth_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('please login to continue')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return inner

def admin_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('please login to continue')
            return redirect(url_for('login'))
        user=User.query.get(session['user_id'])
        if user.is_admin!=True:
            flash('You are not authorized to view this page')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return inner

## Index page routes 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')           
def login():
    return render_template('auth/login.html') 

@app.route('/login', methods=['POST'])
def login_post():
    username=request.form.get('username')
    password=request.form.get('password')
    
    if username=='' or password=='':
        flash('Username and password cannot be empty')

    user=User.query.filter_by(username=username).first()
    
    if not user:
        flash('User details not found')
        return redirect(url_for('login'))
    
    elif not user.check_password(password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    if user.flagged==True:
        flash('This account has been banned temporarily, contact admin')
        return redirect(url_for('login'))
    
    #if login successful
    session['user_id']=user.id
    #session['username']=user.username
    flash('Login successful')

    if user.is_admin==True:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    #session.pop('username', None)
    flash('Logout successful')
    return redirect(url_for('login'))


@app.route('/register')
def register():
    return render_template('auth/register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username=request.form.get('username')
    password=request.form.get('password')
    confirm_password=request.form.get('confirm_password')
    name=request.form.get('name')
    qualification=request.form.get('qualification')
    email=request.form.get('email')
    dob=request.form.get('dob')
    
    try:
        dob = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
    except ValueError:
        flash('Invalid date of birth format. Please use YYYY-MM-DD.')
        return redirect(url_for('register'))
    
    user=User.query.filter_by(username=username).first()
    if user:
        flash('User already exists')
        return redirect(url_for('register'))
    
    email=User.query.filter_by(email=email).first()
    if email:
        flash('Email already exists')
        return redirect(url_for('register'))

    if not username or not password or not confirm_password:
        flash('Please fill out all the required fields')
        return redirect(url_for('register'))
    
    new_user=User(username=username, passhash=generate_password_hash(password), name=name, qualification=qualification,dob=dob,email=email)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Registration successful. Please Log In')
    return redirect(url_for('login'))

## user / student routes 

@app.route('/profile')
@auth_required 
def profile():
    user=User.query.get(session['user_id'])
    return render_template('user/profile.html',user=user)

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')
    qualification = request.form.get('qualification')
    email = request.form.get('email')
    dob = request.form.get('dob')

    try:
        dob = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
    except ValueError:
        flash('Invalid date of birth format. Please use YYYY-MM-DD.')
        return redirect(url_for('register'))
    
    if not username or not cpassword or not password :
        flash('Please fill out all the required fields')
        return redirect(url_for('profile'))
    
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('profile'))
    
    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('profile'))
    
    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    user.qualification = qualification
    user.email = email
    user.dob = dob
        
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))

@app.route('/user/user_dashboard')
@auth_required
def user_dashboard():
    quizzes=Quiz.query.filter(Quiz.start_date != None).all()
    ist = pytz.timezone('Asia/Kolkata')  # IST timezone
    current_date = datetime.now(ist).date()  # Get current IST time
    user = User.query.get(session['user_id'])
    scores = Scores.query.filter_by(user_id=user.id).all()
    total_attempted = len(scores)
    avg_score = 0
    if total_attempted > 0:
        avg_score = sum(score.score for score in scores) / total_attempted

    leaderboard = (
        db.session.query(
            User.id,
            User.name,
            db.func.sum(Scores.score).label('total_score')
        )
        .join(Scores, Scores.user_id == User.id)
        .group_by(User.id)
        .order_by(db.func.sum(Scores.score).desc())
        .all()
    )

    # Calculate leaderboard position
    leaderboard_position = next((index + 1 for index, u in enumerate(leaderboard) if u.id == user.id), None)

    return render_template(
        'user/user_dashboard.html',
        quizzes=quizzes,
        current_date=current_date,
        user=user,
        avg_score=avg_score,
        scores=scores,
        total_attempted=total_attempted,
        leaderboard_position=leaderboard_position  # Pass leaderboard position to the template
    )

@app.route('/user_search', methods=['GET'])
@auth_required
def user_search():
    query = request.args.get('query', '').strip()  # Get the search query from the URL
    if not query:
        flash('Please enter a search term.', 'warning')
        return redirect(request.referrer or url_for('admin_dashboard'))

    # Search across Subjects, Chapters, Quizzes, and Questions
    subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
    chapters = Chapter.query.filter(Chapter.name.ilike(f'%{query}%')).all()
    quizzes = Quiz.query.filter(Quiz.name.ilike(f'%{query}%')).all()
    # Render the search results page
    return render_template(
        'user/user_search_results.html',
        query=query,
        subjects=subjects,
        chapters=chapters,
        quizzes=quizzes
    )


@app.route('/user/user_quiz')
@auth_required
def user_quiz():
    user_id = session.get('user_id')  # Get the logged-in user's ID

    # Fetch all quizzes
    quizzes = Quiz.query.all()

    # Fetch quizzes already attempted by the user
    attempted_quiz_ids = (
        db.session.query(Scores.quiz_id)
        .filter(Scores.user_id == user_id)
        .distinct()
        .all()
    )
    # Convert the list of tuples to a flat list of quiz IDs
    attempted_quiz_ids = [quiz_id[0] for quiz_id in attempted_quiz_ids]

    return render_template(
        'user/user_quiz.html',
        quizzes=quizzes,
        attempted_quiz_ids=attempted_quiz_ids
    )

@app.route('/user/view_quiz/<int:quiz_id>')
@auth_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = session.get('user_id')  # Get the logged-in user's ID

    # Check if the user has already attempted this quiz
    attempted = Scores.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()

    # Set the flag based on whether the quiz has been attempted
    flag = 'false' if attempted else 'true'
    return render_template('user/view_quiz.html', quiz=quiz,flag=flag)


@app.route('/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@auth_required
def attempt_quiz(quiz_id):
    user = User.query.get_or_404(session.get('user_id'))
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz.id).all()
    print(str(quiz.time_duration).split(':'))

    if quiz.is_active == False:
        flash('Quiz is not active')
        return redirect(url_for('user_quiz'))
    
    try:
        if quiz.time_duration:  # Ensure time_duration is not None
            hours, minutes, seconds= map(int, str(quiz.time_duration).split(":"))
            quiz_duration = (hours * 60) + minutes  # Convert to total minutes
        else:
            quiz_duration = 5  # Default to 0 if time_duration is None
    except (ValueError, AttributeError):
        quiz_duration = 5  # Default to 0 if invalid format

    print (quiz_duration)
    if request.method == "POST":
        score = 0
        submitted_answers = {}
        answered_questions = 0
        total_questions = len(questions)

        for question in questions:
            user_answer = request.form.get(f'question_{question.id}')  # Get user's selected option
            if user_answer:  # Ensure we correctly capture selected answers
                submitted_answers[str(question.id)] = user_answer
            else:
                submitted_answers[str(question.id)] = "Not Attempted"

            # Check if answer is correct
            if user_answer :
                answered_questions += 1
                if submitted_answers[str(question.id)] == question.correct_option:
                    score += 1

        # Handle empty submission
        if answered_questions == 0:
            flash('You did not answer any questions. Your score is 0.', 'warning')
        else:
            flash(f'You answered {answered_questions} out of {total_questions} questions. Your score is {score}/{total_questions}.', 'success')

        score= score/quiz.no_of_questions * 100  # Convert to percentage
        quiz.total_attempted += 1  # Increment total attempts for the quiz
        db.session.commit()
        # Store answers in session to pass them to the results page
        session['submitted_answers'] = submitted_answers  # Ensure session key is correctly stored
        new_score = Scores(
        time_stamp_of_attempt=datetime.now(),
        score=score,
        submitted_answers=submitted_answers,
        quiz_id=quiz_id,
        user_id=session.get('user_id')  # Use .get() to avoid KeyError if user_id is missing
        )
        db.session.add(new_score)
        db.session.commit()

        return redirect(url_for('scores'))

    return render_template('user/attempt_quiz.html', quiz=quiz, questions=questions, quiz_duration=quiz_duration)


@app.route('/user/scores')
@auth_required
def scores():
    scores = Scores.query.filter_by(user_id=session.get('user_id')).order_by(Scores.time_stamp_of_attempt.desc()).all()
    return render_template('user/scores.html' ,scores=scores) 

@app.route('/user/delete_score/<int:score_id>', methods=['POST'])
@auth_required
def delete_score(score_id):
    score = Scores.query.get_or_404(score_id)
    db.session.delete(score)
    db.session.commit()
    flash('Score deleted successfully')
    return redirect(url_for('scores'))

@app.route('/user/self_assess/<int:score_id>')
@auth_required
def self_assess(score_id):
    score = Scores.query.get_or_404(score_id)
    quiz = Quiz.query.get_or_404(score.quiz_id)
    questions = Questions.query.filter_by(quiz_id=score.quiz_id).all()
    answers = score.submitted_answers

    return render_template('user/self_assess.html', quiz=quiz, questions=questions, score=score, answers=answers)

@app.route('/user/user_summary')
@auth_required
def user_summary():
    user_id = session.get('user_id')  # Get the logged-in user's ID

    # Fetch user details
    user = User.query.get_or_404(user_id)

    # Leaderboard: Fetch all users and calculate their average scores
    leaderboard = (
        db.session.query(
            User.id,
            User.name,
            db.func.sum(Scores.score).label('total_score'),
            db.func.count(Scores.id).label('quizzes_attempted')
        )
        .join(Scores, Scores.user_id == User.id)
        .group_by(User.id)
        .order_by(db.func.sum(Scores.score).desc())
        .all()
    )

    # Calculate leaderboard position
    leaderboard_position = next((index + 1 for index, u in enumerate(leaderboard) if u.id == user_id), None)

    # Subject-wise Performance
    subject_performance = (
        db.session.query(
            Subject.name.label('subject_name'),
            db.func.avg(Scores.score).label('average_score')
        )
        .join(Quiz, Quiz.subject_id == Subject.id)
        .join(Scores, Scores.quiz_id == Quiz.id)
        .filter(Scores.user_id == user_id)
        .group_by(Subject.name)
        .all()
    )
    subject_scores = {subject.subject_name: subject.average_score for subject in subject_performance}

    # Quiz-wise Performance
    quiz_performance = (
        db.session.query(
            Quiz.name.label('quiz_name'),
            Scores.score.label('score')
        )
        .join(Scores, Scores.quiz_id == Quiz.id)
        .filter(Scores.user_id == user_id)
        .order_by(Scores.time_stamp_of_attempt)
        .all()
    )
    quiz_labels = [quiz.quiz_name for quiz in quiz_performance]
    quiz_scores = [quiz.score for quiz in quiz_performance]

    # Month-wise Performance
    month_performance = (
        db.session.query(
            db.func.strftime('%Y-%m', Scores.time_stamp_of_attempt).label('month'),
            db.func.avg(Scores.score).label('average_score')
        )
        .filter(Scores.user_id == user_id)
        .group_by(db.func.strftime('%Y-%m', Scores.time_stamp_of_attempt))
        .order_by(db.func.strftime('%Y-%m', Scores.time_stamp_of_attempt))
        .all()
    )
    month_labels = [month.month for month in month_performance]
    month_scores = [month.average_score for month in month_performance]
    #no of quiz attended

    # User details
    quizzes_attended = Scores.query.filter_by(user_id=user_id).count()
    missed_quizzes = Quiz.query.count() - quizzes_attended
    user_details = {
        'name': user.name,
        'id': user.id,
        'position': leaderboard_position,
        'quizzes_attended': quizzes_attended,
        'average_score': db.session.query(db.func.avg(Scores.score)).filter_by(user_id=user_id).scalar() or 0,
        'subject_scores': subject_scores,
        'missed_quizzes': missed_quizzes
    }

    # Pass data to template
    return render_template(
        'user/user_summary.html',
        leaderboard=leaderboard,
        user_details=user_details,
        subject_labels=[subject.subject_name for subject in subject_performance],
        subject_scores=[subject.average_score for subject in subject_performance],
        quiz_labels=quiz_labels,
        quiz_scores=quiz_scores,
        month_labels=month_labels,
        month_scores=month_scores
    )
## Admin routes 

@app.route('/admin/dashboard')
@admin_required
@auth_required
def admin_dashboard():
    # Fetch all subjects and their chapters
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    #update question count for each chapter
    for chapter in chapters:
        question_count = Questions.query.filter(Questions.chapter_id == chapter.id).count()
        chapter.no_of_questions = question_count
    db.session.commit()

    if not subjects:
        flash('No subjects found, click + to add subjects')
    return render_template('/admin/admin_dashboard.html', subjects=subjects, chapters=chapters)

## Subject Description page 
@app.route('/admin/subjects')
@admin_required
@auth_required
def subject():
    # Fetch all subjects
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)


## Add subjects 
@app.route('/admin/manage_subject')
@admin_required
def add_subject():
    usage='add'
    return render_template('admin/manage_subject.html', usage='add')

@app.route('/admin/manage_subject', methods=['POST'])
@admin_required
def add_subject_post():
    name=request.form.get('subject_name')
    description=request.form.get('description')
    category= request.form.get('category')

    if not name:
        flash('Subject name cannot be empty')
        return redirect(url_for('add_subject'))
    usage='add'
    subject=Subject.query.filter_by(name=name).first()
    if subject:
        flash('Subject already exists')
        return redirect(url_for('add_subject'))
    
    new_subject=Subject(name=name, Description=description, category=category)
    db.session.add(new_subject)
    db.session.commit()

    flash('Subject added successfully')

    return redirect(url_for('admin_dashboard'))

## Edit Subjects 
@app.route('/admin/manage_subject/<int:subject_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    usage = 'edit'
    if request.method == 'POST':
        subject.name = request.form.get('subject_name')
        subject.Description = request.form.get('description')
        subject.category = request.form['category']

        if subject.name=='' or subject.Description=='':
            flash('Please fill out all fields')
            return redirect(url_for('edit_subject', subject_id=subject_id))

        db.session.commit()
        flash('Subject updated successfully')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/manage_subject.html', subject=subject, usage='edit')

## Delete Subjects
@app.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
@admin_required
@auth_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    chapter = Chapter.query.filter_by(subject_id=subject_id).all()
    quiz = Quiz.query.filter_by(subject_id=subject_id).all()
    for q in quiz:
        question = Questions.query.filter_by(quiz_id=q.id).all()
        for ques in question:
            db.session.delete(ques)
        scores = Scores.query.filter_by(quiz_id=q.id).all()
        for score in scores:
            db.session.delete(score)

        db.session.delete(q)
        
    for chap in chapter:
        db.session.delete(chap)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully')
    return redirect(url_for('admin_dashboard'))

### manage chapters

##view chapters
@app.route('/admin/view_chapter/<int:chapter_id>')
@admin_required
@auth_required
def view_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
    no_of_quizzes = len(quizzes)
    return render_template('admin/view_chapter.html', chapter=chapter, quizzes=quizzes, no_of_quizzes=no_of_quizzes)

@app.route('/admin/manage_chapter/<int:subject_id>', methods=['GET','POST'])
@admin_required
@auth_required
def add_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    usage = "add"
    if request.method == 'POST':
        chapter_name = request.form.get('chapter_name')
        description = request.form.get('description')

        if not chapter_name :
            flash('Please fill out all fields')
            return redirect(url_for('add_chapter', subject_id=subject_id , usage='add'))

        # Add the new chapter to the database
        new_chapter = Chapter(name=chapter_name, Description=description, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
        flash('Chapter added successfully')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/manage_chapter.html', subject_id=subject_id , subject=subject, usage='add')

#edit chapter
@app.route('/manage_chapter/<int:chapter_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    usage = 'edit'
    if request.method == 'POST':
        chapter.name = request.form.get('chapter_name')
        chapter.Description = request.form.get('description')

        if not chapter.name :
            flash('Please fill out all fields')
            return redirect(url_for('edit_chapter', chapter_id=chapter_id, usage='edit'))

        db.session.commit()
        flash('Chapter updated successfully')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/manage_chapter.html', chapter=chapter, usage='edit')

@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
@admin_required
@auth_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()  # Fetch all quizzes for the chapter

    # Loop through each quiz and delete related scores and questions
    for quiz in quizzes:
        # Delete all scores related to the quiz
        scores = Scores.query.filter_by(quiz_id=quiz.id).all()
        for score in scores:
            db.session.delete(score)

        # Delete all questions related to the quiz
        questions = Questions.query.filter_by(quiz_id=quiz.id).all()
        for question in questions:
            db.session.delete(question)

        # Delete the quiz itself
        db.session.delete(quiz)

    # Finally, delete the chapter
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully')
    return redirect(url_for('admin_dashboard'))
## quiz dashboard
@app.route('/admin/quiz')
@admin_required
@auth_required
def quiz_dashboard():
    # Fetch all subjects and their chapters
    quizzes = Quiz.query.all()
    questions = Questions.query.all()
    # Update the question count for each quiz

    for quiz in quizzes:
        question_count = Questions.query.filter(Questions.quiz_id == quiz.id).count()
        quiz.no_of_questions = question_count
    db.session.commit()  # Commit the updates to the database

    if not quizzes:
        flash('No quizzes found, click + to add quizzes')
    return render_template('/admin/quiz.html', quizzes=quizzes,questions=questions)

@app.route('/admin/toggle_quiz_status/<int:quiz_id>', methods=['POST'])
@admin_required
def toggle_quiz_status(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    data = request.get_json()
    quiz.is_active = data.get('is_active', False)
    db.session.commit()
    return jsonify({'success': True})

## Add Quiz
@app.route('/admin/manage_quiz/add/<int:chapter_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def add_quiz(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    usage = 'add'

    if request.method == 'POST':
        name = request.form.get('quiz_name')
        description = request.form.get('description')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        time_duration = request.form.get('time_duration')
        is_active = request.form.get('is_active')
        # Convert start_date and end_date to Python date objects
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        except ValueError:
            flash('Invalid start date format. Please use YYYY-MM-DD.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            flash('Invalid end date format. Please use YYYY-MM-DD.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

         # Validate and parse time_duration
        try:
            if time_duration:  # Ensure time_duration is not empty
                hours, minutes = map(int, time_duration.split(":"))
                time_duration = time(hour=hours, minute=minutes)  # Format as HH:MM
            else:
                time_duration = None  # Default to None if not provided
        except ValueError:
            flash('Invalid time duration format. Please use HH:MM.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        # Validate other fields
        if not name:
            flash('Quiz name is required.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        # Check if quiz already exists
        quiz = Quiz.query.filter_by(name=name).first()
        if quiz:
            flash('Quiz already exists.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        # Get subject_id from the chapter
        subject_id = chapter.subject_id

        # Add the new quiz to the database
        new_quiz = Quiz(
            name=name,
            description=description,
            chapter_id=chapter_id,
            start_date=start_date,
            end_date=end_date,
            time_duration=time_duration,
            is_active=is_active == 'true',  # Convert string to boolean
            subject_id=subject_id
        )
        db.session.add(new_quiz)
        db.session.commit()

        flash('Quiz added successfully.')
        return redirect(url_for('quiz_dashboard'))

    return render_template('admin/manage_quiz.html',chapter_id=chapter_id, chapter=chapter, usage='add')
## Edit Quiz
@app.route('/admin/manage_quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    usage = 'edit'

    if request.method == 'POST':
        name = request.form.get('quiz_name')
        description = request.form.get('description')
        chapter_id = request.form.get('chapter_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        time_duration = request.form.get('time_duration')
        is_active = request.form.get('is_active')
        # Convert start_date and end_date to Python date objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
       
               # Validate and parse time_duration
        try:
            if time_duration:  # Ensure time_duration is not empty
                hours, minutes = map(int, time_duration.split(":"))
                time_duration = time(hour=hours, minute=minutes)  # Format as HH:MM
            else:
                time_duration = None  # Default to None if not provided
        except ValueError:
            flash('Invalid time duration format. Please use HH:MM.')
            return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        quiz.name = name
        quiz.description = description
        quiz.chapter_id = chapter_id
        quiz.start_date =start_date
        quiz.end_date = end_date
        quiz.time_duration = time_duration
        quiz.is_active =is_active=='true'

        db.session.commit()
        flash('Quiz updated successfully')
        return redirect(url_for('quiz_dashboard'))

    return render_template('admin/manage_quiz.html', quiz=quiz, usage='edit')

## Delete Quiz
@app.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
@admin_required
@auth_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    try:
        # Delete all scores related to the quiz
        scores = Scores.query.filter_by(quiz_id=quiz.id).all()
        for score in scores:
            db.session.delete(score)

        # Delete all questions related to the quiz
        questions = Questions.query.filter_by(quiz_id=quiz.id).all()
        for question in questions:
            db.session.delete(question)

        # Delete the quiz itself
        db.session.delete(quiz)

        # Commit the changes to the database
        db.session.commit()
        flash('Quiz and its related data deleted successfully.')
    except Exception as e:
        # Rollback in case of an error
        db.session.rollback()
        flash(f'An error occurred while deleting the quiz: {str(e)}', 'error')

    return redirect(url_for('quiz_dashboard'))
##view question
@app.route('/admin/view_question/<int:question_id>')
@admin_required
@auth_required
def view_question(question_id):
    question = Questions.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(question.quiz_id)
    return render_template('admin/view_question.html', question=question, quiz=quiz)


### Manage Questions
@app.route('/admin/manage_question/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    usage = "add"
    if request.method == 'POST':
        title = request.form.get('title')
        question_statement = request.form.get('question_statement')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_option = request.form.get('correct_option')

        if not question_statement or not option1 or not option2 or not option3 or not option4 or not correct_option:
            flash('Please fill out all fields')
            return redirect(url_for('add_question', quiz_id=quiz_id, usage='add'))
        chapter_id = quiz.chapter_id
        # Add the new question to the database
        new_question = Questions(
            title=title,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option,
            quiz_id=quiz_id,
            chapter_id=chapter_id
        )
        
        # Increment the no_of_questions column in the Quiz table
        quiz.no_of_questions = (quiz.no_of_questions or 0) + 1  # Handle None case
        db.session.commit()

        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully')
        return redirect(url_for('quiz_dashboard'))

    return render_template('admin/manage_question.html', quiz_id=quiz_id, quiz=quiz, usage='add')

# Edit Question
@app.route('/admin/manage_question/edit/<int:question_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def edit_question(question_id):
    question = Questions.query.get_or_404(question_id)
    usage = 'edit'
    if request.method == 'POST':
        question.title = request.form.get('title')
        question.question_statement = request.form.get('question_statement')
        question.option1 = request.form.get('option1')
        question.option2 = request.form.get('option2')
        question.option3 = request.form.get('option3')
        question.option4 = request.form.get('option4')
        question.correct_option = request.form.get('correct_option')

        if  not question.question_statement or not question.option1 or not question.option2 or not question.option3 or not question.option4 or not question.correct_option:
            flash('Please fill out all fields')
            return redirect(url_for('edit_question', question_id=question_id, usage='edit'))

        db.session.commit()
        flash('Question updated successfully')
        return redirect(url_for('quiz_dashboard'))

    return render_template('admin/manage_question.html', question=question, usage='edit')


# Delete Question
@app.route('/delete_question/<int:question_id>', methods=['POST'])
@admin_required
@auth_required
def delete_question(question_id):
    question = Questions.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    quiz=Quiz.query.get(question.quiz_id)
    # decrement the no_of_questions column in the Quiz table
    quiz.no_of_questions = (quiz.no_of_questions ) - 1  # Handle None case
    db.session.commit()

    flash('Question deleted successfully')
    return redirect(url_for('quiz_dashboard'))

## manage user
@app.route('/admin/manage_user')
@admin_required
def manage_user():
    # Fetch active users (not flagged), sorted by average score in descending order
    users = (
        db.session.query(User)
        .outerjoin(Scores, Scores.user_id == User.id)
        .filter(User.flagged == 0, User.is_admin == False)
        .group_by(User.id)
        .order_by(db.func.sum(Scores.score).desc().nullslast())  # Sort by average score, handle nulls
        .all()
    )

    # Fetch flagged users, sorted by average score in descending order
    users_flagged = (
        db.session.query(User)
        .outerjoin(Scores, Scores.user_id == User.id)
        .filter(User.flagged == 1, User.is_admin == False)
        .group_by(User.id)
        .order_by(db.func.sum(Scores.score).desc().nullslast())  # Sort by average score, handle nulls
        .all()
    )

    # Render the template with the sorted users
    return render_template('admin/manage_user.html', users=users, qualify=users_flagged)

#flag user
@app.route('/admin/flag_user/<int:user_id>')
@admin_required
def flag_user(user_id):
    user = User.query.get_or_404(user_id)
    user.flagged = True
    db.session.commit()
    flash('User flagged successfully.')
    return redirect(url_for('manage_user'))

@app.route('/admin/unflag_user/<int:user_id>')
@admin_required
def unflag_user(user_id):
    user = User.query.get_or_404(user_id)
    user.flagged = False
    db.session.commit()
    flash('User unflagged successfully.')
    return redirect(url_for('manage_user'))


@app.route('/admin/summary')
@admin_required
@auth_required
def admin_summary():
    # Total Statistics
    total_students = User.query.count()
    total_chapters = Chapter.query.count()
    total_subjects = Subject.query.count()
    total_quizzes = Quiz.query.count()
    total_questions = Questions.query.count()

    # Subject-wise Questions
    subject_questions_data = (
        db.session.query(
            Subject.name.label('subject_name'),
            db.func.count(Questions.id).label('question_count')
        )
        .join(Chapter, Chapter.subject_id == Subject.id)
        .join(Quiz, Quiz.chapter_id == Chapter.id)
        .join(Questions, Questions.quiz_id == Quiz.id)
        .group_by(Subject.name)
        .all()
    )
    subject_labels = [data.subject_name for data in subject_questions_data]
    subject_questions = [data.question_count for data in subject_questions_data]
    
    # Subject-wise Quizzes
    subject_quizzes_data = (
        db.session.query(
            Subject.name.label('subject_name'),
            db.func.count(Quiz.id).label('quiz_count')
        )
        .join(Chapter, Chapter.subject_id == Subject.id)
        .join(Quiz, Quiz.chapter_id == Chapter.id)
        .group_by(Subject.name)
        .all()
    )
    subject_quizzes = [data.quiz_count for data in subject_quizzes_data]
    print(subject_quizzes)
    # Subject-wise Performance (Average Score)
    subject_performance_data = (
        db.session.query(
            Subject.name.label('subject_name'),
            db.func.avg(Scores.score).label('average_score')
        )
        .join(Chapter, Chapter.subject_id == Subject.id)
        .join(Quiz, Quiz.chapter_id == Chapter.id)
        .join(Scores, Scores.quiz_id == Quiz.id)
        .group_by(Subject.name)
        .all()
    )
    subject_scores = [data.average_score or 0 for data in subject_performance_data]

    # Quiz-wise Students Attempted
    quiz_students_data = (
        db.session.query(
            Quiz.name.label('quiz_name'),
            db.func.count(Scores.user_id).label('students_attempted')
        )
        .join(Scores, Scores.quiz_id == Quiz.id)
        .group_by(Quiz.name)
        .all()
    )
    quiz_labels = [data.quiz_name for data in quiz_students_data]
    quiz_students = [data.students_attempted for data in quiz_students_data]

    # Flagged vs Unflagged Users (if is_flagged exists)
    flagged_users = User.query.filter_by(flagged=True).count() if hasattr(User, 'flagged') else 0
    unflagged_users = total_students - flagged_users

    # Pass all data to the template
    return render_template(
        'admin/admin_summary.html',
        total_students=total_students,
        total_chapters=total_chapters,
        total_subjects=total_subjects,
        total_quizzes=total_quizzes,
        total_questions=total_questions,
        subject_labels=subject_labels,
        subject_questions=subject_questions,
        subject_quizzes=subject_quizzes,
        subject_scores=subject_scores,
        quiz_labels=quiz_labels,
        quiz_students=quiz_students,
        flagged_users=flagged_users,
        unflagged_users=unflagged_users
    )
@app.route('/search', methods=['GET'])
@admin_required
def search():
    query = request.args.get('query', '').strip()  # Get the search query from the URL
    if not query:
        flash('Please enter a search term.', 'warning')
        return redirect(request.referrer or url_for('admin_dashboard'))

    # Search across Subjects, Chapters, Quizzes, and Questions
    subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
    chapters = Chapter.query.filter(Chapter.name.ilike(f'%{query}%')).all()
    quizzes = Quiz.query.filter(Quiz.name.ilike(f'%{query}%')).all()
    questions = Questions.query.filter(Questions.title.ilike(f'%{query}%')).all() + Questions.query.filter(Questions.question_statement.ilike(f'%{query}%')).all()
    users = User.query.filter(User.username.ilike(f'%{query}%')).all() + User.query.filter(User.name.ilike(f'%{query}%')).all()

    # Render the search results page
    return render_template(
        'admin/admin_search_results.html',
        query=query,
        subjects=subjects,
        chapters=chapters,
        quizzes=quizzes,
        questions=questions,
        users=users
    )


### AI routes 
from flask import jsonify, request,Blueprint
import os
from google import genai
from google.genai import types
from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from app import app
from datetime import datetime, date,timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pytesseract
from PIL import Image 
import re
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'



# Set up the Gemini API client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route('/explain_with_ai/<int:question_id>', methods=['GET'])
@auth_required

def explain_with_ai(question_id):

    try:
        # Fetch the question from the database
        question = Questions.query.get_or_404(question_id)
        correct_option = question.correct_option
        correct_answer = getattr(question, f"option{correct_option}")
        question_text = question.question_statement

        # Prepare the prompt for the AI
        prompt = f"Explain why the correct answer to the following question is correct in a structured format:\n\n" \
                 f"Question: {question.question_statement}\n" \
                 f"Options:\n1. {question.option1}\n2. {question.option2}\n3. {question.option3}\n4. {question.option4}\n\n" \
                 f"Correct Answer: {correct_answer}\n" \
                 f"Explanation type: precise to medium."

        # Prepare the content for the Gemini API
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        # Configure the response
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
        )

        # Call the Gemini API and stream the response
        explanation = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=contents,
            config=generate_content_config,
        ):
            explanation += chunk.text

        # Generate book recommendations
        books_prompt = f"Recommend 3 books for learning more about: {question_text}. For each book, provide a brief review (1-2 lines) and explain why someone should buy it."
        books_contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=books_prompt),
                ],
            ),
        ]
        books_response = client.models.generate_content(
            contents=books_contents,
            model="gemini-2.0-flash",
        )
        book_recommendations = books_response.text if hasattr(books_response, "text") else "No book recommendations available."

        def clean_text(text):
            # Convert *bold text* to <strong>bold text</strong>
            text = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', text)
            # Replace single * with <br> to create line breaks
            text = text.replace('*', '<br>').strip()
            # Replace ordered list numbers like 1., 2., with <ul><li> tags
            text = re.sub(r'(\d+)\.\s*', r'<li>', text)  # Convert number+dot to start list item
            text = text.replace('</li>', '</li>')  # Ensure proper closing of list items
            text = f"<ul>{text}</ul>"  # Wrap the list items in <ul> tags
            return text

        # Apply cleaning to explanation and book recommendations
        cleaned_explanation = clean_text(explanation)
        cleaned_book_recommendations = clean_text(book_recommendations)

        # Stylish HTML output for explanation
        styled_explanation = f"""
            <div style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 10px; ">
                {cleaned_explanation}
            </div>
        """
        styled_recommendations = f"""
            <div style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 10px;">
                {cleaned_book_recommendations}
            </div>  
            """

        # Generate Google search link for book recommendations
        google_search_link = f"https://www.google.com/search?q=best+books+on+{question_text.replace(' ', '+')}"

        # Generate YouTube search link
        youtube_search_query = f"best YouTube videos for {question_text}"
        youtube_search_link = f"https://www.youtube.com/results?search_query={youtube_search_query.replace(' ', '+')}"

        print(styled_explanation, styled_recommendations, google_search_link, youtube_search_link)

        # Return the explanation, book recommendations, and YouTube link
        return jsonify({
            "explanation": styled_explanation or "Explanation not available.",
            "google_books_link": google_search_link,
            "youtube_search_link": youtube_search_link,
            "book_recommendations": styled_recommendations or "No book recommendations available."
        })

    except Exception as e:
        print("Error generating explanation:", str(e))
        return jsonify({"error": "Explanation generation failed", "details": str(e)}), 500
    


# ✅ Route to Ask Questions & Generate Quiz
@app.route('/user/ask_question', methods=['GET', 'POST'])
def ask_question():
    if request.method == 'POST':
        user_question = request.form.get('question', '').strip()
        difficulty_level = request.form.get('difficulty', 'medium')

        if not user_question:
            return jsonify({'error': 'No question provided'}), 400

        try:
            # Prepare the prompt for the AI
            prompt = f"Generate {difficulty_level} quiz questions on the topic: {user_question}, with answers and explanations."

            # Prepare the content for the Gemini API
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]

            # Call the Gemini API
            response = client.models.generate_content(
                contents=contents,
                model="gemini-2.0-flash",
            )

            # Parse the response
            questions_answers = response.text if hasattr(response, "text") else "The AI didn't generate valid responses. Please try again."
            #print(questions_answers)
            # Cleaning function to format the text properly
            def clean_text(text):
                text = re.sub(r'\*\*(Question \d+:)\*\*', r'<strong>\1</strong>', text)    # Bold formatting  # Bold formatting
                text = text.replace('*', '').strip()  # Replace * with newline
                return text
            cleaned_response = clean_text(questions_answers)

            # Store the context in session for follow-up chat
            session['chat_context'] = f"Topic: {user_question}\nAI Response: {cleaned_response}"

            return jsonify({"response": cleaned_response})

        except Exception as e:
            return jsonify({"error": "AI processing failed", "details": str(e)}), 500

    return render_template('user/ask_question.html')

# ✅ Route to Analyze Image and Extract Text
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']

    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    try:
        # Extract text from the image using Tesseract OCR
        image = Image.open(image_file)
        extracted_text = pytesseract.image_to_string(image).strip()
        print(extracted_text)
        if not extracted_text:
            return jsonify({'error': 'No text detected in image'}), 400

        # Use Gemini AI to explain the extracted text
        prompt = f"Explain in depth the following text:\n{extracted_text}"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        # Call the Gemini API
        response = client.models.generate_content(
            contents=contents,
            model="gemini-2.0-flash",
        )

        explanation = response.text if hasattr(response, "text") else "The AI didn't generate valid responses. Please try again."

        # Store image analysis in session context for follow-up chat
        session['chat_context'] = f"Extracted Text: {extracted_text}\nAI Explanation: {explanation}"

        return jsonify({"response": explanation})

    except Exception as e:
        return jsonify({'error': 'Failed to analyze image', 'details': str(e)}), 500
    

# ✅ Route to Handle Follow-up Chat (AI Remembers Context)
@app.route('/continue_chat', methods=['POST'])
def continue_chat():
    user_input = request.form.get('chat_input', '').strip()
    context = session.get('chat_context', '')

    if not user_input:
        return jsonify({'error': 'No question provided'}), 400

    try:
        # Prepare the prompt with the conversation context
        prompt = f"Here is the conversation context:\n{context}\nUser asked: {user_input}\nProvide a meaningful response."
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        # Call the Gemini API
        response = client.models.generate_content(
            contents=contents,
            model="gemini-2.0-flash",
        )

        ai_response = response.text if hasattr(response, "text") else "The AI didn't generate valid responses. Please try again."
        print(ai_response)
        # Update session context with the new conversation
        session['chat_context'] += f"\nUser: {user_input}\nAI: {ai_response}"

        return jsonify({"response": ai_response})

    except Exception as e:
        return jsonify({'error': 'AI processing failed', "details": str(e)}), 500