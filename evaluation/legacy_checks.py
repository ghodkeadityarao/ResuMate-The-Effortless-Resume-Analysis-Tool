"""Three checks from the original extraction_score.py, copied unchanged, so the new checks can be compared with them.

The original skills check ended with `return 5` whatever the resume contained, so it is not reproduced here.
"""
import re


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
