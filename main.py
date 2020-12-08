import random
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from config import  BOT_CONFIG



X_texts = []  # реплики
y = []  # их классы

for intent, intent_data in BOT_CONFIG['intents'].items():
    for example in intent_data['examples']:
        X_texts.append(example)
        y.append(intent)


vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
X = vectorizer.fit_transform(X_texts)
clf = LinearSVC().fit(X, y)


def get_intent(question):
    question_vector = vectorizer.transform([question])
    intent = clf.predict(question_vector)[0]

    examples = BOT_CONFIG['intents'][intent]['examples']
    for example in examples:
        dist = nltk.edit_distance(question, example)
        dist_percentage = dist / len(example)
        if dist_percentage < 0.4:
            return intent


def get_answer_by_intent(intent):
    if intent in BOT_CONFIG['intents']:
        phrases = BOT_CONFIG['intents'][intent]['responses']
        return random.choice(phrases)


def filter_text(text):
    text = text.lower()
    text = [c for c in text if c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefjhijklmnopqrstuvwxyz- ']
    text = ''.join(text)
    return text

with open('dialogues.txt', encoding='utf-8') as f:
    content = f.read()
dialogues = [dialogue_line.split('\n') for dialogue_line in content.split('\n\n')]

questions = set()
qa_dataset = []  # [[q, a], ...]

for replicas in dialogues:
    if len(replicas) < 2:
        continue

    question, answer = replicas[:2]
    question = filter_text(question[2:])
    answer = answer[2:]

    if question and question not in questions:
        questions.add(question)
        qa_dataset.append([question, answer])

qa_by_word_dataset = {}  # {'word': [[q, a], ...]}
for question, answer in qa_dataset:
    words = question.split(' ')
    for word in words:
        if word not in qa_by_word_dataset:
            qa_by_word_dataset[word] = []
        qa_by_word_dataset[word].append((question, answer))

qa_by_word_dataset_filtered = {word: qa_list
                               for word, qa_list in qa_by_word_dataset.items()
                               if len(qa_list) < 1000}


def generate_answer_by_text(text):
    text = filter_text(text)
    words = text.split(' ')
    qa = []
    for word in words:
        if word in qa_by_word_dataset_filtered:
            qa += qa_by_word_dataset_filtered[word]
    qa = list(set(qa))[:1000]

    results = []
    for question, answer in qa:
        dist = nltk.edit_distance(question, text)
        dist_percentage = dist / len(question)
        results.append([dist_percentage, question, answer])

    if results:
        dist_percentage, question, answer = min(results, key=lambda pair: pair[0])
        if dist_percentage < 0.3:
            return answer

def get_failure_phrase():
    phrases = BOT_CONFIG['failure_phrases']
    return random.choice(phrases)

stats = [0, 0, 0]


def bot(question):
    # NLU
    intent = get_intent(question)

    # Получение ответа

    # Ищем готовый ответ
    if intent:
        answer = get_answer_by_intent(intent)
        if answer:
            stats[0] += 1
            return answer

    # Генеруем подходящий по контексту ответ
    answer = generate_answer_by_text(question)
    if answer:
        stats[1] += 1
        return answer

    # Используем заглушку
    stats[2] += 1
    answer = get_failure_phrase()
    return answer

question = None

while question not in ['exit', 'выход']:
    question = input()
    answer = bot(question)
    print(answer, stats)
