from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db=SQLAlchemy(app)

class Subject(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(32), unique=True)
    Description=db.Column(db.String(256), nullable=False)
    category=db.Column(db.String(32), nullable=True)
    chapters = db.relationship('Chapter', backref='subject', lazy=True)
    quizzes = db.relationship('Quiz', backref='subject', lazy=True)  
    
class Chapter(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(32), unique=True)
    Description=db.Column(db.String(256), nullable=True)
    no_of_questions=db.Column(db.Integer, nullable=True)
    subject_id=db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)  
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True)  
    questions = db.relationship('Questions', backref='chapter', lazy=True)

class Quiz(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  
    description=db.Column(db.String(256), nullable=True)
    start_date=db.Column(db.Date, nullable=True)
    end_date=db.Column(db.Date, nullable=True)
    time_duration=db.Column(db.Time, nullable=True)
    remarks=db.Column(db.String(256), nullable=True)
    no_of_questions=db.Column(db.Integer, nullable=True)
    is_active=db.Column(db.Boolean, nullable=False, default=False)

    questions = db.relationship('Questions', backref='quiz', lazy=True)
    total_attempted=db.Column(db.Integer, nullable=False, default=0)

    scores = db.relationship('Scores', backref='quiz', lazy=True)
    
    subject_id=db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    chapter_id= db.Column(db.Integer, db.ForeignKey('chapter.id'),nullable=False)
    

class Questions(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(256), nullable=False)
    question_statement=db.Column(db.String(256), nullable=False)
    option1=db.Column(db.String(64), nullable=False)
    option2=db.Column(db.String(64), nullable=False)
    option3=db.Column(db.String(64), nullable=False)
    option4=db.Column(db.String(64), nullable=False)
    correct_option=db.Column(db.String(64), nullable=False)
   
    quiz_id=db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    
    chapter_id=db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    
class Scores(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    time_stamp_of_attempt=db.Column(db.DateTime, nullable=False)
    score=db.Column(db.Integer, nullable=False)
    submitted_answers = db.Column(db.JSON, nullable=True)
    quiz_id=db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class User(db.Model):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    passhash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    qualification = db.Column( db.String(64), nullable=True)
    email = db.Column(db.String(64), unique=True, nullable=True)
    dob = db.Column(db.Date, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    flagged = db.Column(db.Boolean, nullable=False, default=False)
    scores = db.relationship('Scores', backref='user', lazy=True)
    

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash=generate_password_hash(password)
                                             
    def check_password(self, password):
        return check_password_hash(self.passhash, password)
    

with app.app_context():
    db.create_all()
    
    # create admin if admin not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        password_hash=generate_password_hash('admin')
        admin=User(username='admin', passhash=password_hash, name='admin',qualification='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()