import re
import collections
import enchant
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from dateutil import parser
from datetime import datetime
from pyresparser import ResumeParser
from dateparser.search import search_dates
import fitz
from pdfminer.high_level import extract_text
import pandas as pd


nlp = spacy.load("en_core_web_sm")
d = enchant.Dict("en_US")

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def extract_text_from_pyresparser(pdf_path):
    return ResumeParser(pdf_path).get_extracted_data()

resume_score = 0
# Impact:

def quantify_impact(text):    
    percentages = re.findall(r"\d+(?:\.\d+)?%", text)
    float_numbers = re.findall(r"\d+\.\d+", text) 
    matches = re.findall(r"\b\d{1,3}\b", text)
    a = len(percentages) + len(float_numbers) + len(matches)
    final_score = 0
    if(a >= 25):
        final_score += 5
    elif(a > 23 and a <= 25):
        final_score += 4  
    elif(a > 21 and a <= 23):
        final_score += 3 
    elif(a > 19 and a <= 21):
        final_score += 2 
    elif(a > 17 and a <= 19):
        final_score += 1 
    else:
        final_score += 0                                        
    return final_score

def find_repeated_sentences(text):
    sentences = re.split('[.!?]', text)
    counts = collections.defaultdict(int)
    c = 0
    final_score = 0
    for sentence in sentences:
        if sentence.strip() != '':
            counts[sentence.strip()] += 1        
    for sentence, count in counts.items():
        if count > 1:
            c += 1
    if(c == 0):
        final_score += 5
    elif(c == 1):
        final_score += 4 
    elif(c == 2):
        final_score += 3 
    elif(c == 3):
        final_score += 2 
    elif(c == 4):
        final_score += 1 
    else:
        final_score += 0   
    return final_score                                   

def find_repeating_verbs(text):
    pattern = r'\b(\w+ing\s\w+)\b.*\b\1\b'
    matches = re.findall(pattern, text)
    rep = len(matches)
    final_score = 0
    if(rep == 0):
        final_score += 5
    elif(rep == 1):
        final_score += 4 
    elif(rep == 2):
        final_score += 3 
    elif(rep == 3):
        final_score += 2 
    elif(rep == 4):
        final_score += 1 
    else:
        final_score += 0    
    return final_score                                            

def check_spelling_mistakes(text):
    words = text.split()
    mis = []
    for word in words:
        if not d.check(word):
            mis.append(word)
    m = len(mis)
    final_score = 0
    if(m <= 50):
        final_score += 5
    elif(m > 50 and m < 70):
        final_score += 4 
    elif(m >= 70 and m < 90):
        final_score += 3 
    elif(m >= 90 and m < 100):
        final_score += 2 
    elif(m >= 100 and m < 150):
        final_score += 1 
    else:
        final_score += 0      
    return final_score        
            # print(f"Possible spelling mistake: {word}. Suggestions: {suggestions}")

weak_action_verbs = ['do', 'make', 'go', 'get', 'take']

def identify_weak_action_verbs(text):
    words = word_tokenize(text.lower())

    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]

    pos_tags = nltk.pos_tag(words)

    weak_verbs = [word for word, pos in pos_tags if pos.startswith('VB') and word in weak_action_verbs]
    m = len(weak_verbs)
    final_score = 0
    if(m == 0):
        final_score += 5
    elif(m == 1):
        final_score += 4 
    elif(m == 2):
        final_score += 3 
    elif(m == 3):
        final_score += 2 
    elif(m == 4):
        final_score += 1 
    else:
        final_score += 0
    return final_score    


#BREVITY:

def resume_length(text):
    m = len(text.split())
    final_score = 0
    if(m >= 475 and m <= 600):
        final_score += 8  
    elif(m > 450 and m < 475):
        final_score += 5
    elif(m > 300 and m <= 450):
        final_score += 3    
    elif(m > 900 or m < 300):
        final_score += 0   
    return final_score    

def num_bullet_points(text, path):
    doc = fitz.open(path)
    count = 0
    for i in range(text['no_of_pages']):
        page = doc[i]
        paths = page.get_drawings() 
        for path in paths:
            for item in path["items"]:
                if item[0] == "l":  # line
                    count += 1
                elif item[0] == "re":
                    count += 1
                elif item[0] == "qu":
                    count += 1
                elif item[0] == "c":
                    count += 1
                elif item[0] in ["Tj", "TJ"]:  
                    count += 1 if isinstance(item[1], str) else "".join(item[1])
    final_score = 0
    if(count > 100):
        final_score += 7
    elif(count > 0 and count < 100):                         
        final_score += 3
    else:
        final_score += 0    
    return final_score    

def count_filler_words(text):
    superfluous_words = ['I am writing to apply for', 'Responsible for', 'Excellent communication skills', 'Detail-oriented', 
                     'Team player', 'Results-driven', 'Self-starter', 'Hardworking', 'Dynamic', 'Proactive', 'Highly motivated', 
                     'Innovative', 'Ability to work under pressure', 'Outside-the-box thinker', 'Creative problem solver', 
                     'Passionate', 'References available upon request', 'Utilized', 'Assisted with', 'Successfully']
    m1 = []
    for word in superfluous_words:
        if word in text:
            m1.append(word)
    m = len(m1)        
    final_score = 0
    if(m == 0):
        final_score += 7
    elif(m == 1):
        final_score += 5 
    elif(m == 2):
        final_score += 3 
    elif(m == 3):
        final_score += 2 
    elif(m == 4):
        final_score += 1 
    else:
        final_score += 0      
    return final_score      

#STYLE

def buzzwords(text):

    buzz = ['Managed', 'Influenced', 'Motivated', 'Guided', 'Supervised', 'Hired', 'Inspired', 'Facilitated', 'Enabled', 'Directed', 'Maintained', 'Cultivated', 'Trained', 'Taught', 'Aligned', 'Consulted', 'Advised', 'Educated', 'Advocated', 'Resolved', 'Informed', 'Coached', 'Negotiated', 'Partnered', 'Secured', 'Acquired', 'Forged', 'Completed', 'Attained', 'Awarded', 'Earned', 'Demonstrated', 'Exceeded', 'Reached', 'Targeted', 'Outperformed', 'Surpassed', 'Showcased', 'Succeeded', 'Conveyed', 'Defined', 'Authored', 'Critiqued', 'Corresponded', 'Composed', 'Documented', 'Counseled', 'Edited', 'Persuaded', 'Illustrated', 'Lobbied', 'Promoted', 'Publicized', 'Reviewed', 'Operated', 'Controlled', 'Oversaw', 'Produced', 'Coordinated', 'Programmed', 'Organized', 'Executed', 'Planned', 'Orchestrated', 'Built', 'Designed', 'Created', 'Formed', 'Devised', 'Founded', 'Established', 'Initiated', 'Assembled', 'Implemented', 'Incorporated', 'Pioneered', 'Launched', 'Consolidated', 'Deducted', 'Conserved', 'Decreased', 'Reduced', 'Yielded', 'Diagnosed', 'Lessened', 'Evaluated', 'Analyzed', 'Interpreted', 'Assessed', 'Mapped', 'Investigated', 'Explored', 'Measured', 'Discovered', 'Qualified', 'Examined', 'Audited', 'Calculated', 'Quantified', 'Surveyed', 'Tested', 'Achieved', 'Boosted', 'Accelerated', 'Advanced', 'Expanded', 'Delivered', 'Generated', 'Gained', 'Enhanced', 'Improved', 'Amplified', 'Maximized', 'Stimulated', 'Sustained', 'Clarified', 'Centralized', 'Redesigned', 'Merged', 'Customized', 'Integrated', 'Converted', 'Refined', 'Replaced', 'Updated', 'Refocused', 'Upgraded', 'Reorganized', 'Restructured', 'Transformed', 'Volunteered', 'Remodeled', 'Simplified', 'Strengthened', 'Modernized', 'Adept', 'Proficient', 'Savvy', 'Primed', 'Prepared', 'Dexterous', 'Fluent', 'Working', 'on', 'a', 'task', 'Arranged', 'Compiled', 'Developed', 'Crafted', 'Undertook', 'Constructed', 'Formulated', 'Set', 'up']

    rep = 0
    for word in buzz:
        if word.lower() in text:
            rep += 1
    final_score = 0
    if(rep == 0):
        final_score += 5
    elif(rep == 1):
        final_score += 4 
    elif(rep == 2):
        final_score += 3 
    elif(rep == 3):
        final_score += 2 
    elif(rep == 4):
        final_score += 1 
    else:
        final_score += 0
    return final_score    

def extract_dates(text):
      matches1 = re.findall(r'\s20\d{2}\s', text)
      matches2 = re.findall(r'\s19\d{2}\s', text)
      matches3 = re.findall(r'\d{2}/\d{4}', text)
      matches4 = re.findall(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', text)
      matches5 = re.findall(r'\d{2}-\d{4}', text)
      matches6 = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)-\s+\d{4}', text)
      final_score = 0
      if(len(matches3) + len(matches4) + len(matches5) + len(matches6) > 0):
          final_score += 3
      if(len(matches1) + len(matches2) > 0):
          final_score += 2    
          
      return final_score

def extract_details(text):
    final_score = 0
    #links
    url_regex = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_regex, text)
    if(len(urls) > 0):
        final_score += 1
    else:
        final_score += 0    
        

    #phone number
    phone = re.findall(re.compile(r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
    m = []
    if phone:
        number = ''.join(phone[0])
        if len(number) > 10:
            l = '+' + number
            m.append(l)
        else:
            l = number
            m.append(l)

    if(len(m) > 0):
        final_score += 1
    else:
        final_score += 0        

    #emails
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", text)
    n = []
    if email:
        try:
            l = email[0].split()[0].strip(';')
            n.append(l)
        except IndexError:
            return None 
    if(len(n) > 0):
        final_score += 1
    else:
        final_score += 0        
        
    #name    
    name_regex = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
    name = [re.search(name_regex, text).group(0)]  
    if(len(name) > 0):
        final_score += 2
    else:
        final_score += 0  
    return final_score        

def personal_pronouns(text):
    tokens = nltk.word_tokenize(text)
    pattern = re.compile(r'^(he|him|his|she|her|hers|they|them|their|it|its)$', re.IGNORECASE)
    pronouns1 = [token for token in tokens if pattern.match(token)]
    pronouns = len(pronouns1)
    final_score = 0
    if(pronouns == 0):
        final_score += 5  
    elif(pronouns == 1):
        final_score += 4
    elif(pronouns == 2):
        final_score += 3    
    elif(pronouns == 3 ):
        final_score += 2  
    elif(pronouns == 4 ):
        final_score += 1  
    else:
        final_score += 0
    return final_score    

def passive_voices(text):
    doc = nlp(text)
    m1 = [sent.text for sent in doc.sents if any(token.dep_ == "nsubjpass" or token.dep_ == "auxpass" for token in sent)]
    m = len(m1)
    final_score = 0
    if(m == 0):
        final_score += 5
    elif(m == 1):
        final_score += 4 
    elif(m == 2):
        final_score += 3 
    elif(m == 3):
        final_score += 2 
    elif(m == 4):
        final_score += 1 
    else:
        final_score += 0
    return final_score    

#SECTIONS

def experience(text, text1):
    final_score = 0
    exp_count = 0
    if(text['experience'] != None):
        exp_count += 1
    else:    
        t1 = text1.find("WORK EXPERIENCE")
        t2 = text1.find("Work Experience")
        t3 = text1.find("Experience")
        t4 = text1.find("EXPERIENCE")
        if(t1 >= 0 or t2 >= 0 or t3 >= 0 or t4 >= 0):
            exp_count += 1

    pro_count = 0
    t1 = text1.find("Projects")
    t2 = text1.find("PROJECTS")
    t3 = text1.find("Achievements")
    t4 = text1.find("ACHIEVEMENTS")
    if(t1 >= 0 or t2 >= 0 or t3 >= 0 or t4 >= 0):
            pro_count += 1        

    if(exp_count == 0 and pro_count > 0):
        final_score += 7
    elif(exp_count > 0 and pro_count == 0):
        final_score += 7      
    elif(exp_count > 0 and pro_count > 0):
        final_score += 7
    else:
        final_score += 0        
    return final_score    

def education(text):
    edu_count = 0
    t1 = text.find("Education")
    t2 = text.find("EDUCATION")
    t3 = text.find("Qualifications")
    t4 = text.find("QUALIFICATIONS")
    if(t1 >= 0 or t2 >= 0 or t3 >= 0 or t4 >= 0):
            edu_count += 1
    final_score = 0        
    if(edu_count > 0):
        final_score += 7
    return final_score    

def summary(text):
    summ_count = 0
    t1 = text.find("SUMMARY")
    t2 = text.find("OBJECTIVE")
    t3 = text.find("Summary")
    t4 = text.find("Objective")
    t5 = text.find("Profile")
    t6 = text.find("PROFILE")
    if(t1 >= 0 or t2 >= 0 or t3 >= 0 or t4 >= 0 or t5 >= 0 or t6 >= 0):
            summ_count += 1
    final_score = 0        
    if(summ_count > 0):
        final_score += 6
    return final_score    

def skills_extract(text):
    nlp = spacy.load('en_core_web_sm')

    nlp_text = nlp(text)

    tokens = [token.text for token in nlp_text if not token.is_stop]
    data = pd.read_csv("skills.csv") 
    skills = list(data.columns.values)

    data1 = pd.read_csv("resumate_skills.csv") 
    skills1 = list(data1.columns.values)
    skills1 = list(map(lambda x:x.lower(), skills1))
  
    skillset = []
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)
    for token in nlp_text.noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
    for token in tokens:
        if token.lower() in skills1 and token.lower() not in skillset:
            skillset.append(token)
    for token in nlp_text.noun_chunks:
        token = token.text.lower().strip()
        if token in skills and token not in skillset:
            skillset.append(token)        
    ad = [i.capitalize() for i in set([i.lower() for i in skillset])]
    return 5

#display result

def print_text(score):
    if(score <= 50):
        txt = '''Your resume score is less than 50, 
                 it's important not to get discouraged. 
                 This simply means that there is room for improvement, 
                 and with a few simple changes, you can significantly 
                 increase your chances of landing a job.'''
    elif(score > 50 and score <= 70):
        txt = '''That's a good start! It means that your resume still needs improvement. 
                 With a few tweaks, you can increase your score and make your 
                 resume stand out to potential employers.'''   
    elif(score > 70 and score < 90):
        txt = '''Your resume is off to a great start! 
                 Your resume have a strong foundation and have included many of the key 
                 elements that employers and resume screening software look for. 
                 However, there is always room for improvement, 
                 and you can take your resume to the next level by making a few small tweaks.'''    
    elif(score >= 90):
        txt = '''Wow, congratulations! That's an excellent achievement. 
                 It means that your resume has many of the key elements 
                 that employers and resume screening software look for, 
                 and that you've done an outstanding job highlighting 
                 your skills and experiences.'''    

    return txt     

def print_rep_sen(text):
    lst = []
    sentences = re.split('[.!?]', text)
    counts = collections.defaultdict(int)
    for sentence in sentences:
        if sentence.strip() != '':
            counts[sentence.strip()] += 1        
    for sentence, count in counts.items():
        if count > 1:
            lst.append(sentence)
    return lst        

def print_rep_verbs(text):
    pattern = r'\b(\w+ing\s\w+)\b.*\b\1\b'
    matches = re.findall(pattern, text)
    return matches     

def print_weak_action(text):
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    pos_tags = nltk.pos_tag(words)
    weak_verbs = [word for word, pos in pos_tags if pos.startswith('VB') and word in weak_action_verbs]
    return weak_verbs

def res_len(text):
    m = len(text.split())
    return m

def print_filler(text):
    x = []
    superfluous_words = ['I am writing to apply for', 'Responsible for', 'Excellent communication skills', 'Detail-oriented', 
                     'Team player', 'Results-driven', 'Self-starter', 'Hardworking', 'Dynamic', 'Proactive', 'Highly motivated', 
                     'Innovative', 'Ability to work under pressure', 'Outside-the-box thinker', 'Creative problem solver', 
                     'Passionate', 'References available upon request', 'Utilized', 'Assisted with', 'Successfully']
    for word in superfluous_words:
        if word in text:
            x.append(word)
    return x           

def print_buzz(text):
    buzz = ['Managed', 'Influenced', 'Motivated', 'Guided', 'Supervised', 'Hired', 'Inspired', 'Facilitated', 'Enabled', 'Directed', 'Maintained', 'Cultivated', 'Trained', 'Taught', 'Aligned', 'Consulted', 'Advised', 'Educated', 'Advocated', 'Resolved', 'Informed', 'Coached', 'Negotiated', 'Partnered', 'Secured', 'Acquired', 'Forged', 'Completed', 'Attained', 'Awarded', 'Earned', 'Demonstrated', 'Exceeded', 'Reached', 'Targeted', 'Outperformed', 'Surpassed', 'Showcased', 'Succeeded', 'Conveyed', 'Defined', 'Authored', 'Critiqued', 'Corresponded', 'Composed', 'Documented', 'Counseled', 'Edited', 'Persuaded', 'Illustrated', 'Lobbied', 'Promoted', 'Publicized', 'Reviewed', 'Operated', 'Controlled', 'Oversaw', 'Produced', 'Coordinated', 'Programmed', 'Organized', 'Executed', 'Planned', 'Orchestrated', 'Built', 'Designed', 'Created', 'Formed', 'Devised', 'Founded', 'Established', 'Initiated', 'Assembled', 'Implemented', 'Incorporated', 'Pioneered', 'Launched', 'Consolidated', 'Deducted', 'Conserved', 'Decreased', 'Reduced', 'Yielded', 'Diagnosed', 'Lessened', 'Evaluated', 'Analyzed', 'Interpreted', 'Assessed', 'Mapped', 'Investigated', 'Explored', 'Measured', 'Discovered', 'Qualified', 'Examined', 'Audited', 'Calculated', 'Quantified', 'Surveyed', 'Tested', 'Achieved', 'Boosted', 'Accelerated', 'Advanced', 'Expanded', 'Delivered', 'Generated', 'Gained', 'Enhanced', 'Improved', 'Amplified', 'Maximized', 'Stimulated', 'Sustained', 'Clarified', 'Centralized', 'Redesigned', 'Merged', 'Customized', 'Integrated', 'Converted', 'Refined', 'Replaced', 'Updated', 'Refocused', 'Upgraded', 'Reorganized', 'Restructured', 'Transformed', 'Volunteered', 'Remodeled', 'Simplified', 'Strengthened', 'Modernized', 'Adept', 'Proficient', 'Savvy', 'Primed', 'Prepared', 'Dexterous', 'Fluent', 'Working', 'on', 'a', 'task', 'Arranged', 'Compiled', 'Developed', 'Crafted', 'Undertook', 'Constructed', 'Formulated', 'Set', 'up']
    rep = []
    for word in buzz:
        if word.lower() in text:
            rep.append(word)
    return rep

def print_details(text):
    url_regex = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_regex, text)
    return urls

def print_pronouns(text):
    tokens = nltk.word_tokenize(text)
    pattern = re.compile(r'^(he|him|his|she|her|hers|they|them|their|it|its)$', re.IGNORECASE)
    pronouns = [token for token in tokens if pattern.match(token)]
    return pronouns

def print_passive(text):
    doc = nlp(text)
    m = [sent.text for sent in doc.sents if any(token.dep_ == "nsubjpass" or token.dep_ == "auxpass" for token in sent)]
    return m        

