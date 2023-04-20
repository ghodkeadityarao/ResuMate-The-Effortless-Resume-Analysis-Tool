import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from jobdescription import getJob
from extraction_score import *
from skill_show import *
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/pdf'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///aditya.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['resumeName'] = None
app.config['path'] = None
app.config['text_pdfminer'] = None
app.config['text_resparser'] = None
app.config['quantify_impact1'] = None
app.config['repetition1'] = None
app.config['actionverbs1'] = None
app.config['bulletpoints1'] = None
app.config['buzzwords1'] = None
app.config['dates1'] = None
app.config['details1'] = None
app.config['education1'] = None
app.config['experience1'] = None
app.config['fillerwords1'] = None
app.config['passivevoices1'] = None
app.config['pronouns1'] = None
app.config['resume_length1'] = None
app.config['skills1'] = None
app.config['spellingcheck1'] = None
app.config['verbs1'] = None
app.config['Impact'] = None
app.config['Brevity'] = None
app.config['Style'] = None
app.config['Section'] = None
app.config['total'] = None
app.config['summary1'] = None

with app.app_context():
    db = SQLAlchemy(app)

class Details(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    UserName = db.Column(db.String(45), nullable=False)
    Email_Address = db.Column(db.String(45), nullable=False)
    Password = db.Column(db.String(45), nullable=False)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.UserName}"

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/loginpage', methods=['GET', 'POST'])
def login():
    if (request.method == 'POST'):
        uname = request.form['uname']
        email = request.form['email']
        pass1 = request.form['pass']
        dt = Details(UserName=uname, Email_Address=email, Password=pass1)
        db.session.add(dt)
        db.session.commit()
    return render_template('loginpage.html')

@app.route('/start', methods=['GET', 'POST'])
def start():
    try:
        if request.method == 'POST':  
            file = request.files['file']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  
            app.config['resumeName'] = filename
            app.config['path'] = "static/pdf/"+app.config['resumeName']
        return render_template('start1.html')
    except:
        return "ERROR"

@app.route('/jobdesc')
def jobdesc():
    try:
        jobname = getJob(app.config['path'])
        vrbs = skilldisplay(jobname)
        return render_template('jobdesc.html', resumeName=app.config['resumeName'], jobname=jobname, vrbs=vrbs)
    except:
        return "ERROR"
    
@app.route('/moreskills')
def more_skills():
    try:
        jobname = getJob(app.config['path'])
        vrbs = skilldisplay(jobname)
        return render_template('moreskills.html', l=len(vrbs), vrbs=vrbs)
    except:
        return "ERROR"

@app.route('/resumeanalysis')
def resumeanalysis():
    try:
        app.config['text_pdfminer'] = extract_text_from_pdf(app.config['path'])
        app.config['text_resparser'] = extract_text_from_pyresparser(app.config['path'])
        app.config['quantify_impact1'] = quantify_impact(app.config['text_pdfminer'])
        app.config['repetition1'] = find_repeated_sentences(app.config['text_pdfminer'])
        app.config['actionverbs1'] = identify_weak_action_verbs(app.config['text_pdfminer'])
        app.config['bulletpoints1'] = num_bullet_points(app.config['text_resparser'], app.config['path'])
        app.config['buzzwords1'] = buzzwords(app.config['text_pdfminer'])
        app.config['dates1'] = extract_dates(app.config['text_pdfminer'])
        app.config['details1'] = extract_details(app.config['text_pdfminer'])
        app.config['education1'] = education(app.config['text_pdfminer'])
        app.config['experience1'] = experience(app.config['text_resparser'], app.config['text_pdfminer'])
        app.config['fillerwords1'] = count_filler_words(app.config['text_pdfminer'])
        app.config['passivevoices1'] = passive_voices(app.config['text_pdfminer'])
        app.config['pronouns1'] = personal_pronouns(app.config['text_pdfminer'])
        app.config['resume_length1'] = resume_length(app.config['text_pdfminer'])
        app.config['skills1'] = skills_extract(app.config['text_pdfminer'])
        app.config['spellingcheck1'] = check_spelling_mistakes(app.config['text_pdfminer'])
        app.config['verbs1'] = find_repeating_verbs(app.config['text_pdfminer'])
        app.config['summary1'] = summary(app.config['text_pdfminer'])

        app.config['Impact'] = app.config['quantify_impact1']+app.config['repetition1']+app.config['actionverbs1']+app.config['spellingcheck1']+app.config['verbs1']
        app.config['Brevity'] = app.config['resume_length1']+app.config['bulletpoints1']+app.config['fillerwords1']
        app.config['Section'] = app.config['buzzwords1']+app.config['dates1']+app.config['details1']+app.config['pronouns1']+app.config['passivevoices1']
        app.config['Style'] = app.config['experience1']+app.config['education1']+app.config['skills1']+app.config['summary1']
        app.config['total']=app.config['Impact']+app.config['Brevity']+app.config['Section']+app.config['Style']

        txt = print_text(app.config['total'])
        return render_template('resumeanalysis.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], txt=txt)
    except:
        return "Your resume is not in ATS format"

@app.route('/quantify_impact')
def quantify_impact_html():
 
    return render_template('quantifyImpact.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['quantify_impact1']) 

@app.route('/repetition')
def repetition():
    vrbs = print_rep_sen(app.config['text_pdfminer'])
    if(len(vrbs) == 0):
        opt = "Your resume doesnot contain any repeating sentences.."
    else:
        opt = "Here are the repeating sentences from your resume:"
    return render_template('repetition.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['repetition1'], opt=opt, l = len(vrbs), vrbs=vrbs)

@app.route('/verbs')
def verbs():
    vrbs = print_rep_verbs(app.config['text_pdfminer'])
    if(len(vrbs) == 0):
        opt = "Your resume doesnot contain any repeating verbs.."
    else:
        opt = "Here are the repeating verbs from your resume:"
    return render_template('verbs.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['verbs1'], opt=opt, l = len(vrbs), vrbs=vrbs)

@app.route('/spellingcheck')
def spellingcheck():
    return render_template('spellingcheck.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['spellingcheck1'])

@app.route('/actionverbs')
def actionverbs():
    vrbs = print_weak_action(app.config['text_pdfminer'])
    if(len(vrbs) == 0):
        opt = "Your resume doesnot contain any weak action verbs.."
    else:
        opt = "Here are the weak action verbs from your resume:"    
    return render_template('actionverbs.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['actionverbs1'], opt=opt, l = len(vrbs), vrbs=vrbs)

@app.route('/resumelength')
def resumelength():
    l = res_len(app.config['text_pdfminer'])
    return render_template('resumelength.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['resume_length1'], l=l)

@app.route('/bulletpoints')
def bulletpoints():
 
    return render_template('bullets.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['bulletpoints1'])

@app.route('/fillerwords')
def fillerwords():
    vrbs = print_filler(app.config['text_pdfminer'])
    if(len(vrbs) == 0):
        opt = "Your resume doesnot contain any filler words.."
    else:
        opt = "Here the filler words from your resume:"
    return render_template('fillerwords.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['fillerwords1'], opt=opt, l = len(vrbs), vrbs=vrbs)

@app.route('/buzzwords')
def buzzwords_score():
    vrbs = print_buzz(app.config['text_pdfminer'])
    if(len(vrbs) == 0):
        opt = "Your resume doesnot contain any buzzwords.."
    else:
        opt = "Here are the buzzwords from your resume:"
    return render_template('buzzwords.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['buzzwords1'], opt=opt, l = len(vrbs), vrbs=vrbs)

@app.route('/dates')
def dates():
 
    return render_template('dates.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['dates1'])

@app.route('/personaldetails')
def personaldetails():
    vrbs = print_details(app.config['text_pdfminer'])
    if(len(vrbs) == 0):
        opt = "There is no urls or links in your resume"
    else:
        opt = "Your resume contains all the details required.."
 
    return render_template('details.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['details1'], opt=opt)

@app.route('/personalpronouns')
def personalpronouns():
    vrbs = print_pronouns(app.config['text_pdfminer'])
    if(len(vrbs) == 0):
        opt = "Your resume doesnot contain any pronouns.."
    else:
        opt = "Here the pronouns from your resume:"
    return render_template('pronouns.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['pronouns1'], opt=opt, l = len(vrbs), vrbs=vrbs)

@app.route('/passivevoices')
def passivevoices():
    vrbs = print_passive(app.config['text_pdfminer'])
    if(len(vrbs) == 0):
        opt = "Your resume doesnot contain any passive voice sentences.."
    else:
        opt = "Here the passive voices from your resume:"
    return render_template('passive.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['passivevoices1'], opt=opt, l = len(vrbs), vrbs=vrbs)

@app.route('/experience')
def experience_score():
 
    return render_template('experience.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['experience1'])

@app.route('/education')
def education_score():
 
    return render_template('education.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['education1'])

@app.route('/skills')
def skills_score():

    return render_template('skills.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['skills1'])

@app.route('/summary')
def summary_score():

    return render_template('summary.html', resumeName=app.config['resumeName'], imp=app.config['Impact'], bre=app.config['Brevity'], sty=app.config['Section'], sec=app.config['Style'], tot=app.config['total'], marks=app.config['summary1'])
if __name__ == "__main__":
    app.run(debug=True)

