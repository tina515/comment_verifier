import pandas
import re
import string
import csv
from collections import Counter

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



def normalize_text(data,index):
    table = str.maketrans({key: " " for key in string.punctuation})
    table2 = str.maketrans({key: " " for key in "#$%&^@*~å£€‰ÌÛ÷-_¬،:؟؛"})
    words = {"از","تا","به","که","و","با","بی","ولی","برای","بر","هم","یا","را","رو","این","ها","اینا","ا","ب","پ","ت","ث","چ","چ","ح","خ","د","ذ","ر","ز","ژ"
             ,"س","ش","ص","ض","ط","ظ","ع","غ","ف","ق","ک","گ","ل","م","ن","و","ه","ی"}
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


def set_time(time):
        splitted_time = time.split(':')
        hour = int(splitted_time[0].split(' ')[-1])
        if(hour<=12 and hour>6):
            return 'morning'
        elif(hour<=18 and hour>12):
            return 'afternoon'
        elif(hour <= 24 and hour>18):
            return 'night'
        elif(hour <= 6 and hour>=0):
            return 'midnight'


def analyze_length(data,rejected_length_probabilities,verified_length_probabilities,index):
    grouped = data.groupby(['verification_status'])
    num_of_verified = len(grouped.groups['verified'])
    num_of_rejected = len(grouped.groups['rejected'])
    num_of_words = 0
    for row_number in range(0, data.shape[0]):
        num_of_words = data.iloc[row_number,index]
        group = int(num_of_words/10) * 10
        if(data.iloc[row_number,3] == 'verified'):
            if((group,group + 10) in verified_length_probabilities):
                verified_length_probabilities[(group,group + 10)] = verified_length_probabilities[(group,group + 10)] + 1
            else:
                verified_length_probabilities[(group, group + 10)] = 1
        else:
            if((group,group + 10) in rejected_length_probabilities):
                rejected_length_probabilities[(group,group + 10)] = rejected_length_probabilities[(group,group + 10)] + 1
            else:
                rejected_length_probabilities[(group, group + 10)] = 1
    for key in rejected_length_probabilities:
        rejected_length_probabilities[key] = (rejected_length_probabilities[key]+ 1)/(num_of_rejected + len(rejected_length_probabilities))
    for key in verified_length_probabilities:
        verified_length_probabilities[key] = (verified_length_probabilities[key]+1)/(num_of_verified + len(verified_length_probabilities))
    verified_length_probabilities['none'] = 1/num_of_verified
    rejected_length_probabilities['none'] = 1/num_of_rejected

def analyze_words(data,rwp,vwp,title_or_comment):
    word_list = []
    title = '# of ' + title_or_comment+ ' words'
    total_words = data.groupby(['verification_status'])[title].agg('sum')
    rejected_total_words = total_words['rejected']
    verified_total_words = total_words['verified']
    unique_verified_words = 0
    unique_rejected_words = 0
    rwp['1'] = 0
    vwp['1'] = 0
    index = -1
    if(title_or_comment == 'comment'):
        index = 0
    elif(title_or_comment == 'title'):
        index = 1
    for row_number in range(0, data.shape[0]):
        word_list = data.iloc[row_number,index]
        if(data.iloc[row_number,3] == 'rejected'):
            for word in word_list:
                if (word.isdigit() == True):
                    rwp['1'] += int(word)
                    rejected_total_words += (int(word) - 1)
                    continue
                if word in rwp:
                    rwp[word] = rwp[word] + 1
                else:
                    rwp[word] = 1
                    unique_rejected_words += 1
        else:
            for word in word_list:
                if (word.isdigit() == True):
                    verified_total_words += (int(word) -1)
                    vwp['1'] += int(word)
                    continue
                if word in vwp:
                    vwp[word] = vwp[word] + 1
                else:
                    vwp[word] = 1
                    unique_verified_words += 1
    rwp.pop("", None)
    vwp.pop("", None)
    for key in rwp:
        rwp[key] = (rwp[key] + 1)/(rejected_total_words + unique_rejected_words)
    for key in  vwp:
        vwp[key] = (vwp[key] + 1)/(verified_total_words + unique_verified_words)
    rwp['0'] = (1)/(rejected_total_words + unique_rejected_words)
    vwp['0'] = (1)/(verified_total_words + unique_verified_words)

def analyze_time(data,reject_time_probabilities,verified_time_probabilities):
    grouped = data.groupby(['verification_status'])
    num_of_verified = len(grouped.groups['verified'])
    num_of_rejected = len(grouped.groups['rejected'])
    for row_number in range(0, data.shape[0]):
        time = data.iloc[row_number, 8]
        if (data.iloc[row_number, 3] == 'verified'):
            if (time in verified_time_probabilities):
                verified_time_probabilities[time] = verified_time_probabilities[time] + 1
            else:
                verified_time_probabilities[time] = 1
        else:
            if (time in reject_time_probabilities):
                reject_time_probabilities[time] = reject_time_probabilities[time] + 1
            else:
                reject_time_probabilities[time] = 1

    for key in reject_time_probabilities:
        reject_time_probabilities[key] = (reject_time_probabilities[key]) / num_of_rejected
    for key in verified_time_probabilities:
        verified_time_probabilities[key] = (verified_time_probabilities[key] )/ num_of_verified


def analyze_likes(data,reject_likes_probabilities,verified_likes_probabilities):
    grouped = data.groupby(['verification_status'])
    num_of_verified = len(grouped.groups['verified'])
    num_of_rejected = len(grouped.groups['rejected'])
    for row_number in range(0, data.shape[0]):
        likes = data.iloc[row_number, 4]
        if (data.iloc[row_number, 3] == 'verified'):
            if (likes in verified_likes_probabilities):
                verified_likes_probabilities[likes] = verified_likes_probabilities[likes] + 1
            else:
                verified_likes_probabilities[likes] = 1
        else:
            if (likes in reject_likes_probabilities):
                reject_likes_probabilities[likes] = reject_likes_probabilities[likes] + 1
            else:
                reject_likes_probabilities[likes] = 1

    for key in reject_likes_probabilities:
        reject_likes_probabilities[key] = (reject_likes_probabilities[key] + 1) / (num_of_rejected + len(reject_likes_probabilities))
    for key in verified_likes_probabilities:
        verified_likes_probabilities[key] = (verified_likes_probabilities[key] + 1)/ (num_of_verified + len(verified_likes_probabilities))
    verified_likes_probabilities['-1'] = 1 / num_of_verified
    reject_likes_probabilities['-1'] = 1 / num_of_rejected



pandas.options.mode.chained_assignment = None
comments = pandas.read_csv('comments.csv')
comments.columns = comments.columns.str.replace(' ', '')
comments['# of comment words'] = comments['comment'].apply(len)
comments['# of title words'] = comments['title'].apply(len)
comments['time'] = comments['created_at'].apply(set_time)
normalize_text(comments,0)
normalize_text(comments,1)
learn_data_size = int(0.9 * comments.shape[0])
learn_data = comments[ :learn_data_size]
overfit_data = comments[learn_data_size: ]
num_of_rejected = len(learn_data.groupby(['verification_status']).groups['rejected'])
num_of_verified = learn_data.shape[0] - num_of_rejected
reject_probability = num_of_rejected/learn_data.shape[0]
verify_probability = num_of_verified/learn_data.shape[0]
class_probability = {}
class_probability['rejected'] = reject_probability
class_probability['verified'] = verify_probability
reject_comment_length_probabilities = {}
verified_comment_length_probabilities = {}
reject_title_length_probabilities = {}
verified_title_length_probabilities = {}
verified_comment_word_probabilities = {}
reject_comment_word_probabilities = {}
verified_title_word_probabilities = {}
reject_title_word_probabilities = {}
verified_likes_probabilities = {}
reject_likes_probabilities = {}
verified_time_probabilities = {}
reject_time_probabilities = {}
analyze_length(learn_data,reject_comment_length_probabilities,verified_comment_length_probabilities,6)
analyze_length(learn_data,reject_title_length_probabilities,verified_title_length_probabilities,7)
analyze_words(learn_data,reject_title_word_probabilities,verified_title_word_probabilities,'title')
analyze_words(learn_data,reject_comment_word_probabilities,verified_comment_word_probabilities,'comment')
zcvp = verified_comment_word_probabilities['0']
zcrp = reject_comment_word_probabilities['0']
ztvp = verified_title_word_probabilities['0']
ztrp = reject_title_word_probabilities['0']
verified_title_word_probabilities = dict(Counter(verified_title_word_probabilities).most_common(2000))
reject_title_word_probabilities = dict(Counter(reject_title_word_probabilities).most_common(2000))
verified_comment_word_probabilities = dict(Counter(verified_comment_word_probabilities).most_common(5000))
reject_comment_word_probabilities = dict(Counter(reject_comment_word_probabilities).most_common(5000))
verified_title_word_probabilities['0'] = ztvp
verified_comment_word_probabilities['0'] = zcvp
reject_title_word_probabilities['0'] = ztrp
reject_comment_word_probabilities['0'] = zcrp
factor = 1.0 / sum(reject_comment_word_probabilities.values())
for k in reject_comment_word_probabilities:
    reject_comment_word_probabilities[k] = reject_comment_word_probabilities[k] * factor
factor = 1.0 / sum(verified_comment_word_probabilities.values())
for k in verified_comment_word_probabilities:
     verified_comment_word_probabilities[k] = verified_comment_word_probabilities[k] * factor
factor = 1.0 / sum(verified_title_word_probabilities.values())
for k in verified_title_word_probabilities:
     verified_title_word_probabilities[k] = verified_title_word_probabilities[k] * factor

factor = 1.0 / sum(reject_title_word_probabilities.values())
for k in reject_title_word_probabilities:
     reject_title_word_probabilities[k] = reject_title_word_probabilities[k] * factor
analyze_time(learn_data,reject_time_probabilities,verified_time_probabilities)
analyze_likes(learn_data,reject_likes_probabilities,verified_likes_probabilities)

w = csv.writer(open("reject_comment_length_probabilities.csv", "w"))
for key, val in reject_comment_length_probabilities.items():
    w.writerow([key, val])
w = csv.writer(open("verified_comment_length_probabilities.csv", "w"))
for key, val in verified_comment_length_probabilities.items():
    w.writerow([key, val])
w = csv.writer(open("reject_title_length_probabilities.csv", "w"))
for key, val in reject_title_length_probabilities.items():
    w.writerow([key, val])
w = csv.writer(open("verified_title_length_probabilities.csv", "w"))
for key, val in verified_title_length_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("verified_comment_word_probabilities.csv", "w"))
for key, val in verified_comment_word_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("reject_comment_word_probabilities.csv", "w"))
for key, val in reject_comment_word_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("verified_title_word_probabilities.csv", "w"))
for key, val in verified_title_word_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("reject_title_word_probabilities.csv", "w"))
for key, val in reject_title_word_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("verified_likes_probabilities.csv", "w"))
for key, val in verified_likes_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("reject_likes_probabilities.csv", "w"))
for key, val in reject_likes_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("verified_time_probabilities.csv", "w"))
for key, val in verified_time_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("reject_time_probabilities.csv", "w"))
for key, val in reject_time_probabilities.items():
    w.writerow([key, val])

w = csv.writer(open("class_prob.csv", "w"))
for key, val in class_probability.items():
    w.writerow([key, val])