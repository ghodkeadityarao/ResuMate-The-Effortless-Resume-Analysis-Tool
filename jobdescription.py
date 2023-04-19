import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from pdfminer.high_level import extract_text
import re
import joblib
from csv import writer

mapping = {6: 'Data Science',
 12: 'HR',
 0: 'Advocate',
 1: 'Arts',
 24: 'Web Designing',
 16: 'Mechanical Engineer',
 22: 'Sales',
 14: 'Health and fitness',
 5: 'Civil Engineer',
 15: 'Java Developer',
 4: 'Business Analyst',
 21: 'SAP Developer',
 2: 'Automation Testing',
 11: 'Electrical Engineering',
 18: 'Operations Manager',
 20: 'Python Developer',
 8: 'DevOps Engineer',
 17: 'Network Security Engineer',
 19: 'PMO',
 7: 'Database',
 13: 'Hadoop',
 10: 'ETL Developer',
 9: 'DotNet Developer',
 3: 'Blockchain',
 23: 'Testing'}

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def cleanResume(resumeText):
    resumeText = re.sub('http\S+\s*', ' ', resumeText)  # remove URLs
    resumeText = re.sub('#\S+', '', resumeText)  # remove hashtags
    resumeText = re.sub('@\S+', '  ', resumeText)  # remove mentions
    resumeText = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', resumeText)  # remove punctuations
    resumeText = re.sub(r'[^\x00-\x7f]',r' ', resumeText) 
    resumeText = re.sub('\s+', ' ', resumeText)  # remove extra whitespace
    return resumeText

def getJob(path):
    # load trained model and preprocessors
    model = joblib.load('knn_model.joblib')
    vectorizer = TfidfVectorizer(sublinear_tf=True, stop_words='english', max_features=1500)
    vectorizer.fit(pd.read_csv("D:\\Semester 4\\210 DTI\\UpdatedResumeDataSet.csv")['Resume'].apply(lambda x: cleanResume(x)))

    # load real-world data to test on
    data = pd.read_csv("new_resume.csv")
    resumeText = extract_text_from_pdf(path)
    data.loc[len(data.index)] = [str(resumeText)]
    resumes = data['Resume'].apply(lambda x: cleanResume(x))

    # preprocess new resumes and encode target labels
    resumes_features = vectorizer.transform(resumes)
    le = LabelEncoder()

    # make predictions on new data
    predictions = model.predict(resumes_features)
    value = predictions[-1]
    # print("x=", value)

    job = mapping[value]
    return job
