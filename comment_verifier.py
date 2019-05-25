import csv
import pandas
import re
import string
import math

def num_of_numbers(inputString):
    rslt = re.findall(r'\d+', inputString)
    return len(rslt)

def has_mny_sign(text):
    if "تومن" in text:
        return True
    elif "تومان" in text:
        return True
    elif "ریال" in text:
        return True
    elif "تومنی" in text:
        return True
    elif "ریالی" in text:
        return True
    else:
        return False

def set_time(time):
    splitted_time = time.split(':')
    hour = int(splitted_time[0].split(' ')[-1])
    if (hour <= 12 and hour > 6):
        return 'morning'
    elif (hour <= 18 and hour > 12):
        return 'afternoon'
    elif (hour <= 24 and hour > 18):
        return 'night'
    elif (hour <= 6 and hour >= 0):
        return 'midnight'

def normalize_text(data,index):
    table = str.maketrans({key: " " for key in string.punctuation})
    table2 = str.maketrans({key: " " for key in "#$%&^@*~å£€‰ÌÛ÷-_¬،:؟؛"})
    words = {"از", "تا", "به", "که", "و", "با", "بی", "ولی", "برای", "بر", "هم", "یا", "را", "رو", "این", "ها", "اینا",
             "ا", "ب", "پ", "ت", "ث", "چ", "چ", "ح", "خ", "د", "ذ", "ر", "ز", "ژ"
        , "س", "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ک", "گ", "ل", "م", "ن", "و", "ه", "ی"}
    money_words = {"تومن","تومان","ریال","تومنی","ریالی"}
    for row_number in range(0,data.shape[0]):
        new_value = str(data.iloc[row_number,index])
        num_of_digits = num_of_numbers(new_value)
        has_money_signs = has_mny_sign(new_value)
        new_value = new_value.translate(table2)
        new_value = re.sub(r'\d+', '', new_value)
        new_value = new_value.strip(' ')
        new_value = new_value.strip('\n')
        new_value = new_value.translate(table)
        tokens = new_value.split()
        new_value = [i for i in tokens if not i in words]
        new_value = [i for i in new_value if not i in money_words]
        for word in new_value:
            if len(word) == 1:
                new_value.remove(word)
        for i in range(0,len(new_value)):
            if "www" in new_value[i]:
                new_value[i] = "www"
        if has_money_signs:
             new_value.append("$")
        if num_of_digits > 0 :
             new_value.append(str(num_of_digits))

        try:
            if(len(new_value)>1):
                data.iloc[row_number,index] = new_value
            else:
                new_value.append('')
                data.iloc[row_number, index] = new_value
        except:
            if(index == 0):
                data.at[row_number, 'comment'] = new_value
            elif(index == 1):
                data.at[row_number,'title'] = new_value

def calculate_posterior(data,tlp,clp,twp,cwp,lp,tp,cp):
    Lposterior = math.log(cp,10)
    for word in data['comment']:
        if(word == ''):
            continue
        if (word.isdigit() == True):
            Lposterior += math.log((int(word) * float(cwp['1'])),10)
        elif word in cwp:
            Lposterior += math.log(float(cwp[word]),10)
        else:
            Lposterior += math.log(float(cwp['0']),10)
    for word in data['title']:
        if(word == ''):
            continue
        if (word.isdigit() == True):
            Lposterior += math.log((int(word) * float(twp['1'])),10)
        elif word in twp:
            Lposterior += math.log(float(twp[word]),10)
        else:
            Lposterior += math.log(float(twp['0']),10)

    comment_size = int(data['# of comment words'] / 10) * 10
    comment_size = (comment_size,comment_size+10)
    title_size = int(data['# of title words'] / 10) * 10
    title_size = (title_size,title_size+10)
    if(str(comment_size) in clp):
        Lposterior += math.log(float(clp[str(comment_size)]),10)
    else:
        Lposterior += math.log(float(clp['none']),10)
    if(str(title_size) in tlp):
        Lposterior += math.log(float(tlp[str(title_size)]),10)
    else:
        Lposterior += math.log(float(tlp['none']),10)
    Lposterior += math.log(float(tp[data['time']]),10)
    likes = data['likes']
    if str(likes) in lp:
        Lposterior += math.log(float(lp[str(likes)]),10)
    else:
        Lposterior += math.log(float(lp['-1']),10)
    return Lposterior


def calculate_correctness(data):
    data['correctness'] = (data['verification_status'] == data['estimated class'])
    num_of_rejected = len(data.groupby(['verification_status']).groups['rejected'])
    correct_detected_rejects = len(data.loc[(data['verification_status'] == 'rejected') & (data['correctness'] == True)])
    detected_rejects = len(data.loc[data['estimated class'] == 'rejected'])
    Accuracy = data['correctness'].sum() / data.shape[0]
    recall = correct_detected_rejects/num_of_rejected
    precision = correct_detected_rejects/detected_rejects
    message = "accuracy is : " + str(Accuracy) + "\nrecall is " + str(recall) + "\nprecision is " + str(precision)
    print(message)

def calculate_set_probibility(data,reject_title_length_probabilities,reject_comment_length_probabilities,reject_title_word_probabilities,
                          reject_comment_word_probabilities,reject_likes_probabilities,reject_time_probabilities,
                            verified_title_length_probabilities,verified_comment_length_probabilities,verified_title_word_probabilities,
                                verified_comment_word_probabilities,verified_likes_probabilities,verified_time_probabilities,class_probabilities):
    data['estimated class'] = ""
    for row_number in range(0, data.shape[0]):
        reject_posterior = calculate_posterior(data.iloc[row_number,],reject_title_length_probabilities,reject_comment_length_probabilities,reject_title_word_probabilities,
                          reject_comment_word_probabilities,reject_likes_probabilities,reject_time_probabilities,float(class_probabilities['rejected']))
        verified_posterior = calculate_posterior(data.iloc[row_number,], verified_title_length_probabilities,verified_comment_length_probabilities,verified_title_word_probabilities,
                                verified_comment_word_probabilities,verified_likes_probabilities,verified_time_probabilities,float(class_probabilities['verified']))
        if (reject_posterior > verified_posterior):
            data.iloc[row_number, -1] = 'rejected'
        elif (reject_posterior <= verified_posterior):
            data.iloc[row_number, -1] = 'verified'



pandas.options.mode.chained_assignment = None
with open('reject_comment_length_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    reject_comment_length_probabilities = {rows[0]:rows[1] for rows in reader}
with open('verified_comment_length_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    verified_comment_length_probabilities = {rows[0]:rows[1] for rows in reader}

with open('verified_title_length_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    verified_title_length_probabilities = {rows[0]:rows[1] for rows in reader}
with open('reject_title_length_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    reject_title_length_probabilities = {rows[0]:rows[1] for rows in reader}
with open('verified_comment_word_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    verified_comment_word_probabilities = {rows[0]:rows[1] for rows in reader}
with open('reject_comment_word_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    reject_comment_word_probabilities = {rows[0]:rows[1] for rows in reader}
with open('reject_title_word_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    reject_title_word_probabilities = {rows[0]:rows[1] for rows in reader}
with open('verified_title_word_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    verified_title_word_probabilities = {rows[0]:rows[1] for rows in reader}
with open('verified_likes_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    verified_likes_probabilities = {rows[0]:rows[1] for rows in reader}
with open('reject_likes_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    reject_likes_probabilities = {rows[0]:rows[1] for rows in reader}
with open('verified_time_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    verified_time_probabilities = {rows[0]:rows[1] for rows in reader}
with open('reject_time_probabilities.csv', mode='r') as infile:
    reader = csv.reader(infile)
    reject_time_probabilities = {rows[0]:rows[1] for rows in reader}
with open('class_prob.csv', mode='r') as infile:
    reader = csv.reader(infile)
    class_probabilities = {rows[0]:rows[1] for rows in reader}

fileName = input('write your file name.(ex:comments.csv)')
comments = pandas.read_csv(fileName)
comments.columns = comments.columns.str.replace(' ', '')
comments['# of comment words'] = comments['comment'].apply(len)
comments['# of title words'] = comments['title'].apply(len)
comments['time'] = comments['created_at'].apply(set_time)
normalize_text(comments,0)
normalize_text(comments,1)
calculate_set_probibility(comments,reject_title_length_probabilities,reject_comment_length_probabilities,reject_title_word_probabilities,
                          reject_comment_word_probabilities,reject_likes_probabilities,reject_time_probabilities,
                            verified_title_length_probabilities,verified_comment_length_probabilities,verified_title_word_probabilities,
                                verified_comment_word_probabilities,verified_likes_probabilities,verified_time_probabilities,class_probabilities)


anwr = input('does your file include verification_status and do you want to calculate correctness?(y/n)')
if(anwr == 'y'):
    calculate_correctness(comments)
print("classifying result is saved in output.csv")
header = ["estimated class"]
comments.to_csv('output.csv', columns = header, index = True, header = ['estimated_class'])
