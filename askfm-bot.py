import threading, time, mechanize, cookielib, random

#Libs needed
#Mechanize - http://wwwsearch.sourceforge.net/mechanize/

__author__ = 'TJ Aditya'
__version__ = '0.4'

#Method Shorthands
Thread = threading.Thread
sleep = time.sleep

#Get a new browser object
def new_browser():
    # Browser
    br = mechanize.Browser()
      
    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
      
    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
      
    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
      
    # User-Agent (this is cheating, ok?)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    return br

#Globals
USER = '<Your ask.fm username>'
PASS = '<Your ask.fm password>'
qlog = 'QTHREAD LOG: '
alog = 'ATHREAD LOG: '
tab = "\t"
delay = 30
users = {}
answers = set()
is_anon = False
q = []
f = open('q.txt', 'r')
for question in f:
    q.append(question)

#Storing currently answered
br = new_browser()
br.open('http://ask.fm/login')
br.select_form(nr=0)
br.form['login'] = USER
br.form['password'] = PASS
br.submit()
  
br.open('http://ask.fm/account/notifications/answers/latest')
lines = br.response().readlines()
hrefs = lines[0].split('href=\\"')
for m in range(1, len(hrefs)):
    answers.add(hrefs[m][:hrefs[m].find('\\')])

class QuestionPoster(Thread):
    def __init__(self, refresh):
        Thread.__init__(self)
        self.refresh = refresh
    def run(self):
        print qlog + 'Question thread started'
        br = new_browser()
        #Open Login Page
        br.open('http://ask.fm/login')
        br.select_form(nr=0)
        br.form['login'] = USER
        br.form['password'] = PASS
        br.submit()
        print qlog + 'Login successful'
        print qlog + 'Fetching stream'
        #Refreshing Stream
        for i in range(self.refresh):
            #Open Stream
            br.open('http://ask.fm/account/stream')
            lines = br.response().readlines()
            for line in lines:
                if 'str_profile_avatar' in line:
                    tmp = line.split('href="')[1]
                    user = tmp[:tmp.find('"')]
                    #print user
                    if user not in users:
                        #Open User Page
                        br.open('http://ask.fm' + user)
                        #Select Answer Form
                        br.select_form(nr=1)
                        #Generate Random qid
                        qid = random.randint(0, len(q))
                        #Set form options
                        br.form['question[question_text]'] = q[qid]
                        control = br.find_control(type="checkbox").items[0]
                        if control.disabled == False:
                            control.selected = is_anon
                        #Submit form
                        br.submit()
                        print   '\n -------------------- '
                        print   '|QUESTION            |'
                        print   ' -------------------- '
                        print '|Asked user: %s a question: %s' % (user, q[qid])
                        #print '--------------------------------------------------'
                        users[user] = q[qid]
                    sleep(10)
        
class AnswerScraper(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print alog + 'Answer thread started'
        f = open('askans.txt', 'wb')
        br = new_browser()
        #Open Login Page
        br.open('http://ask.fm/login')
        br.select_form(nr=0)
        br.form['login'] = USER
        br.form['password'] = PASS
        br.submit()
        print alog + 'Login successful'
        print alog + 'Fetching latest answers'
        while True:
            #Scrape Answers  
            br.open('http://ask.fm/account/notifications/answers/latest')
            lines = br.response().readlines()
            #print lines[0]
            hrefs = lines[0].split('href=\\"')
            #print hrefs
            for m in range(1, len(hrefs)):
                que = hrefs[m][:hrefs[m].find('\\')]
                if que in answers:
                    break
                else:
                    answers.add(que)
                    #print 'Opening question: %s' % que
                    br.open('http://ask.fm' + que)
                    ql = br.response().readlines()
                    #print ql
                    flag = False
                    index = -1
                    for i in range(0, len(ql)):
                        if 'questionBox' in ql[i]:
                            ques = ''
                            ans = ''
                            us = '/' + que[1:].split('/')[0]
                            for j in range(i + 1, len(ql)):
                                #print ql[j]
                                if USER in ql[j]:
                                    qll = ql[j].split('span')[2]
                                    ques = qll[qll.find('>')+1:qll.rfind('<')]
                                    #print ques
                                if 'ltr' in ql[j] and 'answer' in ql[j]:
                                    for k in range(j + 1, len(ql)):
                                        #print ql[k]
                                        if '</div>' in ql[k]:
                                            flag = True
                                            break
                                        ans = ans + ql[k].strip()
                                    #print 'User %s has answered to your question: %s. ANS: %s' % (us, ques, ans.strip())
                                    print   '\n -------------------- '
                                    print   '|ANSWER              |'
                                    print   ' -------------------- '
                                    print  '|User: %s' % us
                                    print  '|Question: %s' % ques
                                    print  '|Answer: %s' % ans
                                    #print '--------------------------------------------------'
                                    f.write('User: %s\n' % us)
                                    f.write('Question: %s\n' % ques)
                                    f.write('Answer: %s\n' % ans)
                                    f.write('--------------------------------------------------\n')
                                    f.flush()
                                if flag:
                                    break
                        if flag:
                            break
                                
            #print alog + 'Answer thread sleeping'
            sleep(30)




tq = QuestionPoster(1)
ta = AnswerScraper()
tq.start()
ta.start()

